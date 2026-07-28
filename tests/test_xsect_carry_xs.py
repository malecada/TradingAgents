import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.carry_xs import (
    build_funding_matrix, carry_signal, funding_daily,
)


def _prints(day_rates):  # {"2024-01-01": [1e-4, 2e-4, ...]}
    ts, vals = [], []
    for d, rates in day_rates.items():
        for i, r in enumerate(rates):
            ts.append(pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=4 * i))
            vals.append(r)
    idx = pd.DatetimeIndex(ts, name="fundingTime")
    return pd.DataFrame({"fundingRate": vals}, index=idx).sort_index()


def test_funding_daily_sums_prints_not_mean():
    f = funding_daily(_prints({"2024-01-01": [1e-4, 1e-4, 1e-4]}))
    assert f.loc[pd.Timestamp("2024-01-01", tz="UTC")] == pytest.approx(3e-4)


def test_funding_daily_gap_day_is_nan():
    f = funding_daily(_prints({"2024-01-01": [1e-4], "2024-01-03": [1e-4]}))
    assert np.isnan(f.loc[pd.Timestamp("2024-01-02", tz="UTC")])
    assert len(f) == 3  # gapless calendar spans the hole


def test_funding_daily_handles_4h_symbols():
    f = funding_daily(_prints({"2024-01-01": [1e-4] * 6}))  # 4h interval coin
    assert f.iloc[0] == pytest.approx(6e-4)


def test_carry_signal_requires_full_window():
    prints = _prints({"2024-01-01": [1e-4], "2024-01-02": [3e-4], "2024-01-04": [5e-4]})
    F = build_funding_matrix({"XUSDT": prints},
                             funding_daily(prints).index, ["XUSDT"])
    S = carry_signal(F, L=2)
    d = pd.Timestamp("2024-01-02", tz="UTC")
    assert S.loc[d, "XUSDT"] == pytest.approx(2e-4)          # mean of daily sums
    assert np.isnan(S.loc[pd.Timestamp("2024-01-04", tz="UTC"), "XUSDT"])  # gap in window
    assert np.isnan(S.loc[pd.Timestamp("2024-01-01", tz="UTC"), "XUSDT"])  # warmup
