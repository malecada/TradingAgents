from __future__ import annotations

import numpy as np

from tradingagents.strategies.v3.backtest.dsr import (
    deflated_sharpe_ratio,
    expected_max_sharpe,
)


def test_expected_max_sharpe_monotonic_in_n_trials():
    e1 = expected_max_sharpe(n_trials=1, var_sr=1.0)
    e10 = expected_max_sharpe(n_trials=10, var_sr=1.0)
    e100 = expected_max_sharpe(n_trials=100, var_sr=1.0)
    assert e1 < e10 < e100


def test_dsr_zero_when_observed_equals_expected_max():
    sr_obs = 1.5
    sr_exp = 1.5
    se_sr = 0.5
    dsr = deflated_sharpe_ratio(
        sr_observed=sr_obs,
        sr_expected_under_null=sr_exp,
        se_sr=se_sr,
    )
    assert abs(dsr - 0.5) < 1e-6  # Φ((0)/se) = 0.5


def test_dsr_high_when_observed_much_higher_than_expected():
    dsr = deflated_sharpe_ratio(
        sr_observed=3.5,
        sr_expected_under_null=1.0,
        se_sr=0.3,
    )
    assert dsr > 0.99


def test_dsr_low_when_observed_below_expected():
    dsr = deflated_sharpe_ratio(
        sr_observed=0.5,
        sr_expected_under_null=1.5,
        se_sr=0.3,
    )
    assert dsr < 0.01
