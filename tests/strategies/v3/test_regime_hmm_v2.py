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


def test_nh_transition_matrix_softmax_normalizes_rows():
    from tradingagents.strategies.v3.regime.hmm_v2 import NHTransitionMatrix
    import numpy as np

    coefs = np.zeros((3, 3, 2))  # 3 from-states × 3 to-states × 2 covariates
    intercepts = np.zeros((3, 3))
    nh = NHTransitionMatrix(coefs=coefs, intercepts=intercepts)
    cov = np.array([0.5, 0.0001])
    M = nh.transition(cov)
    assert M.shape == (3, 3)
    np.testing.assert_allclose(M.sum(axis=1), [1.0, 1.0, 1.0], atol=1e-9)


def test_nh_transition_matrix_zero_intercepts_uniform():
    from tradingagents.strategies.v3.regime.hmm_v2 import NHTransitionMatrix
    import numpy as np

    coefs = np.zeros((3, 3, 2))
    intercepts = np.zeros((3, 3))
    nh = NHTransitionMatrix(coefs=coefs, intercepts=intercepts)
    M = nh.transition(np.array([0.0, 0.0]))
    np.testing.assert_allclose(M, np.full((3, 3), 1.0 / 3.0), atol=1e-9)


def test_nh_transition_matrix_high_vol_increases_bull_exit():
    """If the vol covariate has a positive coefficient on the
    bull→sideways and bull→bear transitions, raising the vol input
    should lower P(bull→bull) and raise P(bull→bear)+P(bull→sideways).
    """
    from tradingagents.strategies.v3.regime.hmm_v2 import NHTransitionMatrix
    import numpy as np

    coefs = np.zeros((3, 3, 2))
    # bull is state 0, sideways state 1, bear state 2.
    # Make leaving bull more likely under high vol (covariate index 0).
    coefs[0, 1, 0] = 5.0  # bull→sideways gets boost from vol
    coefs[0, 2, 0] = 5.0  # bull→bear gets boost from vol
    intercepts = np.zeros((3, 3))
    nh = NHTransitionMatrix(coefs=coefs, intercepts=intercepts)
    M_low = nh.transition(np.array([0.0, 0.0]))
    M_high = nh.transition(np.array([1.0, 0.0]))
    assert M_high[0, 0] < M_low[0, 0]
    assert M_high[0, 1] + M_high[0, 2] > M_low[0, 1] + M_low[0, 2]
