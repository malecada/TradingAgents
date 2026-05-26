import numpy as np
import pandas as pd

from tradingagents.market.indicators import (
    INDICATOR_CATEGORY,
    INDICATOR_WHITELIST,
    compute_indicator_directions,
    compute_indicator_values,
)


def _make_ohlcv(n: int = 250, trend: float = 0.001, vol: float = 0.01,
                seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(loc=trend, scale=vol, size=n)
    close = 20000.0 * np.exp(np.cumsum(rets))
    high = close * (1.0 + np.abs(rng.normal(0, 0.005, n)))
    low = close * (1.0 - np.abs(rng.normal(0, 0.005, n)))
    openp = close * (1.0 + rng.normal(0, 0.002, n))
    vol_arr = rng.lognormal(mean=10, sigma=0.3, size=n)
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    return pd.DataFrame(
        {"Date": dates, "Open": openp, "High": high, "Low": low,
         "Close": close, "Volume": vol_arr}
    )


def test_whitelist_size_is_13():
    assert len(INDICATOR_WHITELIST) == 13
    assert "close_30_sma" in INDICATOR_WHITELIST
    assert "vwma" in INDICATOR_WHITELIST


def test_indicator_category_covers_whitelist():
    assert set(INDICATOR_CATEGORY.keys()) == set(INDICATOR_WHITELIST)
    for cat in INDICATOR_CATEGORY.values():
        assert cat in {"trend", "momentum", "volatility", "volume"}


def test_compute_indicator_values_uptrending_series():
    df = _make_ohlcv(n=250, trend=0.003, vol=0.01, seed=42)
    vals = compute_indicator_values(df)
    assert set(vals.keys()) == set(INDICATOR_WHITELIST)
    for k, v in vals.items():
        assert np.isfinite(v), f"{k} non-finite: {v}"


def test_directions_uptrend_majority_bullish():
    df = _make_ohlcv(n=250, trend=0.005, vol=0.005, seed=1)
    vals = compute_indicator_values(df)
    directions = compute_indicator_directions(df, vals)
    trend_names = [n for n, c in INDICATOR_CATEGORY.items() if c == "trend"]
    trend_dirs = [directions[n] for n in trend_names]
    assert sum(1 for d in trend_dirs if d == 1) >= 3


def test_directions_downtrend_majority_bearish():
    df = _make_ohlcv(n=250, trend=-0.005, vol=0.005, seed=2)
    vals = compute_indicator_values(df)
    directions = compute_indicator_directions(df, vals)
    trend_names = [n for n, c in INDICATOR_CATEGORY.items() if c == "trend"]
    trend_dirs = [directions[n] for n in trend_names]
    assert sum(1 for d in trend_dirs if d == -1) >= 3


def test_compute_indicator_values_returns_float_scalars():
    df = _make_ohlcv(n=250)
    vals = compute_indicator_values(df)
    for k, v in vals.items():
        assert isinstance(v, float), f"{k}={v!r} not float"
