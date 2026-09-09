import numpy as np
import pandas as pd
from tradingagents.xsect.liq_fade import run_hourly_portfolio, sharpe_daily

RF_D = 1.045 ** (1 / 365) - 1


def test_hand_computed_single_event():
    idx = pd.date_range("2021-01-01", periods=48, freq="1h", tz="UTC")
    W = pd.DataFrame(0.0, index=idx, columns=["A"])
    W.iloc[10:13, 0] = 0.1                     # 3-bar hold
    R = pd.DataFrame(0.01, index=idx, columns=["A"])
    net = run_hourly_portfolio(W, R, cost_bps=10.0)
    # gross: 3 bars * 0.1 * 0.01 = 0.003 ; costs: |dW| = 0.1 + 0.1 -> 2e-4
    # all inside day 1; rf on both calendar days
    assert np.isclose(net.iloc[0], 0.003 - 2e-4 - RF_D)
    assert np.isclose(net.iloc[1], -RF_D)


def test_missing_return_contributes_zero():
    idx = pd.date_range("2021-01-01", periods=24, freq="1h", tz="UTC")
    W = pd.DataFrame(0.1, index=idx, columns=["A"])
    R = pd.DataFrame(np.nan, index=idx, columns=["A"])
    net = run_hourly_portfolio(W, R, cost_bps=0.0)
    assert np.isclose(net.iloc[0], -RF_D)


def test_sharpe_zero_variance_is_zero():
    s = pd.Series(0.0, index=pd.date_range("2021-01-01", periods=10, tz="UTC"))
    assert sharpe_daily(s) == 0.0
