"""Charter 2 lifecycle runner (reader configuration, one registered experiment). No model call.

The record table was extracted before the registration (scripts/reader_extract.py) and is a registered input
together with the call cache it was built from. The runner rebuilds the records from the cache, builds the
asset-week text features, fits the registered forecasters walk-forward, joins the forward returns once and
writes the verdict by code. Everything that can be checked without an outcome is checked before the claim,
including a rehearsal of the whole evaluation on synthetic outcome values, so a defect found there does not
consume the attempt.
Usage: reader_charter2_run.py --registration research/llm-v2-charter2-<date>/gates.json --experiment <id>
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
from tradingagents.agents_v2.portfolio_eval import realized_funding  # noqa: E402
from tradingagents.dossier.quant_forecast import forward_returns  # noqa: E402
from tradingagents.reader import charter2, consensus, schema  # noqa: E402
from tradingagents.reader.extract import CallCache  # noqa: E402
from tradingagents.reader.reading import units  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ("forecasts.json", "evaluation.json", "portfolio.json", "books.json", "reader.json", "verdict.json")
CELLS = ("text-features", "fitted-forecasts", "encompassing-gate", "descriptive-panels", "rule-book")
REHEARSAL_SEED, REHEARSAL_PLACEBO, REHEARSAL_BOOT = 20261112, 20, 50
EXTRACTION_KEYS = ("charter", "prompt_sha256", "model", "universe", "units", "records", "units_call_missing", "readings",
                   "evidence_grounding", "calls", "cache", "head")


def _head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _frame(data: bytes) -> pd.DataFrame:
    return pd.read_parquet(io.BytesIO(data))


def check_manifest(manifest: dict, experiment: dict) -> None:
    """The extraction must belong to the registered charter, prompt, inputs and source files."""
    if manifest["charter"]["sha256"] != experiment["charter"]["sha256"]:
        raise SystemExit("extraction manifest: made under a different charter text")
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


def synthetic_outcomes(top: pd.DataFrame, seed: int = REHEARSAL_SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Forward returns and funding of the registered shape made of seeded noise. No store is read."""
    rng = np.random.default_rng(seed)
    keys = top[["date", "symbol"]].reset_index(drop=True)
    fwd = keys.assign(fwd_ret=0.08 * rng.normal(size=len(keys)), delisted=False)
    fwd = fwd[rng.uniform(size=len(fwd)) > 0.01].reset_index(drop=True)
    return fwd, keys.assign(funding_week=1e-4, n_settlements=21)


def rehearse(ctx: dict) -> None:
    """The whole evaluation on synthetic outcomes; any error, also in a descriptive panel, stops the process."""
    fwd, funding = synthetic_outcomes(ctx["top"])
    out = charter2.finalize(ctx["top"], ctx["feats"], ctx["records"], fwd, funding, ctx["quant"], ctx["flags"],
                            extraction=ctx["extraction"], n_placebo=REHEARSAL_PLACEBO, n_boot=REHEARSAL_BOOT)
    json.dumps(out, allow_nan=False)
    if set(out) != set(OUTPUTS):
        raise SystemExit("rehearsal: output names differ from the registered outputs")
    verdict = out["verdict.json"]
    if verdict["descriptive_errors"] or out["evaluation.json"]["fit_errors"]:
        raise SystemExit(f"rehearsal: errors {verdict['descriptive_errors']} {out['evaluation.json']['fit_errors']}")
    if verdict["verdict"] not in ("PASS", "FAIL"):
        raise SystemExit("rehearsal: no verdict")


def prepare(read, root: Path, experiment: dict, rehearsal: bool) -> dict:
    """Load and verify every registered input and build the text features. ``read(name)`` returns the bytes of a
    registered input. Called once before the run is claimed (a defect then stops the process without consuming
    the attempt) and again through the run helper. No outcome is read here."""
    manifest = json.loads(read("extraction_manifest"))
    check_manifest(manifest, experiment)
    items, docs, cards = _frame(read("items")), _frame(read("docs")), _frame(read("cards"))
    records, quant, flags = _frame(read("records")), _frame(read("quant_forecasts")), _frame(read("reid_flags"))
    top = charter2.universe(cards)
    sets, work = charter2.reading(items, docs, top)
    rows, _, missing = consensus.rebuild(units(work, docs, items), CallCache.from_bytes(read("calls")), manifest["model"]["id"])
    if not consensus.same_records(consensus.record_frame(rows), records):
        raise SystemExit("record table differs from the rebuild out of the registered call cache")
    if sorted(missing) != sorted(manifest["units_call_missing"]):
        raise SystemExit("units without a cached call differ from the extraction manifest")
    feats = charter2.text_features(items, sets, records, top)
    klines_dir = verify_store(root, json.loads(read("klines_digest")), "kline store")
    funding_dir = verify_store(root, json.loads(read("funding_digest")), "funding store")
    symbols = sorted(top["symbol"].unique())
    absent = [s for s in symbols if not (klines_dir / f"{s}.parquet").exists()]
    if absent:
        raise SystemExit(f"kline store: no file for {absent}")
    ctx = {"top": top, "feats": feats, "records": records, "quant": quant, "flags": flags, "symbols": symbols,
           "fridays": sorted(pd.Timestamp(d) for d in top["date"].unique()), "klines_dir": klines_dir, "funding_dir": funding_dir,
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
        print("pre-flight passed: inputs verified, records rebuilt from the cache, rehearsal on synthetic outcomes complete")
        return 0
    with ResearchRun.start(root=root, registration=args.registration, experiment=args.experiment, source=_head(root)) as run:
        ctx = prepare(run.read_input, root, experiment, rehearsal=False)
        fwd = forward_returns(ctx["symbols"], ctx["fridays"], klines_dir=ctx["klines_dir"])       # the single outcome join
        funding = realized_funding(ctx["symbols"], ctx["fridays"], funding_dir=ctx["funding_dir"])
        outputs = charter2.finalize(ctx["top"], ctx["feats"], ctx["records"], fwd, funding, ctx["quant"], ctx["flags"],
                                    extraction=ctx["extraction"])
        for name in OUTPUTS:
            run.write_json(name, outputs[name])
        run.finish([{"id": c, "status": "complete"} for c in CELLS])
        print(json.dumps(outputs["verdict.json"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
