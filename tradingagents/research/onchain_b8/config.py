# tradingagents/research/onchain_b8/config.py
"""Frozen B8 configuration (research/onchain-b8-2026-10-22/config/b8.json) and the frozen
universe (config/universe.json)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b8-2026-10-22'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b8'
B6_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b6'
KLINES = ROOT.parent / 'TradingAgents' / 'data' / 'xsect' / 'klines_1h'
TOKEN_MAP = ROOT.parent / 'TradingAgents-predlab' / 'data' / 'predlab' / 'smw' / 'token_map.json'
EPOCH = date(2017, 1, 1)             # B6's day-ordinal epoch: the activation table is B6's


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b8.json').read_text())


def universe() -> list:
    return json.loads((STUDY / 'config' / 'universe.json').read_text())['tokens']


def days(cfg=None) -> list:
    w = (cfg or load())['window']
    return [d.date().isoformat() for d in pd.date_range(w['first_day'], w['last_day'], freq='D')]


def day_ord(day) -> int:
    return (date.fromisoformat(day) - EPOCH).days
