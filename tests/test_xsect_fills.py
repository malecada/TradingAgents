"""exec_pf passive-fill model — frozen mechanics per gates.json["exec_pf"].

Spec: docs/superpowers/specs/2026-09-03-exec-pf-charter.md.
"""
import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.fills import (
    estimate_spread_rel, first_cross_minute, hourly_exec_aggregates, infer_tick,
    limit_price, passive_overlay, round_to_tick, tick_level_fill,
)
from tradingagents.xsect.liq_fade import run_hourly_portfolio


def _hours(n, start="2021-01-01"):
    return pd.date_range(start, periods=n, freq="h", tz="UTC")


def _minutes(n, start="2021-01-01"):
    return pd.date_range(start, periods=n, freq="min", tz="UTC")


# ── tick inference / rounding ────────────────────────────────────────────────

def test_infer_tick_modal_gap():
    assert infer_tick(np.array([100.0, 100.1, 100.3, 100.2, 100.1])) == pytest.approx(0.1)
    assert infer_tick(np.array([0.32757, 0.32758, 0.32760])) == pytest.approx(1e-5)


def test_infer_tick_ignores_stale_finer_grid_print():
    # amendment A2 (2026-09-03): a single stale 0.01-grid print must not shrink the tick
    px = np.array([100.0, 100.1, 100.2, 100.3, 100.4, 100.5, 100.21])
    assert infer_tick(px) == pytest.approx(0.1)


def test_infer_tick_single_price_is_nan():
    assert np.isnan(infer_tick(np.array([5.0, 5.0])))


def test_round_to_tick_directions():
    assert round_to_tick(100.06, 0.1, "down") == pytest.approx(100.0)
    assert round_to_tick(100.04, 0.1, "up") == pytest.approx(100.1)
    assert round_to_tick(100.1, 0.1, "down") == pytest.approx(100.1)   # on-grid stays


def test_limit_price_buy_below_sell_above_with_spread_floor():
    # spread = max(tick, s_rel*close): tick floor binds -> L = close -/+ half tick, rounded
    assert limit_price(100.0, s_rel=0.0, tick=0.1, side="buy") == pytest.approx(99.9)
    assert limit_price(100.0, s_rel=0.0, tick=0.1, side="sell") == pytest.approx(100.1)
    # spread 20 bp on 100 -> 0.2, half = 0.1
    assert limit_price(100.0, s_rel=0.002, tick=0.01, side="buy") == pytest.approx(99.9)
    assert limit_price(100.0, s_rel=0.002, tick=0.01, side="sell") == pytest.approx(100.1)
    # rounding direction: buy rounds DOWN, sell rounds UP
    assert limit_price(100.05, s_rel=0.0, tick=0.1, side="buy") == pytest.approx(100.0)
    assert limit_price(100.05, s_rel=0.0, tick=0.1, side="sell") == pytest.approx(100.1)


# ── hourly aggregates from 1-minute bars ─────────────────────────────────────

def _one_symbol_1m(n_hours=3):
    idx = _minutes(60 * n_hours)
    df = pd.DataFrame({"open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0}, index=idx)
    return df


def test_aggregates_exclude_minute_zero():
    df = _one_symbol_1m(2)
    df.loc[df.index[0], "low"] = 90.0          # minute 0 of hour 0: must be ignored
    df.loc[df.index[61], "high"] = 110.0       # minute 1 of hour 1: counts
    agg = hourly_exec_aggregates(df)
    assert list(agg.index) == list(_hours(2))
    assert agg["minlow_ex0"].iloc[0] == pytest.approx(99.5)
    assert agg["maxhigh_ex0"].iloc[1] == pytest.approx(110.0)
    assert agg["n_min"].iloc[0] == 60
    assert agg["close_1m"].iloc[1] == pytest.approx(df["close"].iloc[119])


def test_aggregates_count_missing_minutes():
    df = _one_symbol_1m(1).drop(_minutes(60)[10:20])
    agg = hourly_exec_aggregates(df)
    assert agg["n_min"].iloc[0] == 50


def test_first_cross_minute_buy_and_sell():
    df = _one_symbol_1m(1)
    df.loc[df.index[0], "low"] = 98.0    # minute 0 excluded by latency
    df.loc[df.index[7], "low"] = 99.0
    df.loc[df.index[30], "high"] = 101.0
    assert first_cross_minute(df, df.index[0], side="buy", threshold=99.0) == 7
    assert first_cross_minute(df, df.index[0], side="sell", threshold=101.0) == 30
    assert first_cross_minute(df, df.index[0], side="buy", threshold=98.5) is None


# ── overlay: trade-through fill rule ─────────────────────────────────────────

def _panel(closes, minlow=None, maxhigh=None, tick=0.1, sym="A"):
    n = len(closes)
    idx = _hours(n)
    C = pd.DataFrame({sym: closes}, index=idx, dtype=float)
    ML = pd.DataFrame({sym: minlow if minlow is not None else [np.nan] * n}, index=idx, dtype=float)
    MH = pd.DataFrame({sym: maxhigh if maxhigh is not None else [np.nan] * n}, index=idx, dtype=float)
    T = pd.DataFrame({sym: [tick] * n}, index=idx, dtype=float)
    return C, ML, MH, T


def _run(W, C, ML, MH, T, **kw):
    kw.setdefault("s_rel", {c: 0.0 for c in C.columns})
    kw.setdefault("policy", "LTM")
    kw.setdefault("maker_bp", 2.0)
    kw.setdefault("taker_bp", 5.0)
    return passive_overlay(W, C, ML, MH, T, **kw)


def test_touch_does_not_fill_but_one_tick_through_does():
    # order at close of bar 0 (100.0): buy limit L = 99.9 (tick floor). Fill needs minlow <= 99.8.
    C, ML, MH, T = _panel([100.0, 101.0, 101.0], minlow=[np.nan, 99.9, np.nan])
    W = pd.DataFrame({"A": [0.0, 1.0, 1.0]}, index=C.index)
    out = _run(W, C, ML, MH, T)
    assert out["orders"]["filled"].tolist() == [False]
    ML.iloc[1, 0] = 99.8
    out = _run(W, C, ML, MH, T)
    assert out["orders"]["filled"].tolist() == [True]
    assert out["orders"]["fill_price"].iloc[0] == pytest.approx(99.9)


def test_two_tick_tightening_requires_deeper_print():
    C, ML, MH, T = _panel([100.0, 101.0, 101.0], minlow=[np.nan, 99.8, np.nan])
    W = pd.DataFrame({"A": [0.0, 1.0, 1.0]}, index=C.index)
    assert _run(W, C, ML, MH, T, through_ticks=1)["orders"]["filled"].iloc[0]
    assert not _run(W, C, ML, MH, T, through_ticks=2)["orders"]["filled"].iloc[0]
    ML.iloc[1, 0] = 99.7
    assert _run(W, C, ML, MH, T, through_ticks=2)["orders"]["filled"].iloc[0]


def test_sell_fills_on_high_through_above_limit():
    C, ML, MH, T = _panel([100.0, 100.0, 99.0], maxhigh=[np.nan, np.nan, 100.2])
    W = pd.DataFrame({"A": [1.0, 1.0, 0.0]}, index=C.index)   # exit order at close of bar 1 -> bar 2
    out = _run(W, C, ML, MH, T)
    o = out["orders"].iloc[0]
    assert o["side"] == "sell" and o["filled"] and o["fill_price"] == pytest.approx(100.1)
    MH.iloc[2, 0] = 100.1   # touch only
    assert not _run(W, C, ML, MH, T)["orders"]["filled"].iloc[0]


def test_missing_minute_data_means_no_fill():
    C, ML, MH, T = _panel([100.0, 101.0, 101.0])   # all aggregates NaN
    W = pd.DataFrame({"A": [0.0, 1.0, 1.0]}, index=C.index)
    out = _run(W, C, ML, MH, T)
    assert not out["orders"]["filled"].iloc[0]


# ── overlay: booking ──────────────────────────────────────────────────────────

def test_filled_buy_books_segment_identity():
    # bar 1: fill at L=99.9, w_old 0, w_new 1: gross = (101/99.9 - 1); cost 2 bp
    C, ML, MH, T = _panel([100.0, 101.0, 101.0], minlow=[np.nan, 99.5, np.nan])
    W = pd.DataFrame({"A": [0.0, 1.0, 1.0]}, index=C.index)
    out = _run(W, C, ML, MH, T)
    assert out["gross"].iloc[1] == pytest.approx(101.0 / 99.9 - 1)
    assert out["cost"].iloc[1] == pytest.approx(2e-4)
    assert out["gross"].iloc[2] == pytest.approx(0.0)   # 101 -> 101


def test_partial_reduction_books_both_segments():
    # w 1.0 -> 0.5 at close of bar 0; sell L=100.1 fills; gross = 1.0*(100.1/100-1) + 0.5*(99/100.1-1)
    C, ML, MH, T = _panel([100.0, 99.0, 99.0], maxhigh=[np.nan, 100.5, np.nan])
    W = pd.DataFrame({"A": [1.0, 0.5, 0.5]}, index=C.index)
    out = _run(W, C, ML, MH, T)
    assert out["gross"].iloc[1] == pytest.approx(1.0 * (100.1 / 100.0 - 1) + 0.5 * (99.0 / 100.1 - 1))
    assert out["cost"].iloc[1] == pytest.approx(0.5 * 2e-4)


def test_unfilled_ltm_uses_old_weight_then_market_at_bar_end():
    # buy unfilled in bar 1: gross(bar1) = w_old*(101/100-1) = 0; cost = (5 bp + half spread)*1
    # half spread at bar-end close 101 with tick 0.1 -> 0.05/101; then w_new applies in bar 2.
    C, ML, MH, T = _panel([100.0, 101.0, 102.0], minlow=[np.nan, 100.5, np.nan])
    W = pd.DataFrame({"A": [0.0, 1.0, 1.0]}, index=C.index)
    out = _run(W, C, ML, MH, T)
    assert out["gross"].iloc[1] == pytest.approx(0.0)
    assert out["cost"].iloc[1] == pytest.approx(5e-4 + 0.05 / 101.0)
    assert out["gross"].iloc[2] == pytest.approx(102.0 / 101.0 - 1)
    assert out["fill_rate"] == pytest.approx(0.0)


def test_taker_policy_reproduces_parent_engine_exactly():
    rng = np.random.default_rng(3)
    n, syms = 24 * 40, ["A", "B", "C"]
    idx = _hours(n)
    C = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.01, (n, 3)), axis=0)), index=idx, columns=syms)
    C.iloc[100:110, 1] = np.nan                           # gap bars
    W = pd.DataFrame(rng.choice([0.0, 0.1, 0.2], size=(n, 3)), index=idx, columns=syms)
    W.iloc[0] = 0.0
    ML = MH = pd.DataFrame(np.nan, index=idx, columns=syms)
    T = pd.DataFrame(0.01, index=idx, columns=syms)
    R = C.pct_change(fill_method=None)
    parent = run_hourly_portfolio(W, R, cost_bps=10.0, rf_annual=0.045)
    out = passive_overlay(W, C, ML, MH, T, s_rel={s: 0.0 for s in syms}, policy="taker",
                          parent_cost_bp=10.0, maker_bp=2.0, taker_bp=5.0, rf_annual=0.045)
    np.testing.assert_allclose(out["daily_net"].to_numpy(), parent.to_numpy(), atol=1e-12)
    assert out["fill_rate"] == pytest.approx(1.0)


def test_log_booking_option_uses_log_segments():
    C, ML, MH, T = _panel([100.0, 101.0, 101.0], minlow=[np.nan, 99.5, np.nan])
    W = pd.DataFrame({"A": [0.0, 1.0, 1.0]}, index=C.index)
    out = _run(W, C, ML, MH, T, log_booking=True)
    assert out["gross"].iloc[1] == pytest.approx(np.log(101.0 / 99.9))


def test_fill_rate_is_filled_notional_over_ordered_notional():
    # two buys (0.1 each): one fills, one not -> 50%
    C, ML, MH, T = _panel([100.0, 100.0, 100.0, 100.0], minlow=[np.nan, 99.0, np.nan, 100.0])
    W = pd.DataFrame({"A": [0.0, 0.1, 0.1, 0.2]}, index=C.index)
    out = _run(W, C, ML, MH, T)
    assert out["fill_rate"] == pytest.approx(0.5)


def test_maker_stress_changes_only_filled_cost():
    C, ML, MH, T = _panel([100.0, 101.0, 101.0], minlow=[np.nan, 99.5, np.nan])
    W = pd.DataFrame({"A": [0.0, 1.0, 1.0]}, index=C.index)
    a = _run(W, C, ML, MH, T, maker_bp=2.0)["cost"].iloc[1]
    b = _run(W, C, ML, MH, T, maker_bp=3.0)["cost"].iloc[1]
    assert b - a == pytest.approx(1e-4)


# ── overlay: LOC policy ───────────────────────────────────────────────────────

def test_loc_entry_replaced_until_filled_then_position_held():
    # target 1.0 from bar 1 on; bar 1 unfilled, bar 2 fills at L from close of bar 1 (100.9)
    C, ML, MH, T = _panel([100.0, 101.0, 102.0, 103.0], minlow=[np.nan, 100.5, 100.0, np.nan])
    W = pd.DataFrame({"A": [0.0, 1.0, 1.0, 1.0]}, index=C.index)
    out = _run(W, C, ML, MH, T, policy="LOC")
    o = out["orders"]
    assert o["filled"].tolist() == [False, True]
    assert o["fill_price"].iloc[1] == pytest.approx(100.9)
    assert out["gross"].iloc[1] == pytest.approx(0.0)                    # flat, no market
    assert out["cost"].iloc[1] == pytest.approx(0.0)
    assert out["gross"].iloc[2] == pytest.approx(102.0 / 100.9 - 1)
    assert out["gross"].iloc[3] == pytest.approx(103.0 / 102.0 - 1)


def test_loc_entry_never_filled_means_no_trade_at_all():
    C, ML, MH, T = _panel([100.0, 101.0, 102.0, 103.0])
    W = pd.DataFrame({"A": [0.0, 1.0, 1.0, 0.0]}, index=C.index)
    out = _run(W, C, ML, MH, T, policy="LOC")
    assert out["gross"].abs().sum() == pytest.approx(0.0)
    assert out["cost"].abs().sum() == pytest.approx(0.0)
    assert out["fill_rate"] == pytest.approx(0.0)


def test_loc_exit_is_limit_then_market():
    # in position from bar 0; exit wanted for bar 2; sell unfilled -> market at close of bar 2
    C, ML, MH, T = _panel([100.0, 100.0, 100.0, 100.0])
    W = pd.DataFrame({"A": [1.0, 1.0, 0.0, 0.0]}, index=C.index)
    out = _run(W, C, ML, MH, T, policy="LOC")
    assert out["cost"].iloc[2] == pytest.approx(5e-4 + 0.05 / 100.0)
    assert out["gross"].iloc[3] == pytest.approx(0.0)


# ── aggTrades helpers ─────────────────────────────────────────────────────────

def _trades(rows):
    df = pd.DataFrame(rows, columns=["ts", "price", "qty", "is_buyer_maker"])
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df


def test_estimate_spread_rel_from_bid_ask_prints():
    rows = []
    for m in range(3):
        base = f"2021-01-01 00:0{m}:"
        rows += [(base + "01", 100.00, 1, True), (base + "02", 100.02, 1, False),
                 (base + "30", 100.00, 1, True), (base + "31", 100.02, 1, False)]
    assert estimate_spread_rel(_trades(rows)) == pytest.approx(0.02 / 100.01)


def test_tick_level_fill_needs_print_beyond_limit_after_latency():
    rows = [("2021-01-01 00:59:50", 100.0, 1, True), ("2021-01-01 00:59:55", 100.1, 1, False),
            ("2021-01-01 01:00:20", 99.8, 1, True),      # within latency: ignored
            ("2021-01-01 01:05:00", 99.9, 1, True),      # touch at limit-? (limit = bid 100.0 -> needs <= 99.9)
            ("2021-01-01 01:30:00", 100.5, 1, False)]
    tr = _trades(rows)
    t_place = pd.Timestamp("2021-01-01 01:00:00", tz="UTC")
    r = tick_level_fill(tr, t_place, side="buy", tick=0.1, latency_s=60, through_ticks=1)
    assert r["quote"] == pytest.approx(100.0)
    assert r["filled"] is True and r["fill_ts"] == pd.Timestamp("2021-01-01 01:05:00", tz="UTC")
    r0 = tick_level_fill(tr, t_place, side="buy", tick=0.1, latency_s=0, through_ticks=1)
    assert r0["fill_ts"] == pd.Timestamp("2021-01-01 01:00:20", tz="UTC")
    r2 = tick_level_fill(tr, t_place, side="buy", tick=0.1, latency_s=60, through_ticks=2)
    assert r2["filled"] is False
    rs = tick_level_fill(tr, t_place, side="sell", tick=0.1, latency_s=60, through_ticks=1)
    assert rs["quote"] == pytest.approx(100.1) and rs["filled"] is True
