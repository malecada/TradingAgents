"""Reader extraction on the archive documents (Charter 5): the frozen reader of Charter 2 on the archive rows of
the seven-day weekly sets. No outcome is read.

Usage: cmp_read.py --pilot --cap 0.15        pilot weeks, own record file (allowed before the freeze)
       cmp_read.py --cap 4.00                every test week (frozen charter required)
       cmp_read.py --offline                 rebuild the records from the cache and compare, no call
Instruction, schema, consensus and client settings are those of ``scripts/reader_extract.py``. The calls go to a
separate cache (``data/compare/calls.jsonl``); ``--cap`` limits the spend of that cache over all runs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import cmp_common as common  # noqa: E402
from scripts import reader_extract as rx  # noqa: E402
from tradingagents.compare import dossier  # noqa: E402
from tradingagents.reader import consensus, schema  # noqa: E402
from tradingagents.reader.extract import MAX_TOKENS, CallCache, Reader  # noqa: E402
from tradingagents.reader.reading import units  # noqa: E402

CACHE = "data/compare/calls.jsonl"
RECORDS = common.ARCHIVE["records"]
PILOT_RECORDS = "data/compare/pilot_records.parquet"
REPORT = "data/compare/read_report.json"
PILOT_REPORT = "data/compare/pilot_read_report.json"


def archive_units(items: pd.DataFrame, docs: pd.DataFrame, top: pd.DataFrame, fridays) -> tuple[pd.DataFrame, list]:
    """Work rows and units (one per document) of the archive rows in the weekly sets."""
    work = dossier.work_rows(dossier.weekly_sets(items, docs, top, fridays))
    return work, units(work, docs, items)


def main(argv=None, root: Path | None = None, client=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    common.add_week_args(ap)
    ap.add_argument("--cap", type=float, default=None, help="spend limit of the call cache in USD, all runs together")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--accept-missing", type=int, default=0)
    args = ap.parse_args(argv)
    root = Path(root or common.ROOT)
    top, fridays, pilot = common.universe_weeks(args)
    if not pilot and not args.offline:
        common.require_frozen(root)
    items, docs = (pd.read_parquet(root / common.ARCHIVE[k]) for k in ("items", "docs"))
    work, unit_list = archive_units(items, docs, top, fridays)
    model = client.model if client is not None else common.MODEL
    cache = CallCache(root / CACHE)
    print(json.dumps({"weeks": len(fridays), "units": len(unit_list), "work_rows": len(work), "cache_calls": len(cache),
                      "cache_paid_usd": round(cache.paid_usd, 4), "prompt_sha256": schema.prompt_sha256()}), flush=True)
    filled = None
    if not args.offline:
        if args.cap is None:
            raise SystemExit("--cap is required for a run that may call the model")
        remaining = args.cap - cache.paid_usd
        if remaining <= 0:
            raise SystemExit(f"spend limit reached: {cache.paid_usd:.4f} of {args.cap}")
        client = client or common.make_client(remaining, args.workers, MAX_TOKENS)
        filled = rx.fill(Reader(client, cache, model=model), unit_list, workers=args.workers, passes=args.passes)
        print(json.dumps({"phase_1": filled}), flush=True)
    rows, reader, failed = consensus.rebuild(unit_list, cache, model)
    summary = rx.describe(rows, reader, failed, cache)
    frame = consensus.record_frame(rows)
    per_unit = summary["calls"]["cost_usd"] / max(summary["units"], 1)
    report = {"pilot": pilot, "weeks": [str(pd.Timestamp(f).date()) for f in fridays] if pilot else len(fridays),
              "model": model, "prompt_sha256": schema.prompt_sha256(), "phase_1": filled, **summary,
              "cost": {"per_unit_usd": per_unit, "cache_paid_usd": cache.paid_usd}}
    path = root / (PILOT_RECORDS if pilot else RECORDS)
    if args.offline and path.exists():
        same = consensus.same_records(pd.read_parquet(path), frame)
        print(json.dumps({"offline_rebuild_equals_stored_records": bool(same), "records": len(frame)}))
        if not same:
            raise SystemExit("the rebuild from the cache differs from the stored records")
        return report
    if not pilot and ((filled and filled["stopped"]) or len(failed) > args.accept_missing):
        print(json.dumps({"incomplete": filled, "units_call_missing": len(failed)}))
        raise SystemExit("extraction incomplete: no record table written; run again to resume")
    frame.to_parquet(path, index=False)
    rx._write_json(root / (PILOT_REPORT if pilot else REPORT), report)
    print(json.dumps({"records": len(frame), "units": summary["units"], "units_call_missing": len(failed),
                      "quality": summary["quality"], "evidence_grounding": summary["evidence_grounding"],
                      "cost": report["cost"]}), flush=True)
    return report


if __name__ == "__main__":
    main()
