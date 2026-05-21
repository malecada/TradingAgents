# tests/strategies/test_v5_8coin.py
"""Tests for the V5 MIX 8-coin expansion: symbol map, cost tiers, weighting."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_tron_symbol_resolves():
    from tradingagents.dataflows.coingecko_binance import _KNOWN_SYMBOLS
    assert _KNOWN_SYMBOLS["tron"] == "TRXUSDT"
