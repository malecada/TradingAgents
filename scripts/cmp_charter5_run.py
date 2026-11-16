"""Charter 5 lifecycle runner (direct comparison of assets on text; one registered experiment). No model call.

Every model answer of the charter is in a registered call cache. The runner rebuilds from the caches and the
registered store every table the comparison depends on (present reader records, archive link tables, archive
reader records, dossiers, comparison results and scores, identification flags), checks each against its
registered file, counts the attention controls, joins the forward returns once and writes the verdict by code.
Everything that can be checked without an outcome is checked before the claim, including the hashes of the
registered inputs and a rehearsal of the whole evaluation on synthetic returns, so a defect found there does
not consume the attempt.
Usage: cmp_charter5_run.py --registration research/llm-v2-charter5-<date>/gates.json --experiment <id> [--preflight-only]
"""
from __future__ import annotations

import argparse
import hashlib
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
from scripts import cmp_common as common  # noqa: E402
from scripts import cmp_dossiers, cmp_duels, cmp_items_build, cmp_probe, cmp_read  # noqa: E402
from scripts.reader_extract import call_summary  # noqa: E402
from tradingagents.agents_v2.charter1b import verify_store  # noqa: E402
from tradingagents.compare import charter5, duel  # noqa: E402
from tradingagents.dossier.entities import build_dictionary  # noqa: E402
from tradingagents.dossier.quant_forecast import forward_returns  # noqa: E402
from tradingagents.dossier.universe import base_symbol  # noqa: E402
from tradingagents.reader import charter2, consensus, schema  # noqa: E402
from tradingagents.reader.extract import CallCache  # noqa: E402
from tradingagents.reader.reading import units  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ("scores.json", "evaluation.json", "comparison.json", "verdict.json")
CELLS = ("archive-tables", "dossiers", "comparisons", "comparison-gate", "descriptive-panels")
TEXT_STORE = "data/compare/text/ccnews"
REHEARSAL_SEED, REHEARSAL_BOOT = 20261115, 20


def _head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _frame(data: bytes) -> pd.DataFrame:
    return pd.read_parquet(io.BytesIO(data))


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def same_table(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    """Equal columns and equal values row by row after a parquet round trip; a missing value is missing
    whatever its dtype (a column of only missing values has no string dtype in memory)."""
    def values(frame: pd.DataFrame) -> dict:
        buf = io.BytesIO()
        frame.reset_index(drop=True).to_parquet(buf, index=False)
        back = pd.read_parquet(io.BytesIO(buf.getvalue()))
        return {c: back[c].astype(object).where(back[c].notna(), None).tolist() for c in back.columns}
    return list(a.columns) == list(b.columns) and len(a) == len(b) and values(a) == values(b)


def text_digest(root: Path) -> dict[str, str]:
    """sha256 of every month file of the archive store, by path relative to the checkout."""
    return {p.relative_to(root).as_posix(): _sha(p.read_bytes()) for p in sorted((Path(root) / TEXT_STORE).glob("*/*.parquet"))}


def check_inputs(root: Path, experiment: dict) -> None:
    """Every registered input has its registered bytes (the lifecycle checks this again after the claim)."""
    for name, info in experiment["inputs"].items():
        path = Path(root) / info["path"]
        if not path.is_file() or _sha(path.read_bytes()) != info["sha256"]:
            raise SystemExit(f"input {name} differs from the registration")


def synthetic_returns(top: pd.DataFrame, seed: int = REHEARSAL_SEED) -> pd.DataFrame:
    """Forward returns of the registered shape made of seeded noise. No store is read."""
    rng = np.random.default_rng(seed)
    keys = charter5.test_universe(top)[["date", "symbol"]].reset_index(drop=True)
    fwd = keys.assign(fwd_ret=0.08 * rng.normal(size=len(keys)), delisted=False)
    return fwd[rng.uniform(size=len(fwd)) > 0.01].reset_index(drop=True)


def rehearse(ctx: dict) -> None:
    """The whole evaluation on synthetic returns; any error, also in a descriptive panel, stops the process."""
    out = charter5.finalize(*_tables(ctx), synthetic_returns(ctx["top"]), ctx["flags"], ctx["comparison"], n_boot=REHEARSAL_BOOT)
    json.dumps(out, allow_nan=False)
    if set(out) != set(OUTPUTS):
        raise SystemExit("rehearsal: output names differ from the registered outputs")
    verdict = out["verdict.json"]
    if verdict["descriptive_errors"]:
        raise SystemExit(f"rehearsal: errors {verdict['descriptive_errors']}")
    if verdict["verdict"] not in ("PASS", "FAIL") or not verdict["test_weeks"]:
        raise SystemExit("rehearsal: no verdict")


def _tables(ctx: dict) -> tuple:
    return (ctx["top"], ctx["attention"], ctx["dossiers"], ctx["lines"], ctx["scores"], ctx["results"], ctx["quant"])


def typing_cache(data: bytes) -> dict:
    """The typing cache from its bytes (the format of ``tradingagents.reader.items.load_typing_cache``)."""
    out = {}
    for line in data.decode("utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["key"]] = rec["value"]
    return out


def _check(same: bool, what: str) -> None:
    if not same:
        raise SystemExit(f"{what} differs from the rebuild out of the registered caches")


def prepare(read, root: Path, experiment: dict, rehearsal: bool, workers: int = 4) -> dict:
    """Load and verify every registered input and rebuild every table of the comparison from the call caches.
    ``read(name)`` returns the bytes of a registered input. Called once before the run is claimed (a defect then
    stops the process without consuming the attempt) and again through the run helper. No bar that opens at or
    after a decision is used."""
    root = Path(root)
    manifest = json.loads(read("extraction_manifest"))
    check_manifest(manifest, experiment)
    if manifest["model"]["id"] != common.MODEL:
        raise SystemExit("the present records were read with another model than the archive records")
    cards = _frame(read("cards"))
    top = charter2.universe(cards)
    fridays = sorted(charter5.test_universe(top)["date"].unique())
    present = {"items": _frame(read("items")), "docs": _frame(read("docs")), "records": _frame(read("records"))}
    _, work = charter2.reading(present["items"], present["docs"], top)
    rows, _, missing = consensus.rebuild(units(work, present["docs"], present["items"]), CallCache.from_bytes(read("calls")), common.MODEL)
    _check(consensus.same_records(consensus.record_frame(rows), present["records"]), "present record table")
    if sorted(missing) != sorted(manifest["units_call_missing"]):
        raise SystemExit("present units without a cached call differ from the extraction manifest")

    digest = json.loads(read("text_digest"))
    if text_digest(root) != digest:
        raise SystemExit("archive store differs from the registered digest")
    bases = cmp_items_build.card_bases(cards)
    items, docs = cmp_items_build.build_tables([root / p for p in sorted(digest)], typing_cache(read("typing_cache")), bases,
                                               workers=workers, log=lambda _: None)
    archive = {"items": _frame(read("archive_items")), "docs": _frame(read("archive_docs")), "records": _frame(read("archive_records"))}
    _check(same_table(items, archive["items"]), "archive link table")
    _check(same_table(docs, archive["docs"]), "archive document table")
    _, unit_list = cmp_read.archive_units(archive["items"], archive["docs"], top, fridays)
    rows, _, missing_archive = consensus.rebuild(unit_list, CallCache.from_bytes(read("archive_calls")), common.MODEL)
    _check(consensus.same_records(consensus.record_frame(rows), archive["records"]), "archive record table")

    all_items, all_docs, all_records = common.join_frames(present, archive)
    lines, dossiers, report = cmp_dossiers.build(all_items, all_docs, all_records, top, fridays, build_dictionary(bases))
    _check(same_table(lines, _frame(read("lines"))), "dossier line table")
    _check(same_table(dossiers, _frame(read("dossiers"))), "dossier table")
    duel_cache = CallCache.from_bytes(read("duel_calls"))
    results, judge, missing_duels = duel.rebuild(cmp_duels.all_duels(dossiers), duel_cache, common.MODEL)
    if missing_duels:
        raise SystemExit(f"{missing_duels} comparisons without a cached answer")
    _check(same_table(results, _frame(read("duels"))), "comparison result table")
    scores = duel.scores(results, dossiers)
    _check(same_table(scores, _frame(read("scores"))), "comparison score table")
    tickers = sorted(charter5.test_universe(top)["base"].unique())
    flags, missing_probe, _ = cmp_probe.flags(dossiers, CallCache.from_bytes(read("probe_calls")), common.MODEL, tickers)
    if missing_probe:
        raise SystemExit(f"{missing_probe} dossiers without a cached probe answer")
    _check(same_table(flags, _frame(read("flags"))), "identification flag table")

    klines_dir = verify_store(root, json.loads(read("klines_digest")), "kline store")
    symbols = sorted(charter5.test_universe(top)["symbol"].unique())
    absent = [s for s in symbols if not (klines_dir / f"{s}.parquet").exists()]
    if absent:
        raise SystemExit(f"kline store: no file for {absent}")
    comparison = {
        "model": common.MODEL, "k_rounds": duel.K_ROUNDS,
        "prompt_sha256": {"comparison": duel.prompt_sha256(), "reader": schema.prompt_sha256(), "probe": cmp_probe.prompt_sha256()},
        "quality": duel.quality(results), "invalid_answers": judge.stats["invalid"],
        "calls": call_summary(duel_cache, sorted(judge.used)),
        "dossiers": report,
        "archive": {"store_files": len(digest), "documents_linked": int(archive["items"]["doc_id"].nunique()),
                    "documents_typed": len(archive["docs"]), "units_read": len(unit_list), "records": len(archive["records"]),
                    "units_call_missing": len(missing_archive)},
        "probe": {"dossiers": len(flags), "candidate_tickers": len(tickers), "chance": 1 / len(tickers),
                  "identified_share": float(flags["identified"].mean()), "month_within_6_share": float(flags["month_within_6"].mean())},
        "present_extraction": {k: manifest[k] for k in EXTRACTION_KEYS}}
    ctx = {"top": top, "attention": charter5.attention_7d(all_items, top), "dossiers": dossiers, "lines": lines, "scores": scores,
           "results": results, "quant": _frame(read("quant_forecasts")), "flags": flags, "comparison": comparison,
           "fridays": fridays, "symbols": symbols, "klines_dir": klines_dir}
    if rehearsal:
        rehearse(ctx)
    return ctx


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registration", required=True)
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--preflight-only", action="store_true", help="checks and rehearsal only: no claim, no outcome")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)
    root = Path(root) if root else ROOT
    from tradingagents.research import ResearchRun
    experiment = json.loads((root / args.registration).read_text())["experiments"][args.experiment]
    registered = experiment["inputs"]
    check_inputs(root, experiment)
    prepare(lambda name: (root / registered[name]["path"]).read_bytes(), root, experiment, rehearsal=True, workers=args.workers)
    if args.preflight_only:
        print("pre-flight passed: inputs verified, every table rebuilt from the caches, rehearsal on synthetic returns complete")
        return 0
    with ResearchRun.start(root=root, registration=args.registration, experiment=args.experiment, source=_head(root)) as run:
        ctx = prepare(run.read_input, root, experiment, rehearsal=False, workers=args.workers)
        fwd = forward_returns(ctx["symbols"], ctx["fridays"], klines_dir=ctx["klines_dir"])       # the single outcome join
        outputs = charter5.finalize(*_tables(ctx), fwd, ctx["flags"], ctx["comparison"])
        for name in OUTPUTS:
            run.write_json(name, outputs[name])
        run.finish([{"id": c, "status": "complete"} for c in CELLS])
        print(json.dumps(outputs["verdict.json"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
