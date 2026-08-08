import json

import numpy as np
import pandas as pd
import pytest

import scripts.value_xs_dev as vxd
from scripts.value_xs_dev import (VintageStampStale, _lag_from_vintage,
                                   decile_spread, measure_lag,
                                   verdict_from_probes)


def test_measure_lag_detects_two_day_publication_delay():
    days = pd.date_range("2022-01-01", periods=10, freq="D", tz="UTC")
    # metric present only up to day 7 while klines run to day 9 => lag 2
    fund_last = days[7]
    kline_last = days[9]
    assert measure_lag(fund_last, kline_last) == 2


def test_p0_lag_gate_fails_when_vendor_frontier_more_than_two_days_behind_fetch():
    # fix round 2: P0's lag is the vendor's own frontier (vendor_max_time,
    # captured at fetch time from the catalog endpoint) staleness vs the
    # stamp's fetch time -- not a diff against the store's own (truncated)
    # last observation, which was fix round 1's defect.
    vintage = {"fetched_utc": "2026-07-30T10:00:00+00:00",
               "vendor_max_time": "2026-07-25"}  # 5 days behind the fetch
    result = _lag_from_vintage(vintage)
    assert result["lag"] == 5
    assert result["pass"] is False


def test_p0_lag_gate_passes_at_exactly_the_registered_threshold():
    vintage = {"fetched_utc": "2026-07-30T10:00:00+00:00",
               "vendor_max_time": "2026-07-28"}  # exactly 2 days behind
    result = _lag_from_vintage(vintage)
    assert result["lag"] == 2
    assert result["pass"] is True


def test_p0_lag_gate_fails_loudly_when_vendor_max_time_missing():
    # An older vintage stamp (pre fix-round-2) has no vendor_max_time. P0
    # must refuse to run rather than silently falling back to a
    # store-endpoint comparison -- that fallback is exactly the defect that
    # produced the superseded 443-day and 471-day measurements.
    vintage = {"fetched_utc": "2026-07-30T10:00:00+00:00"}
    with pytest.raises(VintageStampStale):
        _lag_from_vintage(vintage)


def test_decile_spread_orders_cheap_minus_expensive():
    days = pd.date_range("2022-01-03", periods=40, freq="D", tz="UTC")
    cols = [f"S{i}" for i in range(10)]
    # cheap (low signal) names earn +1%/day, expensive earn -1%/day
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    R = pd.DataFrame(0.0, index=days, columns=cols)
    R[cols[:5]] = 0.01
    R[cols[5:]] = -0.01
    valid = pd.DataFrame(True, index=days, columns=cols)
    spread = decile_spread(S, R, valid, leg_frac=0.2)
    assert spread > 0


def test_decile_spread_sign_flips_when_signal_inverted():
    days = pd.date_range("2022-01-03", periods=40, freq="D", tz="UTC")
    cols = [f"S{i}" for i in range(10)]
    S = pd.DataFrame(np.tile(np.arange(10.0), (len(days), 1)), index=days, columns=cols)
    R = pd.DataFrame(0.0, index=days, columns=cols)
    R[cols[:5]] = 0.01
    R[cols[5:]] = -0.01
    valid = pd.DataFrame(True, index=days, columns=cols)
    assert decile_spread(-S, R, valid, leg_frac=0.2) < 0


def test_verdict_stops_on_any_failed_probe():
    ok = {"pass": True}
    bad = {"pass": False}
    assert verdict_from_probes(ok, ok, ok) == "CONTINUE"
    assert verdict_from_probes(ok, bad, ok) == "NEGATIVE-at-probe"
    assert verdict_from_probes(bad, ok, ok) == "NEGATIVE-at-probe"


def test_main_exits_2_and_writes_probes_json_on_stale_vintage_stamp(tmp_path, monkeypatch):
    # Fix round 3, Finding 1: VintageStampStale must not bypass the STOP
    # contract. Before this fix, main() had no exception boundary around
    # probe_p0_lag(), so a stale stamp died with Python's default exit 1
    # and wrote no probes.json -- the same bug class that cost two rounds:
    # a failure loud in a unit test but not wired into the contract the
    # rest of the pipeline depends on. Uses a synthetic tmp-dir store via
    # monkeypatch; never touches the real fundamentals/klines stores.
    days = pd.date_range(vxd.WARMUP_START, vxd.MAX_LOAD_END, freq="D", tz="UTC")

    fund_dir = tmp_path / "fundamentals"
    fund_dir.mkdir()
    pd.DataFrame(
        {"AdrActCnt": np.linspace(100, 200, len(days)),
         "TxCnt": np.linspace(1000, 2000, len(days)),
         "CapMrktCurUSD": np.linspace(1e9, 2e9, len(days))},
        index=days,
    ).to_parquet(fund_dir / "testcoin.parquet")

    klines_dir = tmp_path / "klines"
    klines_dir.mkdir()
    pd.DataFrame({"close": np.linspace(1.0, 2.0, len(days))}, index=days
                ).to_parquet(klines_dir / "TESTUSDT.parquet")

    univ_file = tmp_path / "universe.json"
    univ_file.write_text(json.dumps({"2021-01-01": ["TESTUSDT"]}))

    # Stale: no vendor_max_time key (predates fix round 2).
    vintage_file = tmp_path / "vintage.json"
    vintage_file.write_text(json.dumps(
        {"fetched_utc": "2026-07-30T00:00:00+00:00", "source_url": "test",
         "note": "test"}))

    out_dir = tmp_path / "out"

    monkeypatch.setattr(vxd, "FUND_DIR", fund_dir)
    monkeypatch.setattr(vxd, "KLINES_DIR", klines_dir)
    monkeypatch.setattr(vxd, "UNIV_FILE", univ_file)
    monkeypatch.setattr(vxd, "FUND_VINTAGE_FILE", vintage_file)
    monkeypatch.setattr(vxd, "OUT_DIR", out_dir)
    monkeypatch.setattr(vxd, "ASSET_TO_SYMBOL", {"testcoin": "TESTUSDT"})

    with pytest.raises(SystemExit) as exc:
        vxd.main()
    assert exc.value.code == 2

    probes = json.loads((out_dir / "probes.json").read_text())
    assert probes["verdict"] == "NEGATIVE-at-probe"
    p0 = probes["probes"][0]
    assert p0["probe"] == "P0_publication_lag"
    assert p0["pass"] is False
    assert p0["error"] == "vintage_stamp_stale"
    assert "vendor_max_time" in p0["note"]


def test_load_all_klines_never_exceed_max_load_end():
    # Fix round 3, Finding 2: data/xsect/klines/ is a shared,
    # continuously-updated store (observed reaching 2026-07-02 -- deep
    # inside the sealed holdout -- before this fix). _load_all must
    # truncate every frame at MAX_LOAD_END; touches the real store.
    _, klines, _, _, _ = vxd._load_all()
    bound = pd.Timestamp(vxd.MAX_LOAD_END, tz="UTC")
    assert len(klines) > 0
    over = {s: str(d.index.max()) for s, d in klines.items()
           if len(d) and d.index.max() > bound}
    assert over == {}, f"klines frames exceeding MAX_LOAD_END: {over}"


from scripts.value_xs_dev import (
    GRID, LEG_FRAC, circular_shift_columns, dsr_or_nan, gate_config,
    rank_shuffle_columns,
)


def test_grid_is_frozen_at_four_configs():
    assert len(GRID) == 4
    assert set(GRID) == {("nvt_proxy", "decile"), ("nvt_proxy", "tercile"),
                         ("metcalfe_proxy", "decile"), ("metcalfe_proxy", "tercile")}


def test_leg_fractions_match_breadth_names():
    assert LEG_FRAC["decile"] == pytest.approx(0.1)
    assert LEG_FRAC["tercile"] == pytest.approx(1 / 3)


def test_circular_shift_preserves_values_per_column():
    days = pd.date_range("2022-01-01", periods=10, freq="D", tz="UTC")
    S = pd.DataFrame({"A": np.arange(10.0), "B": np.arange(10.0) * 2}, index=days)
    out = circular_shift_columns(S, np.random.default_rng(0))
    for c in S.columns:
        assert sorted(out[c].dropna()) == sorted(S[c].dropna())
    assert not out.equals(S)


def test_rank_shuffle_preserves_row_multiset():
    days = pd.date_range("2022-01-01", periods=5, freq="D", tz="UTC")
    S = pd.DataFrame(np.arange(15.0).reshape(5, 3), index=days, columns=list("ABC"))
    out = rank_shuffle_columns(S, np.random.default_rng(0))
    for t in days:
        assert sorted(out.loc[t]) == sorted(S.loc[t])


def test_dsr_returns_nan_not_crash_on_degenerate_returns():
    # zero-variance series -> se_sr == 0 -> deflated_sharpe_ratio raises
    # ValueError internally; dsr_or_nan must swallow that into NaN, not crash.
    assert np.isnan(dsr_or_nan(pd.Series([0.01] * 50), n_trials=4))


def test_gate_requires_all_four_conditions():
    base = dict(net_sr=1.5, placebo_p_worse=0.01, dsr=0.95,
                delta_c1=0.2, delta_c2=0.3)
    assert gate_config(**base)["pass"] is True
    assert gate_config(**{**base, "net_sr": 0.9})["pass"] is False
    assert gate_config(**{**base, "placebo_p_worse": 0.06})["pass"] is False
    assert gate_config(**{**base, "dsr": 0.89})["pass"] is False
    assert gate_config(**{**base, "delta_c1": -0.01})["pass"] is False
    assert gate_config(**{**base, "delta_c2": 0.0})["pass"] is False


def test_dsr_not_saturated_for_modest_edge():
    # Pin for the 2026-07-30 unit-mismatch bug: dsr_or_nan must feed
    # variance_of_sr a per-bar SR, not the sqrt(365)-annualized SR. Mixing
    # units inflates the z-score by ~sqrt(365) and Phi() saturates -- every
    # positive SR gives exactly 1.0, every negative one gives exactly 0.0,
    # making the dsr_min=0.9 gate inoperative. A modest, realistic edge must
    # land strictly inside (0.01, 0.99), not pinned to a saturation extreme.
    rng = np.random.default_rng(11)
    returns = pd.Series(rng.normal(0.0002, 0.01, 1050))
    dsr = dsr_or_nan(returns, n_trials=4)
    assert 0.01 < dsr < 0.99


def test_dsr_monotone_in_signal_strength():
    n = 1050
    weak = pd.Series(np.random.default_rng(1).normal(0.00005, 0.01, n))
    strong = pd.Series(np.random.default_rng(1).normal(0.0006, 0.01, n))
    dsr_weak = dsr_or_nan(weak, n_trials=4)
    dsr_strong = dsr_or_nan(strong, n_trials=4)
    assert dsr_strong > dsr_weak


def test_gate_fails_on_nan_dsr():
    base = dict(net_sr=1.5, placebo_p_worse=0.01, dsr=float("nan"),
                delta_c1=0.2, delta_c2=0.3)
    assert gate_config(**base)["pass"] is False


# Task 7 build note (2026-07-30): the brief's original planted-signal fixture
# drew a *fresh* iid S value every day and built R from that SAME day's S
# (R = noise - S * 0.003). Under run_config's frozen weekly-Monday-rebalance +
# run_ls_portfolio's 1-bar decision-to-execution shift (deliberately no-
# look-ahead -- the exact discipline this project's PIT stores and the Jul-7
# same-bar audit both exist to enforce), a weight set from day t's ranking is
# never multiplied by day t's own return; it is held through the week and
# multiplied by returns generated on *other*, independently-drawn days. Since
# S has no autocorrelation, that contemporaneous "edge" is structurally
# unreachable by any correctly lagged engine -- verified empirically: the
# literal fixture gave SR in [-2.68, +0.26] across 10 seeds (consistently
# negative, driven by turnover cost + rf drag, not signal), never passing
# `> 1.0` except by chance. Recovering it would require adding a look-ahead
# shortcut to run_config, which is exactly the defect class this experiment's
# controls exist to avoid -- not a fix.
#
# The corrected fixture keeps the same intent (harness must recover a large,
# unmissable, correctly-timed edge) but makes the signal weekly-persistent
# (piecewise-constant from each Monday, matching how a real fundamentals-
# based value signal actually behaves -- slow-moving, not daily noise) and
# times the return relationship to what the engine can actually capture:
# R[s] depends on S[s-1], so the return on the bar following each decision
# day reflects the ranking that produced the active weight. Verified robust
# across 8 seeds: planted SR in [+15.3, +18.4], mistimed SR in [-1.97, -0.01]
# -- both comfortably clear of the 1.0 threshold in the intended direction.
def _weekly_constant_signal(days: pd.DatetimeIndex, cols: list, rng) -> pd.DataFrame:
    monday_vals = pd.DataFrame(rng.normal(size=(len(days), len(cols))),
                               index=days, columns=cols)
    is_monday = pd.Series(days.dayofweek == 0, index=days)
    return monday_vals.mask(~is_monday).ffill()


def test_planted_signal_is_recovered():
    """Harness sanity: inject real alpha, the pipeline must find it."""
    from scripts.value_xs_dev import run_config
    from tradingagents.xsect.ls_common import sharpe_365
    days = pd.date_range("2022-01-03", periods=400, freq="D", tz="UTC")
    cols = [f"S{i}" for i in range(20)]
    rng = np.random.default_rng(7)
    S = _weekly_constant_signal(days, cols, rng)
    # cheap (low S) names outperform by 30bp/day -- a large, unmissable edge,
    # timed to the bar the engine's 1-bar shift actually applies the weight to
    noise = pd.DataFrame(rng.normal(scale=0.01, size=(len(days), 20)), index=days, columns=cols)
    R = noise - S.shift(1) * 0.003
    valid = pd.DataFrame(True, index=days, columns=cols)
    port = run_config(S, R, valid, LEG_FRAC["decile"])
    assert sharpe_365(port) > 1.0


def test_mistimed_signal_does_not_recover_planted_alpha():
    """Kill-test: same data, signal shifted out of alignment -> edge disappears."""
    from scripts.value_xs_dev import run_config
    from tradingagents.xsect.ls_common import sharpe_365
    days = pd.date_range("2022-01-03", periods=400, freq="D", tz="UTC")
    cols = [f"S{i}" for i in range(20)]
    rng = np.random.default_rng(7)
    S = _weekly_constant_signal(days, cols, rng)
    noise = pd.DataFrame(rng.normal(scale=0.01, size=(len(days), 20)), index=days, columns=cols)
    R = noise - S.shift(1) * 0.003
    valid = pd.DataFrame(True, index=days, columns=cols)
    mistimed = S.sample(frac=1.0, random_state=3).set_index(S.index)
    assert sharpe_365(run_config(mistimed, R, valid, LEG_FRAC["decile"])) < 1.0
