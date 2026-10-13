"""Frozen B2 configuration (research/onchain-b2-2026-10-13/config/b2.json)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b2-2026-10-13'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b2'


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b2.json').read_text())