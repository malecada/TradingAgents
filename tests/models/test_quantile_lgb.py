"""Tests for lgb_model.walk_forward_pooled(quantiles=...) — E3 quantile-LGB confidence."""
import numpy as np
import pandas as pd
import pytest


def _toy_pooled(n_dates: int = 60, coins=("BTC", "ETH"), seed: int = 0) -> pd.DataFrame:
    """Small pooled dataset: 2 coins x n_dates, random-walk price + noise features.

    Target `prices_h7` is the coin's own price 7 bars ahead (with per-coin
    grouping preserved so shift() doesn't leak across coins).
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n_dates, freq="D")
    rows = []
    price = {c: 100.0 for c in coins}
    for d in dates:
        for c in coins:
            price[c] *= 1 + rng.normal(0, 0.02)
            rows.append({
                "date": d,
                "coin_id": c,
                "feature_a": rng.normal(),
                "feature_b": rng.normal(),
                "prices": price[c],
            })
    df = pd.DataFrame(rows).sort_values(["coin_id", "date"]).reset_index(drop=True)
    df["prices_h7"] = df.groupby("coin_id")["prices"].shift(-7)
    return df


def test_quantiles_none_is_byte_identical_columns():
    """Default (quantiles=None) must keep the exact pre-E3 column contract."""
    from tradingagents.models.lgb_model import walk_forward_pooled

    pooled = _toy_pooled()
    pred_df, metrics = walk_forward_pooled(pooled, horizon=7, min_train_window=40)

    assert not pred_df.empty
    assert list(pred_df.columns) == ["date", "coin_id", "prediction", "actual", "ref_price"]
    assert "q10" not in pred_df.columns
    assert "q90" not in pred_df.columns
    for key in ("r2", "mae", "rmse", "mape", "directional_accuracy"):
        assert key in metrics


def test_quantiles_none_matches_direct_build_lgb_call():
    """_build_lgb() with no args must be unaffected by the new optional kwargs."""
    from tradingagents.models.lgb_model import _build_lgb

    model = _build_lgb()
    params = model.get_params()
    assert params["objective"] is None or params["objective"] == "regression"
    assert "alpha" not in params or params["alpha"] is None


def test_quantile_columns_present_and_ordered_q10_q90():
    from tradingagents.models.lgb_model import walk_forward_pooled

    pooled = _toy_pooled()
    pred_df, metrics = walk_forward_pooled(
        pooled, horizon=7, min_train_window=40, quantiles=(0.1, 0.5, 0.9),
    )
    assert not pred_df.empty
    assert "q10" in pred_df.columns
    assert "q90" in pred_df.columns
    assert "prediction" in pred_df.columns  # q50
    assert not pred_df["q10"].isna().any()
    assert not pred_df["q90"].isna().any()


def test_quantile_monotonicity_holds_on_at_least_95pct_of_rows():
    """q10 <= q50 <= q90 should hold for the large majority of rows; independent
    per-alpha models can occasionally cross on noisy toy data, hence the 95% bar
    (not 100%) mirroring the task brief's tolerance."""
    from tradingagents.models.lgb_model import walk_forward_pooled

    pooled = _toy_pooled(n_dates=80, seed=7)
    pred_df, metrics = walk_forward_pooled(
        pooled, horizon=7, min_train_window=40, quantiles=(0.1, 0.5, 0.9),
    )
    assert len(pred_df) > 0

    lo_ok = pred_df["q10"] <= pred_df["prediction"] + 1e-9
    hi_ok = pred_df["prediction"] <= pred_df["q90"] + 1e-9
    monotone_rate = (lo_ok & hi_ok).mean()
    assert monotone_rate >= 0.95, f"monotonicity rate {monotone_rate:.2%} < 95%"


def test_quantiles_must_include_0_5():
    from tradingagents.models.lgb_model import walk_forward_pooled

    pooled = _toy_pooled()
    with pytest.raises(ValueError, match="0.5"):
        walk_forward_pooled(
            pooled, horizon=7, min_train_window=40, quantiles=(0.1, 0.9),
        )


def test_model_run_pooled_passes_through_quantiles():
    from tradingagents.models.lgb_model import model_run_pooled

    pooled = _toy_pooled()
    pred_df, metrics = model_run_pooled(
        pooled, horizon=7, min_train_window=40, quantiles=(0.1, 0.5, 0.9),
    )
    assert "q10" in pred_df.columns
    assert "q90" in pred_df.columns


def test_model_run_pooled_default_unaffected():
    from tradingagents.models.lgb_model import model_run_pooled

    pooled = _toy_pooled()
    pred_df, metrics = model_run_pooled(pooled, horizon=7, min_train_window=40)
    assert list(pred_df.columns) == ["date", "coin_id", "prediction", "actual", "ref_price"]
