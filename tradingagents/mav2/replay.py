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

# run label -> {path prefix of an output value: reason}. A difference under a listed prefix is reported as known,
# not as a failed replay. Only differences whose cause has been traced belong here.
KNOWN_DIFFERENCES: dict[str, dict[str, str]] = {
    "V4": {
        "evaluation.json.partial_scores.s_reader_lin.": (
            "Descriptive panel, not a gate. On days when a tone feature is zero for every asset (15 days for "
            "tone_1d; 2024-10-18 to 2024-10-20 for both tone features) its within-day OLS residual is zero in exact "
            "arithmetic and only rounding noise of order 1e-17 in floating point. Whether that noise is constant "
            "depends on the BLAS kernel of the machine, and the exact test np.ptp(x) > 0 then admits or drops the "
            "day (univariate tone_1d: 722 days on the run machine, 707 on the laptop), and on the three days without "
            "any tone the whole linear score is noise of order 1e-21 whose daily correlation is arbitrary. The gate "
            "score s_reader, the forecasts, the reader records and the verdict reproduce exactly."),
    },
}


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

def week_digest(day_dir: Path) -> str:
    """Digest of one week of the per-asset agent cache, by the V1b runner's own function."""
    return _runner(get("V1b"))._week_digest(day_dir)


def post_run_cache(runs_dir: Path, cache: dict, by_day: dict, config: str, new_weeks: dict,
                   truncated_week: str | None = None) -> set[str]:
    """The V1b agent cache as the run left it. The runner's own check (``charter1b.verify_cache``) describes the
    cache before the run and cannot pass afterwards, because the run completed the week V1 was interrupted in
    (rewriting its pinned partial files) and wrote four older weeks. Here: every frozen-week file keeps its
    registered digest, every pinned file outside the weeks the run wrote keeps its digest, every week the run wrote
    matches the digest the run recorded in ``cost.json``, and no other manifested week holds a cached file. The
    exception is ``truncated_week``, where the spend cap stopped the run after some assets were cached: its partial
    files are not used by the evaluation and carry no recorded digest, and the week must hold no book.
    Returns the frozen weeks."""
    from tradingagents.agents_v2.charter1b import sha256_file

    if cache["config_sha"] != config:
        raise ReplayError("V1b cache manifest belongs to another agent config")
    frozen = sorted(cache["complete_weeks"], reverse=True)
    if frozen != sorted(by_day, reverse=True)[:len(frozen)]:
        raise ReplayError("V1b frozen weeks are not the newest contiguous block of the manifested weeks")
    written = set(new_weeks)
    pinned = {**cache["files"], **{k: v for k, v in cache["pinned_other"].items() if k.split("/")[0] not in written}}
    for rel, digest in pinned.items():
        path = Path(runs_dir) / rel
        if not path.exists() or sha256_file(path) != digest:
            raise ReplayError(f"V1b cached file differs from the registered cache: {rel}")
    for day, info in new_weeks.items():
        if week_digest(Path(runs_dir) / day) != info["cache_digest"]:
            raise ReplayError(f"V1b week {day}: cache differs from the digest recorded by the run")
    for day in by_day:
        day_dir = Path(runs_dir) / day
        if day in written or not day_dir.is_dir():
            continue
        if day == truncated_week:
            if (day_dir / "_portfolio.json").exists():
                raise ReplayError(f"V1b truncated week {day} holds a book although the run excluded it")
            continue
        for f in day_dir.glob("*.json"):
            if f"{day}/{f.name}" not in pinned:
                raise ReplayError(f"V1b unregistered cached file: {day}/{f.name}")
    return set(frozen)


def _v1b_context(run: Run, root: Path, new_weeks: dict, truncated_week: str | None) -> dict:
    """The runner's ``prepare`` with its pre-run cache check replaced by :func:`post_run_cache`."""
    import io

    import pandas as pd

    from tradingagents.agents_v2.charter1b import (
        load_cached_week,
        load_dossiers,
        verify_store,
    )
    from tradingagents.agents_v2.graph import config_sha

    read = registered_reader(run, root)
    manifest = json.loads(read("dossier_manifest"))
    cfg = json.loads(read("agent_config"))
    if cfg["config_sha"] != config_sha():
        raise ReplayError("V1b agent config differs from the registered freeze")
    cache = json.loads(read("cache_manifest"))
    by_day = load_dossiers(root, manifest)
    runs_dir = Path(root) / cache["runs_dir"]
    frozen = post_run_cache(runs_dir, cache, by_day, cfg["config_sha"], new_weeks, truncated_week)
    return {"config": cfg["config_sha"], "by_day": by_day, "runs_dir": runs_dir, "frozen": frozen,
            "cards": pd.read_parquet(io.BytesIO(read("cards"))),
            "quant": pd.read_parquet(io.BytesIO(read("quant_forecasts"))),
            "flags": pd.read_parquet(io.BytesIO(read("reid_flags"))),
            "klines_dir": verify_store(root, json.loads(read("klines_digest")), "kline store"),
            "funding_dir": verify_store(root, json.loads(read("funding_digest")), "funding store"),
            "frozen_weeks": {day: load_cached_week(day, by_day[day], runs_dir, cfg["config_sha"]) for day in sorted(frozen)}}


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
    new_weeks = stored_cost["new_weeks"]
    truncated = stored_cost["truncated_at"]
    ctx = _v1b_context(run, root, new_weeks, truncated["week"] if truncated else None)
    by_day, runs_dir, frozen = ctx["by_day"], ctx["runs_dir"], ctx["frozen"]
    rows, books, completed = [], {name: {} for name in BOOK_KEYS}, []
    for day in sorted(set(frozen) | set(new_weeks), reverse=True):
        # a week the run called itself is read from the same per-asset cache, already checked against its digest
        out = ctx["frozen_weeks"][day] if day in frozen else load_cached_week(day, by_day[day], runs_dir, ctx["config"])
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
    compared: dict[str, list[str]] = field(default_factory=dict)    # output name -> unexplained differences
    known: dict[str, list[str]] = field(default_factory=dict)       # output name -> differences in KNOWN_DIFFERENCES
    skipped: list[str] = field(default_factory=list)
    verdict_stored: str | None = None
    verdict_replay: str | None = None

    @property
    def ok(self) -> bool:
        return all(not d for d in self.compared.values()) and self.verdict_stored == self.verdict_replay


def split_known(diffs: list[str], known: dict[str, str]) -> tuple[list[str], list[str]]:
    """(unexplained, known) differences; a difference is known when its path starts with a listed prefix."""
    is_known = [any(d.startswith(prefix) for prefix in known) for d in diffs]
    return [d for d, k in zip(diffs, is_known) if not k], [d for d, k in zip(diffs, is_known) if k]


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
        found = diff(json.loads(stored_path.read_text()), _plain(outputs[name]), name, limit=100_000)
        result.compared[name], known = split_known(found, KNOWN_DIFFERENCES.get(run.label, {}))
        if known:
            result.known[name] = known
    result.verdict_stored = json.loads((run.outputs(root) / "verdict.json").read_text())["verdict"]
    result.verdict_replay = _plain(outputs["verdict.json"])["verdict"]
    return result
