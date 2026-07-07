"""Live predict must produce numbers identical to the backtest feature path.

Rewritten OFFLINE (audit 2026-07-07 R4): the old version used obsolete
signatures, was CI-skipped behind RUN_ONLINE_TESTS, and would have errored if
run — while predict.py claimed it guarded live/backtest equivalence.

Two legs, same synthetic OHLCV data:
  live leg     — run_retrain -> composite .pkl -> run_predict, with OHLCV
                 served from data_root/ohlcv_cache parquets (the live route)
  backtest leg — build_pooled_dataset(ohlcv_frames=...) + _transform_pooled
                 + predict_pooled on the same composite (the eval-script route)

Predictions must match to float precision. Realtime on-chain enrichment is
patched to a no-op in BOTH legs (it needs network; it is additive and
identical in both paths).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd
import pytest

from tradingagents.execution.live import predict, retrain
from tradingagents.models import model_utils
from tradingagents.models.lgb_model import predict_pooled

HORIZONS = [7, 14]
ASOF = "2026-06-19"
POOL = ["bitcoin", "ethereum"]
ROUTING = {"bitcoin": {"pool": POOL, "feature_set": "78f"}}


def _ohlcv(seed: int, n: int = 420) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=ASOF, periods=n, freq="D")
    close = 100.0 * np.cumprod(1 + rng.normal(0.0008, 0.02, n))
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": close * (1 + rng.normal(0, 0.002, n)),
            "High": close * 1.015,
            "Low": close * 0.985,
            "Close": close,
            "Volume": rng.uniform(5e5, 2e6, n),
        }
    )


@pytest.fixture()
def frames() -> dict[str, pd.DataFrame]:
    return {"bitcoin": _ohlcv(1), "ethereum": _ohlcv(2)}


def _write_parquets(frames: dict[str, pd.DataFrame], cache_dir: Path) -> None:
    from tradingagents.execution.live.config import to_binance_symbol

    cache_dir.mkdir(parents=True, exist_ok=True)
    for coin, df in frames.items():
        low = df.rename(columns={c: c.lower() for c in df.columns}).copy()
        low["date"] = low["date"].dt.strftime("%Y-%m-%d")
        low.to_parquet(cache_dir / f"{to_binance_symbol(coin)}_1d.parquet",
                       index=False)


def test_live_predict_matches_backtest_feature_path(tmp_path, frames):
    cache_dir = tmp_path / "ohlcv_cache"
    _write_parquets(frames, cache_dir)

    no_onchain = patch.object(
        model_utils, "add_onchain_features", side_effect=lambda df, *a, **k: df
    )
    # retrain has no frame-injection parameter yet — serve it the same data
    # through the vendor loader seam so both legs train/predict on one input
    def _fake_load(coin, curr_date):
        df = frames[coin].copy()
        return df[df["Date"] <= pd.to_datetime(curr_date)]

    from tradingagents.dataflows import coingecko_binance

    with no_onchain, patch.object(
        coingecko_binance, "_load_crypto_ohlcv", side_effect=_fake_load
    ):
        artifact = retrain.run_retrain(
            routing=ROUTING, horizons=HORIZONS, asof=ASOF,
            checkpoint_dir=tmp_path / "ckpt", lookback_days=400,
        )
        live = predict.run_predict(
            coin_universe=["bitcoin"],
            routing=ROUTING,
            ckpt_path=artifact.path,
            asof=ASOF,
            store_root=tmp_path / "onchain",
            ohlcv_cache=cache_dir,
            horizons=HORIZONS,
        )

        # backtest leg: identical construction path to evaluate_models_multi
        pooled = model_utils.build_pooled_dataset(
            coin_universe=POOL, lookback_days=400, horizons=HORIZONS,
            trade_date=ASOF, add_onchain_pit=False, ohlcv_frames=frames,
        )
        transformed = retrain._transform_pooled(pooled, HORIZONS)
        if "date" not in transformed.columns:
            transformed = transformed.reset_index()
        row = (
            transformed.sort_values("date")
            .groupby("coin_id", as_index=False).tail(1)
        )
        row = row[row["coin_id"] == "bitcoin"]
        composite = joblib.load(artifact.path)

    assert len(live) == len(HORIZONS)
    for h in HORIZONS:
        expected = float(predict_pooled(composite["bitcoin_78f"][h], row))
        actual = float(
            live.loc[(live["coin"] == "bitcoin") & (live["horizon"] == h),
                     "prediction"].iloc[0]
        )
        assert actual == pytest.approx(expected, abs=1e-9), (
            f"h={h}: live={actual} backtest={expected} — live/backtest "
            f"feature paths diverged"
        )
