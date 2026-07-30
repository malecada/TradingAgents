import numpy as np
import pandas as pd
import pytest

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
