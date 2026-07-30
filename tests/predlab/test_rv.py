from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.predlab import rv


def _synth_5m(n_days=30, sigma_daily=0.02, seed=0):
    rng = np.random.default_rng(seed)
    n = n_days * 288
    r = rng.normal(0, sigma_daily / np.sqrt(288), n)
    close = 100 * np.exp(np.cumsum(r))
    ts = pd.date_range("2024-01-01", periods=n, freq="5min", tz="UTC").asi8 // 10**6
    return pd.DataFrame(
        {
            "ts": ts,
            "open": close,
            "high": close * 1.0001,
            "low": close * 0.9999,
            "close": close,
            "quote_volume": 1.0,
            "taker_buy_quote_volume": 0.5,
            "n_trades": 10.0,
        }
    )


def test_rv_recovers_known_daily_variance():
    out = rv.aggregate_rv(_synth_5m(200, sigma_daily=0.02), "1d")
    est = float(np.nanmedian(out["rv"]))
    assert 0.7 * 0.02**2 < est < 1.3 * 0.02**2


def test_first_period_dropped_and_labels_utc():
    out = rv.aggregate_rv(_synth_5m(5), "1d")
    assert len(out) == 4  # first day dropped (no return seed)
    assert str(out.index[0]) == "2024-01-02 00:00:00+00:00"
    hourly = rv.aggregate_rv(_synth_5m(2), "1h")
    assert len(hourly) == 47  # first hour dropped


def test_constant_price_zero_rv():
    d = _synth_5m(5)
    for col in ("open", "high", "low", "close"):
        d[col] = 100.0
    out = rv.aggregate_rv(d, "1d")
    assert np.allclose(out["rv"].dropna(), 0.0)
    assert np.allclose(out["ret"].dropna(), 0.0)


def test_period_isolation_no_lookahead():
    a = _synth_5m(10, seed=1)
    b = a.copy()
    b.loc[b.index[-288:], "close"] = b.loc[b.index[-288:], "close"] * 1.5
    ra, rb = rv.aggregate_rv(a, "1d"), rv.aggregate_rv(b, "1d")
    pd.testing.assert_frame_equal(ra.iloc[:-1], rb.iloc[:-1])


def test_incomplete_period_flagged():
    d = _synth_5m(3).iloc[:-200]  # last day incomplete (88 bars)
    out = rv.aggregate_rv(d, "1d")
    assert np.isnan(out["rv"].iloc[-1])
    assert out["n_bars"].iloc[-1] < 230
    # complete middle day untouched
    assert not np.isnan(out["rv"].iloc[0])


def test_bv_close_to_rv_for_gaussian():
    out = rv.aggregate_rv(_synth_5m(200, seed=3), "1d")
    ratio = float(np.nanmedian(out["bv"] / out["rv"]))
    assert 0.8 < ratio < 1.2  # BV consistent estimator of IV, no jumps planted


def test_volume_and_trades_summed():
    out = rv.aggregate_rv(_synth_5m(3), "1d")
    assert np.isclose(out["quote_volume"].iloc[0], 288.0)
    assert np.isclose(out["taker_buy_quote_volume"].iloc[0], 144.0)
    assert np.isclose(out["n_trades"].iloc[0], 2880.0)
