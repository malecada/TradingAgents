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

    def __init__(self, orders=_DEFAULT_ORDERS, refit_every: int = 5,
                 window_cap: "int | None" = None):
        self.orders = tuple(tuple(o) for o in orders)
        self.refit_every = refit_every  # informational; cadence enforced by runner
        self.window_cap = window_cap  # declared 1h amendment: cap conditioning window
        self._res = None
        self._order = None

    def fit(self, y_train, X_train=None):
        y = np.asarray(y_train, dtype=np.float64)
        y = y[~np.isnan(y)]
        if self.window_cap:
            y = y[-self.window_cap :]
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
        if self.window_cap:
            y = y[-self.window_cap :]
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

    def __init__(self, kind: str = "ANN", refit_every: int = 5,
                 window_cap: "int | None" = None):
        kind = kind.upper()
        if kind not in ("ANN", "AAN"):
            raise ValueError(kind)
        self.kind = kind
        self.name = f"ets_{kind.lower()}"
        self.refit_every = refit_every
        self.window_cap = window_cap
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
        if self.window_cap:
            y = y[-self.window_cap :]
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
        if self.window_cap:
            y = y[-self.window_cap :]
        if len(y) < 2:
            return float(y[-1]) if len(y) else 0.0
        beta = self._beta if self.kind == "AAN" else None
        f, _ = self._run(y, self._alpha, beta)
        return float(f)


class SeasonalAR(Forecaster):
    """OLS on short lags + one seasonal lag: y[t] ~ [1, y[t-1..t-3], y[t-m]]."""

    def __init__(self, m: int, n_lags: int = 3, refit_every: int = 1):
        self.m = int(m)
        self.n_lags = int(n_lags)
        self.name = f"seasonal_ar_m{self.m}"
        self.refit_every = refit_every
        self._coef = None

    def _row(self, y: np.ndarray, t: int) -> "list[float]":
        return [1.0, *[y[t - k] for k in range(1, self.n_lags + 1)], y[t - self.m]]

    def fit(self, y_train, X_train=None):
        y = np.asarray(y_train, dtype=np.float64)
        start = max(self.n_lags, self.m)
        rows, tgt = [], []
        for t in range(start, len(y)):
            window = y[t - start : t + 1]
            if np.any(np.isnan(window)):
                continue
            rows.append(self._row(y, t))
            tgt.append(y[t])
        if len(rows) < 30:
            self._coef = None
            return
        self._coef, *_ = np.linalg.lstsq(np.array(rows), np.array(tgt), rcond=None)

    def predict(self, y_hist, x_now=None):
        y = np.asarray(y_hist, dtype=np.float64)
        y = y[~np.isnan(y)]
        if self._coef is None or len(y) < max(self.n_lags, self.m):
            return float(y[-1]) if len(y) else 0.0
        row = np.array(self._row(y, len(y)))
        return float(row @ self._coef)


class Ar1(Forecaster):
    """OLS AR(1): y[t] ~ c + phi * y[t-1] (the T6 strong baseline)."""

    name = "ar1"

    def __init__(self, refit_every: int = 1):
        self.refit_every = refit_every
        self._c = 0.0
        self._phi = 0.0

    def fit(self, y_train, X_train=None):
        y = np.asarray(y_train, dtype=np.float64)
        y = y[~np.isnan(y)]
        if len(y) < 30:
            return
        A = np.column_stack([np.ones(len(y) - 1), y[:-1]])
        coef, *_ = np.linalg.lstsq(A, y[1:], rcond=None)
        self._c, self._phi = float(coef[0]), float(coef[1])

    def predict(self, y_hist, x_now=None):
        y = np.asarray(y_hist, dtype=np.float64)
        y = y[~np.isnan(y)]
        if not len(y):
            return 0.0
        return self._c + self._phi * float(y[-1])


class Dar1(Forecaster):
    """Double-AR(1) (Ling 2004): y_t = phi*y_{t-1} + eta*sqrt(w + a*y_{t-1}^2).

    MLE via L-BFGS on the train slice; the point forecast is the conditional
    mean phi * y_last (the variance law improves phi estimation under the
    heteroskedasticity funding series exhibit — RESEARCH.md T6 prior).
    """

    name = "dar1"

    def __init__(self, refit_every: int = 5):
        self.refit_every = refit_every
        self._phi = 0.0

    def fit(self, y_train, X_train=None):
        from scipy.optimize import minimize

        y = np.asarray(y_train, dtype=np.float64)
        y = y[~np.isnan(y)]
        if len(y) < 100:
            return
        ylag, ycur = y[:-1], y[1:]
        scale2 = float(np.var(y)) or 1e-12

        def nll(params):
            phi, log_w, log_a = params
            w, a = np.exp(log_w), np.exp(log_a)
            v = w + a * ylag**2
            resid2 = (ycur - phi * ylag) ** 2
            return float(np.sum(0.5 * (np.log(v) + resid2 / v)))

        res = minimize(nll, x0=np.array([0.5, np.log(scale2), np.log(0.1)]),
                       method="L-BFGS-B",
                       bounds=[(-0.999, 0.999), (-60.0, 10.0), (-20.0, 5.0)])
        if res.success or np.isfinite(res.fun):
            self._phi = float(res.x[0])

    def predict(self, y_hist, x_now=None):
        y = np.asarray(y_hist, dtype=np.float64)
        y = y[~np.isnan(y)]
        if not len(y):
            return 0.0
        return self._phi * float(y[-1])


class GarchForecaster(Forecaster):
    """GARCH-family variance forecast conditioned on a return exog column.

    Fits by MLE on the purged train slice (percent returns, zero mean,
    normal dist); predict() rebuilds the model on the realized return
    history with the FIXED fitted params (arch .fix — filter, no
    re-estimation) and forecasts the next `horizon` steps' variance sum,
    rescaled back from percent^2. wants_x_hist: the return column is
    period-labeled (realized at t+h), so only the realized prefix is used.
    """

    wants_x_hist = True

    _SPECS = {
        "garch11": {"vol": "GARCH", "p": 1, "o": 0, "q": 1},
        "egarch11": {"vol": "EGARCH", "p": 1, "o": 0, "q": 1},
        "gjr11": {"vol": "GARCH", "p": 1, "o": 1, "q": 1},
    }

    def __init__(self, kind: str = "garch11", ret_col: int = 0,
                 horizon: int = 1, refit_every: int = 5,
                 window_cap: "int | None" = None):
        if kind not in self._SPECS:
            raise ValueError(kind)
        self.kind = kind
        self.name = kind
        self.ret_col = int(ret_col)
        self.horizon = int(horizon)
        self.refit_every = refit_every
        self.window_cap = window_cap
        self._params = None

    def _model(self, rets_pct: np.ndarray):
        from arch import arch_model

        spec = self._SPECS[self.kind]
        return arch_model(rets_pct, mean="Zero", dist="normal", **spec)

    def fit(self, y_train, X_train=None):
        if X_train is None:
            self._params = None
            return
        rets = np.asarray(X_train[:, self.ret_col], dtype=np.float64)
        rets = rets[~np.isnan(rets)] * 100.0
        if self.window_cap:
            rets = rets[-self.window_cap :]
        if len(rets) < 100:
            self._params = None
            return
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                res = self._model(rets).fit(disp="off", show_warning=False)
                self._params = res.params
            except Exception:
                self._params = None

    def predict(self, y_hist, x_now=None, x_hist=None):
        if self._params is None or x_hist is None:
            y = np.asarray(y_hist, dtype=np.float64)
            y = y[~np.isnan(y)]
            return float(np.mean(y)) if len(y) else 0.0
        rets = np.asarray(x_hist[:, self.ret_col], dtype=np.float64)
        rets = rets[~np.isnan(rets)] * 100.0
        if self.window_cap:
            rets = rets[-self.window_cap :]
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                fixed = self._model(rets).fix(self._params)
                fc = fixed.forecast(horizon=self.horizon, reindex=False)
                var_pct = float(fc.variance.values[-1, : self.horizon].sum())
                return var_pct / 100.0**2
            except Exception:
                y = np.asarray(y_hist, dtype=np.float64)
                y = y[~np.isnan(y)]
                return float(np.mean(y)) if len(y) else 0.0


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
