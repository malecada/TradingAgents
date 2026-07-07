"""Tests for `train_end_offsets` — Experiment E2's training-window-staggered
prediction ensemble in `lgb_model.walk_forward_pooled`.

Covers:
  - Default (None) behavior is untouched (same code path, no pred_off* cols).
  - Offsets path: one model fit PER offset, each offset's training set
    excludes the newest `offset` days relative to offset=0's training set,
    and the emitted `prediction` is the MEAN across the offset models.
  - A single-offset ensemble ([0]) is numerically identical to the base
    (None) path — the ensemble machinery reduces to the original behavior
    when there's nothing to average.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def _toy_single_coin_frame(n_days: int = 30) -> pd.DataFrame:
    """One coin, daily dates, target column = day index (for exact
    exclusion-boundary checks — not meant to be a realistic price series).
    """
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
    day_idx = np.arange(n_days, dtype=float)
    df = pd.DataFrame({
        "date": dates,
        "coin_id": ["BTC"] * n_days,
        "feat": day_idx * 0.01,
        "prices": 100.0 + day_idx,
        "prices_h1": day_idx,
    })
    return df.set_index("date")


def _synthetic_two_coin_frame(n_days: int = 35, seed: int = 0) -> pd.DataFrame:
    """Two coins with a real linear-ish target, for exercising the actual
    LightGBM fit path (used for the None-vs-offset[0] identity check).
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
    rows = []
    for coin in ("bitcoin", "ethereum"):
        f1 = rng.normal(size=n_days)
        f2 = rng.normal(size=n_days)
        price = 100 + np.cumsum(rng.normal(0, 0.1, size=n_days))
        target = price + 5 * f1 - 3 * f2 + rng.normal(0, 0.5, size=n_days)
        for i in range(n_days):
            rows.append({
                "date": dates[i], "coin_id": coin,
                "feat_a": f1[i], "feat_b": f2[i],
                "prices": price[i], "prices_h1": target[i],
            })
    return pd.DataFrame(rows).set_index("date")


def _install_fake_lgb_spy(monkeypatch, calls: list):
    """Replace `_build_lgb` with a spy that records each fit() call's
    training X/y (in `_build_lgb()` call order) and returns a deterministic,
    call-index-dependent prediction so the ensemble mean is exactly known.
    """
    from tradingagents.models import lgb_model

    def fake_build_lgb():
        idx = len(calls)
        record = {"idx": idx}
        calls.append(record)

        class _FakeModel:
            def fit(self, X, y):
                record["X"] = X.copy()
                record["y"] = y.copy()

            def predict(self, X):
                return np.full(len(X), float(idx + 1))

        return _FakeModel()

    monkeypatch.setattr(lgb_model, "_build_lgb", fake_build_lgb)


def test_offsets_train_separate_models_and_emit_mean(monkeypatch):
    from tradingagents.models import lgb_model

    df = _toy_single_coin_frame(n_days=30)
    calls: list = []
    _install_fake_lgb_spy(monkeypatch, calls)

    pred_df, _metrics = lgb_model.walk_forward_pooled(
        df, horizon=1, min_train_window=29, train_end_offsets=[0, 5],
    )

    # Exactly one date is evaluated (min_train_window = n_days - 1), one coin.
    assert len(pred_df) == 1

    # Two models were fit — one per offset.
    assert len(calls) == 2

    # offset=0: trains on all rows strictly before cur_date -> day_idx 0..28.
    assert len(calls[0]["y"]) == 29
    assert calls[0]["y"].max() == pytest.approx(28.0)

    # offset=5: trains on rows before (cur_date - 5 days) -> day_idx 0..23,
    # i.e. it excludes the 5 newest days (24..28) that offset=0 included.
    assert len(calls[1]["y"]) == 24
    assert calls[1]["y"].max() == pytest.approx(23.0)

    row = pred_df.iloc[0]
    assert "pred_off0" in pred_df.columns
    assert "pred_off5" in pred_df.columns
    assert row["pred_off0"] == pytest.approx(1.0)
    assert row["pred_off5"] == pytest.approx(2.0)
    # prediction = mean of the two offset models' outputs
    assert row["prediction"] == pytest.approx(1.5)


def test_offsets_skip_date_when_any_offset_train_set_empty(monkeypatch):
    """If the largest offset's training set is empty for the first eligible
    walk-forward date, that date is skipped entirely (no partial rows)."""
    from tradingagents.models import lgb_model

    df = _toy_single_coin_frame(n_days=30)
    calls: list = []
    _install_fake_lgb_spy(monkeypatch, calls)

    # offset=40 always yields an empty training set on a 30-day frame.
    pred_df, _metrics = lgb_model.walk_forward_pooled(
        df, horizon=1, min_train_window=29, train_end_offsets=[0, 40],
    )

    assert pred_df.empty
    # The offset=0 model may or may not have been constructed depending on
    # iteration order, but no row should ever be emitted with a partial mean.
    assert "prediction" not in pred_df.columns or pred_df["prediction"].empty


def test_none_default_has_no_pred_off_columns():
    from tradingagents.models import lgb_model

    df = _synthetic_two_coin_frame(n_days=35)
    pred_none, _metrics = lgb_model.walk_forward_pooled(
        df, horizon=1, min_train_window=33,
    )

    assert set(pred_none.columns) == {"date", "coin_id", "prediction", "actual", "ref_price"}
    assert not pred_none.empty


def test_none_matches_explicit_none_byte_identical():
    """Calling without the new kwarg vs. passing train_end_offsets=None
    explicitly must be indistinguishable (backward-compatible default)."""
    from tradingagents.models import lgb_model

    df = _synthetic_two_coin_frame(n_days=35)
    pred_default, metrics_default = lgb_model.walk_forward_pooled(
        df.copy(), horizon=1, min_train_window=33,
    )
    pred_explicit, metrics_explicit = lgb_model.walk_forward_pooled(
        df.copy(), horizon=1, min_train_window=33, train_end_offsets=None,
    )

    pd.testing.assert_frame_equal(pred_default, pred_explicit)
    assert metrics_default == pytest.approx(metrics_explicit)


def test_single_offset_zero_reduces_to_base_case():
    """train_end_offsets=[0] fits one model per date (same training rule as
    the None path) — the ensemble "mean of one" must equal the base
    single-model prediction, and pred_off0 must equal that same value."""
    from tradingagents.models import lgb_model

    df = _synthetic_two_coin_frame(n_days=35)
    pred_none, _ = lgb_model.walk_forward_pooled(
        df.copy(), horizon=1, min_train_window=33,
    )
    pred_off0, _ = lgb_model.walk_forward_pooled(
        df.copy(), horizon=1, min_train_window=33, train_end_offsets=[0],
    )

    assert set(pred_off0.columns) == {
        "date", "coin_id", "prediction", "actual", "ref_price", "pred_off0",
    }

    merged = pred_none.merge(
        pred_off0, on=["date", "coin_id"], suffixes=("_none", "_off0"),
    )
    assert len(merged) == len(pred_none) == len(pred_off0)
    np.testing.assert_allclose(
        merged["prediction_none"].values, merged["prediction_off0"].values,
        rtol=0, atol=1e-6,
    )
    np.testing.assert_allclose(
        merged["prediction_off0"].values, merged["pred_off0"].values,
        rtol=0, atol=1e-9,
    )


def test_model_run_pooled_forwards_train_end_offsets(monkeypatch):
    from tradingagents.models import lgb_model

    df = _toy_single_coin_frame(n_days=30)
    calls: list = []
    _install_fake_lgb_spy(monkeypatch, calls)

    pred_df, _metrics = lgb_model.model_run_pooled(
        df, 1, 29, train_end_offsets=[0, 5],
    )

    assert len(calls) == 2
    assert pred_df.iloc[0]["prediction"] == pytest.approx(1.5)


def test_offsets_dedup_and_sort_duplicates(monkeypatch):
    """Duplicate offsets [0, 0, 5] are silently deduplicated to [0, 5];
    the resulting predictions match a run with [0, 5] directly."""
    from tradingagents.models import lgb_model

    df = _synthetic_two_coin_frame(n_days=35)

    # Run with duplicates: [0, 0, 5]
    pred_dup, metrics_dup = lgb_model.walk_forward_pooled(
        df.copy(), horizon=1, min_train_window=33, train_end_offsets=[0, 0, 5],
    )

    # Run with dedup: [0, 5]
    pred_dedup, metrics_dedup = lgb_model.walk_forward_pooled(
        df.copy(), horizon=1, min_train_window=33, train_end_offsets=[0, 5],
    )

    # Both should produce identical results (same two unique offsets)
    pd.testing.assert_frame_equal(pred_dup, pred_dedup)
    assert metrics_dup == pytest.approx(metrics_dedup)


def test_offsets_raises_on_negative_value():
    """Negative offsets are invalid and raise ValueError."""
    from tradingagents.models import lgb_model

    df = _toy_single_coin_frame(n_days=30)

    with pytest.raises(ValueError, match="must be non-negative"):
        lgb_model.walk_forward_pooled(
            df, horizon=1, min_train_window=29, train_end_offsets=[0, -5],
        )
