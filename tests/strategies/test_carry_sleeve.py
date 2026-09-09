"""Tests for the perpetual funding-carry sleeve.

P0: daily funding-INCOME aggregation. The existing scraper takes the daily
MEAN of 8h funding prints (onchain.py:247); a short-perp carry position
collects the SUM of the day's prints, so income must sum, not average.
"""
import math

import pandas as pd


def test_daily_income_sums_intraday_prints_not_mean():
    """Three 8h prints on one day -> income = SUM (carry collected), not mean."""
    from tradingagents.strategies.carry_sleeve import aggregate_daily_funding_income

    raw = pd.DataFrame(
        {
            # three 8h funding settlements on 2024-01-01 (00:00, 08:00, 16:00 UTC)
            "fundingTime": [1704067200000, 1704096000000, 1704124800000],
            "fundingRate": [0.0001, 0.0002, 0.0003],
        }
    )

    income = aggregate_daily_funding_income(raw)

    # SUM = 0.0006 ; MEAN (the bug) would be 0.0002
    assert math.isclose(income.loc[pd.Timestamp("2024-01-01").date()], 0.0006, rel_tol=1e-12)


def test_daily_income_groups_by_day():
    """Prints spanning two days produce one income row per day."""
    from tradingagents.strategies.carry_sleeve import aggregate_daily_funding_income

    raw = pd.DataFrame(
        {
            "fundingTime": [1704067200000, 1704096000000,  # 2024-01-01 x2
                            1704153600000],                  # 2024-01-02 x1
            "fundingRate": [0.0001, 0.0001, 0.0005],
        }
    )

    income = aggregate_daily_funding_income(raw)

    assert len(income) == 2
    assert math.isclose(income.loc[pd.Timestamp("2024-01-01").date()], 0.0002, rel_tol=1e-12)
    assert math.isclose(income.loc[pd.Timestamp("2024-01-02").date()], 0.0005, rel_tol=1e-12)


def test_negative_funding_is_a_loss_for_the_short_leg():
    """Negative funding -> shorts PAY -> daily income negative."""
    from tradingagents.strategies.carry_sleeve import aggregate_daily_funding_income

    raw = pd.DataFrame(
        {
            "fundingTime": [1704067200000, 1704096000000, 1704124800000],
            "fundingRate": [-0.0002, -0.0001, 0.00005],
        }
    )

    income = aggregate_daily_funding_income(raw)

    assert income.loc[pd.Timestamp("2024-01-01").date()] < 0
    assert math.isclose(income.loc[pd.Timestamp("2024-01-01").date()], -0.00025, rel_tol=1e-12)


def test_empty_raw_returns_empty_series():
    from tradingagents.strategies.carry_sleeve import aggregate_daily_funding_income

    income = aggregate_daily_funding_income(pd.DataFrame(columns=["fundingTime", "fundingRate"]))

    assert income.empty
    assert income.name == "funding_income"


# ── P1: sleeve PnL engine (always_on) ────────────────────────────────


def _income(values):
    idx = pd.date_range("2024-01-01", periods=len(values), freq="D").date
    return pd.Series(values, index=idx, name="funding_income")


def test_always_on_zero_cost_return_equals_funding_income():
    """No costs: the delta-neutral sleeve return is exactly the funding collected."""
    from tradingagents.strategies.carry_sleeve import carry_sleeve_return

    income = _income([0.0002, -0.0001, 0.0003])
    ret = carry_sleeve_return(income, sign_mode="always_on",
                              costs={"fee_rate": 0.0, "slippage": 0.0})

    assert list(ret.to_numpy()) == [0.0002, -0.0001, 0.0003]


def test_always_on_charges_entry_cost_once_then_zero_turnover():
    """Entry (both legs) costs 2*(fee+slip) on day 0 only; no cost while held."""
    from tradingagents.strategies.carry_sleeve import carry_sleeve_return

    income = _income([0.0002, 0.0002, 0.0002])
    ret = carry_sleeve_return(income, sign_mode="always_on",
                              costs={"fee_rate": 0.0004, "slippage": 0.0005})

    entry_cost = 2 * (0.0004 + 0.0005)  # both legs, one-way each = 0.0018
    assert math.isclose(ret.iloc[0], 0.0002 - entry_cost, rel_tol=1e-12)
    assert math.isclose(ret.iloc[1], 0.0002, rel_tol=1e-12)
    assert math.isclose(ret.iloc[2], 0.0002, rel_tol=1e-12)


def test_always_on_negative_funding_is_a_loss():
    from tradingagents.strategies.carry_sleeve import carry_sleeve_return

    income = _income([0.0002, -0.0004, 0.0001])
    ret = carry_sleeve_return(income, sign_mode="always_on",
                              costs={"fee_rate": 0.0, "slippage": 0.0})

    assert ret.iloc[1] < 0
    assert math.isclose(ret.iloc[1], -0.0004, rel_tol=1e-12)


# ── P1.5: real basis leg ─────────────────────────────────────────────


def test_price_pnl_added_to_sleeve_return():
    """Real basis-leg PnL is added day-by-day to the funding income."""
    from tradingagents.strategies.carry_sleeve import carry_sleeve_return

    income = _income([0.0002, 0.0002, 0.0002])
    price_pnl = pd.Series([0.0, -0.001, 0.0005], index=income.index)
    ret = carry_sleeve_return(income, sign_mode="always_on",
                              costs={"fee_rate": 0.0, "slippage": 0.0},
                              price_pnl=price_pnl)

    assert math.isclose(ret.iloc[0], 0.0002, rel_tol=1e-12)
    assert math.isclose(ret.iloc[1], 0.0002 - 0.001, rel_tol=1e-12)
    assert math.isclose(ret.iloc[2], 0.0002 + 0.0005, rel_tol=1e-12)


def test_price_pnl_none_is_perfect_hedge_unchanged():
    """price_pnl=None reproduces the P1 perfect-hedge behavior exactly."""
    from tradingagents.strategies.carry_sleeve import carry_sleeve_return

    income = _income([0.0002, -0.0001, 0.0003])
    a = carry_sleeve_return(income, costs={"fee_rate": 0.0, "slippage": 0.0})
    b = carry_sleeve_return(income, costs={"fee_rate": 0.0, "slippage": 0.0}, price_pnl=None)

    assert list(a.to_numpy()) == list(b.to_numpy())


def test_compute_price_pnl_is_spot_ret_minus_perp_ret():
    """Long-spot / short-perp price PnL = spot_ret - perp_ret, first day 0."""
    from tradingagents.strategies.carry_sleeve import compute_price_pnl

    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    spot = pd.Series([100.0, 110.0, 121.0], index=idx)   # +10%, +10%
    perp = pd.Series([100.0, 108.0, 121.0], index=idx)   # +8%, +12.037%

    pnl = compute_price_pnl(spot, perp)

    assert math.isclose(pnl.iloc[0], 0.0, abs_tol=1e-12)
    assert math.isclose(pnl.iloc[1], 0.10 - 0.08, rel_tol=1e-9)
    assert math.isclose(pnl.iloc[2], 0.10 - (121.0 / 108.0 - 1.0), rel_tol=1e-9)


def test_compute_price_pnl_identical_legs_is_zero():
    """If perp tracks spot exactly, the hedge is perfect -> zero price PnL."""
    from tradingagents.strategies.carry_sleeve import compute_price_pnl

    idx = pd.date_range("2024-01-01", periods=4, freq="D")
    s = pd.Series([100.0, 105.0, 99.0, 130.0], index=idx)

    pnl = compute_price_pnl(s, s.copy())

    assert pnl.abs().max() < 1e-12


# ── P4: blend with the core book ─────────────────────────────────────


def test_blend_returns_is_convex_combination_on_shared_dates():
    """blend = (1-alloc)*core + alloc*sleeve, aligned on the shared index."""
    from tradingagents.strategies.carry_sleeve import blend_returns

    idx = pd.date_range("2024-01-01", periods=2, freq="D")
    core = pd.Series([0.01, 0.02], index=idx)
    sleeve = pd.Series([0.005, 0.005], index=idx)

    blended = blend_returns(core, sleeve, alloc=0.2)

    assert math.isclose(blended.iloc[0], 0.8 * 0.01 + 0.2 * 0.005, rel_tol=1e-12)
    assert math.isclose(blended.iloc[1], 0.8 * 0.02 + 0.2 * 0.005, rel_tol=1e-12)


def test_blend_returns_aligns_on_index_intersection():
    """Only dates present in both series are blended."""
    from tradingagents.strategies.carry_sleeve import blend_returns

    core = pd.Series([0.01, 0.02, 0.03],
                     index=pd.date_range("2024-01-01", periods=3, freq="D"))
    sleeve = pd.Series([0.005, 0.005],
                       index=pd.date_range("2024-01-02", periods=2, freq="D"))

    blended = blend_returns(core, sleeve, alloc=0.5)

    assert len(blended) == 2
    assert list(blended.index) == list(sleeve.index)


# ── P2: trailing-sign gate ───────────────────────────────────────────


def test_gated_is_flat_during_warmup_then_holds_when_funding_strong():
    """First gate_k days have no trailing signal -> flat; then holds (constant +funding)."""
    from tradingagents.strategies.carry_sleeve import carry_sleeve_return

    income = _income([0.0002] * 5)
    ret = carry_sleeve_return(income, sign_mode="gated", gate_k=2, gate_hurdle=0.0,
                              costs={"fee_rate": 0.0, "slippage": 0.0})

    # signal_t = mean(funding[t-2:t]); pos requires a full window strictly before t
    assert ret.iloc[0] == 0.0           # no history -> flat
    assert ret.iloc[1] == 0.0           # only 1 prior day -> flat
    assert math.isclose(ret.iloc[2], 0.0002, rel_tol=1e-12)  # holds
    assert math.isclose(ret.iloc[4], 0.0002, rel_tol=1e-12)


def test_gated_goes_flat_when_trailing_funding_drops_below_hurdle():
    """When recent funding turns negative, the gate exits to flat (idle)."""
    from tradingagents.strategies.carry_sleeve import carry_sleeve_return

    income = _income([0.0002, 0.0002, 0.0002, -0.0001, -0.0001, -0.0001])
    ret = carry_sleeve_return(income, sign_mode="gated", gate_k=2, gate_hurdle=0.0,
                              costs={"fee_rate": 0.0, "slippage": 0.0})

    # trailing mean turns <=0 only after two negative prints -> last day flat
    assert math.isclose(ret.iloc[2], 0.0002, rel_tol=1e-12)   # holding
    assert ret.iloc[5] == 0.0                                  # gated out


def test_gated_never_enters_when_hurdle_exceeds_funding():
    """Hurdle above the funding level -> sleeve never deploys (all flat)."""
    from tradingagents.strategies.carry_sleeve import carry_sleeve_return

    income = _income([0.0002] * 6)
    ret = carry_sleeve_return(income, sign_mode="gated", gate_k=2, gate_hurdle=0.001,
                              costs={"fee_rate": 0.0004, "slippage": 0.0005})

    assert (ret == 0.0).all()   # never entered -> no funding, no cost
