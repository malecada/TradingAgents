import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.value_xs import (
    control_signal, simple_returns, value_ratio, zscore_signal,
)


def _fund(days, tx, adr, mcap):
    return pd.DataFrame({"TxCnt": tx, "AdrActCnt": adr, "CapMrktCurUSD": mcap},
                        index=days)


def test_nvt_proxy_is_mcap_over_mean_txcnt():
    days = pd.date_range("2022-01-01", periods=40, freq="D", tz="UTC")
    f = {"AUSDT": _fund(days, 100.0, 50.0, 1000.0)}
    R = value_ratio(f, "nvt_proxy", days, window=30)
    assert R.loc[days[35], "AUSDT"] == pytest.approx(1000.0 / 100.0)


def test_metcalfe_proxy_is_mcap_over_mean_adractcnt():
    days = pd.date_range("2022-01-01", periods=40, freq="D", tz="UTC")
    f = {"AUSDT": _fund(days, 100.0, 50.0, 1000.0)}
    R = value_ratio(f, "metcalfe_proxy", days, window=30)
    assert R.loc[days[35], "AUSDT"] == pytest.approx(1000.0 / 50.0)


def test_ratio_is_nan_before_window_is_full():
    days = pd.date_range("2022-01-01", periods=40, freq="D", tz="UTC")
    f = {"AUSDT": _fund(days, 100.0, 50.0, 1000.0)}
    R = value_ratio(f, "nvt_proxy", days, window=30)
    assert R.loc[days[10], "AUSDT"] != R.loc[days[10], "AUSDT"]   # NaN


def test_zscore_is_cross_sectional_and_lagged():
    days = pd.date_range("2022-01-01", periods=5, freq="D", tz="UTC")
    R = pd.DataFrame({"A": [1.0, 2, 3, 4, 5], "B": [5.0, 4, 3, 2, 1],
                      "C": [3.0, 3, 3, 3, 3]}, index=days)
    Z = zscore_signal(R, lag_days=2)
    # row t reflects raw row t-2
    raw = np.log(R.iloc[0])
    expect = (raw - raw.mean()) / raw.std(ddof=1)
    pd.testing.assert_series_equal(Z.iloc[2], expect, check_names=False)
    assert Z.iloc[0].isna().all() and Z.iloc[1].isna().all()


def test_zscore_row_is_standardised():
    days = pd.date_range("2022-01-01", periods=3, freq="D", tz="UTC")
    R = pd.DataFrame({"A": [1.0, 2, 4], "B": [2.0, 4, 8], "C": [4.0, 8, 16]}, index=days)
    Z = zscore_signal(R, lag_days=0)
    assert Z.iloc[0].mean() == pytest.approx(0.0, abs=1e-12)
    assert Z.iloc[0].std(ddof=1) == pytest.approx(1.0)


# --- mutation kill-tests: these MUST fail if the shift direction is wrong ---

def test_lag_uses_past_not_future():
    days = pd.date_range("2022-01-01", periods=6, freq="D", tz="UTC")
    # a spike on day 2 must appear at day 4 under lag 2, never at day 0
    R = pd.DataFrame({"A": [1.0, 1, 100, 1, 1, 1], "B": [1.0, 1, 1, 1, 1, 1],
                      "C": [2.0, 2, 2, 2, 2, 2]}, index=days)
    Z = zscore_signal(R, lag_days=2)
    assert Z.iloc[4]["A"] > Z.iloc[3]["A"]
    assert Z.iloc[0].isna().all()


def test_simple_returns_are_simple_not_log():
    days = pd.date_range("2022-01-01", periods=3, freq="D", tz="UTC")
    k = {"AUSDT": pd.DataFrame({"close": [100.0, 110.0, 121.0]}, index=days)}
    R = simple_returns(k, days, ["AUSDT"])
    assert R.loc[days[1], "AUSDT"] == pytest.approx(0.10)
    assert R.loc[days[1], "AUSDT"] != pytest.approx(np.log(1.10))


def test_reversal_control_shorts_recent_winners():
    days = pd.date_range("2022-01-01", periods=40, freq="D", tz="UTC")
    up = pd.DataFrame({"close": np.linspace(100, 200, 40)}, index=days)
    dn = pd.DataFrame({"close": np.linspace(200, 100, 40)}, index=days)
    S = control_signal({"UUSDT": up, "DUSDT": dn}, days, ["UUSDT", "DUSDT"], "reversal")
    # higher signal = short leg; the winner must carry the higher signal
    assert S.iloc[-1]["UUSDT"] > S.iloc[-1]["DUSDT"]


def test_vol_control_shorts_high_vol():
    days = pd.date_range("2022-01-01", periods=60, freq="D", tz="UTC")
    rng = np.random.default_rng(1)
    calm = pd.DataFrame({"close": 100 * np.exp(np.cumsum(rng.normal(0, 0.002, 60)))}, index=days)
    wild = pd.DataFrame({"close": 100 * np.exp(np.cumsum(rng.normal(0, 0.05, 60)))}, index=days)
    S = control_signal({"CUSDT": calm, "WUSDT": wild}, days, ["CUSDT", "WUSDT"], "vol")
    assert S.iloc[-1]["WUSDT"] > S.iloc[-1]["CUSDT"]
