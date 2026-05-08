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
