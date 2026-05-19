# tests/strategies/test_sltp_sweep.py
"""Tests for take-profit extension to run_coin_backtest + sweep harness."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402


def test_take_profit_triggers_and_diverges_from_no_tp_path():
    """TP=5% fires on monotonically rising long → equity diverges from TP=off path.

    One-bar-flatten semantics (mirror of SL): when TP fires at bar i, the bar's
    return is already credited, target_pos is set to 0, and the position is
    re-entered at bar i+1 (entry_equity resets).  With a small round-trip fee,
    each forced exit+re-entry costs something, so eq_tp[-1] < eq_no_tp[-1].
    """
    n = 15
    dates = np.arange(n)
    prices = 100.0 * (1.01 ** np.arange(n))
    positions = np.ones(n)

    costs_with_fee = dict(
        fee_rate=0.001, slippage=0.0, spread=0.0,
        price_impact=0.0, funding_rate=0.0,
        max_portfolio_dd=1.0,  # disabled
    )
    common = dict(
        dates=dates, prices=prices, positions=positions,
        initial_capital=10_000.0, stop_loss=1.0,
        **costs_with_fee,
    )
    eq_no_tp, _ = run_coin_backtest(take_profit=0.0, **common)
    eq_tp, _ = run_coin_backtest(take_profit=0.05, **common)
    eq_no_tp = np.asarray(eq_no_tp)
    eq_tp = np.asarray(eq_tp)

    assert not np.allclose(eq_no_tp, eq_tp), \
        "TP=0.05 produced identical equity to TP=off — TP never fired or costs are zero"
    assert eq_tp[-1] < eq_no_tp[-1], (
        f"TP final {eq_tp[-1]:.2f} should be < no-TP {eq_no_tp[-1]:.2f} "
        "(each TP-triggered round-trip costs fees)"
    )
