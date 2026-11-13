"""Charter 3 lifecycle runner (target change: next-week volatility, one registered experiment). No model call.

The record table of Charter 2 and the call cache it was built from are registered inputs. The runner rebuilds
the records from the cache, builds the text features and the price-history features (both use decision-time
data only), computes the forward targets once and writes the verdict by code. Everything that can be checked
without an outcome is checked before the claim, including a rehearsal of the whole evaluation on synthetic
target values, so a defect found there does not consume the attempt.
Usage: reader_charter3_run.py --registration research/llm-v2-charter3-<date>/gates.json --experiment <id>
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
from tradingagents.agents_v2.charter1b import verify_store  # noqa: E402
from tradingagents.reader import charter2, charter3, consensus, schema  # noqa: E402
from tradingagents.reader.charter3 import forward_targets  # noqa: E402
from tradingagents.reader.extract import CallCache  # noqa: E402
from tradingagents.reader.reading import units  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ("forecasts.json", "evaluation.json", "reader.json", "verdict.json")
CELLS = ("history-features", "text-features", "partial-gate", "descriptive-panels")
REHEARSAL_SEED, REHEARSAL_PLACEBO = 20261113, 20
EXTRACTION_KEYS = ("charter", "prompt_sha256", "model", "universe", "units", "records", "units_call_missing", "readings",
                   "evidence_grounding", "calls", "cache", "head")


def _head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _frame(data: bytes) -> pd.DataFrame:
    return pd.read_parquet(io.BytesIO(data))


def check_manifest(manifest: dict, experiment: dict) -> None:
    """The extraction is the one of Charter 2: made under the charter text that is registered here as a source
    file, with the agent instructions of the code and with the registered inputs and source files."""
    charter = manifest["charter"]
    if experiment["source_files"].get(charter["path"]) != charter["sha256"]:
        raise SystemExit("extraction manifest: the charter text of the extraction is not a registered source file")
    if manifest["prompt_sha256"] != schema.prompt_sha256():
        raise SystemExit("extraction manifest: agent instructions differ from the code")
    inputs = experiment["inputs"]
    pairs = [(manifest["inputs"][name]["sha256"], inputs[name]["sha256"], name) for name in ("items", "docs", "cards")]
    pairs += [(manifest["records_file"]["sha256"], inputs["records"]["sha256"], "records"),
              (manifest["cache"]["sha256"], inputs["calls"]["sha256"], "calls")]
    for got, registered, name in pairs:
        if got != registered:
            raise SystemExit(f"extraction manifest: {name} differs from the registered input")
    for path, digest in manifest["source_files"].items():
        if experiment["source_files"].get(path) != digest:
            raise SystemExit(f"extraction manifest: {path} changed since the extraction")


def synthetic_targets(top: pd.DataFrame, seed: int = REHEARSAL_SEED) -> pd.DataFrame:
    """Forward targets of the registered shape made of seeded noise. No store is read."""
    rng = np.random.default_rng(seed)
    keys = top[["date", "symbol"]].reset_index(drop=True)
    variance = 1e-3 * np.exp(rng.normal(size=len(keys)))
    fwd = keys.assign(**{charter3.TARGET: variance,
                         "fwd_absret": np.abs(rng.normal(size=len(keys))) * np.sqrt(7 * variance),
                         "fwd_drawdown": np.abs(rng.normal(size=len(keys))) * np.sqrt(7 * variance),
                         "fwd_maxday": variance * (1.0 + rng.exponential(size=len(keys))), "fwd_bars": 7})
    return fwd[rng.uniform(size=len(fwd)) > 0.01].reset_index(drop=True)[["date", "symbol", *charter3.TARGET_COLUMNS]]


def rehearse(ctx: dict) -> None:
    """The whole evaluation on synthetic targets; any error, also in a descriptive panel, stops the process."""
    out = charter3.finalize(ctx["top"], ctx["feats"], ctx["hist"], synthetic_targets(ctx["top"]), ctx["records"],
                            extraction=ctx["extraction"], n_placebo=REHEARSAL_PLACEBO)
    json.dumps(out, allow_nan=False)
    if set(out) != set(OUTPUTS):
        raise SystemExit("rehearsal: output names differ from the registered outputs")
    verdict = out["verdict.json"]
    if verdict["descriptive_errors"] or out["evaluation.json"]["fit_errors"]:
        raise SystemExit(f"rehearsal: errors {verdict['descriptive_errors']} {out['evaluation.json']['fit_errors']}")
    if verdict["verdict"] not in ("PASS", "FAIL") or verdict["test_weeks"] < 1:
        raise SystemExit("rehearsal: no verdict")


def prepare(read, root: Path, experiment: dict, rehearsal: bool) -> dict:
    """Load and verify every registered input and build the decision-time features. ``read(name)`` returns the
    bytes of a registered input. Called once before the run is claimed (a defect then stops the process without
    consuming the attempt) and again through the run helper. No bar after a decision is used here."""
    manifest = json.loads(read("extraction_manifest"))
    check_manifest(manifest, experiment)
    items, docs, cards, records = _frame(read("items")), _frame(read("docs")), _frame(read("cards")), _frame(read("records"))
    top = charter2.universe(cards)
    sets, work = charter2.reading(items, docs, top)
    rows, _, missing = consensus.rebuild(units(work, docs, items), CallCache.from_bytes(read("calls")), manifest["model"]["id"])
    if not consensus.same_records(consensus.record_frame(rows), records):
        raise SystemExit("record table differs from the rebuild out of the registered call cache")
    if sorted(missing) != sorted(manifest["units_call_missing"]):
        raise SystemExit("units without a cached call differ from the extraction manifest")
    feats = charter3.text_features(items, sets, records, top)
    klines_dir = verify_store(root, json.loads(read("klines_digest")), "kline store")
    absent = [s for s in sorted(top["symbol"].unique()) if not (klines_dir / f"{s}.parquet").exists()]
    if absent:
        raise SystemExit(f"kline store: no file for {absent}")
    keys = top[["date", "symbol"]].reset_index(drop=True)
    hist = charter3.history_features(klines_dir, keys)
    ctx = {"top": top, "feats": feats, "hist": hist, "records": records, "keys": keys, "klines_dir": klines_dir,
           "extraction": {k: manifest[k] for k in EXTRACTION_KEYS}}
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
        outputs = charter3.finalize(ctx["top"], ctx["feats"], ctx["hist"], fwd, ctx["records"], extraction=ctx["extraction"])
        for name in OUTPUTS:
            run.write_json(name, outputs[name])
        run.finish([{"id": c, "status": "complete"} for c in CELLS])
        print(json.dumps(outputs["verdict.json"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
