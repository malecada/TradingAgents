"""Tests for `target_mode="logret"` — return-space LGB target (Task E1).

Adapted from the Task E1 brief's test sketch. The brief's sketch calls
`data_transform(df, horizons=[7], target_mode=...)`, but the real signature
requires `first_day_future` positionally, so these tests thread it through
the same way `scripts/evaluate_models_multi.py::build_pooled_transformed`
and `tests/models/test_data_transform_target_nan.py` do:
`first_day_future = df.index.max() + pd.Timedelta(days=1)`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tradingagents.models.model_utils import data_transform


def _toy() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=60, freq="D")
    return pd.DataFrame({"prices": np.linspace(100, 200, 60)}, index=idx)


def test_logret_target_values():
    """prices_h7 in logret mode == log(P_{t+7}/P_t), computed pre-shift."""
    df = _toy()
    first_day_future = df.index.max() + pd.Timedelta(days=1)
    _, out = data_transform(
        df, first_day_future=first_day_future,
        include_future_row=False, horizons=[7], target_mode="logret",
    )

    p = df["prices"]
    raw_logret = np.log(p.shift(-7) / p)

    # data_transform applies a global t-1 feature shift AFTER computing the
    # target, so out's row at date D holds the target computed from date
    # D-1's row, not date D's. Build the expectation the same way (shift by
    # 1) instead of reindexing the un-shifted series directly onto out.index.
    expected = raw_logret.shift(1)
    expected.index = pd.to_datetime(expected.index, utc=True)
    aligned = expected.reindex(out.index)

    assert np.allclose(
        out["prices_h7"].dropna().values,
        aligned.dropna().values,
        atol=1e-9,
    )
    assert out.attrs.get("target_mode") == "logret"


def test_level_mode_unchanged_default():
    """target_mode defaults to "level"; passing it explicitly must be a no-op."""
    df = _toy()
    first_day_future = df.index.max() + pd.Timedelta(days=1)
    kwargs = dict(first_day_future=first_day_future, include_future_row=True, horizons=[7])

    a_lags, a_final = data_transform(df, **kwargs)
    b_lags, b_final = data_transform(df, target_mode="level", **kwargs)

    pd.testing.assert_frame_equal(a_lags, b_lags)
    pd.testing.assert_frame_equal(a_final, b_final)


def test_last_h_rows_have_nan_target():
    """Regression: the ffill-mask bug (see test_data_transform_target_nan.py)
    must not resurrect for logret targets — the last h rows must stay NaN."""
    df = _toy()
    first_day_future = df.index.max() + pd.Timedelta(days=1)
    _, out = data_transform(
        df, first_day_future=first_day_future,
        include_future_row=True, horizons=[7], target_mode="logret",
    )
    assert out["prices_h7"].tail(7).isna().all()


def test_invalid_target_mode_raises():
    df = _toy()
    first_day_future = df.index.max() + pd.Timedelta(days=1)
    with pytest.raises(ValueError):
        data_transform(
            df, first_day_future=first_day_future,
            include_future_row=False, horizons=[7], target_mode="bogus",
        )


# ── Step 5: lgb_model inverse-transform (logret -> level) ───────────────


class _FakeBooster:
    """Deterministic stand-in for a fitted LGBMRegressor."""

    def __init__(self, raw_pred: float):
        self.raw_pred = raw_pred

    def fit(self, X, y):
        return self

    def predict(self, X):
        return np.full(len(X), self.raw_pred)


def test_predict_pooled_inverse_transforms_logret_bundle():
    """A fitted-mode bundle with target_mode="logret" must return a
    price-level prediction: ref_price * exp(raw_pred)."""
    from tradingagents.models.lgb_model import predict_pooled

    raw_pred = 0.05  # 5% predicted log-return
    ref_price = 100.0
    bundle = {
        "booster": _FakeBooster(raw_pred),
        "feature_names": ["feature_a", "prices"],
        "scaler": None,
        "coin_to_int": {},
        "target_mode": "logret",
    }
    feature_row = pd.DataFrame([{"feature_a": 1.0, "prices": ref_price}])

    pred = predict_pooled(bundle, feature_row)

    assert pred == pytest.approx(ref_price * np.exp(raw_pred))


def test_predict_pooled_level_mode_unchanged():
    """target_mode="level" (or absent from the bundle) must return the raw
    booster output untouched — no inverse-transform."""
    from tradingagents.models.lgb_model import predict_pooled

    raw_pred = 123.4
    bundle = {
        "booster": _FakeBooster(raw_pred),
        "feature_names": ["feature_a"],
        "scaler": None,
        "coin_to_int": {},
    }
    feature_row = pd.DataFrame([{"feature_a": 1.0}])

    pred = predict_pooled(bundle, feature_row)

    assert pred == pytest.approx(raw_pred)


def test_walk_forward_pooled_inverse_transforms_logret_to_level(monkeypatch):
    """CSV-level predictions/actuals must be price level even though the
    fitted model operates in log-return space, and DirAcc must be computed
    consistently in level space (unchanged _dir_acc contract)."""
    from tradingagents.models import lgb_model

    raw_pred = 0.03  # constant 3% predicted log-return
    monkeypatch.setattr(lgb_model, "_build_lgb", lambda: _FakeBooster(raw_pred))

    dates = pd.date_range("2024-01-01", periods=8, freq="D")
    ref_prices = np.array([100.0, 101, 102, 103, 104, 105, 106, 107])
    future_prices = ref_prices + 5.0  # arbitrary "true" future level
    logret_target = np.log(future_prices / ref_prices)

    pooled_df = pd.DataFrame(
        {
            "prices": ref_prices,
            "feature_a": np.arange(8, dtype=float),
            "prices_h1": logret_target,
            "coin_id": "BTC",
        },
        index=dates,
    )

    pred_df, metrics = lgb_model.walk_forward_pooled(
        pooled_df, horizon=1, min_train_window=5, target_mode="logret",
    )

    assert not pred_df.empty
    for _, row in pred_df.iterrows():
        assert row["prediction"] == pytest.approx(row["ref_price"] * np.exp(raw_pred))
        # logret_target was built exactly from future_prices/ref_prices, so
        # the inverse-transformed "actual" must reconstruct the true level.
        assert row["actual"] == pytest.approx(row["ref_price"] + 5.0, rel=1e-6)

    # DirAcc must be computed on the level-space pred_df via the same
    # _dir_acc used for level mode — no separate logret code path.
    expected_dir_acc = lgb_model._dir_acc(pred_df, pooled_df, horizon=1)
    assert metrics["directional_accuracy"] == pytest.approx(expected_dir_acc)
