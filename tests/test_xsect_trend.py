"""Engine tests: refresh dates, weights, t+1 accrual, costs, no-look-ahead, delisting."""
import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.trend import (
    build_matrices, ew_benchmark_weights, monthly_refresh_dates,
    run_daily_portfolio, trend_weights,
)

UTC = "UTC"


def _mk_klines(prices: dict[str, pd.Series]) -> dict:
    return {s: pd.DataFrame({"close": p, "quote_volume": 1e9}, index=p.index)
            for s, p in prices.items()}


def _idx(start, periods):
    return pd.date_range(start, periods=periods, freq="D", tz=UTC)


def test_monthly_refresh_dates_first_mondays():
    d = monthly_refresh_dates("2021-01-01", "2021-04-30")
    assert list(d.strftime("%Y-%m-%d")) == ["2021-01-04", "2021-02-01", "2021-03-01", "2021-04-05"]
    assert (d.dayofweek == 0).all()


def test_run_daily_portfolio_t_plus_1_and_costs():
    days = _idx("2021-01-01", 4)
    # symbol A: log-returns [nan, 0.10, 0.20, -0.05]
    R = pd.DataFrame({"A": [np.nan, 0.10, 0.20, -0.05]}, index=days)
    # decision weights: 0, 1, 1, 0  (enter at close of day1, exit at close of day3)
    W = pd.DataFrame({"A": [0.0, 1.0, 1.0, 0.0]}, index=days)
    port = run_daily_portfolio(W, R, cost_bps=10.0)
    # day2: W[day1]=1 -> ret 0.20, cost of |1-0| = 0.001 charged day2 (first accrual after change)
    # day3: W[day2]=1 -> ret -0.05, no change day2->day1? W[day2]-W[day1]=0 -> no cost
    # day1 not in output? output starts at days[1]
    assert port.index[0] == days[1]
    # day1 accrual: W[day0]=0 -> 0.0, cost |W[day0]-W[-1]|=0
    assert port.loc[days[1]] == pytest.approx(0.0)
    assert port.loc[days[2]] == pytest.approx(0.20 - 0.001)
    assert port.loc[days[3]] == pytest.approx(-0.05)


def test_exit_cost_charged_after_flatten():
    days = _idx("2021-01-01", 4)
    R = pd.DataFrame({"A": [np.nan, 0.0, 0.0, 0.0]}, index=days)
    W = pd.DataFrame({"A": [1.0, 0.0, 0.0, 0.0]}, index=days)
    port = run_daily_portfolio(W, R, cost_bps=10.0)
    # entry cost on days[1] (first accrual after day0 change); exit Δ|0-1| on days[2]
    assert port.loc[days[1]] == pytest.approx(-0.001)
    assert port.loc[days[2]] == pytest.approx(-0.001)


def test_missing_kline_contributes_zero_not_redistributed():
    days = _idx("2021-01-01", 3)
    R = pd.DataFrame({"A": [np.nan, np.nan, 0.10], "B": [np.nan, 0.02, 0.02]}, index=days)
    W = pd.DataFrame({"A": [0.5, 0.5, 0.5], "B": [0.5, 0.5, 0.5]}, index=days)
    port = run_daily_portfolio(W, R, cost_bps=0.0)
    assert port.loc[days[1]] == pytest.approx(0.5 * 0.02)  # A missing -> 0, no redistribution


def test_trend_weights_no_look_ahead():
    """Mutate the last close; weights strictly before the mutated bar must not change."""
    rng = np.random.default_rng(0)
    idx = _idx("2020-10-01", 300)
    px = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.002, 0.03, 300))), index=idx)
    klines = _mk_klines({"A": px})
    refresh = monthly_refresh_dates("2021-01-01", "2021-07-31")
    members = {d: ["A"] for d in refresh}

    def weights_for(kl):
        all_days, R, V, S = build_matrices(kl, ["A"])
        return trend_weights(all_days, R, V, S, members, n_slots=1, vol_target=0.30)

    w1 = weights_for(klines)
    px2 = px.copy()
    px2.iloc[-1] *= 3.0
    w2 = weights_for(_mk_klines({"A": px2}))
    cut = idx[-1]
    pd.testing.assert_frame_equal(w1.loc[w1.index < cut], w2.loc[w2.index < cut])


def test_trend_weights_flat_when_vote_low_and_capped_by_vol_target():
    rng = np.random.default_rng(1)
    idx = _idx("2020-10-01", 300)
    up = pd.Series(100 * np.exp(np.cumsum(np.full(300, 0.01) + rng.normal(0, 0.001, 300))), index=idx)
    down = pd.Series(100 * np.exp(np.cumsum(np.full(300, -0.01) + rng.normal(0, 0.001, 300))), index=idx)
    klines = _mk_klines({"UP": up, "DOWN": down})
    refresh = monthly_refresh_dates("2021-01-01", "2021-07-31")
    members = {d: ["UP", "DOWN"] for d in refresh}
    all_days, R, V, S = build_matrices(klines, ["UP", "DOWN"])
    W = trend_weights(all_days, R, V, S, members, n_slots=2, vol_target=0.30)
    last = W.iloc[-1]
    assert last["DOWN"] == 0.0
    ann_vol = float(S["UP"].iloc[-1]) * np.sqrt(365)
    expected = 0.5 * min(1.0, 0.30 / ann_vol)
    assert last["UP"] == pytest.approx(expected)


def test_delisted_symbol_weight_zero_after_last_bar():
    idx_a = _idx("2020-10-01", 200)  # dies 2021-04-18
    idx_b = _idx("2020-10-01", 300)
    up_a = pd.Series(100 * np.exp(np.cumsum(np.full(200, 0.01))), index=idx_a)
    up_b = pd.Series(100 * np.exp(np.cumsum(np.full(300, 0.01))), index=idx_b)
    klines = _mk_klines({"A": up_a, "B": up_b})
    refresh = monthly_refresh_dates("2021-01-01", "2021-07-31")
    members = {d: ["A", "B"] for d in refresh}
    all_days, R, V, S = build_matrices(klines, ["A", "B"])
    W = trend_weights(all_days, R, V, S, members, n_slots=2, vol_target=0.30)
    after = W.loc[W.index > idx_a[-1], "A"]
    assert (after == 0.0).all()
    assert W.loc[idx_a[-1], "A"] > 0.0  # in-trend while alive


def test_ew_benchmark_constant_within_month():
    idx = _idx("2020-10-01", 300)
    px = pd.Series(np.linspace(100, 200, 300), index=idx)
    klines = _mk_klines({"A": px, "B": px * 2})
    refresh = monthly_refresh_dates("2021-01-01", "2021-05-31")
    members = {d: ["A", "B"] for d in refresh}
    all_days, R, V, S = build_matrices(klines, ["A", "B"])
    W = ew_benchmark_weights(all_days, R, members, n_slots=2)
    feb = W.loc["2021-02-01":"2021-02-28"]
    assert (feb["A"] == 0.5).all() and (feb["B"] == 0.5).all()
    assert (W.loc[W.index < refresh[0]] == 0.0).all().all()
