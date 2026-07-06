"""Unit tests for model_utils._join_sentiment — the pure join step behind
`build_pooled_dataset(..., add_sentiment=True)`.

`build_pooled_dataset` fetches OHLCV over the network, so it can't be
exercised offline. `_join_sentiment(df, coin, engine)` is factored out as a
small, network-free helper: given a model df (date-indexed) and a coin, it
left-joins the 10 PIT sentiment columns and fills missing values with 0.0 —
exactly the join shape used by the existing `add_onchain_pit` block. This is
tested directly here; the `add_sentiment=False` default path never calls
this helper at all (see the `if add_sentiment:` gate in `build_pooled_dataset`),
so flag-off identity follows from code inspection plus the full regression
suite staying green.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from tradingagents.dataflows import sentiment_index_store
from tradingagents.dataflows.sentiment_features import FEATURE_COLS
from tradingagents.models import model_utils as mu


def _fake_model_df(n: int = 10) -> pd.DataFrame:
    dates = pd.date_range("2025-06-01", periods=n, freq="D")
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {"prices": 100.0 + rng.normal(0, 1, n).cumsum()},
        index=dates,
    )


def test_join_sentiment_adds_exactly_ten_columns_and_fills_nan(tmp_path, monkeypatch):
    monkeypatch.setattr(sentiment_index_store, "BASE_ROOT", tmp_path / "index")
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path / "no_fng_root"))

    df = _fake_model_df()
    out = mu._join_sentiment(df, "bitcoin", engine="llm")

    for col in FEATURE_COLS:
        assert col in out.columns
    assert not out[FEATURE_COLS].isna().any().any(), "join must fillna(0.0)"
    assert (out[FEATURE_COLS] == 0.0).all().all(), "empty store -> all-zero after fillna"
    # Original columns untouched.
    pd.testing.assert_series_equal(out["prices"], df["prices"])


def test_join_sentiment_pulls_real_values_when_present(tmp_path, monkeypatch):
    monkeypatch.setattr(sentiment_index_store, "BASE_ROOT", tmp_path / "index2")
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path / "no_fng_root2"))

    day = datetime(2025, 6, 5, tzinfo=timezone.utc)
    rows = pd.DataFrame([{
        "event_ts": day, "as_of_ts": day + timedelta(hours=1),
        "coin": "btc", "metric": "snt_idx_mean", "value": 0.77,
        "source": "sentiment_index", "status": "final",
    }])
    sentiment_index_store.upsert_index_rows(rows, engine="llm")

    df = _fake_model_df()
    out = mu._join_sentiment(df, "bitcoin", engine="llm")

    assert out.loc[pd.Timestamp("2025-06-05"), "snt_idx_mean"] == pytest.approx(0.77)


def _fake_ohlcv(n: int = 20) -> pd.DataFrame:
    dates = pd.date_range("2025-06-01", periods=n, freq="D")
    rng = np.random.default_rng(1)
    close = 100.0 + rng.normal(0, 1, n).cumsum()
    return pd.DataFrame({
        "Date": dates,
        "Open": close, "High": close + 1, "Low": close - 1,
        "Close": close, "Volume": rng.uniform(1e6, 2e6, n),
    })


def test_build_pooled_dataset_flag_off_vs_on(tmp_path, monkeypatch):
    """add_sentiment=False must be identical to HEAD (no sentiment columns,
    _join_sentiment never called); add_sentiment=True must add exactly the
    10 sentiment columns. Network is mocked so this runs fully offline."""
    from tradingagents.dataflows import coingecko_binance

    monkeypatch.setattr(coingecko_binance, "_load_crypto_ohlcv", lambda *a, **k: _fake_ohlcv())
    monkeypatch.setattr(sentiment_index_store, "BASE_ROOT", tmp_path / "index3")
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path / "no_fng_root3"))

    common_kwargs = dict(
        coin_universe=["bitcoin"],
        lookback_days=15,
        horizons=[1],
        trade_date="2025-06-20",
        add_technical=False,
        add_cross_asset=False,
        add_onchain=False,
        add_onchain_pit=False,
    )

    called = {"hit": False}
    orig_join = mu._join_sentiment

    def _spy(*a, **k):
        called["hit"] = True
        return orig_join(*a, **k)

    monkeypatch.setattr(mu, "_join_sentiment", _spy)
    off = mu.build_pooled_dataset(**common_kwargs, add_sentiment=False)
    assert not called["hit"], "_join_sentiment must not be called when add_sentiment=False"
    for col in FEATURE_COLS:
        assert col not in off.columns

    on = mu.build_pooled_dataset(**common_kwargs, add_sentiment=True, sentiment_engine="llm")
    assert called["hit"]
    for col in FEATURE_COLS:
        assert col in on.columns
    # Flag-off columns are an exact subset/prefix of flag-on columns (nothing
    # else changed by turning the flag on).
    assert list(off.columns) == [c for c in on.columns if c not in FEATURE_COLS]
    pd.testing.assert_frame_equal(off, on.drop(columns=FEATURE_COLS))
