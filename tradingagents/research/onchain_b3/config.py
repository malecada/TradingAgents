"""Frozen B3 configuration (research/onchain-b3-2026-10-14/config/b3.json)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b3-2026-10-14'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b3'
B2_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b2'


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b3.json').read_text())