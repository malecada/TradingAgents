# tests/strategies/test_intraday_fills.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.baseline_strategy_v2 import run_coin_backtest
from scripts.intraday_fills import group_intraday_by_day, run_coin_backtest_intrabar

COSTS = dict(
    fee_rate=0.0004, slippage=0.0005, spread=0.0001, price_impact=0.00005,
    funding_rate=0.0001 / 8, stop_loss=0.03, max_portfolio_dd=0.15, take_profit=0.0,
)


def _flat_day_bars(prices, n_bars=4):
    """Intraday bars all at that day's close → no intraday excursion → barriers
    can only fire on close-to-close moves → intrabar MUST match daily engine."""
    day_map = {}
    for i, p in enumerate(prices):
        day_map[i] = np.array([[p, p]] * n_bars, dtype=float)  # (high, low)
    return day_map


def test_equivalence_when_no_intraday_excursion():
    dates = np.array([np.datetime64("2024-01-0%d" % d) for d in range(1, 9)])
    prices = np.array([100, 101, 99, 103, 97, 105, 104, 106], dtype=float)
    positions = np.array([0, 1, 1, 1, 1, 1, 1, 0], dtype=float)
    day_map = _flat_day_bars(prices)
    eq_daily, _ = run_coin_backtest(
        dates=dates, prices=prices, positions=positions, initial_capital=10_000.0, **COSTS)
    eq_intra, _ = run_coin_backtest_intrabar(
        dates=dates, prices=prices, positions=positions, intraday=day_map,
        initial_capital=10_000.0, trailing_stop=0.0, **COSTS)
    np.testing.assert_allclose(eq_intra, eq_daily, rtol=1e-9, atol=1e-6)


def test_long_stop_fires_intrabar_even_when_close_is_up():
    dates = np.array([np.datetime64("2024-01-01"), np.datetime64("2024-01-02")])
    prices = np.array([100.0, 101.0], dtype=float)
    positions = np.array([1.0, 1.0], dtype=float)
    day_map = {0: np.array([[100.0, 100.0]]), 1: np.array([[101.0, 90.0]])}
    costs = dict(COSTS); costs["stop_loss"] = 0.03
    eq, _ = run_coin_backtest_intrabar(
        dates=dates, prices=prices, positions=positions, intraday=day_map,
        initial_capital=10_000.0, trailing_stop=0.0, **costs)
    assert eq[-1] < 10_000.0 * 0.975
    assert eq[-1] > 10_000.0 * 0.95


def test_long_tp_fires_intrabar():
    dates = np.array([np.datetime64("2024-01-01"), np.datetime64("2024-01-02")])
    prices = np.array([100.0, 100.5], dtype=float)
    positions = np.array([1.0, 1.0], dtype=float)
    day_map = {0: np.array([[100.0, 100.0]]), 1: np.array([[112.0, 100.0]])}
    costs = dict(COSTS); costs["stop_loss"] = 0.50; costs["take_profit"] = 0.05
    eq, _ = run_coin_backtest_intrabar(
        dates=dates, prices=prices, positions=positions, intraday=day_map,
        initial_capital=10_000.0, trailing_stop=0.0, **costs)
    assert eq[-1] > 10_000.0 * 1.045


def test_sl_wins_when_both_touched_earlier_bar():
    dates = np.array([np.datetime64("2024-01-01"), np.datetime64("2024-01-02")])
    prices = np.array([100.0, 101.0], dtype=float)
    positions = np.array([1.0, 1.0], dtype=float)
    day_map = {0: np.array([[100.0, 100.0]]),
               1: np.array([[101.0, 90.0], [120.0, 101.0]])}
    costs = dict(COSTS); costs["stop_loss"] = 0.03; costs["take_profit"] = 0.05
    eq, _ = run_coin_backtest_intrabar(
        dates=dates, prices=prices, positions=positions, intraday=day_map,
        initial_capital=10_000.0, trailing_stop=0.0, **costs)
    assert eq[-1] < 10_000.0 * 0.975


def test_trailing_stop_ratchets():
    dates = np.array([np.datetime64("2024-01-01"), np.datetime64("2024-01-02")])
    prices = np.array([100.0, 110.0], dtype=float)
    positions = np.array([1.0, 1.0], dtype=float)
    day_map = {0: np.array([[100.0, 100.0]]), 1: np.array([[120.0, 108.0]])}
    costs = dict(COSTS); costs["stop_loss"] = 0.50; costs["take_profit"] = 0.0
    eq, _ = run_coin_backtest_intrabar(
        dates=dates, prices=prices, positions=positions, intraday=day_map,
        initial_capital=10_000.0, trailing_stop=0.08, **costs)
    assert 10_000.0 * 1.08 < eq[-1] < 10_000.0 * 1.12


def test_group_intraday_by_day_maps_calendar_days():
    df = pd.DataFrame({
        "open_time": pd.to_datetime([
            "2024-01-01 00:00", "2024-01-01 12:00", "2024-01-02 00:00"]),
        "high": [2.0, 3.0, 5.0], "low": [1.0, 1.5, 4.0],
        "open": [1, 2, 4], "close": [1.5, 2.5, 4.5], "volume": [1, 1, 1]})
    days = np.array([np.datetime64("2024-01-01"), np.datetime64("2024-01-02")])
    m = group_intraday_by_day(df, days)
    assert m[0].shape == (2, 2)
    assert m[1].shape == (1, 2)
    assert m[0][1, 0] == 3.0
