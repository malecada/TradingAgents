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


def test_intrabar_tp_truncates_bar_return_at_tp_price():
    """Long position, price ramps up. On bar where high >= entry*(1+TP),
    bar return must be TP%, not the full close-to-close gain (if smaller)."""
    n = 10
    dates = np.arange(n)
    closes = np.array([100.0] * n)
    closes[1:] = 100.0 * (1.005 ** np.arange(n - 1))  # +0.5%/bar = small
    highs = closes.copy()
    highs[5] = 108.0  # big upward wick (+8%) above TP=5% from entry close=100
    lows = closes * 0.999
    positions = np.ones(n)

    eq_intrabar, _ = run_coin_backtest(
        dates=dates, prices=closes, positions=positions,
        initial_capital=10_000.0,
        stop_loss=1.0, take_profit=0.05,
        intrabar=True, highs=highs, lows=lows,
        **_COSTS_NO,
    )
    eq_no_intrabar, _ = run_coin_backtest(
        dates=dates, prices=closes, positions=positions,
        initial_capital=10_000.0,
        stop_loss=1.0, take_profit=0.05,
        intrabar=False,
        **_COSTS_NO,
    )
    eq_intrabar = np.asarray(eq_intrabar)
    eq_no_intrabar = np.asarray(eq_no_intrabar)

    # Intrabar TP captures the wick; close-only TP cannot (high never reaches
    # close). So intrabar bar-5 equity must be strictly higher than close-only.
    assert eq_intrabar[5] > eq_no_intrabar[5], (
        f"intrabar TP must increase equity at bar 5 via wick capture: "
        f"intrabar={eq_intrabar[5]:.2f} close-only={eq_no_intrabar[5]:.2f}"
    )


def test_intrabar_same_bar_collision_is_sl_first_pessimistic():
    """When low <= SL_price AND high >= TP_price in the same bar, fill at SL."""
    n = 5
    dates = np.arange(n)
    # Entry close at bar 1 = 100. Bar 2 has BOTH SL hit (low=94) AND TP hit
    # (high=110). Close=100 (flat). SL-first pessimistic must pick SL.
    closes = np.array([100.0, 100.0, 100.0, 100.0, 100.0])
    highs = np.array([100.0, 100.0, 110.0, 100.0, 100.0])
    lows = np.array([100.0, 100.0, 94.0, 100.0, 100.0])
    positions = np.ones(n)

    eq, _ = run_coin_backtest(
        dates=dates, prices=closes, positions=positions,
        initial_capital=10_000.0,
        stop_loss=0.05, take_profit=0.08,
        intrabar=True, highs=highs, lows=lows,
        **_COSTS_NO,
    )
    eq = np.asarray(eq)

    # Bar 2: entry_price = closes[1] = 100. SL_price = 95. TP_price = 108.
    # Both lo=94 (≤95) and hi=110 (≥108) triggered. SL-first → fill at 95.
    # Equity at bar 2 = equity[1] * (1 + 1.0 * (95 - 100)/100) = equity[1] * 0.95
    # If TP-first were used (wrong), equity[2] = equity[1] * 1.08 (much higher).
    assert eq[2] < eq[1], (
        f"SL-first should reduce equity on collision bar: "
        f"got eq[1]={eq[1]:.2f}, eq[2]={eq[2]:.2f}"
    )
    # Strong assertion: ratio close to 0.95 (SL fill), not 1.08 (TP fill)
    ratio = eq[2] / eq[1]
    assert 0.94 < ratio < 0.96, (
        f"SL-first fill must produce ~5% loss on bar 2: ratio={ratio:.4f} "
        f"(SL=0.95, TP=1.08); SL-first is the pessimistic choice"
    )


def test_intrabar_true_without_highs_raises():
    """intrabar=True requires highs and lows; missing arrays must raise."""
    dates = np.arange(5)
    prices = np.array([100.0] * 5)
    positions = np.ones(5)
    common = dict(
        dates=dates, prices=prices, positions=positions,
        initial_capital=10_000.0, stop_loss=0.05, take_profit=0.0,
        **_COSTS_NO,
    )
    with pytest.raises(ValueError, match="intrabar=True requires"):
        run_coin_backtest(intrabar=True, **common)
    with pytest.raises(ValueError, match="intrabar=True requires"):
        run_coin_backtest(intrabar=True, highs=np.zeros(5), **common)
    with pytest.raises(ValueError, match="intrabar=True requires"):
        run_coin_backtest(intrabar=True, lows=np.zeros(5), **common)
