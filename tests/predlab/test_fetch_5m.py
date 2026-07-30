from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import predlab_fetch_klines_5m as f5  # noqa: E402


def _df(ts_list, close_list):
    idx = pd.DatetimeIndex(pd.to_datetime(ts_list, unit="ms", utc=True), name="ts")
    return pd.DataFrame({"close": close_list}, index=idx)


def test_month_zip_url():
    assert f5.month_zip_url("BTCUSDT", "2021-03") == (
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        "BTCUSDT/5m/BTCUSDT-5m-2021-03.zip"
    )
    assert f5.month_zip_url("ETHUSDT", pd.Period("2020-01", freq="M")) == (
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        "ETHUSDT/5m/ETHUSDT-5m-2020-01.zip"
    )


def test_merge_tail_idempotent_new_wins_sorted():
    old = _df([0, 300000], [1.0, 2.0])
    new = _df([300000, 600000], [2.5, 3.0])
    out = f5.merge_tail(old, new)
    assert list(out.index.view("int64") // 10**6) == [0, 300000, 600000]
    assert out.loc[out.index[1], "close"] == 2.5  # new wins on overlap
    again = f5.merge_tail(out, new)
    assert len(again) == 3


def test_merge_tail_none_existing_still_dedups():
    new = _df([0, 0, 300000], [1.0, 9.0, 2.0])
    out = f5.merge_tail(None, new)
    assert len(out) == 2 and out.iloc[0]["close"] == 9.0  # keep-last


def test_month_needs_fetch_semantics():
    month = pd.Period("2021-02", freq="M")
    # confirmed 404 -> never refetch
    assert not f5.month_needs_fetch(month, None, {month})
    # no data at all, not confirmed-missing -> fetch (incl. failed-last-run months)
    assert f5.month_needs_fetch(month, None, set())
    # data present inside the month -> covered
    inside = _df([int(pd.Timestamp("2021-02-10", tz="UTC").timestamp() * 1000)], [1.0])
    assert not f5.month_needs_fetch(month, inside, set())
    # data only in other months -> still needs fetch
    outside = _df([int(pd.Timestamp("2021-03-10", tz="UTC").timestamp() * 1000)], [1.0])
    assert f5.month_needs_fetch(month, outside, set())


def test_out_columns_keep_taker_and_trades():
    assert "taker_buy_quote_volume" in f5.OUT_COLUMNS
    assert "n_trades" in f5.OUT_COLUMNS
    assert f5.INTERVAL == "5m"
    assert f5.INTERVAL_MS == 300_000
