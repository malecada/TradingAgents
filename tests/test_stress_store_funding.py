"""stress_ews2 — store-derived funding component (charter 2026-09-04)."""
import numpy as np
import pandas as pd
import pytest

from tradingagents.stress.index import daily_funding_from_store


def test_daily_funding_is_mean_of_the_three_settlements():
    idx = pd.to_datetime(["2021-01-01 00:00", "2021-01-01 08:00", "2021-01-01 16:00",
                          "2021-01-02 00:00", "2021-01-02 08:00", "2021-01-02 16:00"], utc=True)
    s = pd.DataFrame({"fundingRate": [0.0001, 0.0002, 0.0003, 0.0004, 0.0004, 0.0004]}, index=idx)
    d = daily_funding_from_store(s)
    assert list(d.index) == list(pd.to_datetime(["2021-01-01", "2021-01-02"], utc=True))
    assert d.iloc[0] == pytest.approx(0.0002)
    assert d.iloc[1] == pytest.approx(0.0004)


def test_daily_funding_partial_day_uses_available_settlements():
    idx = pd.to_datetime(["2021-01-01 08:00", "2021-01-01 16:00"], utc=True)
    s = pd.DataFrame({"fundingRate": [0.0002, 0.0004]}, index=idx)
    assert daily_funding_from_store(s).iloc[0] == pytest.approx(0.0003)
