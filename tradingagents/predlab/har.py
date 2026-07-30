"""HAR family (Corsi 2009): har_levels, log_har, harq.

Design row for target y[t]: [1, y[t-1], mean(y[t-l2:t]), mean(y[t-l3:t])]
with lags (1, 5, 22) on daily grids and (1, 24, 168) on hourly grids.
log_har runs the same design in logs and exponentiates the forecast (naive
back-transform; documented bias, secondary variant per registration).
harq (Bollerslev-Patton-Quaedvlieg) adds sqrt(rq_{t-1}) * y[t-1] where the
realized-quarticity exog column is PRE-LAGGED at series construction (row t
holds rq of the last fully-realized period, so x_now is in the information
set at the origin).
"""

from __future__ import annotations

import numpy as np

from tradingagents.predlab.baselines import Forecaster

_EPS = 1e-12


class HarForecaster(Forecaster):
    def __init__(self, kind: str = "har_levels", rq_col: "int | None" = None,
                 lags: "tuple[int, int, int]" = (1, 5, 22), refit_every: int = 1):
        if kind not in ("har_levels", "log_har", "harq"):
            raise ValueError(kind)
        if kind == "harq" and rq_col is None:
            raise ValueError("harq requires rq_col (pre-lagged realized quarticity)")
        self.kind = kind
        self.name = kind
        self.rq_col = rq_col
        self.lags = tuple(int(v) for v in lags)
        self.refit_every = refit_every
        self._coef = None

    def _transform(self, y: np.ndarray) -> np.ndarray:
        if self.kind == "log_har":
            return np.log(np.maximum(y, _EPS))
        return y

    def _row(self, z: np.ndarray, t: int, rq_last: "float | None") -> "list[float]":
        l1, l2, l3 = self.lags
        row = [1.0, z[t - l1], float(np.mean(z[t - l2 : t])), float(np.mean(z[t - l3 : t]))]
        if self.kind == "harq":
            row.append(float(np.sqrt(max(rq_last or 0.0, 0.0)) * z[t - l1]))
        return row

    def fit(self, y_train, X_train=None):
        y = np.asarray(y_train, dtype=np.float64)
        z = self._transform(y)
        l1, l2, l3 = self.lags
        n = len(z)
        if n <= l3:
            self._coef = None
            return
        # vectorized design (equivalent to the per-row loop; pinned by
        # test_har_vectorized_design_matches_loop_reference)
        c = np.concatenate([[0.0], np.nancumsum(z)])
        t_idx = np.arange(l3, n)
        lag1 = z[t_idx - l1]
        m2 = (c[t_idx] - c[t_idx - l2]) / l2
        m3 = (c[t_idx] - c[t_idx - l3]) / l3
        cols = [np.ones(len(t_idx)), lag1, m2, m3]
        nan_c = np.concatenate([[0], np.cumsum(np.isnan(z))])
        window_nan = (nan_c[t_idx] - nan_c[t_idx - l3]) > 0
        valid = ~np.isnan(z[t_idx]) & ~window_nan
        if self.kind == "harq":
            rq = (np.asarray(X_train[:, self.rq_col], dtype=np.float64)[t_idx]
                  if X_train is not None else np.zeros(len(t_idx)))
            valid &= ~np.isnan(rq)
            cols.append(np.sqrt(np.maximum(np.nan_to_num(rq), 0.0)) * lag1)
        A = np.column_stack(cols)[valid]
        b = z[t_idx][valid]
        if len(b) < 30:
            self._coef = None
            return
        self._coef, *_ = np.linalg.lstsq(A, b, rcond=None)

    def predict(self, y_hist, x_now=None):
        y = np.asarray(y_hist, dtype=np.float64)
        y = y[~np.isnan(y)]
        l3 = self.lags[2]
        if self._coef is None or len(y) < l3 + 1:
            return float(y[-1]) if len(y) else 0.0
        z = self._transform(y)
        rq_last = None
        if self.kind == "harq":
            rq_last = float(np.asarray(x_now, dtype=np.float64)[self.rq_col]) if x_now is not None else 0.0
        row = np.array(self._row(z, len(z), rq_last))
        f = float(row @ self._coef)
        if self.kind == "log_har":
            return float(np.exp(f))
        return f
