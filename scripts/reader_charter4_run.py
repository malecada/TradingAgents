"""Charter 4 lifecycle runner (fresher information: daily decision, next-day return; one registered experiment). No model call.

The record table of Charter 2 and the call cache it was built from are registered inputs. The runner rebuilds
the records from the cache, builds the daily text features and the price-history features (both use
decision-time data only), computes the forward targets once and writes the verdict by code. Everything that
can be checked without an outcome is checked before the claim, including a rehearsal of the whole evaluation
on synthetic target values, so a defect found there does not consume the attempt.
Usage: reader_charter4_run.py --registration research/llm-v2-charter4-<date>/gates.json --experiment <id>
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reader_charter3_run import EXTRACTION_KEYS, check_manifest  # noqa: E402
from tradingagents.agents_v2.charter1b import verify_store  # noqa: E402
from tradingagents.reader import charter2, charter4, consensus  # noqa: E402
from tradingagents.reader.charter4 import forward_targets  # noqa: E402
from tradingagents.reader.extract import CallCache  # noqa: E402
from tradingagents.reader.reading import units  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ("forecasts.json", "evaluation.json", "reader.json", "verdict.json")
CELLS = ("history-features", "text-features", "partial-gate", "descriptive-panels")
REHEARSAL_SEED, REHEARSAL_PLACEBO = 20261114, 20


def _head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _frame(data: bytes) -> pd.DataFrame:
    return pd.read_parquet(io.BytesIO(data))


def synthetic_targets(universe: pd.DataFrame, seed: int = REHEARSAL_SEED) -> pd.DataFrame:
    """Forward targets of the registered shape made of seeded noise. No store is read."""
    rng = np.random.default_rng(seed)
    keys = universe[["date", "symbol"]].reset_index(drop=True)
    ret = 0.05 * rng.normal(size=len(keys))
    fwd = keys.assign(fwd_ret_1d=ret, fwd_absret_1d=np.abs(ret), fwd_rv_1d=2.5e-3 * np.exp(rng.normal(size=len(keys))),
                      fwd_ret_3d=ret + 0.07 * rng.normal(size=len(keys)))
    return fwd[rng.uniform(size=len(fwd)) > 0.01].reset_index(drop=True)[["date", "symbol", *charter4.TARGET_COLUMNS]]


def rehearse(ctx: dict) -> None:
    """The whole evaluation on synthetic targets; any error, also in a descriptive panel, stops the process."""
    out = charter4.finalize(ctx["universe"], ctx["feats"], ctx["hist"], synthetic_targets(ctx["universe"]), ctx["records"],
                            extraction=ctx["extraction"], timing=ctx["timing"], n_placebo=REHEARSAL_PLACEBO)
    json.dumps(out, allow_nan=False)
    if set(out) != set(OUTPUTS):
        raise SystemExit("rehearsal: output names differ from the registered outputs")
    verdict = out["verdict.json"]
    if verdict["descriptive_errors"] or out["evaluation.json"]["fit_errors"]:
        raise SystemExit(f"rehearsal: errors {verdict['descriptive_errors']} {out['evaluation.json']['fit_errors']}")
    if verdict["verdict"] not in ("PASS", "FAIL") or verdict["test_days"] < 1:
        raise SystemExit("rehearsal: no verdict")


def prepare(read, root: Path, experiment: dict, rehearsal: bool) -> dict:
    """Load and verify every registered input and build the decision-time features. ``read(name)`` returns the
    bytes of a registered input. Called once before the run is claimed (a defect then stops the process without
    consuming the attempt) and again through the run helper. No bar that opens at or after a decision is used."""
    manifest = json.loads(read("extraction_manifest"))
    check_manifest(manifest, experiment)
    items, docs, cards, records = _frame(read("items")), _frame(read("docs")), _frame(read("cards")), _frame(read("records"))
    top = charter2.universe(cards)
    _, work = charter2.reading(items, docs, top)
    rows, _, missing = consensus.rebuild(units(work, docs, items), CallCache.from_bytes(read("calls")), manifest["model"]["id"])
    if not consensus.same_records(consensus.record_frame(rows), records):
        raise SystemExit("record table differs from the rebuild out of the registered call cache")
    if sorted(missing) != sorted(manifest["units_call_missing"]):
        raise SystemExit("units without a cached call differ from the extraction manifest")
    universe = charter4.daily_universe(top)
    feats = charter4.text_features(items, docs, records, universe)
    klines_dir = verify_store(root, json.loads(read("klines_digest")), "kline store")
    absent = [s for s in sorted({*universe["symbol"].unique(), charter4.MARKET}) if not (klines_dir / f"{s}.parquet").exists()]
    if absent:
        raise SystemExit(f"kline store: no file for {absent}")
    keys = universe[["date", "symbol"]].reset_index(drop=True)
    hist = charter4.history_features(klines_dir, keys)
    ctx = {"universe": universe, "feats": feats, "hist": hist, "records": records, "keys": keys, "klines_dir": klines_dir,
           "extraction": {k: manifest[k] for k in EXTRACTION_KEYS}, "timing": charter4.timing_facts(items)}
    if rehearsal:
        rehearse(ctx)
    return ctx


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registration", required=True)
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--preflight-only", action="store_true", help="checks and rehearsal only: no claim, no outcome")
    args = ap.parse_args(argv)
    root = Path(root) if root else ROOT
    from tradingagents.research import ResearchRun
    experiment = json.loads((root / args.registration).read_text())["experiments"][args.experiment]
    registered = experiment["inputs"]
    prepare(lambda name: (root / registered[name]["path"]).read_bytes(), root, experiment, rehearsal=True)   # no claim yet
    if args.preflight_only:
        print("pre-flight passed: inputs verified, records rebuilt from the cache, rehearsal on synthetic targets complete")
        return 0
    with ResearchRun.start(root=root, registration=args.registration, experiment=args.experiment, source=_head(root)) as run:
        ctx = prepare(run.read_input, root, experiment, rehearsal=False)
        fwd = forward_targets(ctx["klines_dir"], ctx["keys"])                                    # the single outcome join
        outputs = charter4.finalize(ctx["universe"], ctx["feats"], ctx["hist"], fwd, ctx["records"], extraction=ctx["extraction"],
                                    timing=ctx["timing"])
        for name in OUTPUTS:
            run.write_json(name, outputs[name])
        run.finish([{"id": c, "status": "complete"} for c in CELLS])
        print(json.dumps(outputs["verdict.json"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
