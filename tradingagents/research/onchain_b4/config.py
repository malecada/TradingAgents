# tradingagents/research/onchain_b4/config.py
"""Frozen B4 configuration (research/onchain-b4-2026-10-15/config/b4.json)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b4-2026-10-15'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b4'
B2_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b2'


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b4.json').read_text())


def windows(cfg=None) -> dict:
    return {k: date.fromisoformat(v) for k, v in (cfg or load())['windows'].items()}


def days(cfg=None) -> list:
    p = (cfg or load())['pass']
    return [d.date().isoformat() for d in pd.date_range(p['first_day'], p['last_day'], freq='D')]
