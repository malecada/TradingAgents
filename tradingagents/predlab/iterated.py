"""Iterated multi-step forecasting from a fitted one-step Forecaster."""

from __future__ import annotations

import numpy as np


def iterate_forecast(model, y_hist: np.ndarray, h: int, agg: str = "sum") -> float:
    """Roll a fitted 1-step model h steps, feeding forecasts back as history.

    agg="sum" returns the sum of the h step forecasts (matches direct
    h-aggregated targets like 7d return sums); agg="last" returns the h-th
    step forecast.
    """
    y = list(np.asarray(y_hist, dtype=np.float64))
    steps = []
    for _ in range(int(h)):
        f = float(model.predict(np.asarray(y)))
        steps.append(f)
        y.append(f)
    if agg == "sum":
        return float(np.sum(steps))
    if agg == "last":
        return float(steps[-1])
    raise ValueError(agg)
