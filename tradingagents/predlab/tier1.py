"""Tier-1 classical forecasters (ARIMA / ETS / sign-logit).

All follow the Forecaster protocol (fit on the purged train slice at refit
origins; predict from the realized y_hist only). Parameters learned at fit
time are APPLIED to y_hist at predict time — predict never re-estimates, so
between refits the model uses stale parameters but fresh data, matching the
registered refit cadence.
"""

from __future__ import annotations

import warnings

import numpy as np
from sklearn.linear_model import LogisticRegression
from statsmodels.tsa.statespace.sarimax import SARIMAX

from tradingagents.predlab.baselines import Forecaster

_DEFAULT_ORDERS = ((1, 0, 0), (0, 0, 1), (1, 0, 1), (2, 0, 2))


class ArimaForecaster(Forecaster):
    """SARIMAX on the target series; order chosen by in-train AIC at refit.

    predict() applies the fitted parameters to y_hist via SARIMAXResults.apply
    (Kalman filter over the new data, no re-estimation) and forecasts 1 step.
    """

    name = "arima_aic"

    def __init__(self, orders=_DEFAULT_ORDERS, refit_every: int = 5):
        self.orders = tuple(tuple(o) for o in orders)
        self.refit_every = refit_every  # informational; cadence enforced by runner
        self._res = None
        self._order = None

    def fit(self, y_train, X_train=None):
        y = np.asarray(y_train, dtype=np.float64)
        y = y[~np.isnan(y)]
        best_aic, best_res, best_order = np.inf, None, None
        for order in self.orders:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    res = SARIMAX(y, order=order, trend="c").fit(disp=False)
                if res.aic < best_aic:
                    best_aic, best_res, best_order = res.aic, res, order
            except Exception:
                continue
        self._res, self._order = best_res, best_order

    def predict(self, y_hist, x_now=None):
        y = np.asarray(y_hist, dtype=np.float64)
        y = y[~np.isnan(y)]
        if self._res is None or len(y) < 10:
            return 0.0
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            applied = self._res.apply(y, refit=False)
            return float(applied.forecast(1)[0])


class EtsForecaster(Forecaster):
    """Exponential smoothing, ANN (level) or AAN (Holt level+trend).

    Smoothing weights are grid-fit on the train slice by one-step SSE
    (deterministic, no optimizer dependence); predict runs the recursion over
    y_hist with the fitted weights.
    """

    _GRID = np.round(np.arange(0.05, 1.0, 0.05), 2)

    def __init__(self, kind: str = "ANN", refit_every: int = 5):
        kind = kind.upper()
        if kind not in ("ANN", "AAN"):
            raise ValueError(kind)
        self.kind = kind
        self.name = f"ets_{kind.lower()}"
        self.refit_every = refit_every
        self._alpha = 0.3
        self._beta = 0.1

    @staticmethod
    def _run(y: np.ndarray, alpha: float, beta: "float | None"):
        """Return one-step-ahead forecast after consuming y (and SSE over y)."""
        level = y[0]
        trend = 0.0
        sse = 0.0
        for v in y[1:]:
            f = level + (trend if beta is not None else 0.0)
            sse += (v - f) ** 2
            if beta is not None:
                new_level = alpha * v + (1 - alpha) * (level + trend)
                trend = beta * (new_level - level) + (1 - beta) * trend
                level = new_level
            else:
                level = alpha * v + (1 - alpha) * level
        return level + (trend if beta is not None else 0.0), sse

    def fit(self, y_train, X_train=None):
        y = np.asarray(y_train, dtype=np.float64)
        y = y[~np.isnan(y)]
        if len(y) < 10:
            return
        best = (np.inf, self._alpha, self._beta)
        betas = self._GRID if self.kind == "AAN" else [None]
        for a in self._GRID:
            for b in betas:
                _, sse = self._run(y, a, b)
                if sse < best[0]:
                    best = (sse, a, b)
        self._alpha, self._beta = best[1], (best[2] if self.kind == "AAN" else None)

    def predict(self, y_hist, x_now=None):
        y = np.asarray(y_hist, dtype=np.float64)
        y = y[~np.isnan(y)]
        if len(y) < 2:
            return float(y[-1]) if len(y) else 0.0
        beta = self._beta if self.kind == "AAN" else None
        f, _ = self._run(y, self._alpha, beta)
        return float(f)


class LogitLags(Forecaster):
    """Logistic regression on the signs of the last n_lags targets → P(up)."""

    def __init__(self, n_lags: int = 5, refit_every: int = 5):
        self.n_lags = int(n_lags)
        self.name = f"logit_lags{self.n_lags}"
        self.refit_every = refit_every
        self._clf = None
        self._base = 0.5

    def _design(self, y: np.ndarray):
        s = np.sign(y)
        n = len(y)
        rows = []
        labels = []
        for t in range(self.n_lags, n):
            rows.append(s[t - self.n_lags : t][::-1])  # most recent lag first
            labels.append(1.0 if y[t] > 0 else 0.0)
        return np.array(rows), np.array(labels)

    def fit(self, y_train, X_train=None):
        y = np.asarray(y_train, dtype=np.float64)
        y = y[~np.isnan(y)]
        self._base = float(np.mean(y > 0)) if len(y) else 0.5
        if len(y) <= self.n_lags + 20:
            self._clf = None
            return
        X, lab = self._design(y)
        if len(np.unique(lab)) < 2:
            self._clf = None
            return
        self._clf = LogisticRegression(C=1.0, max_iter=200)
        self._clf.fit(X, lab)

    def predict(self, y_hist, x_now=None):
        y = np.asarray(y_hist, dtype=np.float64)
        y = y[~np.isnan(y)]
        if self._clf is None or len(y) < self.n_lags:
            return self._base
        x = np.sign(y[-self.n_lags :][::-1]).reshape(1, -1)
        return float(self._clf.predict_proba(x)[0, 1])
