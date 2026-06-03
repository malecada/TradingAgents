# tests/dataflows/test_intraday_fetch.py
from __future__ import annotations

import pandas as pd
import pytest

from tradingagents.dataflows import coingecko_binance as cgb


def _fake_kline(open_ms: int, o: float, h: float, l: float, c: float) -> list:
    # Binance kline row layout: [openTime, open, high, low, close, volume, closeTime, ...]
    return [open_ms, str(o), str(h), str(l), str(c), "1.0", open_ms + 3_600_000, "0", 0, "0", "0", "0"]


def test_interval_passthrough(monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured.update(params)

        class R:
            def raise_for_status(self):
                pass

            def json(self):
                return [_fake_kline(1_600_000_000_000, 1, 2, 0.5, 1.5)]

        return R()

    monkeypatch.setattr(cgb.requests, "get", fake_get)
    out = cgb._binance_klines("BTCUSDT", 1_600_000_000_000, 1_600_003_600_000, interval="1h")
    assert captured["interval"] == "1h"
    assert len(out) == 1


def test_fetch_klines_range_parses_ohlc(monkeypatch):
    base = 1_600_000_000_000

    def fake_chunked(symbol, from_ms, to_ms, interval="1d", step_ms=None):
        return [_fake_kline(base + i * 3_600_000, 10 + i, 11 + i, 9 + i, 10.5 + i) for i in range(3)]

    monkeypatch.setattr(cgb, "_binance_klines_chunked", fake_chunked)
    df = cgb.fetch_binance_klines_range("BTCUSDT", base, base + 3 * 3_600_000, interval="1h")
    assert list(df.columns) == ["open_time", "open", "high", "low", "close", "volume"]
    assert len(df) == 3
    assert df["high"].iloc[0] == 11.0
    assert df["open_time"].is_monotonic_increasing
