"""Audit 2026-07-07 R3: live feature path must read the refreshed OHLCV cache.

Before this fix the feature pipeline (build_features_asof -> build_pooled_dataset
-> fetch_ohlcv_for_model) read the package-dir CSV cache, while sizing read the
daily-refreshed data_root/ohlcv_cache/{SYMBOL}_1d.parquet — two independent
caches that can diverge for the same date. build_features_asof also accepted
store_root/ohlcv_cache parameters and silently ignored both.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from tradingagents.models import model_utils
from tradingagents.dataflows import coingecko_binance as model_utils_cgb
from tradingagents.execution.live import predict


def _ohlcv_frame(n: int = 60, start: str = "2026-01-01") -> pd.DataFrame:
    rng = np.random.default_rng(3)
    dates = pd.date_range(start, periods=n, freq="D")
    close = 100.0 * np.cumprod(1 + rng.normal(0.001, 0.01, n))
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": close * 0.99,
            "High": close * 1.01,
            "Low": close * 0.98,
            "Close": close,
            "Volume": np.full(n, 1e6),
        }
    )


def test_build_pooled_dataset_uses_provided_frames():
    frame = _ohlcv_frame()
    with patch.object(
        model_utils_cgb, "_load_crypto_ohlcv",
        side_effect=AssertionError("network path must not be hit"),
    ):
        pooled = model_utils.build_pooled_dataset(
            coin_universe=["bitcoin"],
            lookback_days=60,
            horizons=[7],
            trade_date="2026-03-01",
            add_technical=False,
            add_cross_asset=False,
            add_onchain=False,
            ohlcv_frames={"bitcoin": frame},
        )
    assert not pooled.empty
    assert (pooled["coin_id"] == "bitcoin").all()
    # prices column must come from the provided frame
    assert pooled["prices"].iloc[-1] == pytest.approx(frame["Close"].iloc[-1])


def test_build_features_asof_reads_refreshed_parquet(tmp_path: Path):
    frame = _ohlcv_frame()
    asof = frame["Date"].iloc[-2].strftime("%Y-%m-%d")  # last row = "in-flight"
    parquet = frame.rename(
        columns={c: c.lower() for c in frame.columns}
    )
    parquet["date"] = parquet["date"].dt.strftime("%Y-%m-%d")
    parquet.to_parquet(tmp_path / "BTCUSDT_1d.parquet", index=False)

    with patch.object(
        model_utils_cgb, "_load_crypto_ohlcv",
        side_effect=AssertionError("feature path must use the parquet cache"),
    ):
        latest = predict.build_features_asof(
            coin_pool=["bitcoin"],
            asof=asof,
            ohlcv_cache=tmp_path,
            add_onchain_pit=False,
            horizons=[7],
            lookback_days=60,
        )
    assert len(latest) == 1
    # data_transform shifts features by 1: latest row (dated asof) carries
    # close(asof-1); the in-flight bar after asof must have been filtered out
    assert latest["ref_price"].iloc[0] == pytest.approx(frame["Close"].iloc[-3])


def test_build_features_asof_forwards_store_root(tmp_path: Path):
    frame = _ohlcv_frame()
    asof = frame["Date"].iloc[-1].strftime("%Y-%m-%d")
    seen_roots = []

    def _fake_pit(coin, dates, root=None, **kwargs):
        seen_roots.append(root)
        return pd.DataFrame(index=pd.DatetimeIndex(dates))

    with patch(
        "tradingagents.dataflows.onchain_features.build_pit_onchain_features",
        side_effect=_fake_pit,
    ):
        predict.build_features_asof(
            coin_pool=["bitcoin"],
            asof=asof,
            store_root=tmp_path / "pit_store",
            add_onchain_pit=True,
            horizons=[7],
            lookback_days=60,
            ohlcv_frames={"bitcoin": frame},
        )
    assert seen_roots and all(r == tmp_path / "pit_store" for r in seen_roots)
