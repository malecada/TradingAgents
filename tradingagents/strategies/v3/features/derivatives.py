"""Derivatives features: funding rate, basis, OI, liquidation asymmetry.

Look-ahead-safe by construction: ``build_daily_derivatives_features`` slices
input to ``df.index <= as_of`` before any rolling op. Tests assert this.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from tradingagents.strategies.v3.features._http import RateLimitError, with_backoff

logger = logging.getLogger(__name__)

_BINANCE_FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"


def _fetch_funding_page(symbol: str, start_ms: int, limit: int = 1000) -> list[dict]:
    """One funding-rate page from Binance Futures."""
    resp = requests.get(
        _BINANCE_FUNDING_URL,
        params={"symbol": symbol, "startTime": start_ms, "limit": limit},
        timeout=10,
    )
    if resp.status_code == 429:
        raise RateLimitError("Binance Futures 429")
    resp.raise_for_status()
    return resp.json()


def fetch_funding_rate(
    symbol: str,
    cache_dir: Path,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
    limit: int = 1000,
) -> pd.DataFrame:
    """Fetch full funding-rate history, paginated, cached to parquet.

    Returns DataFrame indexed by funding-time (UTC) with column ``funding_rate``.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{symbol}_funding.parquet"
    if cache_file.exists():
        return pd.read_parquet(cache_file)

    if start is None:
        start = pd.Timestamp("2020-01-01", tz="UTC")
    if end is None:
        end = pd.Timestamp.utcnow().tz_convert("UTC")

    cursor_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    all_rows: list[dict] = []

    while cursor_ms < end_ms:
        page = with_backoff(
            lambda: _fetch_funding_page(symbol, cursor_ms, limit)
        )
        if not page:
            break
        all_rows.extend(page)
        last_time = page[-1]["fundingTime"]
        if last_time <= cursor_ms:
            break
        cursor_ms = last_time + 1

    if not all_rows:
        df = pd.DataFrame(columns=["funding_rate"])
    else:
        df = pd.DataFrame(
            {
                "funding_rate": [float(r["fundingRate"]) for r in all_rows],
            },
            index=pd.to_datetime(
                [r["fundingTime"] for r in all_rows], unit="ms", utc=True
            ),
        )
        df.index.name = "ts"
        df = df.sort_index()
    df.to_parquet(cache_file)
    return df


_BINANCE_OI_HIST_URL = "https://fapi.binance.com/fapi/v1/openInterestHist"
_BINANCE_PREMIUM_URL = "https://fapi.binance.com/fapi/v1/premiumIndex"


def _fetch_oi_page(symbol: str, period: str, start_ms: int, limit: int = 500) -> list[dict]:
    """One open-interest history page. ``period`` is one of 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d."""
    resp = requests.get(
        _BINANCE_OI_HIST_URL,
        params={
            "symbol": symbol,
            "period": period,
            "startTime": start_ms,
            "limit": limit,
        },
        timeout=10,
    )
    if resp.status_code == 429:
        raise RateLimitError("Binance Futures 429 (OI)")
    resp.raise_for_status()
    return resp.json()


def fetch_open_interest_history(
    symbol: str,
    cache_dir: Path,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
    period: str = "1d",
    limit: int = 500,
) -> pd.DataFrame:
    """Fetch full OI history, paginated, cached to ``{symbol}_oi.parquet``."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{symbol}_oi.parquet"
    if cache_file.exists():
        return pd.read_parquet(cache_file)

    if start is None:
        start = pd.Timestamp.utcnow().tz_convert("UTC") - pd.Timedelta(days=730)
    if end is None:
        end = pd.Timestamp.utcnow().tz_convert("UTC")

    cursor_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    rows: list[dict] = []

    while cursor_ms < end_ms:
        page = with_backoff(
            lambda: _fetch_oi_page(symbol, period, cursor_ms, limit)
        )
        if not page:
            break
        rows.extend(page)
        last_time = page[-1]["timestamp"]
        if last_time <= cursor_ms:
            break
        cursor_ms = last_time + 1

    if not rows:
        df = pd.DataFrame(columns=["open_interest", "open_interest_value"])
    else:
        df = pd.DataFrame(
            {
                "open_interest": [float(r["sumOpenInterest"]) for r in rows],
                "open_interest_value": [float(r["sumOpenInterestValue"]) for r in rows],
            },
            index=pd.to_datetime(
                [r["timestamp"] for r in rows], unit="ms", utc=True
            ),
        )
        df.index.name = "ts"
        df = df.sort_index()
    df.to_parquet(cache_file)
    return df


def _fetch_premium_index_raw(symbol: str) -> dict:
    resp = requests.get(_BINANCE_PREMIUM_URL, params={"symbol": symbol}, timeout=10)
    if resp.status_code == 429:
        raise RateLimitError("Binance Futures 429 (premium)")
    resp.raise_for_status()
    return resp.json()


def fetch_premium_index(symbol: str) -> dict:
    """Snapshot mark price + index price + last funding rate for ``symbol``.

    Returns dict with keys: ``mark_price``, ``index_price``, ``basis``,
    ``last_funding_rate``, ``timestamp`` (pd.Timestamp UTC). ``basis`` is
    ``(mark - index) / index``.
    """
    raw = with_backoff(lambda: _fetch_premium_index_raw(symbol))
    mark = float(raw["markPrice"])
    index = float(raw["indexPrice"])
    return {
        "mark_price": mark,
        "index_price": index,
        "basis": (mark - index) / index if index > 0 else 0.0,
        "last_funding_rate": float(raw["lastFundingRate"]),
        "timestamp": pd.Timestamp(raw["time"], unit="ms", tz="UTC"),
    }
