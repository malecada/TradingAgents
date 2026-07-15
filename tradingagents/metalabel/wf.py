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
    """Build purged, expanding walk-forward train/test folds over an event space.

    Adapted from AFML ch.7. Test blocks tile ``[dev_start + 365d, dev_end)``
    contiguously in ``retrain_every_days``-wide chunks. A train event is
    admissible for a given test block iff its label window has fully
    resolved before the block start minus an embargo, i.e.
    ``touch_date < block_start - embargo_days``. This prevents any train
    event whose outcome touch overlaps (or nearly overlaps) the upcoming
    test block from leaking information into it.

    ``embargo_bars`` (a bar count) is converted to calendar days via
    ``embargo_days = round(embargo_bars * 1.4)`` — the 1.4 factor reflects
    the average calendar-day span of a trading bar in this dataset (the
    default ``embargo_bars=15`` maps to the module constant
    ``EMBARGO_CAL_DAYS = 21``).

    Args:
        meta: Event-level metadata with ``event_date`` and ``touch_date``
            columns (coercible to datetime).
        dev_start: Start of the development window (inclusive), as an
            ISO date string.
        dev_end: End of the development window (exclusive), as an ISO
            date string. The first 365 days of ``[dev_start, dev_end)``
            are train-only (no test block is emitted there).
        retrain_every_days: Width, in calendar days, of each test block.
        embargo_bars: Embargo width in bars, converted to calendar days
            (see above) and subtracted from the test block start when
            deciding which train events are admissible.
        min_train_events: Minimum number of admissible train events
            required to emit a fold; folds with fewer are skipped with a
            warning.

    Returns:
        A list of ``(train_idx, test_idx)`` tuples, each a pair of
        integer position arrays into ``meta``, one tuple per emitted
        fold in chronological order.
    """
    ev = pd.to_datetime(meta["event_date"])
    touch = pd.to_datetime(meta["touch_date"])
    start, end = pd.Timestamp(dev_start), pd.Timestamp(dev_end)
    embargo_days = int(round(embargo_bars * 1.4))

    folds = []
    block_start = start + pd.Timedelta(days=365)  # first year is train-only
    while block_start < end:
        block_end = min(block_start + pd.Timedelta(days=retrain_every_days), end)
        te = np.where((ev >= block_start) & (ev < block_end))[0]
        tr = np.where(
            (ev >= start)
            & (touch < block_start - pd.Timedelta(days=embargo_days))
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
