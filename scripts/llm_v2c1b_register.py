"""Build the lifecycle registration for Charter 1b (replacement of the Charter 1 dev run) from committed files.

The registration is a follow-up of the failed first attempt: same family and attempt budget, same dataset
identity, the parent experiment entry copied verbatim from its own registration. Run after the source files,
the cache manifest and the funding digest are committed and the charter is frozen (status line changed from
DRAFT). Writes research/llm-v2-charter1b-<date>/gates.json and never overwrites.
Usage: llm_v2c1b_register.py --date 20261112            (--check validates without writing)
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
CHARTER = "docs/superpowers/specs/2026-11-11-llm-v2-charter1b-dev-run-charter.md"
PARENT_REGISTRATION = "research/llm-v2-charter1-20261111/gates.json"
PARENT = "llm-v2c1-dev-run-20261111"
FAMILY_KEY = "llm-multiagent-v2"
DATASET = "dev-dossiers-2022-2024"
# files of the agent system, the dossier side and the environment: byte-identical to the parent registration
UNCHANGED = (
    "tradingagents/agents_v2/__init__.py", "tradingagents/agents_v2/schemas.py", "tradingagents/agents_v2/roles.py",
    "tradingagents/agents_v2/graph.py", "tradingagents/agents_v2/runner.py", "tradingagents/dossier/or_client.py",
    "tradingagents/dossier/quant_forecast.py", "tradingagents/dossier/numeric_card.py", "tradingagents/dossier/universe.py",
    "scripts/llm_v2c0_client.py", "uv.lock", "tradingagents/__init__.py",
)
# evaluation tail and run script: changed or new in the replacement
CHANGED = (
    "tradingagents/agents_v2/evaluate.py", "tradingagents/agents_v2/portfolio_eval.py", "tradingagents/agents_v2/charter1b.py",
    "scripts/llm_v2c1b_run.py", "scripts/llm_v2c1b_manifest.py", "scripts/llm_v2c1b_register.py",
)
# registered inputs: the parent's inputs by the same bytes, plus the call-cache manifest and the funding digest
INPUTS = {
    "dossier_manifest": "data/agents_v2/charter1/dossier_manifest.json",
    "klines_digest": "data/agents_v2/charter1/klines_digest.json",
    "agent_config": "data/agents_v2/charter1/agent_config.json",
    "cards": "data/llm_rank_xs/cards.parquet",
    "quant_forecasts": "data/dossier/quant_forecasts.parquet",
    "reid_flags": "data/dossier/reid_flags_v26.parquet",
    "cache_manifest": "data/agents_v2/charter1b/cache_manifest.json",
    "funding_digest": "data/agents_v2/charter1b/funding_digest.json",
}
NEW_INPUTS = ("cache_manifest", "funding_digest")
HISTORY_ADDENDUM = (" First registered attempt llm-v2c1-dev-run-20261111 (started 2026-11-10, interrupted 2026-11-11 12:14 UTC, "
                    "failed receipt): the agent forecasts of the 61 newest weeks (2023-11-03 to 2024-12-27) and part of week "
                    "2023-10-27 were generated and cached; its evaluation tail never ran, no forecast was joined with a "
                    "forward return and no gate statistic was computed. The replacement reuses those cached calls.")


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build(date: str) -> tuple[str, dict]:
    from llm_v2c1b_run import CELLS, OUTPUTS
    from tradingagents.research.admission import runtime_hashes
    parent_spec = json.loads((ROOT / PARENT_REGISTRATION).read_text())
    parent = parent_spec["experiments"][PARENT]
    for path in UNCHANGED:
        if _sha(path) != parent["source_files"][path]:
            raise SystemExit(f"{path} differs from the parent registration; the agent system must be unchanged")
    inputs = {name: {"path": path, "sha256": _sha(path), "dataset": DATASET} for name, path in INPUTS.items()}
    for name, item in inputs.items():
        if name not in NEW_INPUTS and item != parent["inputs"][name]:
            raise SystemExit(f"input {name} differs from the parent registration")
    dataset = json.loads(json.dumps(parent_spec["datasets"][DATASET]))
    dataset["history_reference"] += HISTORY_ADDENDUM
    program, experiment = f"llm-v2-charter1b-{date}", f"llm-v2c1b-dev-run-{date}"
    spec = {"schema_version": 1, "program_id": program, "families": {FAMILY_KEY: parent_spec["families"][FAMILY_KEY]},
            "datasets": {DATASET: dataset},
            "experiments": {
                PARENT: parent,                                         # verbatim, required by parent admission
                experiment: {
                    "family": FAMILY_KEY, "parent": PARENT,
                    "question": ("Does the dossier-fed anonymized multi-agent system produce weekly cross-sectional forecasts "
                                 "with detectable skill on the completed weeks of 2022-01 to 2024-12 (newest first under the "
                                 "Charter 1 spend cap), and does it add skill over the quant-only ridge twin? Replacement of "
                                 "the first attempt with a corrected evaluation tail; agents, prompts, dossiers and gate "
                                 "thresholds unchanged."),
                    "charter": {"path": CHARTER, "sha256": _sha(CHARTER)}, "stage": "development", "reuse": "exploratory",
                    "selection": None,
                    "source_files": {p: _sha(p) for p in (*UNCHANGED, *CHANGED)}, "runtime_hashes": runtime_hashes(),
                    "windows": [dict(w) for w in parent["windows"]],
                    "inputs": inputs, "cells": list(CELLS), "outputs": list(OUTPUTS)}}}
    return f"research/{program}/gates.json", spec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYYMMDD used in program/experiment ids")
    ap.add_argument("--check", action="store_true", help="build and validate the registration without writing it")
    args = ap.parse_args()
    if not args.check and "DRAFT, NOT FROZEN" in (ROOT / CHARTER).read_text():
        raise SystemExit("charter still marked DRAFT; freeze it first")
    target, spec = build(args.date)
    if args.check:
        exp = spec["experiments"][f"llm-v2c1b-dev-run-{args.date}"]
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
