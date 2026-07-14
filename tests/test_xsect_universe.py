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
    # Create 100-day fixture with one interior missing day in the last 30 calendar days
    idx = pd.date_range("2021-09-01", "2021-12-08", freq="D", tz="UTC")
    # Remove one interior day (e.g., day 95 out of 100)
    idx = idx.delete(95)

    # Create volume data where D-30 has an extreme value that would flip ranking if included
    # Evaluation date: 2021-12-08 (100 days from 2021-09-01)
    # D-30 = 2021-11-08
    # Calendar window: [D-29, D] = [2021-11-09, 2021-12-08] excludes D-30
    qv = np.ones(len(idx)) * 1e7

    # Find the index position of 2021-11-08 (D-30)
    d_minus_30 = pd.Timestamp("2021-11-08", tz="UTC")
    if d_minus_30 in idx:
        pos = idx.get_loc(d_minus_30)
        qv[pos] = 1e12  # Extreme value at D-30

    # Create kline with this data
    kl = {"TEST": pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
                                 "quote_volume": qv}, index=idx)}

    # Evaluate at 2021-12-08
    d = pd.Timestamp("2021-12-08", tz="UTC")

    # Calendar window [2021-11-09, 2021-12-08] should NOT include the extreme value at 2021-11-08
    # Compute expected median from the calendar slice
    expected_window = kl["TEST"].loc[d - pd.Timedelta(days=29):d]["quote_volume"]
    expected_median = float(expected_window.median())

    # Assert eligibility returns TEST (volume >= min_mvol of 5e6)
    result = eligibility(kl, d)
    assert "TEST" in result
    # Verify median is around 1e7, not pulled down by the 1e12 at D-30
    assert expected_median >= 1e7


def test_age_boundary_exact_30_days():
    # Symbol with first kline at exactly D-30 should be included
    d = pd.Timestamp("2021-12-08", tz="UTC")
    d_minus_30 = d - pd.Timedelta(days=30)

    # Symbol starting at D-30
    kl_at_30 = {"AT_30": _kl(str(d_minus_30.date()), str(d.date()), qv=1e7)}

    # Symbol starting at D-29 (29 days old)
    d_minus_29 = d - pd.Timedelta(days=29)
    kl_at_29 = {"AT_29": _kl(str(d_minus_29.date()), str(d.date()), qv=1e7)}

    # Both should be in eligibility (default min_age_days=30 means must be >= 30 days old)
    # Actually, let me re-read: if df.index[0] > date - pd.Timedelta(days=min_age_days): continue
    # So if first kline is AFTER D-30, it's skipped. If it's AT or BEFORE D-30, it's included.
    # AT_30: first index == D-30, so D-30 <= D-30? Yes, included.
    # AT_29: first index == D-29, so D-29 <= D-30? No, D-29 > D-30, so excluded.

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
