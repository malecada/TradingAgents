# tests/strategies/test_intrabar_stop.py
import numpy as np
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.baseline_strategy_v2 import run_coin_backtest

COSTS = dict(fee_rate=0.0, slippage=0.0, spread=0.0, price_impact=0.0,
             funding_rate=0.0, stop_loss=1.0, max_portfolio_dd=1.0)


def _dates(n):
    return np.arange(n)


def test_no_stop_params_is_byte_identical():
    """highs/lows omitted -> exact old behavior (golden guard)."""
    prices = np.array([100.0, 101.0, 99.0, 102.0, 103.0])
    positions = np.array([0.0, 1.0, 1.0, 1.0, 0.0])
    eq_old, m_old = run_coin_backtest(_dates(5), prices, positions.copy(),
                                      10_000.0, **COSTS)
    eq_new, m_new = run_coin_backtest(_dates(5), prices, positions.copy(),
                                      10_000.0, **COSTS,
                                      highs=None, lows=None, price_stop_pct=0.0)
    assert eq_old == eq_new
    assert m_old == m_new


def test_long_stop_triggers_on_low():
    """Long from bar1 (entry=prices[0]=100, stop 3% -> 97). Bar2 low=96
    triggers: bar2 return = (97-101)/101, position flat after."""
    prices = np.array([100.0, 101.0, 100.0, 105.0])
    highs  = np.array([100.0, 102.0, 101.0, 106.0])
    lows   = np.array([100.0, 100.0,  96.0, 104.0])
    positions = np.array([0.0, 1.0, 1.0, 1.0])
    eq, m = run_coin_backtest(_dates(4), prices, positions, 10_000.0, **COSTS,
                              highs=highs, lows=lows, price_stop_pct=0.03)
    # bar1: (101-100)/100 = +1%
    assert eq[1] == pytest.approx(10_000.0 * 1.01)
    # bar2: stopped at 97 -> (97-101)/101
    assert eq[2] == pytest.approx(eq[1] * (1 + (97.0 - 101.0) / 101.0))
    # bar3: positions array says 1.0 again -> re-entry at prices[2]=100,
    # low 104 doesn't touch new stop 97 -> full close-to-close return
    assert eq[3] == pytest.approx(eq[2] * (1 + (105.0 - 100.0) / 100.0))


def test_short_stop_triggers_on_high():
    prices = np.array([100.0, 99.0, 101.0, 95.0])
    highs  = np.array([100.0, 100.0, 103.5, 96.0])
    lows   = np.array([100.0,  98.0, 100.0, 94.0])
    positions = np.array([0.0, -1.0, -1.0, -1.0])
    eq, _ = run_coin_backtest(_dates(4), prices, positions, 10_000.0, **COSTS,
                              highs=highs, lows=lows, price_stop_pct=0.03)
    # entry 100, short stop 103; bar2 high 103.5 triggers; fill at 103:
    # ret = -1 * (103-99)/99
    assert eq[2] == pytest.approx(eq[1] * (1 - (103.0 - 99.0) / 99.0))


def test_no_trigger_when_low_stays_above_stop():
    prices = np.array([100.0, 101.0, 102.0])
    highs  = np.array([100.0, 102.0, 103.0])
    lows   = np.array([100.0, 99.0, 100.5])
    positions = np.array([0.0, 1.0, 1.0])
    eq_stop, _ = run_coin_backtest(_dates(3), prices, positions, 10_000.0,
                                   **COSTS, highs=highs, lows=lows,
                                   price_stop_pct=0.03)
    eq_plain, _ = run_coin_backtest(_dates(3), prices, positions, 10_000.0,
                                    **COSTS)
    assert eq_stop == eq_plain


def test_exit_cost_charged_on_stop():
    prices = np.array([100.0, 101.0, 100.0])
    highs  = np.array([100.0, 102.0, 101.0])
    lows   = np.array([100.0, 100.0, 96.0])
    positions = np.array([0.0, 1.0, 1.0])
    costs = dict(COSTS, fee_rate=0.001)
    eq, _ = run_coin_backtest(_dates(3), prices, positions, 10_000.0, **costs,
                              highs=highs, lows=lows, price_stop_pct=0.03)
    # bar2: gross (97-101)/101; costs = normal holding-bar cost (no resize:
    # trade_notional 0) + exit cost (2*fee)*|pos|=0.002
    expected = eq[1] * (1 + (97.0 - 101.0) / 101.0 - 0.002)
    assert eq[2] == pytest.approx(expected)
