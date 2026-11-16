"""Build the lifecycle registration for Charter 5 (direct comparison of assets on text, with the news archive).

Sixth and last attempt of family llm-multiagent-v2: same family entry and attempt budget, the dataset and
experiment entries of the Charter 4 registration copied verbatim (parent admission), a new dataset entry for the
dossiers and comparison tables. Run after the charter is frozen (status line changed from DRAFT), the full typing,
reading, comparison and probe are complete and the source files are committed. Writes the digest of the archive
store once (data/compare/text_digest.json) and research/llm-v2-charter5-<date>/gates.json, never overwrites.
Usage: cmp_charter5_register.py --date 20261120            (--check validates without writing the registration)
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import reader_charter4_register as parent_reg  # noqa: E402
from scripts import cmp_common as common  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CHARTER = common.CHARTER
PARENT_CHARTER = parent_reg.CHARTER                                       # frozen, charter of the parent run
DRAFT_MARK = common.DRAFT_MARK
PARENT_REGISTRATION = "research/llm-v2-charter4-20261114/gates.json"
PARENT = "llm-v2c4-fresh-news-dev-run-20261114"
QUANT_SOURCE = "llm-v2c2-reader-dev-run-20261112"                         # registered the quant forecasts last
FAMILY_KEY = "llm-multiagent-v2"
DATASET = "dev-compare-weekly-2023-2024"
DATASET_IDENTITY = "multiagent-v2-dev-text-dossiers-news-archive-pairwise-comparisons-v1"
WINDOW = {"start": "2022-01-01T00:00:00Z", "end": "2025-01-08T00:00:00Z"}  # the weekly window of Charters 1 to 3
TEXT_DIGEST = "data/compare/text_digest.json"
# Every project file the registered run imports (the research helper is pinned by its runtime hashes), every file
# pinned by the Charter 4 registration (unchanged since), the charter text of the parent run, the drivers that made
# the registered tables and the dependency lock. A test compares this with the imports.
SOURCE_FILES = (
    *parent_reg.SOURCE_FILES, PARENT_CHARTER,
    "tradingagents/compare/__init__.py", "tradingagents/compare/archive.py", "tradingagents/compare/scope.py",
    "tradingagents/compare/dossier.py", "tradingagents/compare/duel.py", "tradingagents/compare/charter5.py",
    "tradingagents/xsect/__init__.py", "tradingagents/xsect/pair_xs.py",
    "scripts/__init__.py", "scripts/cmp_common.py", "scripts/cmp_archive_ingest.py", "scripts/cmp_items_build.py", "scripts/cmp_type.py",
    "scripts/cmp_read.py", "scripts/cmp_dossiers.py", "scripts/cmp_duels.py", "scripts/cmp_probe.py",
    "scripts/cmp_null_gate.py", "scripts/cmp_charter5_run.py", "scripts/cmp_charter5_register.py",
)
INPUTS = {
    **parent_reg.INPUTS,                                                  # present store, reader cache and records, cards, bars
    "quant_forecasts": "data/dossier/quant_forecasts.parquet",
    "text_digest": TEXT_DIGEST,
    "typing_cache": "data/compare/typing_cache.jsonl",
    "archive_items": common.ARCHIVE["items"],
    "archive_docs": common.ARCHIVE["docs"],
    "archive_calls": "data/compare/calls.jsonl",
    "archive_records": common.ARCHIVE["records"],
    "lines": "data/compare/lines.parquet",
    "dossiers": "data/compare/dossiers.parquet",
    "duel_calls": "data/compare/duel_calls.jsonl",
    "duels": "data/compare/duels.parquet",
    "scores": "data/compare/scores.parquet",
    "probe_calls": "data/compare/probe_calls.jsonl",
    "flags": "data/compare/flags.parquet",
}
SAME_AS_PARENT = tuple(parent_reg.INPUTS)                                 # the bytes of the Charter 4 run
HISTORY = ("De-identified seven-day text dossiers of the weekly top-50 perp universe on the 104 test weeks 2023-01-06 "
           "to 2024-12-27, built from the reader records of the present store (data/reader, extracted under Charter 2) "
           "and of the archive store (data/compare/text: a public news-feed archive of 67 outlets, CC-BY-NC-4.0, typed "
           "and read with the frozen typing and reader instructions for the archive documents whose primary asset is a "
           "universe asset other than BTC and ETH), and the pairwise comparisons of these dossiers by two analyst "
           "agents and an adjudicator. The whole window is exposed: features built from the present records were "
           "joined with the forward weekly returns of the same weeks in llm-v2c2-reader-dev-run-20261112 (verdict "
           "FAIL), with next-week variance in llm-v2c3-volatility-dev-run-20261113 (FAIL) and with next-day returns "
           "in llm-v2c4-fresh-news-dev-run-20261114 (FAIL); in all three the attention counts carried a weak signal "
           "and the reader judgements none. Before this registration no dossier, comparison result or comparison "
           "score of this charter was joined with a return or any other price quantity dated at or after its "
           "decision. The archive was examined for coverage, publication timing, backfill and licence (feed times "
           "only); typing, reading, comparison and identification probe ran as a pilot on three seeded test weeks "
           "under a stop rule on answer quality, without any outcome; the gate was simulated on synthetic returns "
           "only.")
QUESTION = ("Do pairwise comparisons of the de-identified seven-day text dossiers of two assets of the same week, made "
            "by two analyst agents and, where they disagree, an adjudicator, who name the asset whose reports give the "
            "better price outlook over the next seven days, carry information on the next-week return rank beyond "
            "the existing quant forecast, the price controls and the attention counts, on the 104 test weeks "
            "2023-01-06 to 2024-12-27? The comparison score of an asset and week is its Bradley-Terry strength over "
            "the decided comparisons of the week; an asset without a dossier takes the neutral score 0. Gate: weekly "
            "OLS coefficient of the within-week rank of the comparison score in a regression of the within-week "
            "return rank on an intercept and the ranks of the quant forecast, the price controls and three attention "
            "controls (seven-day linked documents, dossier lines, dossier present); Newey-West t (lag 4) of the mean "
            "weekly coefficient at least 2.0 with a positive mean over at least 78 weeks, and a positive mean in 2023 "
            "and in 2024.")


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def experiment_id(date: str) -> str:
    return f"llm-v2c5-direct-comparison-dev-run-{date}"


def store_digest() -> dict:
    """The digest of the archive store, written once; a later store that differs from it stops the process."""
    from cmp_charter5_run import text_digest
    now, path = text_digest(ROOT), ROOT / TEXT_DIGEST
    if not now:
        raise SystemExit("the archive store is empty")
    if path.exists():
        if json.loads(path.read_text()) != now:
            raise SystemExit("the archive store differs from its written digest")
    else:
        path.write_text(json.dumps(now, indent=1) + "\n")
    return now


def build(date: str) -> tuple[str, dict]:
    from cmp_charter5_run import CELLS, OUTPUTS
    from tradingagents.research.admission import runtime_hashes
    parent_spec = json.loads((ROOT / PARENT_REGISTRATION).read_text())
    parent = parent_spec["experiments"][PARENT]
    inputs = {name: {"path": path, "sha256": _sha(path), "dataset": DATASET} for name, path in INPUTS.items()}
    for name in SAME_AS_PARENT:
        if inputs[name]["sha256"] != parent["inputs"][name]["sha256"]:
            raise SystemExit(f"input {name} differs from the Charter 4 registration")
    if inputs["quant_forecasts"]["sha256"] != parent_spec["experiments"][QUANT_SOURCE]["inputs"]["quant_forecasts"]["sha256"]:
        raise SystemExit("input quant_forecasts differs from the Charter 2 registration")
    sources = {p: _sha(p) for p in SOURCE_FILES}
    for path, digest in parent["source_files"].items():
        if sources.get(path) != digest:
            raise SystemExit(f"source file {path} changed since the Charter 4 registration")
    if sources[PARENT_CHARTER] != parent["charter"]["sha256"]:
        raise SystemExit("the Charter 4 text differs from the one registered for its run")
    if DATASET in parent_spec["datasets"]:
        raise SystemExit(f"dataset {DATASET} already exists in the parent registration")
    program = f"llm-v2-charter5-{date}"
    spec = {"schema_version": 1, "program_id": program, "families": {FAMILY_KEY: parent_spec["families"][FAMILY_KEY]},
            "datasets": {**parent_spec["datasets"],                     # verbatim, used by the parents
                         DATASET: {"identity": DATASET_IDENTITY, "history_reference": HISTORY,
                                   "exposures": [{**WINDOW, "state": "exposed"}]}},
            "experiments": {
                **parent_spec["experiments"],                           # verbatim, required by parent admission
                experiment_id(date): {
                    "family": FAMILY_KEY, "parent": PARENT, "question": QUESTION,
                    "charter": {"path": CHARTER, "sha256": _sha(CHARTER)}, "stage": "development", "reuse": "exploratory",
                    "selection": None,
                    "source_files": sources, "runtime_hashes": runtime_hashes(),
                    "windows": [{"dataset": DATASET, **WINDOW, "availability": "existing"}],
                    "inputs": inputs, "cells": list(CELLS), "outputs": list(OUTPUTS)}}}
    return f"research/{program}/gates.json", spec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--date", required=True, help="YYYYMMDD used in program/experiment ids")
    ap.add_argument("--check", action="store_true", help="build and validate the registration without writing it")
    args = ap.parse_args(argv)
    if not args.check and DRAFT_MARK in (ROOT / CHARTER).read_text():
        raise SystemExit("charter still marked DRAFT; freeze it first")
    store_digest()
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
