import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.carry_xs import (
    MIN_FUND_DAYS, build_funding_matrix, carry_signal, carry_weights,
    funding_daily,
)


def _prints(day_rates):  # {"2024-01-01": [1e-4, 2e-4, ...]}
    ts, vals = [], []
    for d, rates in day_rates.items():
        for i, r in enumerate(rates):
            ts.append(pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=4 * i))
            vals.append(r)
    idx = pd.DatetimeIndex(ts, name="fundingTime")
    return pd.DataFrame({"fundingRate": vals}, index=idx).sort_index()


def test_funding_daily_sums_prints_not_mean():
    f = funding_daily(_prints({"2024-01-01": [1e-4, 1e-4, 1e-4]}))
    assert f.loc[pd.Timestamp("2024-01-01", tz="UTC")] == pytest.approx(3e-4)


def test_funding_daily_gap_day_is_nan():
    f = funding_daily(_prints({"2024-01-01": [1e-4], "2024-01-03": [1e-4]}))
    assert np.isnan(f.loc[pd.Timestamp("2024-01-02", tz="UTC")])
    assert len(f) == 3  # gapless calendar spans the hole


def test_funding_daily_handles_4h_symbols():
    f = funding_daily(_prints({"2024-01-01": [1e-4] * 6}))  # 4h interval coin
    assert f.iloc[0] == pytest.approx(6e-4)


def test_carry_signal_requires_full_window():
    prints = _prints({"2024-01-01": [1e-4], "2024-01-02": [3e-4], "2024-01-04": [5e-4]})
    F = build_funding_matrix({"XUSDT": prints},
                             funding_daily(prints).index, ["XUSDT"])
    S = carry_signal(F, L=2)
    d = pd.Timestamp("2024-01-02", tz="UTC")
    assert S.loc[d, "XUSDT"] == pytest.approx(2e-4)          # mean of daily sums
    assert np.isnan(S.loc[pd.Timestamp("2024-01-04", tz="UTC"), "XUSDT"])  # gap in window
    assert np.isnan(S.loc[pd.Timestamp("2024-01-01", tz="UTC"), "XUSDT"])  # warmup


def _panel(n_sym=8, n_days=80):
    days = pd.date_range("2024-01-01", periods=n_days, freq="D", tz="UTC")
    syms = [f"S{i}USDT" for i in range(n_sym)]
    # persistent funding levels: S0 highest ... S7 lowest (incl. negative)
    levels = np.linspace(3e-3, -1e-3, n_sym)
    F = pd.DataFrame({s: np.full(n_days, lv) for s, lv in zip(syms, levels)},
                     index=days)
    return days, syms, F


def test_carry_weights_dollar_neutral_and_leg_sizes():
    days, syms, F = _panel()
    S = carry_signal(F, L=7)
    W = carry_weights(days, S, F, {days[0]: syms}, leg_frac=0.25)  # n_leg=2
    t = days[MIN_FUND_DAYS + 10]
    row = W.loc[t]
    assert row.sum() == pytest.approx(0.0)
    assert row.abs().sum() == pytest.approx(1.0)
    assert row["S0USDT"] == pytest.approx(-0.25)   # highest funding shorted
    assert row["S7USDT"] == pytest.approx(+0.25)   # lowest funding long
    assert (row[["S3USDT", "S4USDT"]] == 0).all()  # middle untouched


def test_carry_weights_warmup_flat():
    days, syms, F = _panel()
    S = carry_signal(F, L=7)
    W = carry_weights(days, S, F, {days[0]: syms}, leg_frac=0.25)
    assert (W.iloc[:MIN_FUND_DAYS - 1] == 0).all().all()  # funding-history gate


def test_carry_weights_min_valid_flat():
    days, syms, F = _panel(n_sym=3)  # n_valid=3 < MIN_VALID=5
    S = carry_signal(F, L=7)
    W = carry_weights(days, S, F, {days[0]: syms}, leg_frac=0.2)
    assert (W == 0).all().all()


def test_carry_weights_respects_monthly_membership():
    days, syms, F = _panel()
    refresh2 = days[40]
    members = {days[0]: syms[:6], refresh2: syms[2:]}  # S0,S1 rotate out
    S = carry_signal(F, L=7)
    W = carry_weights(days, S, F, members, leg_frac=0.2)
    assert (W.loc[days[45]:, ["S0USDT", "S1USDT"]] == 0).all().all()


def test_carry_weights_long_leg_tie_break_ascending():
    # Regression: LONG leg must pick alphabetically-FIRST among tied-lowest
    # signals (bottom n_leg by (signal asc, symbol asc)), not the alphabetical
    # tail of a single descending sort.
    n_days = 40
    days = pd.date_range("2024-01-01", periods=n_days, freq="D", tz="UTC")
    syms = ["X1", "X2", "X3", "A", "B", "C"]
    levels = {"X1": 5e-3, "X2": 4e-3, "X3": 3e-3, "A": -1e-3, "B": -1e-3, "C": -1e-3}
    F = pd.DataFrame({s: np.full(n_days, levels[s]) for s in syms}, index=days)
    S = carry_signal(F, L=7)
    W = carry_weights(days, S, F, {days[0]: syms}, leg_frac=1 / 3)  # n_leg=2
    t = days[MIN_FUND_DAYS + 5]
    row = W.loc[t]
    # SHORT: top-2 by signal desc, no tie involved
    assert row["X1"] == pytest.approx(-0.25)
    assert row["X2"] == pytest.approx(-0.25)
    assert row["X3"] == 0
    # LONG: bottom-2 among {A,B,C} tied at -1e-3 -> alphabetically-first A,B win
    assert row["A"] == pytest.approx(0.25)
    assert row["B"] == pytest.approx(0.25)
    assert row["C"] == 0
