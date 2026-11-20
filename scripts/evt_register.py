"""Build the lifecycle registration of the event-time study (new family llm-event-time, attempt 1).

Run after the charter is frozen (the draft mark removed) and the source files are committed. The digest of the
minute bar store is written once with --digest. Writes research/llm-event-time-<date>/gates.json and never
overwrites.
Usage: evt_register.py --digest | evt_register.py --date 20261121 [--check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
CHARTER = "docs/superpowers/specs/2026-11-20-llm-event-time-charter.md"
EXTRACTION_CHARTER = "docs/superpowers/specs/2026-11-12-llm-v2-charter2-reader-charter.md"   # frozen, instructions of the records
DRAFT_MARK = "DRAFT, NOT FROZEN"
FAMILY_KEY = "llm-event-time"
FAMILY = {
    "mechanism_id": "reader-record-event-time-reaction",
    "attempt_budget": 2,
    "prior_attempts": 0,
    "history_reference": (
        "New mechanism: the direction of single fact records of the reader agents, placed at the publication time of "
        "the news document, against the market-relative return of the asset's perpetual contract from minutes after "
        "the publication. Family llm-multiagent-v2 (six attempts, all FAIL, closed 2026-11-17) tested the same agents "
        "and partly the same records at decisions once a week or once a day, about ten hours or more after the news, "
        "as a ranking of the cross-section; it is a different mechanism and is cited as history. Its records are "
        "reused here. The earlier no-go on event-driven news trading (2026-07-14) rested on published studies, not on "
        "a test in this repository."),
}
DATASET = "reader-records-minute-bars-2023-2024"
DATASET_IDENTITY = "reader-records-charter2-charter5-minute-bars-event-clock-v1"
WINDOW = {"start": "2022-12-31T00:00:00Z", "end": "2025-01-03T00:00:00Z"}
KLINES_DIR = "data/xsect/klines_1m"
KLINES_DIGEST = "data/eventtime/klines_1m_digest.json"
SOURCE_FILES = (
    "tradingagents/__init__.py", "tradingagents/eventtime/__init__.py", "tradingagents/eventtime/study.py",
    "scripts/evt_run.py", "scripts/evt_register.py", "scripts/evt_events_build.py", "scripts/evt_null_gate.py",
    "tradingagents/compare/__init__.py", "tradingagents/compare/archive.py",
    EXTRACTION_CHARTER, "uv.lock",
)
INPUTS = {
    "page_items": "data/reader/items.parquet", "page_records": "data/reader/records.parquet",
    "feed_items": "data/compare/items.parquet", "feed_records": "data/compare/records.parquet",
    "pub_times": "data/eventtime/pub_times.parquet", "klines_digest": KLINES_DIGEST,
}
HISTORY = (
    "Fact records of the reader agents over news documents (page archive of three outlets, extracted under Charter 2; "
    "news feed archive of 67 further outlets, extracted under Charter 5), placed at the publication time of the "
    "document, joined with minute bars of the perpetual contracts of the same assets. The daily and weekly returns of "
    "the window are exposed: features built from these records were joined with weekly returns (Charters 2 and 5), "
    "weekly realised variance (Charter 3) and next-day returns (Charter 4), all FAIL. The minute bars of the window "
    "were used by an earlier program on passive execution (exec-pf, 2026-09), without any text. Before this "
    "registration no record was joined with a price at or around its publication time; the event table, the lead "
    "rule and the counts were built from text stores only, and the noise pass rate and the power of the gate were "
    "measured on the events moved back by 104 weeks with random signs.")
QUESTION = (
    "Does the direction that the reader agents give to an asset-specific news event (favourable or unfavourable) "
    "separate the market-relative return of the asset's perpetual contract from 5 minutes after the publication to "
    "4 hours later, on the lead events of 2023 and 2024? Gate: slope of the return on the sign with one intercept "
    "per year, standard error clustered by day, t at least 2.0 with a positive slope, and a positive slope in both "
    "years. The descriptive tables show how much of the move happens before the publication and in the first minutes.")


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def experiment_id(date: str) -> str:
    return f"llm-event-time-run-{date}"


def build(date: str) -> tuple[str, dict]:
    from evt_run import CELLS, OUTPUTS

    from tradingagents.research.admission import runtime_hashes
    program = f"llm-event-time-{date}"
    inputs = {name: {"path": path, "sha256": _sha(path), "dataset": DATASET} for name, path in INPUTS.items()}
    spec = {"schema_version": 1, "program_id": program, "families": {FAMILY_KEY: FAMILY},
            "datasets": {DATASET: {"identity": DATASET_IDENTITY, "history_reference": HISTORY,
                                   "exposures": [{**WINDOW, "state": "exposed"}]}},
            "experiments": {experiment_id(date): {
                "family": FAMILY_KEY, "parent": None, "question": QUESTION,
                "charter": {"path": CHARTER, "sha256": _sha(CHARTER)}, "stage": "development", "reuse": "exploratory",
                "selection": None, "source_files": {p: _sha(p) for p in SOURCE_FILES}, "runtime_hashes": runtime_hashes(),
                "windows": [{"dataset": DATASET, **WINDOW, "availability": "existing"}],
                "inputs": inputs, "cells": list(CELLS), "outputs": list(OUTPUTS)}}}
    return f"research/{program}/gates.json", spec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--date", help="YYYYMMDD used in program/experiment ids")
    ap.add_argument("--check", action="store_true", help="build and validate the registration without writing it")
    ap.add_argument("--digest", action="store_true", help="write the digest of the minute bar store (once)")
    args = ap.parse_args(argv)
    if args.digest:
        from tradingagents.eventtime.study import store_digest
        target = ROOT / KLINES_DIGEST
        if target.exists():
            raise SystemExit(f"{target} exists; the digest is written once")
        digest = store_digest(ROOT, KLINES_DIR)
        target.write_text(json.dumps(digest, indent=1) + "\n")
        print(f"{KLINES_DIGEST}: {len(digest)} files")
        return 0
    if not args.date:
        raise SystemExit("--date is required")
    if not args.check and DRAFT_MARK in (ROOT / CHARTER).read_text():
        raise SystemExit("charter still marked DRAFT; freeze it first")
    target, spec = build(args.date)
    exp = spec["experiments"][experiment_id(args.date)]
    if args.check:
        print(f"check only: {target} not written; {len(exp['source_files'])} source files, {len(exp['inputs'])} inputs, "
              f"outputs {exp['outputs']}, cells {exp['cells']}")
        return 0
    if (ROOT / target).exists():
        raise SystemExit(f"{target} exists; registrations are never overwritten")
    (ROOT / target).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / target).write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n")
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
