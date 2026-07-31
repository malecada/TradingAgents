from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.predlab import features


def _store(n=400, seed=0, freq="h"):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq=freq, tz="UTC")
    rv = np.exp(rng.normal(-9, 0.6, n))
    qv = np.exp(rng.normal(15, 0.4, n))
    return pd.DataFrame(
        {
            "rv": rv,
            "bv": rv * 0.9,
            "rq": rv**2 * 3.0,
            "ret": rng.normal(0, 0.01, n),
            "quote_volume": qv,
            "taker_buy_quote_volume": qv * rng.uniform(0.3, 0.7, n),
            "n_bars": 12.0,
            "park": rv * 1.1,
            "n_trades": 1000.0,
        },
        index=idx,
    )


def test_build_features_are_strictly_lagged():
    # feature row at t must be computable from store rows <= t-1:
    # mutate row t of the store; features at t must NOT change (only t+1.. may)
    st = _store()
    f_a = features.build_features(st, grid="1h")
    st2 = st.copy()
    st2.iloc[200] = st2.iloc[200] * 3.0
    f_b = features.build_features(st2, grid="1h")
    pd.testing.assert_frame_equal(f_a.iloc[:201], f_b.iloc[:201])
    assert not f_a.iloc[201].equals(f_b.iloc[201])  # t+1 does see row t


def test_taker_imbalance_range_and_lag():
    st = _store()
    f = features.build_features(st, grid="1h")
    ti = f["ti_lag1"].dropna()
    assert ((ti >= -1.0) & (ti <= 1.0)).all()
    # ti_lag1[t] == 2*taker_share[t-1] - 1
    t = 100
    share = st["taker_buy_quote_volume"].iloc[t - 1] / st["quote_volume"].iloc[t - 1]
    assert np.isclose(f["ti_lag1"].iloc[t], 2 * share - 1)


def test_rv_ratio_and_lag_columns():
    st = _store()
    f = features.build_features(st, grid="1h")
    t = 300
    assert np.isclose(f["rv_lag1"].iloc[t], st["rv"].iloc[t - 1])
    expected = st["rv"].iloc[t - 24 : t].mean()
    assert np.isclose(f["rv_mean24"].iloc[t], expected)
    assert np.isclose(
        f["rv_ratio_1_24"].iloc[t], st["rv"].iloc[t - 1] / expected
    )


def test_calendar_features_deterministic():
    st = _store()
    f = features.build_features(st, grid="1h")
    hod = st.index.hour.to_numpy()
    assert np.allclose(f["hod_sin"], np.sin(2 * np.pi * hod / 24))
    assert np.allclose(f["dow_cos"], np.cos(2 * np.pi * st.index.dayofweek.to_numpy() / 7))


def test_funding_features_aligned_to_prints():
    rng = np.random.default_rng(5)
    idx = pd.date_range("2022-01-01", periods=90, freq="8h", tz="UTC")
    rate = pd.Series(rng.normal(1e-4, 5e-5, 90), index=idx)
    hourly_idx = pd.date_range("2022-01-01", periods=400, freq="h", tz="UTC")
    f = features.funding_features(rate, hourly_idx)
    # at any t, fund_last must equal the most recent print STRICTLY BEFORE t
    t = hourly_idx[100]
    last_print = rate[rate.index < t].iloc[-1]
    assert np.isclose(f.loc[t, "fund_last"], last_print)
    assert set(f.columns) == {"fund_last", "fund_mean3", "fund_cum24h"}


def test_daily_grid_uses_weekly_windows():
    st = _store(freq="D")
    f = features.build_features(st, grid="24h")
    t = 200
    assert np.isclose(f["rv_mean7"].iloc[t], st["rv"].iloc[t - 7 : t].mean())
    assert "rv_mean24" not in f.columns
