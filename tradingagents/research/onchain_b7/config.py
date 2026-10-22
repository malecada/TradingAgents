# tradingagents/research/onchain_b7/config.py
"""Frozen B7 configuration (research/onchain-b7-2026-10-22/config/b7.json)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b7-2026-10-22'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b7'
B4_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b4'
B6_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b6'


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b7.json').read_text())
