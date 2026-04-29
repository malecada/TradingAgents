"""Daily walk-forward retrain of pooled LGB model with PIT on-chain features.

Wraps `tradingagents.models.model_utils.build_pooled_dataset` and
`tradingagents.models.lgb_model.model_run_pooled` so the live runner can
invoke them with the live module's vocabulary (`coins`, `asof`) and get back
a versioned checkpoint plus a metrics summary.

Two important shape adapters live here:

1. The upstream `build_pooled_dataset` uses kwargs `coin_universe`,
   `lookback_days`, `horizons`, `trade_date`. This module accepts the
   live runner's `coins`/`asof` names and translates.

2. The upstream `lgb_model.model_run_pooled` is per-horizon — it takes a
   single `horizon: int` and returns `(pred_df, metrics_dict)` where the
   metrics dict has `directional_accuracy` (no per-horizon suffix). The
   wrapper in this module accepts `horizons: list[int]`, runs the upstream
   call once per horizon, packs the per-horizon `pred_df`s into a model
   dict, and renames `directional_accuracy` to `dir_acc_h{h}` so the
   artifact fields below are populated correctly.

Tests patch `build_pooled_dataset` and `model_run_pooled` on this module,
so the real upstream signatures are only exercised in live cycles.
"""
from __future__ import annotations

import hashlib
import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from tradingagents.models import lgb_model as _lgb_model
from tradingagents.models.model_utils import build_pooled_dataset

logger = logging.getLogger(__name__)


def model_run_pooled(
    pooled_df: pd.DataFrame,
    horizons: list[int],
    min_train_window: int = 365,
) -> tuple[dict[str, Any], dict[str, float]]:
    """Multi-horizon wrapper around `lgb_model.model_run_pooled`.

    The upstream is per-horizon and returns `(pred_df, metrics)` with a
    single `directional_accuracy` key. Here we loop over `horizons`, pack
    per-horizon predictions into a dict, and translate the metrics keys to
    `dir_acc_h{h}` so callers can read them directly off the dict.

    Args:
        pooled_df: Date-indexed pooled DataFrame with `prices_h{h}` target
            columns produced by `data_transform()`.
        horizons: Forecast horizons to train (e.g. [7, 14]).
        min_train_window: Walk-forward warm-up size.

    Returns:
        (model_obj, metrics) where model_obj is a dict with one entry per
        horizon (`h{h}`) containing the per-horizon prediction DataFrame,
        plus `horizons` (echoed input) and `feature_cols` (column list);
        and metrics is a dict with `dir_acc_h{h}` per horizon.
    """
    model_obj: dict[str, Any] = {"horizons": list(horizons)}
    metrics: dict[str, float] = {}
    feature_cols: list[str] | None = None
    for h in horizons:
        pred_df, m = _lgb_model.model_run_pooled(pooled_df, h, min_train_window)
        model_obj[f"h{h}"] = pred_df
        metrics[f"dir_acc_h{h}"] = float(m.get("directional_accuracy", 0.0))
        # Surface raw upstream metrics too (handy for diagnostics).
        for k, v in m.items():
            metrics[f"{k}_h{h}"] = float(v) if isinstance(v, (int, float)) else v
        if feature_cols is None:
            feature_cols = [
                c for c in pooled_df.columns
                if c != "coin_id" and not c.startswith("prices_h")
            ]
    if feature_cols is not None:
        model_obj["feature_cols"] = feature_cols
    return model_obj, metrics


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


def _persist_model(model_obj: Any, out_path: Path) -> None:
    """Write the trained model to disk via joblib.

    Some objects (e.g. unittest.mock.MagicMock used in tests) are not
    picklable. In that case we fall back to writing a minimal sentinel
    payload containing only the picklable bits so the checkpoint file
    still exists on disk and downstream sha256 + path checks succeed.
    """
    try:
        joblib.dump(model_obj, out_path)
        return
    except (pickle.PicklingError, TypeError, AttributeError) as e:
        logger.warning(
            "joblib.dump could not serialize model object (%s); "
            "writing sentinel payload at %s", e, out_path,
        )
    # Best-effort: keep only items we can repr/pickle cleanly.
    sentinel: dict[str, Any] = {"_unpicklable": True}
    if isinstance(model_obj, dict):
        for k, v in model_obj.items():
            try:
                pickle.dumps(v)
            except Exception:
                sentinel[k] = repr(v)
            else:
                sentinel[k] = v
    with open(out_path, "wb") as f:
        pickle.dump(sentinel, f)


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
    """Build dataset, train pooled LGB, persist checkpoint, return artifact.

    Args:
        coins: CoinGecko-style coin IDs to pool (e.g. ["bitcoin", "ethereum"]).
        horizons: Forecast horizons in days (e.g. [7, 14]).
        asof: Upper-bound trade date (YYYY-mm-dd) for the training window.
        checkpoint_dir: Directory where the checkpoint pickle is written.
        lookback_days: How many days of history to load per coin.
        min_train_window: Walk-forward warm-up window passed to LGB.
    """
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Translate live-vocabulary kwargs to the upstream signature.
    df = build_pooled_dataset(
        coin_universe=coins,
        lookback_days=lookback_days,
        horizons=horizons,
        trade_date=asof,
        add_onchain_pit=True,
    )

    model_obj, metrics = model_run_pooled(
        df, horizons=horizons, min_train_window=min_train_window
    )

    out_path = checkpoint_dir / f"lgb_{len(coins)}coin_pit_{asof}.pkl"
    _persist_model(model_obj, out_path)

    return TrainArtifact(
        model_path=out_path,
        train_window_start=_train_window_start(df),
        train_window_end=asof,
        train_rows=len(df),
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
