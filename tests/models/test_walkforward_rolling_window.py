"""walk_forward_pooled train_window_days: rolling window bounds the training set.

Live retraining (execution/live/retrain.py) fits on a rolling 730-day lookback,
while the backtest walk-forward trains on an expanding window. The
train_window_days parameter lets the backtest reproduce the live contract.
"""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from tradingagents.models import lgb_model


class _RecorderModel:
    """Stub LGB that records training-set sizes per fold."""

    train_sizes: list[int] = []

    def fit(self, X, y):
        _RecorderModel.train_sizes.append(len(X))
        return self

    def predict(self, X):
        return np.zeros(len(X))


def _pooled_df(n_days: int = 100, coins=("bitcoin", "ethereum")) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D", tz="UTC")
    rows = []
    for coin in coins:
        for i, d in enumerate(dates):
            rows.append(
                {
                    "date": d,
                    "coin_id": coin,
                    "prices": 100.0 + i,
                    "feat_a": float(i),
                    "prices_h7": 100.0 + i + 7,
                }
            )
    return pd.DataFrame(rows).set_index("date")


@pytest.fixture(autouse=True)
def _reset_recorder():
    _RecorderModel.train_sizes = []
    yield
    _RecorderModel.train_sizes = []


def test_rolling_window_caps_training_set():
    df = _pooled_df(n_days=100)
    with patch.object(lgb_model, "_build_lgb", lambda: _RecorderModel()):
        lgb_model.walk_forward_pooled(
            df, horizon=7, min_train_window=50, train_window_days=30
        )
    sizes = _RecorderModel.train_sizes
    assert sizes, "no folds ran"
    # 30-day window x 2 coins = at most 60 training rows per fold, every fold
    assert max(sizes) <= 60
    # window should be full (not degenerate) once past warmup
    assert min(sizes) >= 40


def test_purge_days_drops_label_overlap():
    df = _pooled_df(n_days=100)
    with patch.object(lgb_model, "_build_lgb", lambda: _RecorderModel()):
        preds, _ = lgb_model.walk_forward_pooled(
            df, horizon=7, min_train_window=50, purge_days=7
        )
    # rebuild the train masks the function must have used: for each test date,
    # the newest allowed training date is test_date - 7 days
    dates = sorted(df.index.unique())
    per_fold_rows = [
        2 * sum(1 for d in dates if d <= t - pd.Timedelta(days=7))
        for t in sorted(preds["date"].unique())
    ]
    assert _RecorderModel.train_sizes == per_fold_rows


def test_default_stays_expanding():
    df = _pooled_df(n_days=100)
    with patch.object(lgb_model, "_build_lgb", lambda: _RecorderModel()):
        lgb_model.walk_forward_pooled(df, horizon=7, min_train_window=50)
    sizes = _RecorderModel.train_sizes
    # expanding: strictly growing training set, final fold sees ~99 dates x 2
    assert sizes[-1] > sizes[0]
    assert sizes[-1] >= 190
