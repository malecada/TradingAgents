"""Daily fit-once-on-full-history retrain of pooled LGB models.

Wraps `tradingagents.models.model_utils.build_pooled_dataset` +
`tradingagents.models.lgb_model.fit_pooled_full` so the live runner can
invoke them with the live module's vocabulary (`coins`, `asof`) and get back
a versioned, joblib-persistable checkpoint plus a metrics summary.

Architecture note — why not `model_run_pooled`?
   The upstream `model_run_pooled` is walk-forward EVAL: for each iteration
   it fits a per-iteration model and throws it away, returning predictions +
   metrics. That contract has no persistable booster usable by live
   inference. The live cycle needs a "fit once on the full history → save →
   .predict()" path, which is what `lgb_model.fit_pooled_full` provides.
   This module is the integration glue.

Per-horizon bundle layout on disk (joblib.dump of):
    {
        7:  {booster, feature_names, horizon, target_col, n_train_rows,
              scaler, coin_to_int},
        14: {... same shape ...},
    }

Tests patch `build_pooled_dataset`, `_transform_pooled`, and
`fit_pooled_full` on this module; the real upstream signatures are only
exercised in live cycles.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from tradingagents.models.lgb_model import fit_pooled_full
from tradingagents.models.model_utils import build_pooled_dataset, data_transform

logger = logging.getLogger(__name__)


@dataclass
class TrainArtifact:
    """Metadata for a freshly trained (or fallback) checkpoint."""

    model_path: Path
    train_window_start: str
    train_window_end: str
    train_rows: int
    train_dir_acc_h7: float
    train_dir_acc_h14: float
    sha256: str
    is_fallback: bool = False


def _transform_pooled(pooled_df: pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    """Apply `data_transform` per coin so .shift() respects coin boundaries.

    Mirrors the canonical wiring in `scripts/evaluate_models_multi.py`
    (`build_pooled_transformed`): split by coin, run the per-coin transform,
    re-tag with `coin_id`, concat, and set the `date` column as index.

    Args:
        pooled_df: Raw output of `build_pooled_dataset` (date-indexed,
            with a `coin_id` column).
        horizons: Forecast horizons to materialize as `prices_h{h}` columns.

    Returns:
        Date-indexed pooled DataFrame with one `coin_id` column and
        `prices_h{h}` target columns. Empty if no coin produced data.
    """
    if pooled_df is None or len(pooled_df) == 0 or "coin_id" not in pooled_df.columns:
        return pd.DataFrame()

    pieces: list[pd.DataFrame] = []
    for coin in pooled_df["coin_id"].unique():
        sub = pooled_df[pooled_df["coin_id"] == coin].drop(columns=["coin_id"])
        if sub.empty:
            continue
        first_future = sub.index.max() + pd.Timedelta(days=1)
        try:
            reframed, _ = data_transform(
                sub, first_future, include_future_row=False, horizons=horizons,
            )
        except Exception as e:
            logger.warning(f"data_transform failed for {coin}: {e}")
            continue
        reframed["coin_id"] = coin
        pieces.append(reframed)

    if not pieces:
        return pd.DataFrame()

    pooled = pd.concat(pieces, ignore_index=True)
    pooled["date"] = pd.to_datetime(pooled["date"])
    pooled = pooled.set_index("date").sort_index()
    return pooled


def _train_dir_acc(bundle: dict, transformed_df: pd.DataFrame) -> float:
    """In-sample directional accuracy on the full training set.

    Compares the sign of (predicted - prior_price) to (actual - prior_price)
    where prior_price is the row's `prices` value (the spot at the time the
    features were drawn). Returns 0.0 if the input lacks the required
    columns.
    """
    target_col = bundle["target_col"]
    if "prices" not in transformed_df.columns or target_col not in transformed_df.columns:
        return 0.0

    df = transformed_df.dropna(subset=[target_col]).copy()
    if df.empty:
        return 0.0

    feat_names = bundle["feature_names"]
    # Auto-fill coin_int from coin_id if needed.
    if (
        "coin_int" in feat_names
        and "coin_int" not in df.columns
        and "coin_id" in df.columns
        and bundle.get("coin_to_int")
    ):
        df["coin_int"] = df["coin_id"].map(bundle["coin_to_int"]).astype(int)

    missing = [c for c in feat_names if c not in df.columns]
    if missing:
        return 0.0

    X = df[feat_names].to_numpy(dtype=np.float32)
    scaler = bundle.get("scaler")
    if scaler is not None:
        X = scaler.transform(X)
    preds = bundle["booster"].predict(X)

    prior = df["prices"].to_numpy(dtype=float)
    actual = df[target_col].to_numpy(dtype=float)
    mask = prior > 0
    if not mask.any():
        return 0.0
    pred_dir = np.where(preds[mask] > prior[mask], 1, -1)
    actual_dir = np.where(actual[mask] > prior[mask], 1, -1)
    correct = int(np.sum(pred_dir == actual_dir))
    total = int(mask.sum())
    return correct / total if total > 0 else 0.0


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _train_window_start(df: pd.DataFrame) -> str:
    """Best-effort earliest date string from a pooled DataFrame."""
    if df is None or len(df) == 0:
        return ""
    if isinstance(df.index, pd.DatetimeIndex):
        try:
            return df.index.min().strftime("%Y-%m-%d")
        except Exception:
            return ""
    if "date" in df.columns:
        try:
            return pd.to_datetime(df["date"]).min().strftime("%Y-%m-%d")
        except Exception:
            return ""
    return ""


def run_retrain(
    coins: list[str],
    horizons: list[int],
    asof: str,
    checkpoint_dir: Path,
    lookback_days: int = 730,
    min_train_window: int = 365,
) -> TrainArtifact:
    """Build dataset, fit one LGB per horizon on full history, persist.

    Steps:
      1. `build_pooled_dataset` with PIT on-chain features.
      2. `_transform_pooled` to apply `data_transform` per coin → produces
         `prices_h{h}` target columns.
      3. For each horizon, `fit_pooled_full` returns a persistable bundle.
      4. joblib.dump `{horizon: bundle}` to a versioned `.pkl`.
      5. Compute in-sample DirAcc per horizon for diagnostics.

    Args:
        coins: CoinGecko coin IDs to pool (e.g. ["bitcoin", "ethereum"]).
        horizons: Forecast horizons in days (e.g. [7, 14]).
        asof: Upper-bound trade date (YYYY-mm-dd) for the training window.
        checkpoint_dir: Directory where the checkpoint pickle is written.
        lookback_days: How many days of history to load per coin.
        min_train_window: Kept in the signature for API compatibility with
            the caller; not used here (full-fit has no walk-forward).
    """
    del min_train_window  # API compatibility; full-fit has no walk-forward.

    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    raw = build_pooled_dataset(
        coin_universe=coins,
        lookback_days=lookback_days,
        horizons=horizons,
        trade_date=asof,
        add_onchain_pit=True,
    )

    transformed = _transform_pooled(raw, horizons)
    if transformed is None or len(transformed) == 0:
        raise RuntimeError("Transformed pooled DataFrame is empty")

    bundles: dict[int, dict[str, Any]] = {}
    metrics: dict[str, float] = {}
    for h in horizons:
        bundle = fit_pooled_full(transformed, horizon=h)
        bundles[h] = bundle
        metrics[f"dir_acc_h{h}"] = _train_dir_acc(bundle, transformed)

    out_path = checkpoint_dir / f"lgb_{len(coins)}coin_pit_{asof}.pkl"
    joblib.dump(bundles, out_path)

    return TrainArtifact(
        model_path=out_path,
        train_window_start=_train_window_start(transformed),
        train_window_end=asof,
        train_rows=int(len(transformed)),
        train_dir_acc_h7=float(metrics.get("dir_acc_h7", float("nan"))),
        train_dir_acc_h14=float(metrics.get("dir_acc_h14", float("nan"))),
        sha256=_sha256_of(out_path),
    )


def run_retrain_with_fallback(
    coins: list[str],
    horizons: list[int],
    asof: str,
    checkpoint_dir: Path,
    lookback_days: int = 730,
    min_train_window: int = 365,
) -> TrainArtifact:
    """Try retrain; if it fails, return the most recent existing checkpoint.

    Used by the live runner so a single bad data fetch (CoinMetrics outage,
    DefiLlama 5xx, ...) doesn't break the daily cycle — we keep trading with
    yesterday's model and surface the failure via `is_fallback=True`.
    """
    try:
        return run_retrain(
            coins, horizons, asof, checkpoint_dir,
            lookback_days=lookback_days,
            min_train_window=min_train_window,
        )
    except Exception as e:
        logger.error(
            "Retrain failed: %s — falling back to previous checkpoint", e
        )
        previous = sorted(Path(checkpoint_dir).glob("lgb_*coin_pit_*.pkl"))
        if not previous:
            raise RuntimeError(
                "No previous checkpoint to fall back to"
            ) from e
        prev = previous[-1]
        return TrainArtifact(
            model_path=prev,
            train_window_start="",
            train_window_end="",
            train_rows=0,
            train_dir_acc_h7=float("nan"),
            train_dir_acc_h14=float("nan"),
            sha256=_sha256_of(prev),
            is_fallback=True,
        )
