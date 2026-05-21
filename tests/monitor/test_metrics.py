import math

from tradingagents.monitor import metrics


def test_max_drawdown():
    # peak 120, trough 90 -> (90-120)/120 = -0.25
    series = [100.0, 120.0, 110.0, 90.0, 130.0]
    assert math.isclose(metrics.max_drawdown(series), -0.25)


def test_max_drawdown_monotonic_increasing():
    assert metrics.max_drawdown([100.0, 110.0, 120.0]) == 0.0


def test_max_drawdown_too_short():
    assert metrics.max_drawdown([100.0]) == 0.0


def test_sharpe_zero_variance():
    # constant equity -> no returns variance -> Sharpe 0.0
    assert metrics.sharpe([100.0, 100.0, 100.0]) == 0.0


def test_sharpe_positive_trend():
    series = [100.0, 101.0, 102.0, 103.5, 104.0, 106.0]
    assert metrics.sharpe(series) > 0.0


def test_sharpe_too_short():
    assert metrics.sharpe([100.0]) == 0.0


def test_cumulative_pnl():
    trades = [{"pnl": 100.0}, {"pnl": -30.0}, {"pnl": None}, {"pnl": 50.0}]
    assert metrics.cumulative_pnl(trades) == 120.0


def test_equity_series_from_snapshots():
    snaps = [
        {"ts": "2026-05-19T07:05:00+00:00", "total_value": 10150.0},
        {"ts": "2026-05-20T07:05:00+00:00", "total_value": 10280.0},
    ]
    series = metrics.equity_series(snaps, trades=[], start_capital=10000.0)
    assert series == [
        {"ts": "2026-05-19T07:05:00+00:00", "value": 10150.0},
        {"ts": "2026-05-20T07:05:00+00:00", "value": 10280.0},
    ]


def test_equity_series_fallback_to_trades():
    # no snapshots -> reconstruct from cumulative realized PnL
    trades = [
        {"cycle_id": "c1", "pnl": 100.0},
        {"cycle_id": "c1", "pnl": 50.0},
        {"cycle_id": "c2", "pnl": -30.0},
    ]
    series = metrics.equity_series([], trades=trades, start_capital=10000.0)
    assert series[-1]["value"] == 10120.0
    assert series[0]["value"] == 10000.0  # start point prepended


def test_equity_series_empty():
    assert metrics.equity_series([], trades=[], start_capital=10000.0) == []
