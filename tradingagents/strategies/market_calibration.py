"""Per-coin isotonic calibration of the v2 market analyst's conviction.

Same algorithm as tradingagents.strategies.calibration but stored under a
separate filename so the sentiment and market calibrators do not collide.

The modulator multiplies the analyst's verbalized conviction by the
calibrator's output, so the effective per-coin weight is endogenous: a
coin where the analyst has no edge ends up with a calibrator that maps
all convictions toward ~0.5 → effective contribution ≈ 0.
"""
from __future__ import annotations

import os
from typing import Union

import numpy as np

from tradingagents.strategies.calibration import IsotonicCalibrator

MARKET_CALIBRATOR_FILENAME = "market_isotonic_{coin}.pkl"


def fit_market_calibrator(
    raw_confidences: Union[np.ndarray, list],
    realised_outcomes: Union[np.ndarray, list],
    coin: str,
    root: str = "data/checkpoints",
) -> IsotonicCalibrator:
    c = IsotonicCalibrator().fit(
        np.asarray(raw_confidences, dtype=float),
        np.asarray(realised_outcomes, dtype=float),
        coin=coin,
    )
    os.makedirs(root, exist_ok=True)
    c.to_pkl(os.path.join(root, MARKET_CALIBRATOR_FILENAME.format(coin=coin)))
    return c


def load_market_calibrator(
    coin: str, root: str = "data/checkpoints"
) -> IsotonicCalibrator:
    path = os.path.join(root, MARKET_CALIBRATOR_FILENAME.format(coin=coin))
    if not os.path.exists(path):
        identity = IsotonicCalibrator()
        identity.coin = coin
        return identity
    return IsotonicCalibrator.from_pkl(path)
