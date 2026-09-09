"""liq_mr_t1 unit tests — frozen mechanics per gates.json["liq_mr_t1"].

Spec: docs/superpowers/specs/2026-07-28-liq-mr-design.md.
"""
import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.liq_mr import (
    RF_DAILY, UNIT_W, Z_MIN, Z_WINDOW, event_weights, liq_zscore,
    run_liq_portfolio,
)


def _days(n, start="2021-01-01"):
    return pd.date_range(start, periods=n, freq="D", tz="UTC")


# ── liq_zscore ───────────────────────────────────────────────────────────────

def test_zscore_causal_and_min_periods():
    idx = _days(200)
    rng = np.random.default_rng(0)
    liq = pd.DataFrame({"A": rng.uniform(1, 2, 200)}, index=idx)
    oi = pd.DataFrame({"A": np.full(200, 10.0)}, index=idx)
    z = liq_zscore(liq, oi)
    # min_periods: first Z_MIN-1 rows NaN, row Z_MIN-1 (60th obs) defined
    assert z["A"].iloc[: Z_MIN - 1].isna().all()
    assert np.isfinite(z["A"].iloc[Z_MIN - 1])
    # causal: perturbing future data leaves z at t unchanged
    liq2 = liq.copy()
    liq2.iloc[150:, 0] = 999.0
    z2 = liq_zscore(liq2, oi)
    pd.testing.assert_series_equal(z["A"].iloc[:150], z2["A"].iloc[:150])


def test_zscore_matches_manual_ddof1():
    idx = _days(Z_WINDOW + 10)
    vals = np.arange(Z_WINDOW + 10, dtype=float) + 1.0
    liq = pd.DataFrame({"A": vals}, index=idx)
    oi = pd.DataFrame({"A": np.full(len(idx), 2.0)}, index=idx)
    z = liq_zscore(liq, oi)
    t = Z_WINDOW + 5
    win = (vals / 2.0)[t - Z_WINDOW + 1 : t + 1]
    expect = (vals[t] / 2.0 - win.mean()) / win.std(ddof=1)
    assert z["A"].iloc[t] == pytest.approx(expect)


def test_zscore_nan_on_zero_or_missing_oi():
    idx = _days(Z_WINDOW + 20)
    liq = pd.DataFrame({"A": np.full(len(idx), 1.0)}, index=idx)
    oi = pd.DataFrame({"A": np.full(len(idx), 5.0)}, index=idx)
    oi.iloc[100, 0] = 0.0
    oi.iloc[101, 0] = np.nan
    z = liq_zscore(liq, oi)
    assert np.isnan(z["A"].iloc[100]) and np.isnan(z["A"].iloc[101])


# ── event_weights ────────────────────────────────────────────────────────────

def _z_frame(events_long, events_short, n=30):
    idx = _days(n)
    zl = pd.DataFrame({"A": np.zeros(n)}, index=idx)
    zs = pd.DataFrame({"A": np.zeros(n)}, index=idx)
    for t in events_long:
        zl.iloc[t, 0] = 5.0
    for t in events_short:
        zs.iloc[t, 0] = 5.0
    return zl, zs


def test_event_hold_window_and_unit_weight():
    zl, zs = _z_frame(events_long=[10], events_short=[])
    W = event_weights(zl, zs, thr=2.5, hold=3)
    w = W["A"]
    assert w.iloc[9] == 0.0
    assert (w.iloc[10:13] == UNIT_W).all()   # rows t..t+H-1 -> earns bars t+1..t+H
    assert w.iloc[13] == 0.0


def test_event_triggers_at_exact_threshold():
    zl, zs = _z_frame(events_long=[], events_short=[])
    zl.iloc[10, 0] = 2.5
    W = event_weights(zl, zs, thr=2.5, hold=1)
    assert W["A"].iloc[10] == UNIT_W
    zl.iloc[10, 0] = 2.4999
    W = event_weights(zl, zs, thr=2.5, hold=1)
    assert W["A"].iloc[10] == 0.0


def test_same_direction_reevent_resets_timer():
    zl, zs = _z_frame(events_long=[10, 12], events_short=[])
    W = event_weights(zl, zs, thr=2.5, hold=3)
    assert (W["A"].iloc[10:15] == UNIT_W).all()  # 10..14 = union of [10,12] and [12,14]
    assert W["A"].iloc[15] == 0.0


def test_opposite_events_net_to_zero():
    zl, zs = _z_frame(events_long=[10], events_short=[10])
    W = event_weights(zl, zs, thr=2.5, hold=3)
    assert (W["A"].iloc[10:13] == 0.0).all()


def test_partial_overlap_nets_only_common_days():
    zl, zs = _z_frame(events_long=[10], events_short=[12])
    W = event_weights(zl, zs, thr=2.5, hold=3)
    assert (W["A"].iloc[10:12] == UNIT_W).all()    # long only
    assert W["A"].iloc[12] == 0.0                  # overlap nets
    assert (W["A"].iloc[13:15] == -UNIT_W).all()   # short tail
    assert W["A"].iloc[15] == 0.0


def test_nan_z_is_no_event():
    zl, zs = _z_frame(events_long=[], events_short=[])
    zl.iloc[10, 0] = np.nan
    W = event_weights(zl, zs, thr=2.5, hold=3)
    assert (W["A"] == 0.0).all()


# ── run_liq_portfolio ────────────────────────────────────────────────────────

def test_engine_causal_accrual_cost_and_rf_pinned():
    idx = _days(4)
    W = pd.DataFrame({"A": [0.0, UNIT_W, UNIT_W, 0.0]}, index=idx)
    R = pd.DataFrame({"A": [0.0, 0.10, 0.20, -0.10]}, index=idx)
    port = run_liq_portfolio(W, R, cost_bps=10.0, rf_daily=RF_DAILY)
    # bar1: Wprev=0 -> no price leg; cost on |W0-W_{-1}|=0; -rf
    assert port.iloc[0] == pytest.approx(-RF_DAILY)
    # bar2: Wprev=UNIT_W earns R=0.20; cost 10bps*|W1-W0|=10bps*UNIT_W; -rf
    assert port.iloc[1] == pytest.approx(UNIT_W * 0.20 - 1e-3 * UNIT_W - RF_DAILY)
    # bar3: Wprev=UNIT_W earns R=-0.10; no weight change at bar2; -rf
    assert port.iloc[2] == pytest.approx(UNIT_W * -0.10 - RF_DAILY)


def test_engine_decision_bar_never_earns_own_return():
    idx = _days(3)
    W = pd.DataFrame({"A": [0.0, UNIT_W, 0.0]}, index=idx)
    R = pd.DataFrame({"A": [0.0, 99.0, 0.0]}, index=idx)  # spike ON decision bar
    port = run_liq_portfolio(W, R, cost_bps=0.0, rf_daily=0.0)
    assert (port == 0.0).all()  # position earns bar t+1 only; never bar t


def test_engine_missing_return_contributes_zero():
    idx = _days(3)
    W = pd.DataFrame({"A": [UNIT_W, UNIT_W, UNIT_W]}, index=idx)
    R = pd.DataFrame({"A": [0.0, np.nan, 0.05]}, index=idx)
    port = run_liq_portfolio(W, R, cost_bps=0.0, rf_daily=0.0)
    assert port.iloc[0] == 0.0
    assert port.iloc[1] == pytest.approx(UNIT_W * 0.05)


def test_engine_index_mismatch_raises():
    W = pd.DataFrame({"A": [0.0]}, index=_days(1))
    R = pd.DataFrame({"B": [0.0]}, index=_days(1))
    with pytest.raises(ValueError):
        run_liq_portfolio(W, R)


# ── placebo kill-test (compact) ──────────────────────────────────────────────

def test_planted_reversal_signal_beats_placebos():
    """Synthetic: price mean-reverts hard the day after a 'cascade'. The real
    aligned weights must out-SR circularly shifted weights under both families."""
    from tradingagents.xsect.trend import circular_shift_weights, shared_shift_weights
    from tradingagents.xsect.portfolio import sr

    rng = np.random.default_rng(7)
    n, syms = 600, ["A", "B", "C", "D"]
    idx = _days(n)
    R = pd.DataFrame(rng.normal(0, 0.01, (n, len(syms))), index=idx, columns=syms)
    zl = pd.DataFrame(0.0, index=idx, columns=syms)
    zs = pd.DataFrame(0.0, index=idx, columns=syms)
    for s in syms:
        ev = rng.choice(np.arange(60, n - 2), size=25, replace=False)
        for t in ev:
            zl.iloc[t, syms.index(s)] = 5.0
            R.iloc[t + 1, syms.index(s)] += 0.03  # next-day rebound
    W = event_weights(zl, zs, thr=2.5, hold=1)
    real_sr = sr(run_liq_portfolio(W, R, cost_bps=10.0, rf_daily=RF_DAILY))
    for fam in (circular_shift_weights, shared_shift_weights):
        placebo = [
            sr(run_liq_portfolio(fam(W, np.random.default_rng(seed=p)), R,
                                 cost_bps=10.0, rf_daily=RF_DAILY))
            for p in range(30)
        ]
        assert real_sr > np.quantile(placebo, 0.95)
