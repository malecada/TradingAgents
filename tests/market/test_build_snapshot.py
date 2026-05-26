from datetime import datetime, timezone
from unittest.mock import patch

import numpy as np
import pandas as pd

from tradingagents.market.build_snapshot import build_market_snapshot


def _ohlcv(n=260, drift=0.0, vol=0.01, seed=0):
    rng = np.random.default_rng(seed)
    r = rng.normal(drift, vol, n)
    close = 20000.0 * np.exp(np.cumsum(r))
    return pd.DataFrame({
        "Date": pd.date_range("2025-04-01", periods=n, freq="D"),
        "Open": close, "High": close*1.005, "Low": close*0.995,
        "Close": close, "Volume": np.ones(n) * 1e6,
    })


def test_build_snapshot_returns_market_snapshot(monkeypatch):
    df = _ohlcv(drift=0.003, vol=0.005, seed=99)

    with patch("tradingagents.market.build_snapshot._load_ohlcv",
               return_value=df):
        snap = build_market_snapshot(
            coin="bitcoin",
            trade_date=datetime(2025, 12, 15, tzinfo=timezone.utc),
            horizon_days=7,
        )
    from tradingagents.market.snapshot import MarketSnapshot
    assert isinstance(snap, MarketSnapshot)
    assert snap.horizon_days == 7
    assert 0.0 <= snap.conflict_score <= 1.0
    assert snap.default_direction in {"LONG", "SHORT", "FLAT"}
    assert snap.regime in {"TREND_UP", "TREND_DOWN", "RANGE", "HIGH_VOL"}
    assert len(snap.indicators) == 13


def test_build_snapshot_uptrend_default_long(monkeypatch):
    df = _ohlcv(drift=0.006, vol=0.004, seed=1)
    with patch("tradingagents.market.build_snapshot._load_ohlcv",
               return_value=df):
        snap = build_market_snapshot(
            coin="bitcoin",
            trade_date=datetime(2025, 12, 15, tzinfo=timezone.utc),
            horizon_days=7,
        )
    assert snap.regime == "TREND_UP"
    assert snap.default_direction == "LONG"
    assert snap.conflict_score == 0.0


def test_build_snapshot_anonymize_asset_alias(monkeypatch):
    from tradingagents.agents.utils import anonymizer
    df = _ohlcv(drift=0.002, vol=0.005, seed=2)
    anonymizer.configure(enabled=True)
    try:
        with patch("tradingagents.market.build_snapshot._load_ohlcv",
                   return_value=df):
            snap = build_market_snapshot(
                coin="bitcoin",
                trade_date=datetime(2025, 12, 15, tzinfo=timezone.utc),
                horizon_days=7,
                anonymize=True,
            )
        assert snap.asset.startswith("Asset_")
    finally:
        anonymizer.configure(enabled=False)


def test_build_snapshot_no_anonymize_uses_coin_label(monkeypatch):
    df = _ohlcv(drift=0.001, vol=0.005, seed=3)
    from tradingagents.agents.utils import anonymizer
    anonymizer.configure(enabled=False)
    with patch("tradingagents.market.build_snapshot._load_ohlcv",
               return_value=df):
        snap = build_market_snapshot(
            coin="bitcoin",
            trade_date=datetime(2025, 12, 15, tzinfo=timezone.utc),
            horizon_days=7,
            anonymize=False,
        )
    assert snap.asset == "bitcoin"
