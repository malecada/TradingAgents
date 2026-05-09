"""Smoke tests for v3 regime module promotion.

Task 17 promotes the existing HMM regime detector from
``tradingagents.strategies.regime`` into the v3 sub-package. These tests
verify the module imports and exposes the expected public API. Behavioral
tests for NH-HMM extensions come in Tasks 18-21.
"""

from __future__ import annotations

import pandas as pd


def test_hmm_v2_imports():
    from tradingagents.strategies.v3.regime import hmm_v2

    # Public names match the parent regime module
    assert hasattr(hmm_v2, "FittedHMM")
    assert hasattr(hmm_v2, "build_regime_features")


def test_hmm_v2_build_features_runs(synthetic_ohlcv):
    from tradingagents.strategies.v3.regime.hmm_v2 import build_regime_features

    df = build_regime_features(synthetic_ohlcv["close"])
    # dropna() removes the initial NaN rows from rolling windows (vol_lookback=30,
    # smooth_window=20 → max lag = 30 bars dropped), so output < input length.
    assert len(df) < len(synthetic_ohlcv)
    assert len(df) > 0
    assert df.columns.tolist() == [
        "log_return_smooth",
        "realized_vol",
        "abs_return_smooth",
    ]
