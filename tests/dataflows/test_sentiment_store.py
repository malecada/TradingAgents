"""Unit tests for tradingagents.dataflows.sentiment_store."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from tradingagents.dataflows import sentiment_store


def _row(ts: datetime, article_id: int, symbols: str = "BTCUSD",
         headline: str = "Example", content: str = "", source: str = "Benzinga") -> dict:
    return {
        "event_ts": ts,
        "as_of_ts": ts,
        "id": article_id,
        "headline": headline,
        "content": content,
        "summary": "",
        "symbols": symbols,
        "source": source,
        "author": "",
        "url": f"https://example.com/{article_id}",
    }


def test_roundtrip_single_month(tmp_path):
    """Ingest 3 rows, query the window containing them, get them back."""
    base = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
    rows = pd.DataFrame([
        _row(base.replace(day=10), 1, headline="Article 1"),
        _row(base.replace(day=15), 2, headline="Article 2"),
        _row(base.replace(day=20), 3, headline="Article 3"),
    ])

    sentiment_store.upsert_alpaca_rows(rows, year=2024, month=1, root=tmp_path)

    out = sentiment_store.query_news(
        coin="bitcoin",
        ts_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ts_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
        as_of=datetime(2024, 2, 1, tzinfo=timezone.utc),
        root=tmp_path,
    )
    assert len(out) == 3
    assert sorted(out["headline"].tolist()) == ["Article 1", "Article 2", "Article 3"]


def test_pit_filter_excludes_future_observations(tmp_path):
    """A row whose event_ts is before as_of but whose as_of_ts is AFTER
    must be excluded — this is the PIT rule."""
    rows = pd.DataFrame([
        # event ts in Jan; observed in Jan (visible at Feb 1)
        _row(datetime(2024, 1, 10, tzinfo=timezone.utc), 1, headline="Known early"),
        # event ts in Jan but only entered the store in March (NOT visible at Feb 1)
        {
            "event_ts": datetime(2024, 1, 25, tzinfo=timezone.utc),
            "as_of_ts": datetime(2024, 3, 5, tzinfo=timezone.utc),
            "id": 2, "headline": "Late ingest", "content": "",
            "summary": "", "symbols": "BTCUSD", "source": "x", "author": "", "url": "",
        },
    ])
    sentiment_store.upsert_alpaca_rows(rows, year=2024, month=1, root=tmp_path)

    out = sentiment_store.query_news(
        coin="bitcoin",
        ts_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ts_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
        as_of=datetime(2024, 2, 1, tzinfo=timezone.utc),
        root=tmp_path,
    )
    ids = out["id"].tolist()
    assert 1 in ids, "row observed before as_of should be visible"
    assert 2 not in ids, "row ingested after as_of must be filtered out"


def test_symbol_filter_isolates_coin(tmp_path):
    """bitcoin query must not return rows tagged only with ETHUSD."""
    rows = pd.DataFrame([
        _row(datetime(2024, 1, 10, tzinfo=timezone.utc), 1, symbols="BTCUSD"),
        _row(datetime(2024, 1, 11, tzinfo=timezone.utc), 2, symbols="ETHUSD"),
        _row(datetime(2024, 1, 12, tzinfo=timezone.utc), 3, symbols="BTCUSD,ETHUSD"),
        _row(datetime(2024, 1, 13, tzinfo=timezone.utc), 4, symbols="SOLUSD"),
    ])
    sentiment_store.upsert_alpaca_rows(rows, year=2024, month=1, root=tmp_path)

    btc = sentiment_store.query_news(
        coin="bitcoin",
        ts_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ts_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
        as_of=datetime(2024, 2, 1, tzinfo=timezone.utc),
        root=tmp_path,
    )
    assert sorted(btc["id"].tolist()) == [1, 3]

    eth = sentiment_store.query_news(
        coin="ethereum",
        ts_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ts_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
        as_of=datetime(2024, 2, 1, tzinfo=timezone.utc),
        root=tmp_path,
    )
    assert sorted(eth["id"].tolist()) == [2, 3]
