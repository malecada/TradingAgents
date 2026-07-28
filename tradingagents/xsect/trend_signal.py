"""Frozen model-free trend vote — verbatim rules from tradingagents/metalabel/primary.py
(§44 registration, branch feature/meta-labeling). Input adapted to a close Series;
parameters MUST NOT change (spec 2026-07-28-trend-wide-design.md).

Vote = mean of 4 binary rules: MA-cross 5/20, 10/40, 20/60 and a stateful
Donchian 20-entry/10-exit channel. Long when vote > 0.5.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MA_PAIRS = ((5, 20), (10, 40), (20, 60))
DONCHIAN_ENTRY = 20
DONCHIAN_EXIT = 10
WARMUP = 60


def compute_votes(close: pd.Series) -> pd.Series:
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
    votes.iloc[: WARMUP - 1] = np.nan
    votes.name = "vote"
    return votes
