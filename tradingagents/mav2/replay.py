"""Offline replay of a registered run: recompute its outputs and compare them with the stored ones.

Each completed runner in ``scripts/`` has the same shape: ``prepare(read, ...)`` loads and checks every registered
input (and rebuilds every agent table from the call caches), one outcome join reads the forward returns or targets,
and ``finalize(...)`` computes the outputs and the verdict. The replay calls those pinned functions unchanged and
repeats only the short glue between them, with three differences from the run itself:

* no ``ResearchRun`` claim is made and nothing is written into ``research_runs/``;
* every registered input is read through its sha256 in the claim, as ``ResearchRun.read_input`` does;
* no model is called. Every agent answer comes from the registered call caches; a missing answer is an error.

The outcome join covers only the development window already joined by the run (2022-2024); no sealed window is read.
A replay therefore reproduces a verdict, it does not re-test the hypothesis.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import math
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tradingagents.mav2.registry import ROOT, Run, get

# outputs that depend on the process rather than on the inputs (spend tallies, caps) are not compared
NOT_COMPARED: dict[str, set[str]] = {"V1b": {"cost.json"}}


class ReplayError(RuntimeError):
    pass


def _runner(run: Run):
    if run.runner is None:
        raise ReplayError(f"{run.label} has no runner to replay")
    for p in (str(ROOT / "scripts"), str(ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    return importlib.import_module(run.runner)


def registered_reader(run: Run, root: Path = ROOT) -> Callable[[str], bytes]:
    """``read(name)`` over the inputs pinned in the claim; a byte change raises."""
    inputs = run.claim(root)["experiment"]["inputs"]

    def read(name: str) -> bytes:
        if name not in inputs:
            raise ReplayError(f"unregistered input {name!r}")
        path = Path(root) / inputs[name]["path"]
        if not path.is_file():
            raise ReplayError(f"input {name!r} absent: {inputs[name]['path']}")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != inputs[name]["sha256"]:
            raise ReplayError(f"input {name!r} differs from the registered bytes: {inputs[name]['path']}")
        return data

    return read


def missing_inputs(run: Run, root: Path = ROOT) -> list[str]:
    """Registered input files that are not present (data is not versioned; it is synced separately)."""
    inputs = run.claim(root)["experiment"]["inputs"]
    return sorted(i["path"] for i in inputs.values() if not (Path(root) / i["path"]).is_file())


# --- per-run glue, mirroring the ``with ResearchRun.start(...)`` block of each runner -----------------------------

def _v1b(run: Run, root: Path) -> dict:
    import pandas as pd

    m = _runner(run)
    from tradingagents.agents_v2.charter1b import (
        BOOK_KEYS,
        asset_rows,
        finalize,
        load_cached_week,
    )
    from tradingagents.agents_v2.portfolio_eval import realized_funding
    from tradingagents.dossier.quant_forecast import forward_returns

    stored_cost = json.loads((run.outputs(root) / "cost.json").read_text())
    ctx = m.prepare(registered_reader(run, root), root, 0.0)
    by_day, runs_dir, frozen = ctx["by_day"], ctx["runs_dir"], ctx["frozen"]
    new_weeks = stored_cost["new_weeks"]
    rows, books, completed = [], {name: {} for name in BOOK_KEYS}, []
    for day in sorted(set(frozen) | set(new_weeks), reverse=True):
        if day in frozen:
            out = ctx["frozen_weeks"][day]
        else:   # a week the run itself called; its answers are in the same per-asset cache
            if m._week_digest(runs_dir / day) != new_weeks[day]["cache_digest"]:
                raise ReplayError(f"V1b week {day}: cache differs from the digest recorded by the run")
            out = load_cached_week(day, by_day[day], runs_dir, ctx["config"])
        rows += asset_rows(day, out["results"], by_day[day])
        for name, key in BOOK_KEYS.items():
            books[name][pd.Timestamp(day, tz="UTC")] = out["portfolio"][key]
        completed.append(day)
    fridays = [pd.Timestamp(day, tz="UTC") for day in sorted(completed)]
    symbols = sorted({r["symbol"] for r in rows})
    fwd = forward_returns(symbols, fridays, klines_dir=ctx["klines_dir"])
    funding = realized_funding(symbols, fridays, funding_dir=ctx["funding_dir"])
    weeks = {"completed": sorted(completed), "n_completed": len(completed), "n_frozen": len(frozen), "n_new": len(new_weeks),
             "n_manifested": len(by_day), "truncated_at": stored_cost["truncated_at"]}
    return finalize(rows, books, fwd, funding, ctx["cards"], ctx["quant"], ctx["flags"], weeks)


def _experiment(run: Run, root: Path) -> dict:
    claim = run.claim(root)
    registration = json.loads((Path(root) / claim["registration"]).read_text())
    return registration["experiments"][claim["experiment_id"]]


def _v2(run: Run, root: Path) -> dict:
    m = _runner(run)
    ctx = m.prepare(registered_reader(run, root), root, _experiment(run, root), rehearsal=False)
    fwd = m.forward_returns(ctx["symbols"], ctx["fridays"], klines_dir=ctx["klines_dir"])
    funding = m.realized_funding(ctx["symbols"], ctx["fridays"], funding_dir=ctx["funding_dir"])
    return m.charter2.finalize(ctx["top"], ctx["feats"], ctx["records"], fwd, funding, ctx["quant"], ctx["flags"],
                               extraction=ctx["extraction"])


def _v3(run: Run, root: Path) -> dict:
    m = _runner(run)
    ctx = m.prepare(registered_reader(run, root), root, _experiment(run, root), rehearsal=False)
    fwd = m.forward_targets(ctx["klines_dir"], ctx["keys"])
    return m.charter3.finalize(ctx["top"], ctx["feats"], ctx["hist"], fwd, ctx["records"], extraction=ctx["extraction"])


def _v4(run: Run, root: Path) -> dict:
    m = _runner(run)
    ctx = m.prepare(registered_reader(run, root), root, _experiment(run, root), rehearsal=False)
    fwd = m.forward_targets(ctx["klines_dir"], ctx["keys"])
    return m.charter4.finalize(ctx["universe"], ctx["feats"], ctx["hist"], fwd, ctx["records"], extraction=ctx["extraction"],
                               timing=ctx["timing"])


def _v5(run: Run, root: Path, workers: int = 4) -> dict:
    m = _runner(run)
    experiment = _experiment(run, root)
    m.check_inputs(root, experiment)
    ctx = m.prepare(registered_reader(run, root), root, experiment, rehearsal=False, workers=workers)
    fwd = m.forward_returns(ctx["symbols"], ctx["fridays"], klines_dir=ctx["klines_dir"])
    return m.charter5.finalize(*m._tables(ctx), fwd, ctx["flags"], ctx["comparison"])


ADAPTERS: dict[str, Callable[[Run, Path], dict]] = {"V1b": _v1b, "V2": _v2, "V3": _v3, "V4": _v4, "V5": _v5}


# --- comparison -----------------------------------------------------------------------------------------------------

def _plain(value: Any) -> Any:
    """The JSON form the run wrote (``ResearchRun.write_json``), so in-memory types compare as stored."""
    return json.loads(json.dumps(value, default=str))


def diff(a: Any, b: Any, path: str = "", rel: float = 1e-9, abs_: float = 1e-12, limit: int = 20) -> list[str]:
    """Differences between two JSON values; floats within ``rel``/``abs_`` are equal, NaN equals NaN."""
    out: list[str] = []

    def walk(x: Any, y: Any, p: str) -> None:
        if len(out) >= limit:
            return
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y), key=str):
                if k not in x or k not in y:
                    out.append(f"{p}.{k}: only in {'stored' if k in x else 'replay'}")
                else:
                    walk(x[k], y[k], f"{p}.{k}")
        elif isinstance(x, list) and isinstance(y, list):
            if len(x) != len(y):
                out.append(f"{p}: length {len(x)} != {len(y)}")
            for i, (u, v) in enumerate(zip(x, y)):
                walk(u, v, f"{p}[{i}]")
        elif isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool) and not isinstance(y, bool):
            if not (math.isclose(x, y, rel_tol=rel, abs_tol=abs_) or (math.isnan(x) and math.isnan(y))):
                out.append(f"{p}: stored {x!r} != replay {y!r}")
        elif x != y or isinstance(x, bool) != isinstance(y, bool):
            out.append(f"{p}: stored {x!r} != replay {y!r}")

    walk(a, b, path)
    return out


@dataclass
class ReplayResult:
    label: str
    compared: dict[str, list[str]] = field(default_factory=dict)    # output name -> differences
    skipped: list[str] = field(default_factory=list)
    verdict_stored: str | None = None
    verdict_replay: str | None = None

    @property
    def ok(self) -> bool:
        return all(not d for d in self.compared.values()) and self.verdict_stored == self.verdict_replay


def replay(label: str, root: Path = ROOT) -> ReplayResult:
    run = get(label)
    if run.label not in ADAPTERS:
        raise ReplayError(f"{run.label} has no verdict to replay (completed runs: {', '.join(ADAPTERS)})")
    absent = missing_inputs(run, root)
    if absent:
        raise ReplayError(f"{run.label}: {len(absent)} registered inputs absent, e.g. {absent[:3]}")
    outputs = ADAPTERS[run.label](run, Path(root))
    result = ReplayResult(run.label)
    for name in sorted(outputs):
        stored_path = run.outputs(root) / name
        if name in NOT_COMPARED.get(run.label, set()) or not stored_path.is_file():
            result.skipped.append(name)
            continue
        result.compared[name] = diff(json.loads(stored_path.read_text()), _plain(outputs[name]), name)
    result.verdict_stored = json.loads((run.outputs(root) / "verdict.json").read_text())["verdict"]
    result.verdict_replay = _plain(outputs["verdict.json"])["verdict"]
    return result
