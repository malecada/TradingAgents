"""Tier-2 ML forecasters (registered small feature sets).

Both consume the runner's exog matrix: fit(y_train, X_train) on the purged
train slice, predict(y_hist, x_now) from the origin's pre-lagged feature row.
Deterministic by construction (fixed seeds / closed-form fits); leak-tight via
the runner protocol (truncation-equivalence pinned in tests).
"""

from __future__ import annotations

import numpy as np

from tradingagents.predlab.baselines import Forecaster


class ElasticNetForecaster(Forecaster):
    """Standardized elastic net; alpha picked by SSE on the train tail (20%)."""

    name = "enet"

    def __init__(self, alphas=(1e-5, 1e-4, 1e-3, 1e-2), l1_ratio: float = 0.5,
                 refit_every: int = 24, n_features: "int | None" = None):
        self.alphas = tuple(alphas)
        self.l1_ratio = float(l1_ratio)
        self.refit_every = refit_every
        # use only the first n_features exog columns (guards against
        # period-labeled helper columns appended for other models)
        self.n_features = n_features
        self._model = None
        self._mu = None
        self._sd = None

    def _slice(self, X):
        return X if self.n_features is None else X[..., : self.n_features]

    def fit(self, y_train, X_train=None):
        from sklearn.linear_model import ElasticNet

        self._model = None
        if X_train is None:
            return
        y = np.asarray(y_train, dtype=np.float64)
        X = self._slice(np.asarray(X_train, dtype=np.float64))
        ok = ~(np.isnan(y) | np.isnan(X).any(axis=1))
        y, X = y[ok], X[ok]
        if len(y) < 60:
            return
        self._mu = X.mean(axis=0)
        self._sd = X.std(axis=0, ddof=1)
        self._sd[self._sd == 0] = 1.0
        Xs = (X - self._mu) / self._sd
        cut = max(int(len(y) * 0.8), 30)
        best = (np.inf, None)
        for a in self.alphas:
            m = ElasticNet(alpha=a, l1_ratio=self.l1_ratio, max_iter=5000)
            m.fit(Xs[:cut], y[:cut])
            sse = float(np.sum((y[cut:] - m.predict(Xs[cut:])) ** 2)) if cut < len(y) else 0.0
            if sse < best[0]:
                best = (sse, a)
        m = ElasticNet(alpha=best[1], l1_ratio=self.l1_ratio, max_iter=5000)
        m.fit(Xs, y)
        self._model = m

    def predict(self, y_hist, x_now=None):
        if self._model is None or x_now is None:
            return 0.0
        x = self._slice(np.asarray(x_now, dtype=np.float64))
        if np.isnan(x).any():
            return 0.0
        xs = (x - self._mu) / self._sd
        return float(self._model.predict(xs.reshape(1, -1))[0])


class ProbClip(Forecaster):
    """Adapter: regression forecaster on a 0/1 target -> probability forecast.

    Registered T2 convention (predlab_p2_ml protocol.note_t2): fit the inner
    regressor on the 0/1 up-indicator, clip the output to [0.02, 0.98].
    """

    def __init__(self, inner, lo: float = 0.02, hi: float = 0.98):
        self.inner = inner
        self.name = inner.name
        self.lo, self.hi = float(lo), float(hi)
        if hasattr(inner, "refit_every"):
            self.refit_every = inner.refit_every

    def fit(self, y_train, X_train=None):
        import numpy as _np

        self.inner.fit((_np.asarray(y_train, dtype=float) > 0).astype(float), X_train)

    def predict(self, y_hist, x_now=None):
        import numpy as _np

        p = self.inner.predict((_np.asarray(y_hist, dtype=float) > 0).astype(float), x_now)
        return float(min(max(p, self.lo), self.hi))


class LGBForecaster(Forecaster):
    """LightGBM regressor, registered fixed params, seed 0."""

    name = "lgb"

    _PARAMS = dict(
        n_estimators=300, learning_rate=0.05, num_leaves=31,
        min_child_samples=50, subsample=0.9, subsample_freq=1,
        colsample_bytree=0.9, random_state=0, deterministic=True,
        force_row_wise=True, verbosity=-1, n_jobs=4,
    )

    def __init__(self, refit_every: int = 24, params: "dict | None" = None,
                 n_features: "int | None" = None):
        self.refit_every = refit_every
        self.params = {**self._PARAMS, **(params or {})}
        self.n_features = n_features
        self._model = None

    def _slice(self, X):
        return X if self.n_features is None else X[..., : self.n_features]

    def fit(self, y_train, X_train=None):
        import lightgbm as lgb

        self._model = None
        if X_train is None:
            return
        y = np.asarray(y_train, dtype=np.float64)
        X = self._slice(np.asarray(X_train, dtype=np.float64))
        ok = ~np.isnan(y)
        y, X = y[ok], X[ok]
        if len(y) < 200:
            return
        self._model = lgb.LGBMRegressor(**self.params).fit(X, y)

    def predict(self, y_hist, x_now=None):
        if self._model is None or x_now is None:
            return 0.0
        x = self._slice(np.asarray(x_now, dtype=np.float64)).reshape(1, -1)
        return float(self._model.predict(x)[0])
