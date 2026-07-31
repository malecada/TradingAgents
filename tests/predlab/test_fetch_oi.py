from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from predlab_fetch_oi_5m import day_needs_fetch, day_zip_url, merge_days, parse_csv  # noqa: E402


def test_day_zip_url():
    assert day_zip_url("BTCUSDT", pd.Timestamp("2021-06-15")) == (
        "https://data.binance.vision/data/futures/um/daily/metrics/"
        "BTCUSDT/BTCUSDT-metrics-2021-06-15.zip"
    )


def test_parse_csv_schema_and_ts():
    raw = (
        "create_time,symbol,sum_open_interest,sum_open_interest_value,"
        "count_toptrader_long_short_ratio,sum_toptrader_long_short_ratio,"
        "count_long_short_ratio,sum_taker_long_short_vol_ratio\n"
        "2021-06-15 00:00:00,BTCUSDT,49644.993,2010191510.02,1.11,1.104,1.092,0.7196\n"
        "2021-06-15 00:05:00,BTCUSDT,49700.761,2002442914.25,1.10,1.104,1.078,0.9077\n"
    )
    df = parse_csv(raw)
    assert list(df.columns) == [
        "oi", "oi_value", "top_ls_accounts", "top_ls_positions", "ls_accounts",
        "taker_ls_vol",
    ]
    assert df.index.tz is not None and str(df.index[0]) == "2021-06-15 00:00:00+00:00"
    assert float(df["oi"].iloc[1]) == 49700.761


def test_merge_days_dedup_new_wins():
    idx1 = pd.date_range("2021-06-15", periods=3, freq="5min", tz="UTC")
    idx2 = pd.date_range("2021-06-15 00:10:00", periods=3, freq="5min", tz="UTC")
    a = pd.DataFrame({"oi": [1.0, 2.0, 3.0]}, index=idx1)
    b = pd.DataFrame({"oi": [30.0, 4.0, 5.0]}, index=idx2)
    out = merge_days(a, b)
    assert len(out) == 5
    assert out["oi"].loc[idx2[0]] == 30.0  # new wins on overlap


def test_day_needs_fetch_semantics():
    day = pd.Timestamp("2021-06-15")
    idx = pd.date_range("2021-06-15", periods=288, freq="5min", tz="UTC")
    existing = pd.DataFrame({"oi": 1.0}, index=idx)
    assert not day_needs_fetch(day, existing, set())
    assert day_needs_fetch(pd.Timestamp("2021-06-16"), existing, set())
    assert not day_needs_fetch(pd.Timestamp("2021-06-16"), existing,
                               {pd.Timestamp("2021-06-16")})
    assert day_needs_fetch(day, None, set())
