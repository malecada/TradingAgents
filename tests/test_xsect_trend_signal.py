"""Parity + shape tests for the frozen trend vote (verbatim from metalabel primary)."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.trend_signal import WARMUP, compute_votes

FIXTURE = Path(__file__).parent / "fixtures" / "trend_votes_btc.csv"
KLINES = Path(__file__).parents[1] / "data" / "xsect" / "klines"


def test_parity_with_metalabel_primary():
    fix = pd.read_csv(FIXTURE, parse_dates=["date"])
    close = pd.read_parquet(KLINES / "BTCUSDT.parquet").loc["2020-06-01":"2022-06-01", "close"]
    votes = compute_votes(close)
    assert len(votes) == len(fix)
    np.testing.assert_allclose(
        votes.values, fix["vote"].values, rtol=0, atol=1e-12, equal_nan=True
    )


def test_warmup_is_nan():
    idx = pd.date_range("2021-01-01", periods=120, freq="D", tz="UTC")
    close = pd.Series(np.linspace(100, 200, 120), index=idx)
    votes = compute_votes(close)
    assert votes.iloc[: WARMUP - 1].isna().all()
    assert votes.iloc[WARMUP:].notna().all()


def test_uptrend_votes_high_downtrend_low():
    idx = pd.date_range("2021-01-01", periods=200, freq="D", tz="UTC")
    up = pd.Series(np.linspace(100, 400, 200), index=idx)
    down = pd.Series(np.linspace(400, 100, 200), index=idx)
    assert compute_votes(up).iloc[-1] == 1.0
    assert compute_votes(down).iloc[-1] == 0.0
