"""Frozen model-free trend primary. Parameters pinned in experiments/metalabel/freeze.json.

Vote = mean of 4 binary rules: MA-cross 5/20, 10/40, 20/60 and a stateful
Donchian 20-entry/10-exit channel. Entry event = vote crossing above 0.5.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MA_PAIRS = ((5, 20), (10, 40), (20, 60))
DONCHIAN_ENTRY = 20
DONCHIAN_EXIT = 10
WARMUP = 60


def compute_votes(ohlcv: pd.DataFrame) -> pd.Series:
    close = pd.Series(ohlcv["Close"].values, index=pd.DatetimeIndex(ohlcv["Date"]))
    rules = []
    for fast, slow in MA_PAIRS:
        rules.append((close.rolling(fast).mean() > close.rolling(slow).mean()).astype(float))

    # Stateful Donchian: 1 after close > prior 20d high, 0 after close < prior 10d low.
    hi = close.shift(1).rolling(DONCHIAN_ENTRY).max()
    lo = close.shift(1).rolling(DONCHIAN_EXIT).min()
    raw = pd.Series(np.nan, index=close.index)
    raw[close > hi] = 1.0
    raw[close < lo] = 0.0
    rules.append(raw.ffill().fillna(0.0))

    votes = pd.concat(rules, axis=1).mean(axis=1)
    votes.iloc[:WARMUP - 1] = np.nan
    votes.name = "vote"
    return votes


def extract_events(votes: pd.Series) -> pd.DatetimeIndex:
    prev = votes.shift(1)
    cross = (votes > 0.5) & (prev <= 0.5) & prev.notna()
    return pd.DatetimeIndex(votes.index[cross])


def primary_positions(votes: pd.Series) -> pd.Series:
    pos = (votes > 0.5).astype(float)
    pos[votes.isna()] = np.nan
    pos.name = "position"
    return pos
