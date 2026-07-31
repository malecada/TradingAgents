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


def _oi_5m(n_days=10, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n_days * 288, freq="5min", tz="UTC")
    oi = 50000 * np.exp(np.cumsum(rng.normal(0, 0.001, len(idx))))
    return pd.DataFrame(
        {
            "oi": oi,
            "oi_value": oi * 40000,
            "top_ls_accounts": rng.uniform(0.8, 1.4, len(idx)),
            "top_ls_positions": rng.uniform(0.8, 1.4, len(idx)),
            "ls_accounts": rng.uniform(0.8, 1.4, len(idx)),
            "taker_ls_vol": rng.uniform(0.5, 1.6, len(idx)),
        },
        index=idx,
    )


def test_oi_features_strictly_lagged_and_aggregated():
    df = _oi_5m()
    f = features.oi_features(df, grid="1h")
    assert len(f) == 240  # 10 days of hourly rows
    # oi_dlog1[t] = log(oi_close[t-1]) - log(oi_close[t-2]) where oi_close is
    # the last 5m observation of each hour
    hourly_close = df["oi"].resample("1h").last()
    t = 100
    expected = np.log(hourly_close.iloc[t - 1]) - np.log(hourly_close.iloc[t - 2])
    assert np.isclose(f["oi_dlog1"].iloc[t], expected)
    # mutation: change 5m rows inside hour t -> features at t unchanged
    df2 = df.copy()
    hr_start = f.index[t]
    mask = (df2.index >= hr_start) & (df2.index < hr_start + pd.Timedelta(hours=1))
    df2.loc[mask, "oi"] = df2.loc[mask, "oi"] * 2.0
    f2 = features.oi_features(df2, grid="1h")
    pd.testing.assert_frame_equal(f.iloc[: t + 1], f2.iloc[: t + 1])


def test_oi_z_and_ratio_columns_present():
    f = features.oi_features(_oi_5m(20), grid="1h")
    for col in ("oi_dlog1", "oi_dlog24", "oi_z168", "top_ls_lag1", "taker_ls_lag1"):
        assert col in f.columns
    z = f["oi_z168"].dropna()
    assert len(z) > 0 and z.abs().median() < 3.0


def test_daily_grid_uses_weekly_windows():
    st = _store(freq="D")
    f = features.build_features(st, grid="24h")
    t = 200
    assert np.isclose(f["rv_mean7"].iloc[t], st["rv"].iloc[t - 7 : t].mean())
    assert "rv_mean24" not in f.columns
