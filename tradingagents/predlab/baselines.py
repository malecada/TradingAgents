"""Tier-0 forecasters — the nulls every later tier is measured against.

Forecaster protocol (duck-typed, consumed by runner + every tier):
  name: str
  fit(y_train, X_train=None) -> None      # purged train slice at refit origins
  predict(y_hist, x_now=None) -> float    # one forecast of y[origin]

y_hist is the REALIZED target history at the origin (labels fully known);
y_train is the purged/embargoed subset used for parameter fitting. With
embargo=0 the two coincide. All Tier-0 models are closed-form and are refit
every origin.
"""

from __future__ import annotations

import numpy as np


class Forecaster:
    name = "forecaster"

    def fit(self, y_train: np.ndarray, X_train: "np.ndarray | None" = None) -> None:
        return None

    def predict(self, y_hist: np.ndarray, x_now: "np.ndarray | None" = None) -> float:
        raise NotImplementedError


class RWZero(Forecaster):
    """Random-walk / zero forecast (the T1 strong baseline)."""

    name = "rw_zero"

    def predict(self, y_hist, x_now=None):
        return 0.0


class HistMean(Forecaster):
    """Expanding mean of realized targets."""

    name = "hist_mean"

    def predict(self, y_hist, x_now=None):
        return float(np.nanmean(y_hist))


class Persistence(Forecaster):
    """Last realized target value."""

    name = "persistence"

    def predict(self, y_hist, x_now=None):
        return float(y_hist[-1])


class SeasonalNaive(Forecaster):
    """Value one seasonal period (m target bars) ago; persistence fallback."""

    def __init__(self, m: int):
        self.m = int(m)
        self.name = f"seasonal_naive_m{self.m}"

    def predict(self, y_hist, x_now=None):
        if len(y_hist) < self.m:
            return float(y_hist[-1])
        return float(y_hist[-self.m])


class EWMA(Forecaster):
    """RiskMetrics-style exponential smoothing of the target series.

    s_t = lam * s_{t-1} + (1 - lam) * y_t, seeded at y[0]; forecast = s_last.
    For T3 cells the target is realized variance, so this is the classic EWMA
    variance forecast (weak vol baseline).
    """

    def __init__(self, lam: float = 0.94):
        self.lam = float(lam)
        self.name = f"ewma_{self.lam:g}"

    def predict(self, y_hist, x_now=None):
        y = np.asarray(y_hist, dtype=np.float64)
        y = y[~np.isnan(y)]
        s = y[0]
        for v in y[1:]:
            s = self.lam * s + (1.0 - self.lam) * v
        return float(s)


class Climatology(Forecaster):
    """Expanding mean of the target by season bin (exog column bin_col).

    Refit every origin with the purged train slice; unseen bins fall back to
    the global train mean.
    """

    def __init__(self, bin_col: int = 0):
        self.bin_col = int(bin_col)
        self.name = "climatology"
        self._means: "dict[float, float]" = {}
        self._global = float("nan")

    def fit(self, y_train, X_train=None):
        y = np.asarray(y_train, dtype=np.float64)
        self._global = float(np.nanmean(y))
        self._means = {}
        if X_train is None:
            return
        bins = np.asarray(X_train, dtype=np.float64)[:, self.bin_col]
        for b in np.unique(bins[~np.isnan(bins)]):
            mask = bins == b
            if mask.any():
                self._means[float(b)] = float(np.nanmean(y[mask]))

    def predict(self, y_hist, x_now=None):
        if x_now is None:
            return self._global
        b = float(np.asarray(x_now, dtype=np.float64)[self.bin_col])
        return self._means.get(b, self._global)


class BaseRate(Forecaster):
    """Expanding share of up-moves — probability forecast for T2 cells."""

    name = "base_rate"

    def predict(self, y_hist, x_now=None):
        y = np.asarray(y_hist, dtype=np.float64)
        y = y[~np.isnan(y)]
        return float(np.mean(y > 0))
