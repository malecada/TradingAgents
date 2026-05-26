import numpy as np
import pandas as pd

from tradingagents.market.regime_tag import (
    RegimeFeatures,
    compute_regime_features,
    deterministic_regime,
)


def _series(n: int, start: float = 20000.0, drift: float = 0.0,
            vol: float = 0.01, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = rng.normal(drift, vol, n)
    close = start * np.exp(np.cumsum(r))
    high = close * (1.0 + np.abs(rng.normal(0, 0.005, n)))
    low = close * (1.0 - np.abs(rng.normal(0, 0.005, n)))
    return pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=n, freq="D"),
        "Open": close, "High": high, "Low": low, "Close": close,
        "Volume": np.ones(n) * 1e6,
    })


def test_compute_regime_features_keys():
    df = _series(250, drift=0.0, vol=0.01)
    feats = compute_regime_features(df)
    assert isinstance(feats, RegimeFeatures)
    for k in ("adx", "atr_percentile", "return_30d"):
        assert hasattr(feats, k)


def test_strong_uptrend_classified_trend_up():
    df = _series(250, drift=0.006, vol=0.005, seed=10)
    label, conf, _feats = deterministic_regime(df)
    assert label == "TREND_UP"
    assert 0.0 <= conf <= 1.0


def test_strong_downtrend_classified_trend_down():
    df = _series(250, drift=-0.006, vol=0.005, seed=11)
    label, conf, _ = deterministic_regime(df)
    assert label == "TREND_DOWN"


def test_high_vol_classified_high_vol():
    # seed=42: ADX=17.9 (< 25 threshold), atr_percentile=0.978 → HIGH_VOL
    # original seed=7 triggered TREND_DOWN (ADX=32.4, large 30d return) — fixture adjusted
    rng = np.random.default_rng(42)
    n = 250
    base = np.full(n, 0.005)
    base[-40:] = 0.05
    rets = rng.normal(0.0, base, n)
    close = 20000.0 * np.exp(np.cumsum(rets))
    df = pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=n, freq="D"),
        "Open": close,
        "High": close * 1.02, "Low": close * 0.98,
        "Close": close, "Volume": np.ones(n) * 1e6,
    })
    label, _, feats = deterministic_regime(df)
    assert label == "HIGH_VOL"
    assert feats.atr_percentile > 0.8


def test_chop_classified_range():
    df = _series(250, drift=0.0, vol=0.005, seed=3)
    label, _, _ = deterministic_regime(df)
    assert label == "RANGE"
