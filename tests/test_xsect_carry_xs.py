import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.carry_xs import (
    MIN_FUND_DAYS, RF_DAILY, build_funding_matrix, carry_signal, carry_weights,
    funding_daily, run_ls_portfolio,
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


def _one_symbol_frames(w, r, f, n=4):
    days = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    W = pd.DataFrame({"XUSDT": w}, index=days)
    R = pd.DataFrame({"XUSDT": r}, index=days)
    F = pd.DataFrame({"XUSDT": f}, index=days)
    return W, R, F


def test_funding_sign_long_pays_short_receives():
    Wl, R, F = _one_symbol_frames([0.5, 0.5, 0.5, 0.5], [0.0] * 4, [2e-3] * 4)
    pl = run_ls_portfolio(Wl, R, F, cost_bps=0.0, rf_daily=0.0)
    assert pl.iloc[1] == pytest.approx(-0.5 * 2e-3)   # long pays positive funding
    Ws = Wl * -1
    ps = run_ls_portfolio(Ws, R, F, cost_bps=0.0, rf_daily=0.0)
    assert ps.iloc[1] == pytest.approx(+0.5 * 2e-3)   # short receives


def test_causal_next_bar_accrual():
    # weight appears at t=1; day-1 return must NOT accrue, day-2 must
    W, R, F = _one_symbol_frames([0.0, 1.0, 1.0, 1.0],
                                 [0.0, 0.10, 0.02, 0.0], [0.0] * 4)
    p = run_ls_portfolio(W, R, F, cost_bps=0.0, rf_daily=0.0)
    assert p.loc[W.index[1]] == pytest.approx(0.0)     # decision bar: no accrual
    assert p.loc[W.index[2]] == pytest.approx(0.02)


def test_costs_on_weight_change_and_rf_every_day():
    W, R, F = _one_symbol_frames([0.0, 1.0, 1.0, 1.0], [0.0] * 4, [0.0] * 4)
    p = run_ls_portfolio(W, R, F, cost_bps=10.0)
    assert p.iloc[1] == pytest.approx(-10 / 1e4 * 1.0 - RF_DAILY)  # |dW|=1 charged
    assert p.iloc[2] == pytest.approx(-RF_DAILY)                    # rf alone


def test_nan_funding_on_held_symbol_accrues_zero():
    W, R, F = _one_symbol_frames([0.5] * 4, [0.0] * 4, [np.nan] * 4)
    p = run_ls_portfolio(W, R, F, cost_bps=0.0, rf_daily=0.0)
    assert (p == 0).all()


from tradingagents.xsect.portfolio import rank_placebo_pvalue, sr
from tradingagents.xsect.trend import circular_shift_weights, shared_shift_weights


def _placebo_p(W, R, F, shift_fn, n=50):
    real = sr(run_ls_portfolio(W, R, F, cost_bps=0.0, rf_daily=0.0))
    srs = []
    for p in range(n):
        rng = np.random.default_rng(seed=p)
        srs.append(sr(run_ls_portfolio(shift_fn(W, rng), R, F,
                                       cost_bps=0.0, rf_daily=0.0)))
    return rank_placebo_pvalue(real, srs)


# Regime-rotation fixture: funding-level->symbol assignment is permuted every
# regime_len days, so short/long leg membership churns (~10 distinct regimes
# over 600d) instead of being column-constant. A circular-shift placebo can
# only destroy a TIMING relationship between weight and return; the earlier
# column-constant version made the book's long/short assignment nearly
# time-invariant, so no time-shift null could distinguish real from placebo
# (real SR sat mid-pack of the placebo distribution regardless of k). With
# rotating regimes the alpha genuinely depends on alignment-in-time, which
# circular/shared shifts destroy.
def _synthetic(k, seed=0, n_sym=20, n_days=600, regime_len=60, spread=4e-3):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2022-01-01", periods=n_days, freq="D", tz="UTC")
    syms = [f"S{i:02d}USDT" for i in range(n_sym)]
    base = np.linspace(spread / 2, -spread / 2, n_sym)
    F = np.empty((n_days, n_sym))
    for b in range(0, n_days, regime_len):
        m = min(regime_len, n_days - b)
        perm = rng.permutation(n_sym)
        F[b:b + m] = base[perm] + rng.normal(0, 2e-4, (m, n_sym))
    F = pd.DataFrame(F, index=days, columns=syms)
    S = carry_signal(F, L=7)
    noise = rng.normal(0, 0.01, (n_days, n_sym))
    R = pd.DataFrame(noise, index=days, columns=syms) - k * S.shift(1).fillna(0.0)
    W = carry_weights(days, S, F, {days[0]: syms}, leg_frac=0.2)
    return W, R, F


def test_placebo_kill_planted_signal_detected_both_families():
    W, R, F = _synthetic(k=2.0)  # high funding -> lower future return
    assert _placebo_p(W, R, F, circular_shift_weights) <= 0.05
    assert _placebo_p(W, R, F, shared_shift_weights) <= 0.05


# spread=0.0 is required here, not just k=0.0: run_ls_portfolio always accrues
# real funding P&L from F regardless of k (funding is the strategy's actual
# harvest mechanism), so a persistent cross-sectional funding SPREAD is a real,
# detectable effect on its own -- k=0.0 with the default spread only nulls the
# price-timing channel, not the funding-differential channel, and the placebo
# machinery correctly flagged it (ablation: p=0.0196 with spread=4e-3 vs.
# 0.37/0.16/0.45 across seeds with spread=0.0). A true null needs zero
# persistent structure in BOTH channels.
def test_placebo_null_not_detected():
    W, R, F = _synthetic(k=0.0, spread=0.0)
    assert _placebo_p(W, R, F, circular_shift_weights) > 0.05
