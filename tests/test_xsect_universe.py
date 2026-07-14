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
