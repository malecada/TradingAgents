"""Frozen protocol configuration for Branch B (research/onchain-replication-b-2026-10-12/config)."""
from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-replication-b-2026-10-12'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-replication-b'


def load(name: str) -> dict:
    return json.loads((STUDY / 'config' / f'{name}.json').read_text())
