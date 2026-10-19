# tradingagents/research/onchain_b5/config.py
"""Frozen B5 configuration (research/onchain-b5-2026-10-19/config/b5.json)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b5-2026-10-19'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b5'
B4_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b4'


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b5.json').read_text())


def days(cfg=None) -> list:
    w = (cfg or load())['window']
    return [d.date().isoformat() for d in pd.date_range(w['start'], w['end'], freq='D')]
