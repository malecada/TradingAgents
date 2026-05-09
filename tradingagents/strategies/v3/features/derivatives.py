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
