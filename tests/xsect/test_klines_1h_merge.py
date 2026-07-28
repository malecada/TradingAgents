import pandas as pd
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "fetch1h", Path(__file__).parents[2] / "scripts" / "fetch_xsect_klines_1h.py")
fetch1h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch1h)


def _df(hours, val):
    idx = pd.date_range("2024-01-01", periods=hours, freq="1h", tz="UTC", name="ts")
    return pd.DataFrame({c: float(val) for c in
        ["open", "high", "low", "close", "volume", "quote_volume",
         "taker_buy_quote_volume"]}, index=idx)


def test_merge_tail_dedups_keep_last_sorted():
    old = _df(48, 1.0)
    new = _df(24, 2.0).shift(freq="36h")  # overlaps last 12 bars of old
    out = fetch1h.merge_tail(old, new)
    assert out.index.is_monotonic_increasing and out.index.is_unique
    assert len(out) == 60
    assert out.loc["2024-01-02 12:00", "close"].item() == 2.0  # new wins overlap


def test_merge_tail_none_existing():
    new = _df(5, 3.0)
    assert fetch1h.merge_tail(None, new).equals(new)
