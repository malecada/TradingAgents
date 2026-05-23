from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import pytest

from tradingagents.dataflows import gtrends_store


def _utc(y, m, d, h=0):
    return datetime(y, m, d, h, tzinfo=timezone.utc)


def test_write_then_query_returns_rows(tmp_path):
    root = tmp_path / "gtrends"
    df = pd.DataFrame([
        {"coin": "bitcoin", "query": "bitcoin",
         "event_ts": _utc(2026, 1, 1), "as_of_ts": _utc(2026, 1, 2),
         "value": 70.0, "value_z90": 0.5, "value_z365": 0.3},
        {"coin": "bitcoin", "query": "bitcoin",
         "event_ts": _utc(2026, 1, 2), "as_of_ts": _utc(2026, 1, 3),
         "value": 80.0, "value_z90": 0.8, "value_z365": 0.6},
    ])
    gtrends_store.write_rows(df, root=root)
    out = gtrends_store.query_attention(
        coin="bitcoin", trade_date=_utc(2026, 1, 5),
        lookback_days=30, root=root,
    )
    assert len(out) == 2


def test_query_enforces_24h_embargo(tmp_path):
    root = tmp_path / "gtrends"
    df = pd.DataFrame([
        {"coin": "bitcoin", "query": "bitcoin",
         "event_ts": _utc(2026, 1, 1), "as_of_ts": _utc(2026, 1, 4, 12),
         "value": 70.0, "value_z90": 0.5, "value_z365": 0.3},
    ])
    gtrends_store.write_rows(df, root=root)
    # trade_date = Jan 5, embargo = 24h, cutoff = Jan 4 00:00.
    # Row's as_of = Jan 4 12:00 → AFTER cutoff → must be excluded.
    out = gtrends_store.query_attention(
        coin="bitcoin", trade_date=_utc(2026, 1, 5),
        lookback_days=30, root=root,
    )
    assert out.empty


def test_query_returns_empty_when_path_missing(tmp_path):
    out = gtrends_store.query_attention(
        coin="bitcoin", trade_date=_utc(2026, 1, 5),
        lookback_days=30, root=tmp_path / "missing",
    )
    assert out.empty
