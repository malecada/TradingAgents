"""Load latest checkpoint, build PIT features asof, predict per coin per horizon.

Inference companion to `retrain.py`. Loads the per-horizon bundle dict that
retrain wrote to disk, materializes the same PIT-aware feature frame the
training pipeline used (via `build_pooled_dataset` + `_transform_pooled`),
selects the latest row per coin, and calls `predict_pooled` once per
(coin, horizon).

Output shape:
    {
        "BTC": {"ref_price": 60000.0, "pred_h7": 70000.0, "pred_h14": 72000.0},
        "ETH": {...},
        ...
    }

Design note — feature parity with retrain:
    `build_features_asof` lazily imports `_transform_pooled` from
    `retrain.py`. The lazy import avoids any cycle at module load time, and
    reusing the exact transform helper guarantees that live and backtest
    paths see identical feature schemas. The equivalence test in
    `tests/execution/live/test_predict_equivalence.py` is the contract
    guarding this property — adding a feature in retrain without exposing
    it through this transform will fail that test.
"""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import pandas as pd

from tradingagents.models.lgb_model import predict_pooled

logger = logging.getLogger(__name__)


def build_features_asof(
    coins: list[str],
    asof: str,
    lookback_days: int = 730,
    horizons: list[int] = (7, 14),
) -> pd.DataFrame:
    """Build a feature frame for the asof date — one row per coin.

    Reuses the same pipeline as retrain (`build_pooled_dataset` +
    `_transform_pooled`) so live and backtest produce identical features.
    The latest row per coin is selected — that row's features describe the
    state of the world at asof, and the model predicts the next-period
    target from them.

    Args:
        coins: CoinGecko coin IDs to fetch (e.g. ["bitcoin", "ethereum"]).
        asof: Upper-bound trade date (YYYY-mm-dd).
        lookback_days: How many days of history to load per coin.
        horizons: Forecast horizons to materialize as `prices_h{h}` columns
            (forwarded to `_transform_pooled`).

    Returns:
        DataFrame with `coin_id`, `ref_price`, and all feature columns —
        one row per coin (the latest available date). Empty if no coin
        produced data.
    """
    from tradingagents.models.model_utils import build_pooled_dataset
    # Lazy import keeps `predict` independent of `retrain` at module load.
    # Both modules must use the same transform to preserve live↔backtest
    # feature equivalence; the equivalence test guards this.
    from tradingagents.execution.live.retrain import _transform_pooled

    pooled = build_pooled_dataset(
        coin_universe=list(coins),
        lookback_days=lookback_days,
        horizons=list(horizons),
        trade_date=asof,
        add_onchain_pit=True,
    )
    transformed = _transform_pooled(pooled, list(horizons))
    if transformed is None or len(transformed) == 0:
        return pd.DataFrame()

    # `_transform_pooled` returns a date-indexed frame; surface `date` as a
    # regular column so we can sort/groupby uniformly.
    if "date" not in transformed.columns:
        transformed = transformed.reset_index()
    latest = (
        transformed.sort_values("date")
        .groupby("coin_id", as_index=False)
        .tail(1)
    )
    return latest


def run_predict(
    checkpoint_path: Path,
    coins: list[str],
    horizons: list[int],
    asof: str,
) -> dict:
    """Load bundle dict, build PIT features asof, predict per coin per horizon.

    Args:
        checkpoint_path: Path to the pickle written by `retrain.run_retrain`
            (a dict keyed by horizon, each value a fit_pooled_full bundle).
        coins: Coin IDs to predict for. Coins lacking features at asof are
            silently skipped (warning logged).
        horizons: Forecast horizons in days. Each must have a bundle in the
            checkpoint or this raises.
        asof: Upper-bound trade date (YYYY-mm-dd).

    Returns:
        Dict keyed by coin id, each value a dict with `ref_price` plus
        `pred_h{h}` for every requested horizon.
    """
    bundles = joblib.load(checkpoint_path)
    if not isinstance(bundles, dict):
        raise ValueError(
            f"Checkpoint at {checkpoint_path} is not a dict-keyed-by-horizon"
        )
    for h in horizons:
        if h not in bundles:
            raise ValueError(
                f"No bundle for horizon {h} in {checkpoint_path}"
            )

    features = build_features_asof(coins, asof, horizons=horizons)
    out: dict = {}
    for coin in coins:
        if features.empty:
            logger.warning("No features for %s asof %s — skipping", coin, asof)
            continue
        row = features[features["coin_id"] == coin]
        if row.empty:
            logger.warning("No features for %s asof %s — skipping", coin, asof)
            continue
        result: dict = {"ref_price": float(row["ref_price"].iloc[0])}
        for h in horizons:
            bundle = bundles[h]
            pred = predict_pooled(bundle, row)
            result[f"pred_h{h}"] = float(pred)
        out[coin] = result
    return out
