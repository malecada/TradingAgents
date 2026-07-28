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


def test_merge_tail_dedups_new_against_itself_when_existing_is_none():
    # Finding 3: the empty-existing early-return must still dedup+sort `new` -- it must
    # not be passed through unconditionally just because there's nothing to merge it with.
    a = _df(10, 1.0)
    b = _df(10, 2.0)  # same index as `a`, different values
    new = pd.concat([a, b])  # internally duplicated, and out of a naive-append order
    out = fetch1h.merge_tail(None, new)
    assert out.index.is_monotonic_increasing and out.index.is_unique
    assert len(out) == 10
    assert (out["close"] == 2.0).all()  # keep-last wins within `new` itself


def test_merge_tail_empty_existing_df_also_dedups():
    empty = _df(0, 0.0)  # existing is an empty (but non-None) DataFrame
    a = _df(5, 1.0)
    b = _df(5, 2.0)
    new = pd.concat([a, b])
    out = fetch1h.merge_tail(empty, new)
    assert out.index.is_unique
    assert len(out) == 5
    assert (out["close"] == 2.0).all()


# --- Finding 1: a Vision month that fails for an unknown reason (not a confirmed 404)
# must never be silently skipped just because later months already have data. ---

def test_month_needs_fetch_retries_a_failed_month_even_if_later_months_are_covered():
    # Simulates: 2021-03 fetch failed with a transient 503 (not confirmed 404, no bars
    # exist for it), but 2021-04 succeeded and is present in `existing`. The old buggy
    # logic inferred coverage from a single max-timestamp watermark and would have
    # skipped 2021-03 forever. month_needs_fetch must not do that.
    existing = _df(24, 1.0)
    existing.index = pd.date_range("2021-04-01", periods=24, freq="1h", tz="UTC", name="ts")
    failed_month = pd.Period("2021-03", freq="M")
    assert fetch1h.month_needs_fetch(failed_month, existing, confirmed_missing=set()) is True


def test_month_needs_fetch_skips_confirmed_missing_month():
    existing = _df(24, 1.0)
    existing.index = pd.date_range("2021-04-01", periods=24, freq="1h", tz="UTC", name="ts")
    not_listed_month = pd.Period("2019-09", freq="M")
    assert fetch1h.month_needs_fetch(
        not_listed_month, existing, confirmed_missing={not_listed_month}) is False


def test_month_needs_fetch_skips_month_already_covered_by_data():
    existing = _df(24, 1.0)
    existing.index = pd.date_range("2021-04-01", periods=24, freq="1h", tz="UTC", name="ts")
    covered_month = pd.Period("2021-04", freq="M")
    assert fetch1h.month_needs_fetch(covered_month, existing, confirmed_missing=set()) is False


def test_month_needs_fetch_true_when_no_existing_data():
    month = pd.Period("2021-04", freq="M")
    assert fetch1h.month_needs_fetch(month, None, confirmed_missing=set()) is True
