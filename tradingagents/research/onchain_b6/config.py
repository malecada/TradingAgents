# tradingagents/research/onchain_b6/config.py
"""Frozen B6 configuration (research/onchain-b6-2026-10-19/config/b6.json)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b6-2026-10-19'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b6'
B2_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b2'
B4_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b4'
B5_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b5'
EPOCH = date(2017, 1, 1)


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b6.json').read_text())


def days(cfg=None) -> list:
    w = (cfg or load())['window']
    return [d.date().isoformat() for d in pd.date_range(w['first_day'], w['last_day'], freq='D')]


def day_ord(day) -> int:
    return (date.fromisoformat(day) - EPOCH).days
