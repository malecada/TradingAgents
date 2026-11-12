"""Fitted forecasters of the reader configuration (Charter 2 §3.4). No model call.

Features are ranked within the week over the universe members (percentile rank minus 0.5, missing -> 0) and
the target is the within-week percentile rank of the 7-day forward return minus 0.5. Ridge uses the penalty
and the burn-in of the existing quant forecast and is refitted every Friday on the earlier Fridays whose
outcome is realised before the decision. The boosted tree is a descriptive column with fixed parameters.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.dossier.quant_forecast import BURN_IN_WEEKS, FEATURES as QUANT_FEATURES, HORIZON_DAYS, RIDGE_ALPHA

GBM_PARAMS = {"objective": "regression", "learning_rate": 0.03, "num_leaves": 4, "max_depth": 2, "min_data_in_leaf": 100,
              "feature_fraction": 0.8, "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 10.0, "seed": 20261112,
              "deterministic": True, "force_row_wise": True, "num_threads": 1, "verbose": -1}
GBM_ROUNDS = 200
CROSS_FIT_BLOCKS, CROSS_FIT_EMBARGO_WEEKS = 6, 1
HORIZON = pd.Timedelta(days=HORIZON_DAYS)


def xs_rank(panel: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Within-week percentile rank minus 0.5 (average ties); a missing value sits at the neutral rank 0."""
    return (panel.groupby("date")[cols].rank(pct=True) - 0.5).fillna(0.0)


def target(panel: pd.DataFrame, ret_col: str = "fwd_ret") -> pd.Series:
    return panel.groupby("date")[ret_col].rank(pct=True) - 0.5


def fit_ridge(X: np.ndarray, y: np.ndarray, alpha: float = RIDGE_ALPHA):
    beta = np.linalg.solve(X.T @ X + alpha * np.eye(X.shape[1]), X.T @ y)
    return (lambda Z: Z @ beta), beta


def fit_gbm(X: np.ndarray, y: np.ndarray):
    import lightgbm as lgb
    booster = lgb.train(dict(GBM_PARAMS), lgb.Dataset(X, label=y), num_boost_round=GBM_ROUNDS)
    return booster.predict, booster.feature_importance(importance_type="gain")


def _arrays(panel: pd.DataFrame, cols: list[str]):
    """(ranked features, target, date of every row as UTC nanoseconds)."""
    dates = pd.to_datetime(panel["date"], utc=True).dt.as_unit("ns").astype("int64").to_numpy()
    return xs_rank(panel, cols).to_numpy(dtype=float), target(panel).to_numpy(dtype=float), dates


def walk_forward(panel: pd.DataFrame, cols: list[str], fit=fit_ridge, burn_in: int = BURN_IN_WEEKS) -> tuple[pd.Series, pd.DataFrame]:
    """(score per panel row, fit information per test week). A week is forecast from the weeks whose 7-day
    outcome is realised by its Friday; the first ``burn_in`` weeks are training only (score missing)."""
    X, y, dates = _arrays(panel, cols)
    weeks = np.unique(dates)
    score = np.full(len(panel), np.nan)
    info = {}
    for d in weeks:
        past = weeks[weeks + HORIZON.value <= d]
        if len(past) < burn_in:
            continue
        train = np.isin(dates, past) & np.isfinite(y)
        predict, detail = fit(X[train], y[train])
        score[dates == d] = predict(X[dates == d])
        info[pd.Timestamp(int(d), tz="UTC")] = detail
    frame = pd.DataFrame.from_dict(info, orient="index", columns=cols).sort_index() if info else pd.DataFrame(columns=cols)
    return pd.Series(score, index=panel.index), frame


def cross_fit(panel: pd.DataFrame, cols: list[str], fit=fit_ridge, n_blocks: int = CROSS_FIT_BLOCKS,
              embargo_weeks: int = CROSS_FIT_EMBARGO_WEEKS) -> pd.Series:
    """Blocked cross-fit over every week: each block of consecutive weeks is forecast from the weeks outside
    it, leaving ``embargo_weeks`` out on both sides. Uses later data, so it is descriptive only."""
    X, y, dates = _arrays(panel, cols)
    weeks = np.unique(dates)
    score = np.full(len(panel), np.nan)
    for block in np.array_split(np.arange(len(weeks)), n_blocks):
        if not len(block):
            continue
        lo, hi = block[0] - embargo_weeks, block[-1] + embargo_weeks
        outside = weeks[(np.arange(len(weeks)) < lo) | (np.arange(len(weeks)) > hi)]
        train = np.isin(dates, outside) & np.isfinite(y)
        if not train.any():
            continue
        predict, _ = fit(X[train], y[train])
        test = np.isin(dates, weeks[block])
        score[test] = predict(X[test])
    return pd.Series(score, index=panel.index)


__all__ = ["QUANT_FEATURES", "GBM_PARAMS", "GBM_ROUNDS", "xs_rank", "target", "fit_ridge", "fit_gbm", "walk_forward", "cross_fit"]
