"""VPIN + Order Flow Imbalance from Binance aggTrades.

This module currently provides volume bucketing and the VPIN imbalance
computation. The ``as_of`` look-ahead guard is added by the daily builder
function in Task 9 (``build_daily_microstructure_features``).
"""

from __future__ import annotations

from typing import Iterator

import numpy as np
import pandas as pd


def volume_buckets(
    trades: pd.DataFrame, bucket_size: float
) -> Iterator[pd.DataFrame]:
    """Split ``trades`` into volume-equal buckets of size ``bucket_size``.

    Trades are fractionally split when a single trade spans a bucket boundary.
    The fractional portion of a trade is proportionally allocated to buy/sell
    based on the trade's ``is_buyer_maker`` flag. Last bucket may be partial;
    it is yielded only if its qty >= 0.5 * bucket_size.
    """
    rows: list[dict] = []
    cum = 0.0

    for idx, row in trades.iterrows():
        remaining = float(row["qty"])
        while remaining > 1e-12:
            space = bucket_size - cum
            take = min(remaining, space)
            rows.append(
                {
                    "price": row["price"],
                    "qty": take,
                    "is_buyer_maker": row["is_buyer_maker"],
                    "_idx": idx,
                }
            )
            cum += take
            remaining -= take
            if cum >= bucket_size - 1e-12:
                bucket_df = pd.DataFrame(rows).set_index("_idx")
                bucket_df.index.name = trades.index.name
                yield bucket_df
                rows = []
                cum = 0.0

    if rows:
        partial = sum(r["qty"] for r in rows)
        if partial >= 0.5 * bucket_size:
            bucket_df = pd.DataFrame(rows).set_index("_idx")
            bucket_df.index.name = trades.index.name
            yield bucket_df


def compute_vpin(trades: pd.DataFrame, n_buckets: int = 50) -> float:
    """VPIN over the most recent ``n_buckets`` volume buckets.

    ``trades`` columns: ``price``, ``qty``, ``is_buyer_maker``. ``is_buyer_maker``
    True means the taker was a seller (aggressive sell). VPIN = mean(|buy_vol −
    sell_vol|) / bucket_size.
    """
    if len(trades) == 0:
        return 0.0
    total_vol = float(trades["qty"].sum())
    bucket_size = total_vol / max(n_buckets, 1)
    if bucket_size <= 0:
        return 0.0

    imbalances = []
    for bucket in volume_buckets(trades, bucket_size):
        sell_vol = float(bucket.loc[bucket["is_buyer_maker"], "qty"].sum())
        buy_vol = float(bucket.loc[~bucket["is_buyer_maker"], "qty"].sum())
        imbalances.append(abs(buy_vol - sell_vol))
    if not imbalances:
        return 0.0
    return float(np.mean(imbalances) / bucket_size)


def build_daily_microstructure_features(
    trades: pd.DataFrame,
    as_of: pd.Timestamp,
    bucket_count: int = 50,
    z_window: int = 30,
    weekly_window: int = 7,
) -> pd.DataFrame:
    """Aggregate tick-level ``trades`` into daily microstructure features.

    Columns produced:
      - ``vpin_50``         : VPIN over rolling daily window of trades
      - ``vpin_50_z``       : ``z_window``-day Z-score of VPIN
      - ``ofi_d``           : daily order flow imbalance
      - ``ofi_d_w``         : ``weekly_window``-day volume-weighted OFI
      - ``aggressor_ratio`` : share of taker-buy trades

    Look-ahead guard: input is sliced to ``trades.index <= as_of`` first.
    """
    if not isinstance(as_of, pd.Timestamp):
        raise TypeError("as_of must be a pandas Timestamp")

    trades = trades[trades.index <= as_of].copy()
    if trades.empty:
        return pd.DataFrame(
            columns=["vpin_50", "vpin_50_z", "ofi_d", "ofi_d_w", "aggressor_ratio"]
        )

    trades["date"] = trades.index.tz_convert("UTC").floor("D")
    daily_groups = trades.groupby("date")

    rows: list[dict[str, float]] = []
    for date, group in daily_groups:
        sell_vol = float(group.loc[group["is_buyer_maker"], "qty"].sum())
        buy_vol = float(group.loc[~group["is_buyer_maker"], "qty"].sum())
        total = sell_vol + buy_vol
        ofi = (buy_vol - sell_vol) / total if total > 0 else 0.0
        aggressor = buy_vol / total if total > 0 else 0.0
        vpin = compute_vpin(group, n_buckets=bucket_count)
        rows.append(
            {
                "date": date,
                "vpin_50": vpin,
                "ofi_d": ofi,
                "aggressor_ratio": aggressor,
                "_buy_vol": buy_vol,
                "_sell_vol": sell_vol,
            }
        )

    df = pd.DataFrame(rows).set_index("date").sort_index()
    df["vpin_50_z"] = (
        (df["vpin_50"] - df["vpin_50"].rolling(z_window).mean())
        / df["vpin_50"].rolling(z_window).std()
    )
    weekly_buy = df["_buy_vol"].rolling(weekly_window).sum()
    weekly_sell = df["_sell_vol"].rolling(weekly_window).sum()
    df["ofi_d_w"] = (weekly_buy - weekly_sell) / (weekly_buy + weekly_sell).replace(
        0.0, np.nan
    )
    df = df.drop(columns=["_buy_vol", "_sell_vol"])
    return df[["vpin_50", "vpin_50_z", "ofi_d", "ofi_d_w", "aggressor_ratio"]]


import logging
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

_BINANCE_AGGTRADES_URL = "https://api.binance.com/api/v3/aggTrades"


class RateLimitError(RuntimeError):
    pass


def _fetch_one_day(symbol: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """Pull one day of aggTrades. Paginates 1000 trades at a time."""
    rows: list[dict] = []
    cursor = start_ms
    while cursor < end_ms:
        resp = requests.get(
            _BINANCE_AGGTRADES_URL,
            params={
                "symbol": symbol,
                "startTime": cursor,
                "endTime": min(cursor + 60 * 60 * 1000, end_ms),
                "limit": 1000,
            },
            timeout=10,
        )
        if resp.status_code == 429:
            raise RateLimitError("Binance 429 rate limit")
        resp.raise_for_status()
        data = resp.json()
        if not data:
            cursor += 60 * 60 * 1000
            continue
        for d in data:
            rows.append(
                {
                    "ts": pd.Timestamp(d["T"], unit="ms", tz="UTC"),
                    "price": float(d["p"]),
                    "qty": float(d["q"]),
                    "is_buyer_maker": bool(d["m"]),
                }
            )
        last_ts = data[-1]["T"]
        cursor = last_ts + 1
    if not rows:
        return pd.DataFrame(columns=["price", "qty", "is_buyer_maker"])
    df = pd.DataFrame(rows).set_index("ts").sort_index()
    return df


def fetch_aggtrades(
    symbol: str,
    date: pd.Timestamp,
    cache_dir: Path,
    max_retries: int = 5,
    base_backoff: float = 1.0,
    max_backoff: float = 60.0,
) -> pd.DataFrame:
    """Fetch one day of Binance aggTrades, cached to parquet on disk.

    On 429, retries with exponential backoff up to ``max_retries`` times.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    day_str = date.strftime("%Y-%m-%d")
    cache_file = cache_dir / f"{symbol}_{day_str}.parquet"
    if cache_file.exists():
        return pd.read_parquet(cache_file)

    start_ms = int(date.normalize().timestamp() * 1000)
    end_ms = start_ms + 24 * 60 * 60 * 1000

    for attempt in range(max_retries):
        try:
            df = _fetch_one_day(symbol, start_ms, end_ms)
            df.to_parquet(cache_file)
            return df
        except RateLimitError:
            wait = min(base_backoff * (2**attempt), max_backoff)
            logger.warning("Binance 429, sleeping %.1fs", wait)
            time.sleep(wait)
    raise RateLimitError(f"Failed after {max_retries} retries for {symbol} {day_str}")
