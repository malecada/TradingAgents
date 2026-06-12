"""Signed real-funding support in the agent-signal backtest engine.

The engine (`run_backtest`) is shared by V3 and the LLM system backtests; it
previously modelled no funding (only a short borrow cost). A `funding_series`
param deducts SIGNED funding (long pays, short receives) when supplied; None
preserves the legacy behavior.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _two_day(signals, fseries):
    from tradingagents.backtesting.engine import run_backtest
    from tradingagents.backtesting.strategies import FiveLevelSignal

    dates = pd.Series(pd.to_datetime(["2024-01-01", "2024-01-02"]))
    actuals = np.array([100.0, 100.0])  # zero price return -> isolate funding
    return run_backtest(
        dates, actuals, signals, FiveLevelSignal(),
        fee_rate=0.0, slippage=0.0, short_cost=0.0, funding_series=fseries,
    )


def test_engine_signed_funding_long_pays_short_receives():
    fseries = np.array([0.0, 0.0002])  # +funding on day 1
    r_long = _two_day(["HOLD", "BUY"], fseries)   # pos +1
    r_short = _two_day(["HOLD", "SELL"], fseries)  # pos -1

    assert r_long.daily_returns[-1] < 0    # long PAYS funding
    assert r_short.daily_returns[-1] > 0   # short RECEIVES funding
    assert math.isclose(r_long.daily_returns[-1], -0.0002, rel_tol=1e-12)
    assert math.isclose(r_short.daily_returns[-1], +0.0002, rel_tol=1e-12)


def test_engine_funding_none_is_legacy_no_funding():
    r = _two_day(["HOLD", "BUY"], None)  # no funding series
    assert math.isclose(r.daily_returns[-1], 0.0, abs_tol=1e-12)  # zero fees, no funding


def _two_day_with_short_cost(signals, fseries, short_cost):
    from tradingagents.backtesting.engine import run_backtest
    from tradingagents.backtesting.strategies import FiveLevelSignal

    dates = pd.Series(pd.to_datetime(["2024-01-01", "2024-01-02"]))
    actuals = np.array([100.0, 100.0])
    return run_backtest(
        dates, actuals, signals, FiveLevelSignal(),
        fee_rate=0.0, slippage=0.0, short_cost=short_cost,
        funding_series=fseries,
    )


def test_real_funding_replaces_short_cost_not_stacks():
    """With real signed funding supplied, the legacy short borrow proxy must
    NOT also be charged — perps have no borrow fee and charging both
    double-counts the short's carry (the V2 path already replaces it)."""
    fseries = np.array([0.0, 0.0002])
    r_short = _two_day_with_short_cost(["HOLD", "SELL"], fseries, short_cost=0.0003)
    # Funding-only: short receives +0.0002. If short_cost stacked, the day
    # would net 0.0002 - 0.0003 = -0.0001.
    assert math.isclose(r_short.daily_returns[-1], +0.0002, rel_tol=1e-12)


def test_legacy_short_cost_still_charged_without_funding():
    r_short = _two_day_with_short_cost(["HOLD", "SELL"], None, short_cost=0.0003)
    assert math.isclose(r_short.daily_returns[-1], -0.0003, rel_tol=1e-12)
