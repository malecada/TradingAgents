"""Build the lifecycle registration for Charter 2 (reader configuration) from committed files.

Third attempt of family llm-multiagent-v2: same family entry and attempt budget, the experiment entries of the
Charter 1b registration copied verbatim (parent admission), a new dataset entry for the reader records. Run
after the charter is frozen (status line changed from DRAFT), the extraction is complete and the source files
are committed. Writes research/llm-v2-charter2-<date>/gates.json and never overwrites.
Usage: reader_charter2_register.py --date 20261113            (--check validates without writing)
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
CHARTER = "docs/superpowers/specs/2026-11-12-llm-v2-charter2-reader-charter.md"
DRAFT_MARK = "DRAFT, NOT FROZEN"
PARENT_REGISTRATION = "research/llm-v2-charter1b-20261112/gates.json"
PARENT = "llm-v2c1b-dev-run-20261112"
FAMILY_KEY = "llm-multiagent-v2"
PARENT_DATASET = "dev-dossiers-2022-2024"
DATASET = "dev-reader-2022-2024"
DATASET_IDENTITY = "multiagent-v2-dev-reader-records-v1"
WINDOW = {"start": "2022-01-01T00:00:00Z", "end": "2025-01-08T00:00:00Z"}
# Every project file the registered run, the extraction and the key loader import (the research helper is pinned
# by its runtime hashes), the reading-list builder and the dependency lock. A test compares this with the imports.
SOURCE_FILES = (
    "tradingagents/__init__.py", "tradingagents/reader/__init__.py", "tradingagents/reader/schema.py",
    "tradingagents/reader/reading.py", "tradingagents/reader/extract.py", "tradingagents/reader/consensus.py",
    "tradingagents/reader/features.py", "tradingagents/reader/model.py", "tradingagents/reader/charter2.py",
    "tradingagents/reader/items.py",
    "tradingagents/agents_v2/__init__.py", "tradingagents/agents_v2/charter1b.py", "tradingagents/agents_v2/evaluate.py",
    "tradingagents/agents_v2/portfolio_eval.py", "tradingagents/agents_v2/graph.py", "tradingagents/agents_v2/roles.py",
    "tradingagents/agents_v2/schemas.py",
    "tradingagents/dossier/__init__.py", "tradingagents/dossier/or_client.py", "tradingagents/dossier/quant_forecast.py",
    "tradingagents/dossier/universe.py", "tradingagents/dossier/builder.py", "tradingagents/dossier/anonymizer.py",
    "tradingagents/dossier/calendar.py", "tradingagents/dossier/entities.py", "tradingagents/dossier/llm_text.py",
    "tradingagents/dossier/numeric_card.py", "tradingagents/dossier/store.py",
    "scripts/reader_extract.py", "scripts/reader_charter2_run.py", "scripts/reader_charter2_register.py",
    "scripts/reader_items_build.py", "scripts/llm_v2c0_client.py", "scripts/llm_v2c0_prompt.py",
    "scripts/llm_event_xs_extract.py", "scripts/llm_jev_questions.py",
    "uv.lock",
)
INPUTS = {
    "items": "data/reader/items.parquet",
    "docs": "data/reader/docs.parquet",
    "cards": "data/llm_rank_xs/cards.parquet",
    "calls": "data/reader/calls.jsonl",
    "records": "data/reader/records.parquet",
    "extraction_manifest": "data/reader/extraction_manifest.json",
    "quant_forecasts": "data/dossier/quant_forecasts.parquet",
    "reid_flags": "data/dossier/reid_flags_v26.parquet",
    "klines_digest": "data/agents_v2/charter1/klines_digest.json",
    "funding_digest": "data/agents_v2/charter1b/funding_digest.json",
}
SAME_AS_PARENT = ("cards", "quant_forecasts", "reid_flags", "klines_digest", "funding_digest")     # same bytes as Charter 1b
HISTORY = ("Fact records of two reader agents and an adjudicator over the typed news and community items of the weekly "
           "top-50 perp universe 2022-01 to 2024-12 (reader store data/reader, record schema and instructions of Charter 2), "
           "joined with the same card panel, forward returns and funding as the dossier dataset of the family. The whole "
           "window is exposed: the forward returns of 66 of its weeks were joined with agent forecasts in "
           "llm-v2c1b-dev-run-20261112 (verdict FAIL), the quant forecast and the card features were developed on the "
           "window, and earlier programs used the same returns. Before this registration the records were read only by "
           "code that never joins an outcome (extraction quality, coverage); no text feature was joined with a forward "
           "return and no gate statistic was computed.")
QUESTION = ("Do asset-week features built by code from de-identified fact records of two reader agents and an adjudicator "
            "carry weekly cross-sectional forecast information beyond the existing quant forecast on the 104 test weeks "
            "2023-01 to 2024-12, when a fitted walk-forward ridge model, not an agent, makes the forecast? Gate: "
            "encompassing coefficient of the text-only score next to the quant forecast, t at least 2.0 and positive in "
            "both years.")


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build(date: str) -> tuple[str, dict]:
    from reader_charter2_run import CELLS, OUTPUTS
    from tradingagents.research.admission import runtime_hashes
    parent_spec = json.loads((ROOT / PARENT_REGISTRATION).read_text())
    parent = parent_spec["experiments"][PARENT]
    inputs = {name: {"path": path, "sha256": _sha(path), "dataset": DATASET} for name, path in INPUTS.items()}
    for name in SAME_AS_PARENT:
        if inputs[name]["sha256"] != parent["inputs"][name]["sha256"]:
            raise SystemExit(f"input {name} differs from the Charter 1b registration")
    program, experiment = f"llm-v2-charter2-{date}", f"llm-v2c2-reader-dev-run-{date}"
    spec = {"schema_version": 1, "program_id": program, "families": {FAMILY_KEY: parent_spec["families"][FAMILY_KEY]},
            "datasets": {PARENT_DATASET: parent_spec["datasets"][PARENT_DATASET],            # verbatim, used by the parents
                         DATASET: {"identity": DATASET_IDENTITY, "history_reference": HISTORY,
                                   "exposures": [{**WINDOW, "state": "exposed"}]}},
            "experiments": {
                **parent_spec["experiments"],                           # verbatim, required by parent admission
                experiment: {
                    "family": FAMILY_KEY, "parent": PARENT, "question": QUESTION,
                    "charter": {"path": CHARTER, "sha256": _sha(CHARTER)}, "stage": "development", "reuse": "exploratory",
                    "selection": None,
                    "source_files": {p: _sha(p) for p in SOURCE_FILES}, "runtime_hashes": runtime_hashes(),
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
    exp = spec["experiments"][f"llm-v2c2-reader-dev-run-{args.date}"]
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
