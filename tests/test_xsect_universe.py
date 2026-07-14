import numpy as np
import pandas as pd
from tradingagents.xsect.universe import eligibility, weekly_rebalance_dates


def _kl(first, last, qv=1e7):
    idx = pd.date_range(first, last, freq="D", tz="UTC")
    return pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
                         "quote_volume": qv}, index=idx)


def test_age_filter():
    kl = {"OLD": _kl("2021-01-01", "2021-12-31"), "NEW": _kl("2021-11-20", "2021-12-31")}
    d = pd.Timestamp("2021-12-06", tz="UTC")
    assert eligibility(kl, d) == ["OLD"]  # NEW is 16 days old


def test_volume_filter_and_ranking():
    kl = {"BIG": _kl("2021-01-01", "2021-12-31", qv=2e7),
          "MID": _kl("2021-01-01", "2021-12-31", qv=1e7),
          "DUST": _kl("2021-01-01", "2021-12-31", qv=1e5)}
    d = pd.Timestamp("2021-06-07", tz="UTC")
    got = eligibility(kl, d, top_n=2)
    assert got == ["BIG", "MID"]  # DUST fails $5M floor; ranked by volume


def test_delisted_symbol_leaves_universe():
    kl = {"DEAD": _kl("2021-01-01", "2021-06-01"), "LIVE": _kl("2021-01-01", "2021-12-31")}
    assert "DEAD" in eligibility(kl, pd.Timestamp("2021-05-03", tz="UTC"))
    assert "DEAD" not in eligibility(kl, pd.Timestamp("2021-06-07", tz="UTC"))


def test_weekly_mondays():
    dates = weekly_rebalance_dates("2021-01-01", "2021-01-31")
    assert all(d.dayofweek == 0 for d in dates)
    assert str(dates[0].date()) == "2021-01-04"


def test_volume_window_is_calendar_anchored():
    # Discriminating fixture: calendar window [D-29, D] with ONE interior gap
    # tests that eligibility uses calendar anchoring, not last-N-observations.
    # This kills the tail(30) regression.
    d = pd.Timestamp("2021-12-08", tz="UTC")
    d_minus_29 = d - pd.Timedelta(days=29)  # 2021-11-09
    d_minus_30 = d - pd.Timedelta(days=30)  # 2021-11-08

    # Create ~100-day index (actually 99 from 2021-09-01 to 2021-12-08), remove one interior day
    idx = pd.date_range("2021-09-01", "2021-12-08", freq="D", tz="UTC")
    interior_gap_date = pd.Timestamp("2021-11-20", tz="UTC")
    idx = idx.delete(idx.get_loc(interior_gap_date))
    assert len(idx) == 98  # 99 - 1 = 98

    # Volume distribution:
    # - D-30 (outside calendar window): 1e12 (extreme; only old tail(30) would include it)
    # - Calendar window [D-29, D] (29 rows due to gap): 15×4e6 + 14×1e7
    #   Median of 29 values = sorted[14] (0-idx) = 4e6 < 5e6 floor → EXCLUDED
    # - Before D-30: all 1e7
    qv = np.ones(len(idx)) * 1e7
    pos_d_minus_30 = idx.get_loc(d_minus_30)
    qv[pos_d_minus_30] = 1e12

    # Assign 15×4e6 and 14×1e7 within calendar window [D-29, D]
    calendar_mask = (idx >= d_minus_29) & (idx <= d)
    calendar_pos = np.where(calendar_mask)[0]
    assert len(calendar_pos) == 29, f"Expected 29 rows in calendar window, got {len(calendar_pos)}"
    qv[calendar_pos[:15]] = 4e6
    qv[calendar_pos[15:]] = 1e7

    kl = {"TEST": pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
                                 "quote_volume": qv}, index=idx)}

    # Assertion 1: Calendar window [D-29, D] excludes D-30 → median 4e6 < floor
    result = eligibility(kl, d)
    assert "TEST" not in result, \
        f"TEST should be excluded at {d} (calendar window median 4e6 < 5e6 floor)"

    # Assertion 2: Verify the gap exists in [D-29, D]
    window_dates = kl["TEST"].loc[d_minus_29:d].index
    full_range = pd.date_range(d_minus_29, d, freq="D", tz="UTC")
    gaps = full_range.difference(window_dates)
    assert len(gaps) == 1, \
        f"Expected 1 missing day in [{d_minus_29}, {d}], got {len(gaps)}: {gaps}"
    assert gaps[0] == interior_gap_date

    # Assertion 3: Positive control — earlier date where window is all 1e7 → included
    d_control = d - pd.Timedelta(days=60)  # Far enough back to avoid D-30
    result_control = eligibility(kl, d_control)
    assert "TEST" in result_control, \
        f"TEST should be included at {d_control} (control window median 1e7 >= floor)"


def test_age_boundary_exact_30_days():
    # Symbol with first kline at exactly D-30 should be included
    d = pd.Timestamp("2021-12-08", tz="UTC")
    d_minus_30 = d - pd.Timedelta(days=30)

    # Symbol starting at D-30
    kl_at_30 = {"AT_30": _kl(str(d_minus_30.date()), str(d.date()), qv=1e7)}

    # Symbol starting at D-29 (29 days old)
    d_minus_29 = d - pd.Timedelta(days=29)
    kl_at_29 = {"AT_29": _kl(str(d_minus_29.date()), str(d.date()), qv=1e7)}

    # If df.index[0] > date - pd.Timedelta(days=min_age_days): skip
    # AT_30: first index == D-30, condition false, included
    # AT_29: first index == D-29 > D-30, condition true, excluded

    result_at_30 = eligibility(kl_at_30, d)
    result_at_29 = eligibility(kl_at_29, d)

    assert "AT_30" in result_at_30, "Symbol at exactly D-30 should be included"
    assert "AT_29" not in result_at_29, "Symbol at D-29 (only 29 days old) should be excluded"


def test_equal_volume_tiebreak_alphabetical():
    # Two symbols with identical constant volume
    kl = {"BBB": _kl("2021-01-01", "2021-12-31", qv=1e7),
          "AAA": _kl("2021-01-01", "2021-12-31", qv=1e7)}
    d = pd.Timestamp("2021-06-07", tz="UTC")
    got = eligibility(kl, d, top_n=2)
    # Should return in alphabetical order
    assert got == ["AAA", "BBB"]
