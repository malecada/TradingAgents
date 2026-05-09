from __future__ import annotations

import pandas as pd
import pytest


def test_fetch_funding_rate_uses_cache(tmp_path, monkeypatch):
    from tradingagents.strategies.v3.features.derivatives import fetch_funding_rate

    cache_file = tmp_path / "BTCUSDT_funding.parquet"
    df_cached = pd.DataFrame(
        {"funding_rate": [0.0001]},
        index=pd.date_range("2026-01-01", periods=1, freq="8h", tz="UTC"),
    )
    df_cached.to_parquet(cache_file)

    def _fail(*args, **kwargs):
        raise AssertionError("network must not be hit when cache present")

    monkeypatch.setattr(
        "tradingagents.strategies.v3.features.derivatives._fetch_funding_page",
        _fail,
    )
    df = fetch_funding_rate(symbol="BTCUSDT", cache_dir=tmp_path)
    assert len(df) == 1
    assert df["funding_rate"].iloc[0] == 0.0001


def test_fetch_funding_rate_paginates(tmp_path, monkeypatch):
    from tradingagents.strategies.v3.features import derivatives

    pages = [
        [
            {"fundingTime": 1735689600000, "fundingRate": "0.0001"},  # 2025-01-01 UTC
            {"fundingTime": 1735718400000, "fundingRate": "0.0002"},
        ],
        [
            {"fundingTime": 1735747200000, "fundingRate": "0.0003"},
        ],
        [],  # empty signals end
    ]

    call_count = {"n": 0}

    def _fake(symbol, start_ms, limit):
        idx = call_count["n"]
        call_count["n"] += 1
        if idx < len(pages):
            return pages[idx]
        return []

    monkeypatch.setattr(derivatives, "_fetch_funding_page", _fake)
    df = derivatives.fetch_funding_rate(
        symbol="BTCUSDT",
        cache_dir=tmp_path,
        start=pd.Timestamp("2025-01-01", tz="UTC"),
        end=pd.Timestamp("2025-01-02", tz="UTC"),
    )
    assert len(df) == 3
    assert df["funding_rate"].iloc[0] == 0.0001


def test_fetch_funding_rate_backoff_on_429(tmp_path, monkeypatch):
    from tradingagents.strategies.v3.features import derivatives
    from tradingagents.strategies.v3.features._http import RateLimitError

    calls = {"n": 0}

    def _fake(symbol, start_ms, limit):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RateLimitError("429")
        return [{"fundingTime": 1735689600000, "fundingRate": "0.0001"}]

    # Avoid actual sleeping
    monkeypatch.setattr(
        "tradingagents.strategies.v3.features._http.time.sleep", lambda _s: None
    )
    monkeypatch.setattr(derivatives, "_fetch_funding_page", _fake)
    df = derivatives.fetch_funding_rate(
        symbol="BTCUSDT",
        cache_dir=tmp_path,
        start=pd.Timestamp("2025-01-01", tz="UTC"),
        end=pd.Timestamp("2025-01-02", tz="UTC"),
    )
    assert len(df) >= 1
    assert calls["n"] >= 3


def test_fetch_open_interest_uses_cache(tmp_path, monkeypatch):
    from tradingagents.strategies.v3.features.derivatives import fetch_open_interest_history

    cache_file = tmp_path / "BTCUSDT_oi.parquet"
    df_cached = pd.DataFrame(
        {"open_interest": [1000.0]},
        index=pd.date_range("2026-01-01", periods=1, freq="D", tz="UTC"),
    )
    df_cached.to_parquet(cache_file)

    def _fail(*args, **kwargs):
        raise AssertionError("network must not be hit when cache present")

    monkeypatch.setattr(
        "tradingagents.strategies.v3.features.derivatives._fetch_oi_page",
        _fail,
    )
    df = fetch_open_interest_history(symbol="BTCUSDT", cache_dir=tmp_path)
    assert len(df) == 1
    assert df["open_interest"].iloc[0] == 1000.0


def test_fetch_open_interest_paginates(tmp_path, monkeypatch):
    from tradingagents.strategies.v3.features import derivatives

    pages = [
        [
            {"timestamp": 1735689600000, "sumOpenInterest": "1000.0", "sumOpenInterestValue": "30000000.0"},
            {"timestamp": 1735776000000, "sumOpenInterest": "1100.0", "sumOpenInterestValue": "33000000.0"},
        ],
        [
            {"timestamp": 1735862400000, "sumOpenInterest": "1200.0", "sumOpenInterestValue": "36000000.0"},
        ],
        [],
    ]
    call_count = {"n": 0}

    def _fake(symbol, period, start_ms, limit):
        idx = call_count["n"]
        call_count["n"] += 1
        if idx < len(pages):
            return pages[idx]
        return []

    monkeypatch.setattr(derivatives, "_fetch_oi_page", _fake)
    df = derivatives.fetch_open_interest_history(
        symbol="BTCUSDT",
        cache_dir=tmp_path,
        start=pd.Timestamp("2025-01-01", tz="UTC"),
        end=pd.Timestamp("2025-01-04", tz="UTC"),
    )
    assert len(df) == 3
    assert df["open_interest"].iloc[0] == 1000.0
    assert df["open_interest"].iloc[2] == 1200.0


def test_fetch_premium_index(monkeypatch):
    from tradingagents.strategies.v3.features import derivatives

    def _fake(symbol):
        return {
            "symbol": "BTCUSDT",
            "markPrice": "50000.0",
            "indexPrice": "49950.0",
            "lastFundingRate": "0.0001",
            "time": 1735689600000,
        }

    monkeypatch.setattr(derivatives, "_fetch_premium_index_raw", _fake)
    out = derivatives.fetch_premium_index(symbol="BTCUSDT")
    assert out["mark_price"] == 50000.0
    assert out["index_price"] == 49950.0
    assert out["basis"] == pytest.approx(50.0 / 49950.0, rel=1e-6)
