"""Deterministic regime tag for prompt conditioning.

NOT the HMM regime in tradingagents/strategies/regime.py — that one is
trained per-coin and used by the modulator. This one is a fast
training-free per-bar tag suitable for inclusion in the market
analyst's prompt. It uses ADX, 30-day return sign, and ATR percentile.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd

from tradingagents.market._stockstats_utils import to_stockstats

_ATR_PCT_WINDOW = 90


@dataclass
class RegimeFeatures:
    adx: float
    atr_percentile: float
    return_30d: float


def compute_regime_features(df: pd.DataFrame) -> RegimeFeatures:
    sdf = to_stockstats(df)
    adx_series = sdf["adx"]
    adx = float(adx_series.iloc[-1]) if np.isfinite(adx_series.iloc[-1]) else 0.0

    atr_series = sdf["atr"]
    tail = atr_series.tail(_ATR_PCT_WINDOW).dropna()
    if len(tail) >= 10 and np.isfinite(atr_series.iloc[-1]):
        atr_pct = float(np.clip((tail < atr_series.iloc[-1]).mean(), 0.0, 1.0))
    else:
        atr_pct = 0.5

    close = df["Close"].astype(float)
    if len(close) >= 31:
        return_30d = float(close.iloc[-1] / close.iloc[-31] - 1.0)
    else:
        return_30d = 0.0

    return RegimeFeatures(adx=adx, atr_percentile=atr_pct, return_30d=return_30d)


def deterministic_regime(df: pd.DataFrame) -> Tuple[str, float, RegimeFeatures]:
    """Return ``(label, confidence, features)``.

    Precedence: TREND_* dominates if ADX > 25; HIGH_VOL only when no trend
    is detected. This avoids labelling a strong trending market HIGH_VOL
    just because volatility is elevated.
    """
    feats = compute_regime_features(df)
    if feats.adx > 25.0 and feats.return_30d > 0.0:
        return "TREND_UP", float(np.clip(0.5 + 0.5 * min(feats.adx / 40.0, 1.0),
                                         0.0, 1.0)), feats
    if feats.adx > 25.0 and feats.return_30d < 0.0:
        return "TREND_DOWN", float(np.clip(0.5 + 0.5 * min(feats.adx / 40.0, 1.0),
                                            0.0, 1.0)), feats
    if feats.atr_percentile > 0.8:
        return "HIGH_VOL", float(np.clip(0.5 + 0.5 * (feats.atr_percentile - 0.8) / 0.2,
                                          0.0, 1.0)), feats
    denom = max(feats.atr_percentile, 0.05)
    conf = float(np.clip(0.6 - 0.1 * abs(feats.return_30d) / denom, 0.0, 1.0))
    return "RANGE", conf, feats
