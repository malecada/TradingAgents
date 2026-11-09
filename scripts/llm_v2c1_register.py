"""Build the lifecycle registration for Charter 1 (dev run) from committed files.
Run after llm_v2c1_manifest.py and the reid probe (--all) outputs are committed, and after the charter
is frozen (status line changed from DRAFT). Writes research/llm-v2-charter1-<date>/gates.json.
Usage: llm_v2c1_register.py --date 20261112
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_v2c1_run import CELLS, OUTPUTS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CHARTER = "docs/superpowers/specs/2026-11-09-llm-v2-charter1-dev-run-charter.md"
SOURCE_FILES = (
    "tradingagents/agents_v2/__init__.py", "tradingagents/agents_v2/schemas.py", "tradingagents/agents_v2/roles.py",
    "tradingagents/agents_v2/graph.py", "tradingagents/agents_v2/runner.py", "tradingagents/agents_v2/evaluate.py",
    "tradingagents/agents_v2/portfolio_eval.py", "tradingagents/dossier/or_client.py", "tradingagents/dossier/quant_forecast.py",
    "tradingagents/dossier/numeric_card.py", "scripts/llm_v2c1_run.py", "scripts/llm_v2c1_manifest.py", "scripts/llm_v2c0_client.py",
    "uv.lock", "tradingagents/__init__.py",
)
FAMILY_KEY = "llm-multiagent-v2"
FAMILY = {"mechanism_id": "dossier-fed-anonymized-debate-cross-section", "attempt_budget": 6, "prior_attempts": 0,
          "history_reference": ("New mechanism: deterministic anonymized dossiers feeding schema-constrained analysts, an "
                                "order-swapped debate and a judge, weekly over the top-50 perp cross-section. The legacy "
                                "tool-fetching multi-agent cells on named daily BTC/ETH (THESIS_FINDINGS 23, 48) are a different "
                                "mechanism and are cited as history only.")}
DATASET = "dev-dossiers-2022-2024"


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYYMMDD used in program/experiment ids")
    args = ap.parse_args()
    charter = (ROOT / CHARTER).read_text()
    if "DRAFT, NOT FROZEN" in charter:
        raise SystemExit("charter still marked DRAFT; freeze it first")
    manifest = json.loads((ROOT / "data/agents_v2/charter1/dossier_manifest.json").read_text())
    program = f"llm-v2-charter1-{args.date}"
    experiment = f"llm-v2c1-dev-run-{args.date}"
    from tradingagents.research.admission import runtime_hashes
    inputs = {
        "dossier_manifest": {"path": "data/agents_v2/charter1/dossier_manifest.json", "sha256": _sha("data/agents_v2/charter1/dossier_manifest.json"), "dataset": DATASET},
        "klines_digest": {"path": "data/agents_v2/charter1/klines_digest.json", "sha256": _sha("data/agents_v2/charter1/klines_digest.json"), "dataset": DATASET},
        "agent_config": {"path": "data/agents_v2/charter1/agent_config.json", "sha256": _sha("data/agents_v2/charter1/agent_config.json"), "dataset": DATASET},
        "cards": {"path": "data/llm_rank_xs/cards.parquet", "sha256": _sha("data/llm_rank_xs/cards.parquet"), "dataset": DATASET},
        "quant_forecasts": {"path": "data/dossier/quant_forecasts.parquet", "sha256": _sha("data/dossier/quant_forecasts.parquet"), "dataset": DATASET},
    }
    if (ROOT / "data/dossier/reid_flags.parquet").exists():
        (ROOT / "data/agents_v2/charter1/reid_flags_path.json").write_text(json.dumps({"path": "data/dossier/reid_flags.parquet"}) + "\n")
        inputs["reid_flags_path"] = {"path": "data/agents_v2/charter1/reid_flags_path.json", "sha256": _sha("data/agents_v2/charter1/reid_flags_path.json"), "dataset": DATASET}
        inputs["reid_flags"] = {"path": "data/dossier/reid_flags.parquet", "sha256": _sha("data/dossier/reid_flags.parquet"), "dataset": DATASET}
    spec = {"schema_version": 1, "program_id": program, "families": {FAMILY_KEY: dict(FAMILY)},
            "datasets": {DATASET: {"identity": f"multiagent-v2-dev-dossiers-{manifest['builder_version']}",
                                   "history_reference": ("Dossiers built from Wayback news, Arctic Shift Reddit and the card panel; "
                                                         "pilot weeks 2022-01-07 and 2022-01-14 were exposed during validity probes "
                                                         "(research/multiagent-v2/STATE.md); the re-identification probe inspected every dossier."),
                                   "exposures": [{"start": "2022-01-01T00:00:00Z", "end": "2022-01-22T00:00:00Z", "state": "exposed"}]}},
            "experiments": {experiment: {
                "family": FAMILY_KEY, "parent": None,
                "question": ("Does the dossier-fed anonymized multi-agent system produce weekly cross-sectional forecasts with "
                             "detectable skill on 2022-01 to 2024-12, and does it add skill over the quant-only ridge twin?"),
                "charter": {"path": CHARTER, "sha256": _sha(CHARTER)}, "stage": "development", "reuse": "exploratory", "selection": None,
                "source_files": {p: _sha(p) for p in SOURCE_FILES}, "runtime_hashes": runtime_hashes(),
                "windows": [{"dataset": DATASET, "start": "2022-01-01T00:00:00Z", "end": "2025-01-08T00:00:00Z", "availability": "existing"}],
                "inputs": inputs, "cells": list(CELLS), "outputs": list(OUTPUTS)}}}
    target = ROOT / "research" / program / "gates.json"
    if target.exists():
        raise SystemExit(f"{target} exists; registrations are never overwritten")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n")
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
