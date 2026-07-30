"""Per-observation forecast losses.

All functions are vectorized, take/return float64 ndarrays, and return one loss
per observation so downstream tests (DM/CW/GW) can work on loss differentials.
"""

from __future__ import annotations

import numpy as np


def se(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """Squared error."""
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    return (y_true - y_pred) ** 2


def ae(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """Absolute error."""
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    return np.abs(y_true - y_pred)


def qlike(var_forecast: np.ndarray, rv: np.ndarray) -> np.ndarray:
    """Patton (2011) normalized QLIKE: rv/var - log(rv/var) - 1.

    Proxy-robust loss for variance forecasts. Non-negative, zero iff
    var_forecast == rv elementwise. Elements where either input is
    non-positive are nan (variance forecasts and realized variance must be
    strictly positive to be scoreable).
    """
    var_forecast = np.asarray(var_forecast, dtype=np.float64)
    rv = np.asarray(rv, dtype=np.float64)
    out = np.full(np.broadcast(var_forecast, rv).shape, np.nan, dtype=np.float64)
    ok = (var_forecast > 0) & (rv > 0)
    r = np.divide(rv, var_forecast, out=np.ones_like(out), where=ok)
    np.subtract(r - np.log(r, out=np.zeros_like(out), where=ok), 1.0, out=out, where=ok)
    return out


def mase_scale(y_train: np.ndarray, m: int = 1) -> float:
    """Hyndman-Koehler MASE scaling: mean |seasonal-naive in-sample error|.

    Computed on the TRAIN portion only (train-only scaling is the leakage-safe
    convention); m is the seasonal period (1 = non-seasonal naive).
    """
    y_train = np.asarray(y_train, dtype=np.float64)
    if len(y_train) <= m:
        return float("nan")
    return float(np.mean(np.abs(y_train[m:] - y_train[:-m])))


def mase(y_true: np.ndarray, y_pred: np.ndarray, scale: float) -> np.ndarray:
    """Per-observation absolute error scaled by a train-period MASE scale."""
    return ae(y_true, y_pred) / scale


def brier(p_up: np.ndarray, y_up: np.ndarray) -> np.ndarray:
    """Brier loss for probability-of-up forecasts against 0/1 outcomes."""
    p_up = np.asarray(p_up, dtype=np.float64)
    y_up = np.asarray(y_up, dtype=np.float64)
    return (p_up - y_up) ** 2
