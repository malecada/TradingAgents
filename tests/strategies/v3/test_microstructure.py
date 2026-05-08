from __future__ import annotations

import pandas as pd

from tradingagents.strategies.v3.features.microstructure import (
    compute_vpin,
    volume_buckets,
)


def test_volume_buckets_split_correctly():
    trades = pd.DataFrame(
        {
            "price": [100.0] * 10,
            "qty": [1.0] * 10,
            "is_buyer_maker": [True, False] * 5,
        },
        index=pd.date_range("2026-01-01", periods=10, freq="min", tz="UTC"),
    )
    buckets = list(volume_buckets(trades, bucket_size=2.5))
    assert len(buckets) == 4
    for b in buckets:
        assert abs(b["qty"].sum() - 2.5) < 1e-6


def test_vpin_zero_when_balanced():
    trades = pd.DataFrame(
        {
            "price": [100.0] * 100,
            "qty": [1.0] * 100,
            "is_buyer_maker": [True, False] * 50,
        },
        index=pd.date_range("2026-01-01", periods=100, freq="min", tz="UTC"),
    )
    vpin = compute_vpin(trades, n_buckets=10)
    assert vpin < 0.05


def test_vpin_high_when_imbalanced():
    trades = pd.DataFrame(
        {
            "price": [100.0] * 100,
            "qty": [1.0] * 100,
            "is_buyer_maker": [True] * 100,  # all sells
        },
        index=pd.date_range("2026-01-01", periods=100, freq="min", tz="UTC"),
    )
    vpin = compute_vpin(trades, n_buckets=10)
    assert vpin > 0.9
