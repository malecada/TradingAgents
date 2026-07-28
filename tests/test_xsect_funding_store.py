import pandas as pd

from scripts.fetch_xsect_funding import manifest_entry, merge_prints


def _rows(ts_rates):
    return [{"symbol": "XUSDT", "fundingTime": int(pd.Timestamp(t, tz="UTC").timestamp() * 1000),
             "fundingRate": str(r), "markPrice": "1.0"} for t, r in ts_rates]


def test_merge_prints_from_empty_sorts_and_types():
    df = merge_prints(None, _rows([("2024-01-02 08:00", 1e-4), ("2024-01-02 00:00", 2e-4)]))
    assert list(df.columns) == ["fundingRate"]
    assert df.index.tz is not None and df.index.is_monotonic_increasing
    assert df["fundingRate"].dtype == float and len(df) == 2


def test_merge_prints_tail_append_dedupes():
    base = merge_prints(None, _rows([("2024-01-02 00:00", 2e-4)]))
    out = merge_prints(base, _rows([("2024-01-02 00:00", 2e-4), ("2024-01-02 08:00", 1e-4)]))
    assert len(out) == 2  # overlap deduped on timestamp
    # idempotent: re-append same rows changes nothing
    again = merge_prints(out, _rows([("2024-01-02 08:00", 1e-4)]))
    assert again.equals(out)


def test_manifest_entry_fields():
    df = merge_prints(None, _rows([("2024-01-02 00:00", 2e-4), ("2024-01-03 00:00", 1e-4)]))
    e = manifest_entry(df)
    assert e["rows"] == 2
    assert e["first"].startswith("2024-01-02") and e["last"].startswith("2024-01-03")
