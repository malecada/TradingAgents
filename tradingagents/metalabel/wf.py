"""Purged expanding walk-forward over event space (AFML ch.7 adapted).

Purge rule: a train event is admissible for a test block starting at S
iff its label window has fully resolved before S minus the embargo:
touch_date < S - EMBARGO_CAL_DAYS.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

EMBARGO_CAL_DAYS = 21  # 15 trading bars ~ 21 calendar days


def purged_walk_forward(
    meta: pd.DataFrame,
    dev_start: str,
    dev_end: str,
    retrain_every_days: int = 90,
    embargo_bars: int = 15,
    min_train_events: int = 150,
) -> list[tuple[np.ndarray, np.ndarray]]:
    ev = pd.to_datetime(meta["event_date"])
    touch = pd.to_datetime(meta["touch_date"])
    start, end = pd.Timestamp(dev_start), pd.Timestamp(dev_end)

    folds = []
    block_start = start + pd.Timedelta(days=365)  # first year is train-only
    while block_start < end:
        block_end = min(block_start + pd.Timedelta(days=retrain_every_days), end)
        te = np.where((ev >= block_start) & (ev < block_end))[0]
        tr = np.where(
            (ev >= start)
            & (touch < block_start - pd.Timedelta(days=EMBARGO_CAL_DAYS))
        )[0]
        if len(te):
            if len(tr) >= min_train_events:
                folds.append((tr, te))
            else:
                warnings.warn(
                    f"fold at {block_start.date()} skipped: "
                    f"{len(tr)} < {min_train_events} train events"
                )
        block_start = block_end
    return folds
