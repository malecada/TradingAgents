"""Build the lifecycle registration for Charter 3 (target change: next-week volatility) from committed files.

Fourth attempt of family llm-multiagent-v2: same family entry and attempt budget, the dataset and experiment
entries of the Charter 2 registration copied verbatim (parent admission), a new dataset entry for the reader
records joined with the daily bars. Run after the charter is frozen (status line changed from DRAFT) and the
source files are committed. Writes research/llm-v2-charter3-<date>/gates.json and never overwrites.
Usage: reader_charter3_register.py --date 20261113            (--check validates without writing)
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
CHARTER = "docs/superpowers/specs/2026-11-13-llm-v2-charter3-volatility-charter.md"
EXTRACTION_CHARTER = "docs/superpowers/specs/2026-11-12-llm-v2-charter2-reader-charter.md"     # frozen, text of the extraction
DRAFT_MARK = "DRAFT, NOT FROZEN"
PARENT_REGISTRATION = "research/llm-v2-charter2-20261112/gates.json"
PARENT = "llm-v2c2-reader-dev-run-20261112"
FAMILY_KEY = "llm-multiagent-v2"
DATASET = "dev-reader-volatility-2022-2024"
DATASET_IDENTITY = "multiagent-v2-dev-reader-records-daily-bars-v1"
WINDOW = {"start": "2022-01-01T00:00:00Z", "end": "2025-01-08T00:00:00Z"}
# Every project file the registered run imports (the research helper is pinned by its runtime hashes), every file
# pinned by the Charter 2 registration (extraction, reading list, key loader: unchanged since), the charter text
# under which the records were extracted and the dependency lock. A test compares this with the imports.
SOURCE_FILES = (
    "tradingagents/__init__.py", "tradingagents/reader/__init__.py", "tradingagents/reader/schema.py",
    "tradingagents/reader/reading.py", "tradingagents/reader/extract.py", "tradingagents/reader/consensus.py",
    "tradingagents/reader/features.py", "tradingagents/reader/model.py", "tradingagents/reader/charter2.py",
    "tradingagents/reader/charter3.py", "tradingagents/reader/items.py",
    "tradingagents/agents_v2/__init__.py", "tradingagents/agents_v2/charter1b.py", "tradingagents/agents_v2/evaluate.py",
    "tradingagents/agents_v2/portfolio_eval.py", "tradingagents/agents_v2/graph.py", "tradingagents/agents_v2/roles.py",
    "tradingagents/agents_v2/schemas.py",
    "tradingagents/dossier/__init__.py", "tradingagents/dossier/or_client.py", "tradingagents/dossier/quant_forecast.py",
    "tradingagents/dossier/universe.py", "tradingagents/dossier/builder.py", "tradingagents/dossier/anonymizer.py",
    "tradingagents/dossier/calendar.py", "tradingagents/dossier/entities.py", "tradingagents/dossier/llm_text.py",
    "tradingagents/dossier/numeric_card.py", "tradingagents/dossier/store.py",
    "scripts/reader_extract.py", "scripts/reader_charter2_run.py", "scripts/reader_charter2_register.py",
    "scripts/reader_charter3_run.py", "scripts/reader_charter3_register.py",
    "scripts/reader_items_build.py", "scripts/llm_v2c0_client.py", "scripts/llm_v2c0_prompt.py",
    "scripts/llm_event_xs_extract.py", "scripts/llm_jev_questions.py",
    EXTRACTION_CHARTER,
    "uv.lock",
)
INPUTS = {
    "items": "data/reader/items.parquet",
    "docs": "data/reader/docs.parquet",
    "cards": "data/llm_rank_xs/cards.parquet",
    "calls": "data/reader/calls.jsonl",
    "records": "data/reader/records.parquet",
    "extraction_manifest": "data/reader/extraction_manifest.json",
    "klines_digest": "data/agents_v2/charter1/klines_digest.json",
}
SAME_AS_PARENT = tuple(INPUTS)                                          # every input has the bytes of the Charter 2 run
HISTORY = ("Fact records of two reader agents and an adjudicator over the typed news and community items of the weekly "
           "top-50 perp universe 2022-01 to 2024-12 (reader store data/reader, extracted under Charter 2), joined with "
           "the card panel and the daily bars of the same contracts. The whole window is exposed. Text features built "
           "from these records were joined with the forward weekly returns of the 156 weeks in "
           "llm-v2c2-reader-dev-run-20261112 (verdict FAIL, 104 test weeks); the attention counts carried the weak "
           "return signal found there and the reader judgements none. The daily bars of the window were used by earlier "
           "programs of the repository, also for volatility forecasts from price, option and on-chain data. Before this "
           "registration no feature built from the records was joined with a realised variance, a range or any other "
           "price quantity dated after its decision, and no gate statistic of Charter 3 was computed; the features were "
           "joined with price history up to the decision only (coverage, simulation of the gate on synthetic targets). "
           "Bars dated before 2022-01-01 were used to measure, from price alone, how persistent the target residual is "
           "and how curved its relation to the price history is.")
QUESTION = ("Do unsigned asset-week features built by code from the de-identified fact records of Charter 2 carry "
            "information on the realised variance of the next seven days, relative to the other assets of the week, "
            "beyond price history up to the decision and beyond attention counts, on the 104 test weeks 2023-01 to "
            "2024-12? Gate: weekly partial correlation of a walk-forward ridge score of the reader features with the "
            "target, the history and attention controls removed from both in two steps (a flexible fit on earlier "
            "weeks, then a regression within the week), Newey-West t at least 2.0 and positive mean in both years.")


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def experiment_id(date: str) -> str:
    return f"llm-v2c3-volatility-dev-run-{date}"


def build(date: str) -> tuple[str, dict]:
    from reader_charter3_run import CELLS, OUTPUTS
    from tradingagents.research.admission import runtime_hashes
    parent_spec = json.loads((ROOT / PARENT_REGISTRATION).read_text())
    parent = parent_spec["experiments"][PARENT]
    inputs = {name: {"path": path, "sha256": _sha(path), "dataset": DATASET} for name, path in INPUTS.items()}
    for name in SAME_AS_PARENT:
        if inputs[name]["sha256"] != parent["inputs"][name]["sha256"]:
            raise SystemExit(f"input {name} differs from the Charter 2 registration")
    sources = {p: _sha(p) for p in SOURCE_FILES}
    for path, digest in parent["source_files"].items():
        if sources.get(path) != digest:
            raise SystemExit(f"source file {path} changed since the Charter 2 registration")
    if sources[EXTRACTION_CHARTER] != parent["charter"]["sha256"]:
        raise SystemExit("the Charter 2 text differs from the one registered for its run")
    if DATASET in parent_spec["datasets"]:
        raise SystemExit(f"dataset {DATASET} already exists in the parent registration")
    program = f"llm-v2-charter3-{date}"
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
