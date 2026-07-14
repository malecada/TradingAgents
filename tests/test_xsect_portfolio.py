import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.portfolio import (momentum_scores, paired_bootstrap,
                                            rank_placebo_pvalue, run_weekly_portfolio, sr)


def _kl(prices, first="2021-01-01"):
    idx = pd.date_range(first, periods=len(prices), freq="D", tz="UTC")
    p = pd.Series(prices, index=idx, dtype=float)
    return pd.DataFrame({"open": p, "high": p, "low": p, "close": p, "quote_volume": 1e7})


def test_momentum_score_window():
    # 10 flat days then +1%/day for 5 days; L=5, skip=0 at the last day => 5*log(1.01)
    prices = [100.0] * 10 + [100 * 1.01 ** i for i in range(1, 6)]
    kl = {"A": _kl(prices)}
    d = kl["A"].index[-1]
    s = momentum_scores(kl, ["A"], d, L=5, skip=0)
    assert s["A"] == pytest.approx(5 * np.log(1.01), rel=1e-9)


def test_momentum_skip_shifts_window():
    prices = [100.0] * 10 + [100 * 1.01 ** i for i in range(1, 6)]
    kl = {"A": _kl(prices)}
    d = kl["A"].index[-1]
    s1 = momentum_scores(kl, ["A"], d, L=4, skip=1)  # excludes last day
    assert s1["A"] == pytest.approx(4 * np.log(1.01), rel=1e-9)


def test_portfolio_no_lookahead():
    # coin B jumps +50% ON the rebalance Monday; selecting B at that close must NOT earn the jump
    up = [100.0] * 32 + [150.0] + [150.0] * 13
    flat = [100.0] * 46
    kl = {"B": _kl(up), "F": _kl(flat)}
    reb = pd.DatetimeIndex([kl["B"].index[32]])  # the jump day
    series = run_weekly_portfolio(kl, reb, lambda t: ["B"], cost_bps=0.0)
    assert series.loc[kl["B"].index[33]:].abs().sum() == pytest.approx(0.0)  # flat after jump
    assert kl["B"].index[32] not in series.index or series.loc[kl["B"].index[32]] == 0.0


def test_costs_deducted_once_per_rebalance():
    flat = [100.0] * 46
    kl = {"A": _kl(flat)}
    reb = pd.DatetimeIndex([kl["A"].index[10]])
    gross = run_weekly_portfolio(kl, reb, lambda t: ["A"], cost_bps=0.0)
    net = run_weekly_portfolio(kl, reb, lambda t: ["A"], cost_bps=10.0)
    diff = (gross - net).sum()
    assert diff == pytest.approx(10 / 1e4, rel=1e-6)  # one full entry, one side


def test_no_lookahead_second_rebalance():
    up = [100.0] * 39 + [150.0] * 14          # +50% jump ON 2nd rebalance Monday
    flat = [100.0] * 53
    kl = {"B": _kl(up), "F": _kl(flat)}
    idx = kl["B"].index
    reb = pd.DatetimeIndex([idx[32], idx[39]])
    sel = lambda t: ["B"] if t >= idx[39] else ["F"]
    series = run_weekly_portfolio(kl, reb, sel, cost_bps=0.0)
    assert series.abs().sum() == pytest.approx(0.0)


def test_delisted_member_contributes_zero_not_reweighted():
    # A gets delisted mid-week (klines simply stop); B survives at +1%/day.
    # Weight must NOT redistribute to the survivor intra-week.
    up = [100.0 * 1.01 ** i for i in range(10)]
    kl_full_A = _kl([100.0] * 10)
    kl = {"A": kl_full_A.iloc[:5], "B": _kl(up)}
    idx = kl["B"].index
    reb = pd.DatetimeIndex([idx[0]])
    series = run_weekly_portfolio(kl, reb, lambda t: ["A", "B"], cost_bps=0.0)
    delisted_day = idx[6]  # A has no kline from idx[5] onward
    assert series.loc[delisted_day] == pytest.approx(0.5 * np.log(1.01), rel=1e-9)


def test_exit_to_empty_charges_sell_side():
    flat = [100.0] * 40
    kl = {"A": _kl(flat)}
    idx = kl["A"].index
    reb = pd.DatetimeIndex([idx[5], idx[15], idx[25]])

    def select_fn(t):
        if t == idx[5]:
            return ["A"]
        if t == idx[15]:
            return []
        return ["A"]

    gross = run_weekly_portfolio(kl, reb, select_fn, cost_bps=0.0)
    net = run_weekly_portfolio(kl, reb, select_fn, cost_bps=10.0)
    cost = gross - net
    # each one-side leg must hit on the first accrual day after its own
    # rebalance — not be silently dropped (gate bug) or lumped into a later
    # rebalance's charge (assignment-overwrite bug)
    one_side = 10 / 1e4 * 1.0
    assert cost.loc[idx[6]] == pytest.approx(one_side)   # entry leg
    assert cost.loc[idx[16]] == pytest.approx(one_side)  # exit-to-empty leg
    assert cost.loc[idx[26]] == pytest.approx(one_side)  # re-entry leg
    assert cost.sum() == pytest.approx(3 * one_side, rel=1e-6)


def test_momentum_gap_drops_symbol():
    prices = [100.0] * 20
    kl = {"A": _kl(prices)}
    idx = kl["A"].index
    kl["A"] = kl["A"].drop(idx[16])  # gap inside the L=5,skip=0 window ending at idx[19]
    d = idx[-1]
    s = momentum_scores(kl, ["A"], d, L=5, skip=0)
    assert "A" not in s


def test_paired_bootstrap_direction():
    idx = pd.date_range("2021-01-01", periods=400, freq="D", tz="UTC")
    rng = np.random.default_rng(0)
    base = pd.Series(rng.normal(0, 0.01, 400), index=idx)
    better = base + 0.002
    r = paired_bootstrap(better, base, n=200, seed=1)
    assert r["delta_sr"] > 0 and r["p_pos"] > 0.95


def test_rank_placebo():
    assert rank_placebo_pvalue(2.0, [1.0] * 99) == pytest.approx(1 / 100)
    assert rank_placebo_pvalue(0.0, [1.0] * 99) == pytest.approx(1.0)
