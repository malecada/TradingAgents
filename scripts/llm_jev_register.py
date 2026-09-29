"""Build the lifecycle registrations for the Jev P0 probe from committed files.

  e1  research/llm-jev-event-2026-09-29/gates.json      (E1 only)
  e2  research/llm-jev-event-2026-09-29/gates_e2.json   (E1 unchanged + E2)
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_event_xs_truth import C1_DIR, ROUND_FILES, ROUNDS  # noqa: E402
from llm_jev_event_p0 import (  # noqa: E402
    E1, E1_CELLS, E1_OUTPUTS, E2, E2_CELLS, E2_OUTPUTS, PROGRAM_DIR, SHEET_PATH,
)

ROOT = Path(__file__).resolve().parents[1]
PROGRAM_ID = "llm-jev-event-2026-09-29"
CHARTER = "docs/superpowers/specs/2026-09-29-llm-jev-event-probe-charter.md"
SOURCE_FILES = (
    "scripts/llm_event_xs_truth.py", "scripts/llm_jev_questions.py", "scripts/llm_jev_client.py",
    "scripts/llm_jev_labels.py", "scripts/llm_jev_review.py", "scripts/llm_jev_score.py",
    "scripts/llm_jev_event_p0.py", "scripts/llm_jev_smoke.py", "scripts/llm_event_xs_extract.py",
    "scripts/llm_event_xs_p0_score.py", "uv.lock", "tradingagents/__init__.py",
)
FAMILY_KEY = "llm-news-event-extraction"
FAMILY = {
    "mechanism_id": "llm-typed-news-event-extraction",
    "attempt_budget": 12,
    "prior_attempts": 2,
    "history_reference": (
        "docs/superpowers/specs/2026-08-11-llm-c1-event-xs-charter.md and "
        "data/llm_event_xs/trial_ledger.jsonl: llm_c1_event_xs declared <=12 ledgered configs; "
        "P0 v1 (FAIL) and P0 v2 (STOP) consumed 2 on 2026-08-14 with gpt-5.4-mini; C1 dead "
        "that cycle (THESIS_FINDINGS section 63)."),
}
DATASET = "c1-p0-samples"
WINDOW = {"dataset": DATASET, "start": "2021-01-01T00:00:00Z",
          "end": "2025-04-01T00:00:00Z", "availability": "existing"}
DATASETS = {DATASET: {
    "identity": "llm-c1-event-xs-p0-samples-20260813",
    "history_reference": (
        "data/llm_event_xs/corpus_manifest.json frozen 2026-08-13; P0 v1 (300) and v2 (100) "
        "articles inspected 2026-08-14 with gpt-5.4-mini labels, claude-haiku-4-5 pre-labels "
        "and blind human adjudication."),
    "exposures": [{"start": "2021-01-01T00:00:00Z", "end": "2025-04-01T00:00:00Z",
                   "state": "exposed"}],
}}
E1_QUESTION = ("Label the 400 adjudicated C1 P0 articles with Jev (sole class extractor, no "
               "keyword prefilter) and emit the blind review sheet, without computing metrics.")
E2_QUESTION = ("Does Jev meet the C1 P0 extraction floors (per-class precision >= 0.8, recall "
               ">= 0.6, asset link >= 0.9, anonymization agreement >= 0.8) on the 400 "
               "adjudicated C1 P0 articles after blind human review of its disputes?")


def _sha(root: Path, path: str) -> str:
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def c1_inputs(root: Path) -> dict:
    return {f"{kind}_{rnd}": {"path": f"{C1_DIR}/{name}", "sha256": _sha(root, f"{C1_DIR}/{name}"),
                              "dataset": DATASET}
            for rnd in ROUNDS for kind, name in ROUND_FILES[rnd].items()}


def experiment(root: Path, *, parent, question, inputs, cells, outputs) -> dict:
    from tradingagents.research.admission import runtime_hashes
    return {"family": FAMILY_KEY, "parent": parent, "question": question,
            "charter": {"path": CHARTER, "sha256": _sha(root, CHARTER)},
            "stage": "development", "reuse": "exploratory", "selection": None,
            "source_files": {p: _sha(root, p) for p in SOURCE_FILES},
            "runtime_hashes": runtime_hashes(), "windows": [dict(WINDOW)],
            "inputs": inputs, "cells": list(cells), "outputs": list(outputs)}


def build_e1(root: Path) -> dict:
    return {"schema_version": 1, "program_id": PROGRAM_ID,
            "families": {FAMILY_KEY: dict(FAMILY)}, "datasets": copy.deepcopy(DATASETS),
            "experiments": {E1: experiment(root, parent=None, question=E1_QUESTION,
                                           inputs=c1_inputs(root), cells=E1_CELLS,
                                           outputs=E1_OUTPUTS)}}


def build_e2(root: Path) -> dict:
    """E1 entry is copied from the committed gates.json so it stays byte-for-byte equal."""
    spec = json.loads((root / PROGRAM_DIR / "gates.json").read_text())
    inputs = c1_inputs(root)
    for name in ("jev_labels", "jev_labels_anon", "review_sheet", "review_key", "run_meta"):
        path = f"research_runs/{E1}/outputs/{name}.json"
        inputs[name] = {"path": path, "sha256": _sha(root, path), "dataset": DATASET}
    inputs["review_filled"] = {"path": SHEET_PATH, "sha256": _sha(root, SHEET_PATH),
                               "dataset": DATASET}
    e2 = experiment(root, parent=E1, question=E2_QUESTION, inputs=inputs,
                    cells=E2_CELLS, outputs=E2_OUTPUTS)
    e1 = spec["experiments"][E1]
    if (e2["source_files"] != e1["source_files"]
            or e2["runtime_hashes"] != e1["runtime_hashes"]):
        raise SystemExit("source files or runtime hashes changed since E1 registration")
    spec["experiments"][E2] = e2
    return spec


def write(root: Path, name: str, spec: dict) -> Path:
    target = root / PROGRAM_DIR / name
    if target.exists():
        raise SystemExit(f"{target} exists; registrations are never overwritten")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n")
    return target


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("which", choices=("e1", "e2"))
    args = parser.parse_args(argv)
    if args.which == "e1":
        print(write(ROOT, "gates.json", build_e1(ROOT)))
    else:
        print(write(ROOT, "gates_e2.json", build_e2(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
