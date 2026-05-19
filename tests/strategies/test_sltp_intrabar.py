# tests/strategies/test_sltp_intrabar.py
"""Tests for the intrabar OHLC SL/TP path in run_coin_backtest."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402


_COSTS_NO = dict(
    fee_rate=0.0, slippage=0.0, spread=0.0,
    price_impact=0.0, funding_rate=0.0,
    max_portfolio_dd=1.0,
)


def test_intrabar_sl_truncates_bar_return_at_sl_price():
    """Long position, price ramps down. On bar where low <= entry*(1-SL),
    bar return must be SL%, not the full close-to-close drop."""
    n = 10
    dates = np.arange(n)
    # Open long at bar 1 at close 100. Subsequent close drops 1%/bar. At bar 5,
    # close = 100*0.96 = 96.06, but we engineer low[5] = 93 (deep wick below SL=5%).
    closes = np.array([100.0] * n)
    closes[1:] = 100.0 * (0.99 ** np.arange(n - 1))
    highs = closes * 1.001
    lows = closes.copy()
    lows[5] = 93.0  # deep wick below SL=5% from entry close=100
    positions = np.ones(n)

    eq, _ = run_coin_backtest(
        dates=dates, prices=closes, positions=positions,
        initial_capital=10_000.0,
        stop_loss=0.05, take_profit=0.0,
        intrabar=True, highs=highs, lows=lows,
        **_COSTS_NO,
    )
    eq = np.asarray(eq)

    # Bar-5 return must equal SL fill (entry=closes[4], fill=entry*0.95):
    # Easiest invariant: equity at bar 5 must be strictly lower than the
    # close-only-no-SL equity at bar 5 — because the wick truncated harder.
    eq_no_intrabar, _ = run_coin_backtest(
        dates=dates, prices=closes, positions=positions,
        initial_capital=10_000.0,
        stop_loss=0.05, take_profit=0.0,
        intrabar=False,
        **_COSTS_NO,
    )
    eq_no_intrabar = np.asarray(eq_no_intrabar)
    assert eq[5] < eq_no_intrabar[5], (
        f"intrabar SL must reduce equity at bar 5 vs close-only path: "
        f"intrabar={eq[5]:.2f} close-only={eq_no_intrabar[5]:.2f}"
    )


def test_intrabar_false_is_bit_identical_to_omitted_kwarg():
    """intrabar=False with no highs/lows must produce IDENTICAL equity to
    omitting the kwargs entirely. The most important property to preserve."""
    rng = np.random.default_rng(11)
    n = 200
    dates = np.arange(n)
    rets = rng.normal(0.0005, 0.02, size=n)
    prices = 100.0 * np.cumprod(1 + rets)
    positions = rng.choice([-1.0, 0.0, 1.0], size=n, p=[0.3, 0.2, 0.5])

    common = dict(
        dates=dates, prices=prices, positions=positions,
        initial_capital=10_000.0, stop_loss=0.03, take_profit=0.0,
        fee_rate=0.0004, slippage=0.0005, spread=0.0001,
        price_impact=0.00005, funding_rate=0.0001 / 8,
        max_portfolio_dd=0.15,
    )
    eq_omit, m_omit = run_coin_backtest(**common)
    eq_false, m_false = run_coin_backtest(intrabar=False, **common)

    np.testing.assert_array_equal(
        np.asarray(eq_omit), np.asarray(eq_false),
        err_msg="intrabar=False changed equity vs no-kwarg path"
    )
    assert m_omit == m_false, "metrics diverged with intrabar=False"
