"""Liquidation-cascade mean-reversion fade — frozen mechanics per gates.json
liq_mr_t1.

Spec: docs/superpowers/specs/2026-07-28-liq-mr-design.md. Per coin, per
direction: z-score of daily liquidations/OI over a trailing 90d window
(min_periods 60, inclusive of day t — all inputs complete at close t per the
Coinglass bar-open stamp, verified by the contemporaneity probe). Event at
close t holds a fixed 1/8 fade position over bars t+1..t+H; same-direction
re-events reset the timer; opposite directions net. Decision at close t applies
to bar t+1; costs 10 bps/side on |dW|; rf on full capital. Price leg uses
simple returns (spec convention; trend/carry use log — do not swap).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RF_DAILY = 1.045 ** (1 / 365) - 1  # house section-41 convention, = carry_xs_t1
Z_WINDOW = 90                       # rolling z-score window (fixed, not gridded)
Z_MIN = 60                          # min_periods for the rolling stats
N_COINS = 8                         # fixed universe size
UNIT_W = 1.0 / N_COINS              # per-coin unit weight (no vol scaling)


def liq_zscore(liq_usd: pd.DataFrame, oi_close: pd.DataFrame) -> pd.DataFrame:
    """Trailing z-score of liq/OI; zero or missing OI -> NaN (no signal)."""
    oi = oi_close.where(oi_close > 0)
    x = liq_usd / oi
    mean = x.rolling(Z_WINDOW, min_periods=Z_MIN).mean()
    std = x.rolling(Z_WINDOW, min_periods=Z_MIN).std()  # ddof=1
    return (x - mean) / std


def event_weights(z_long: pd.DataFrame, z_short: pd.DataFrame,
                  thr: float, hold: int) -> pd.DataFrame:
    """W[t] earns bar t+1 (engine convention), so an event at close t sets
    rows t..t+H-1. rolling(H).max over the event indicator implements both the
    hold window and the same-direction timer reset; opposite directions net."""
    act_long = (z_long >= thr).astype(float).rolling(hold, min_periods=1).max()
    act_short = (z_short >= thr).astype(float).rolling(hold, min_periods=1).max()
    return (act_long - act_short) * UNIT_W


def run_liq_portfolio(W: pd.DataFrame, R: pd.DataFrame, cost_bps: float = 10.0,
                      rf_daily: float = RF_DAILY) -> pd.Series:
    """Identical accrual/cost arithmetic to trend.run_daily_portfolio plus the
    flat rf deduction on full capital (mirrors carry_xs.run_ls_portfolio
    without the funding leg)."""
    if not W.index.equals(R.index) or list(W.columns) != list(R.columns):
        raise ValueError("W and R must share identical index and columns")
    Wv = W.to_numpy()
    Rv = np.nan_to_num(R.to_numpy(), nan=0.0)
    Wprev = np.vstack([np.zeros((1, Wv.shape[1])), Wv[:-1]])       # W[t-1]
    Wprev2 = np.vstack([np.zeros((2, Wv.shape[1])), Wv[:-2]])      # W[t-2]
    price = (Wprev * Rv).sum(axis=1)
    cost = cost_bps / 1e4 * np.abs(Wprev - Wprev2).sum(axis=1)
    port = pd.Series(price - cost - rf_daily, index=W.index)
    return port.iloc[1:]
