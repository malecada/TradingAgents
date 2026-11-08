"""Dossier core: universe symbols, bitemporal store semantics, URL canonicalization, row building."""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.dossier import store  # noqa: E402
from tradingagents.dossier.reddit import to_store_rows  # noqa: E402
from tradingagents.dossier.universe import base_symbol, weekly_top  # noqa: E402
from tradingagents.dossier.wayback import Fetched, canonical_url, date_from_url, to_store_row  # noqa: E402


def test_base_symbol():
    assert [base_symbol(s) for s in ("BTCUSDT", "1000PEPEUSDT", "1000000MOGUSDT", "1MBABYDOGEUSDT", "ETHUSDC")] \
        == ["BTC", "PEPE", "MOG", "BABYDOGE", "ETH"]


def test_weekly_top_ranks_by_volume_within_date():
    cards = pd.DataFrame({"date": pd.to_datetime(["2024-01-05"] * 3 + ["2024-01-12"] * 3, utc=True),
                          "symbol": ["AUSDT", "BUSDT", "CUSDT"] * 2,
                          "dvol_30d": [1.0, 3.0, 2.0, 5.0, None, 4.0]})
    top = weekly_top(cards, n=2)
    assert top[top["date"] == "2024-01-05"]["symbol"].tolist() == ["BUSDT", "CUSDT"]
    assert top[top["date"] == "2024-01-12"]["symbol"].tolist() == ["AUSDT", "CUSDT"]
    assert top["vol_rank"].tolist() == [1, 2, 1, 2]


def test_store_keeps_earliest_capture_and_filters_pit(tmp_path):
    rows = pd.DataFrame([
        {"doc_id": "a", "event_ts": "2024-01-02", "as_of_ts": "2024-01-03T10:00", "source": "wayback",
         "outlet": "coindesk", "url": "u", "title": "t", "body": "b", "lang": "en", "author": "", "extra": "{}"},
        {"doc_id": "a", "event_ts": "2024-01-02", "as_of_ts": "2024-01-02T12:00", "source": "wayback",
         "outlet": "coindesk", "url": "u", "title": "t", "body": "b", "lang": "en", "author": "", "extra": "{}"},
        {"doc_id": "b", "event_ts": "2024-01-20", "as_of_ts": "2024-01-20", "source": "wayback",
         "outlet": "coindesk", "url": "v", "title": "t2", "body": "b2", "lang": "en", "author": "", "extra": "{}"},
    ])
    store.upsert(rows, root=tmp_path)
    got = store.query("2024-01-01", "2024-01-31", as_of="2024-01-02T13:00", root=tmp_path)
    assert got["doc_id"].tolist() == ["a"]
    assert got["as_of_ts"].iloc[0] == pd.Timestamp("2024-01-02T12:00", tz="UTC")
    got = store.query("2024-01-01", "2024-01-31", as_of="2024-02-01", root=tmp_path)
    assert got["doc_id"].tolist() == ["a", "b"]
    bad = rows.iloc[[0]].assign(as_of_ts="2023-12-01")
    with pytest.raises(ValueError):
        store.upsert(bad, root=tmp_path)


def test_canonical_url_and_dates():
    u = canonical_url("http://coindesk.com/Markets/2024/01/02/Bitcoin-Begins/amp?utm=x")
    assert u == "https://www.coindesk.com/markets/2024/01/02/bitcoin-begins/"
    assert canonical_url("https://www.cointelegraph.com/news/foo") == "https://cointelegraph.com/news/foo/"
    assert date_from_url(u) == "2024-01-02" and date_from_url("https://cointelegraph.com/news/foo/") is None


def test_to_store_row_rules():
    f = Fetched("https://www.coindesk.com/markets/2024/01/02/x/", pd.Timestamp("2024-01-02T05:00", tz="UTC"),
                200, "T", None, "A", "x" * 300)
    row = to_store_row("coindesk", f)
    assert row["event_ts"] == pd.Timestamp("2024-01-02", tz="UTC") and row["source"] == "wayback"
    assert to_store_row("coindesk", Fetched("u", f.capture_ts, 404, None, None, None, None)) is None
    assert to_store_row("coindesk", Fetched("u", f.capture_ts, 200, "T", None, None, "short")) is None
    late = Fetched("https://cointelegraph.com/news/x/", f.capture_ts, 200, "T", "2024-03-01", None, "y" * 300)
    assert to_store_row("cointelegraph", late)["event_ts"] == f.capture_ts


def test_reddit_rows_strip_removed_bodies():
    posts = pd.DataFrame({"id": ["p1", "p2"], "created_utc": [1704153305, 1704153400], "title": ["a", "b"],
                          "selftext": ["[removed]", "hello"], "score": [3, None], "num_comments": [1, 2],
                          "author": ["x", "y"], "link_flair_text": [None, "DISCUSSION"],
                          "subreddit": ["CryptoCurrency", "CryptoCurrency"]})
    rows = to_store_rows(posts)
    assert rows["body"].tolist() == ["", "hello"] and rows["outlet"].iloc[0] == "cryptocurrency"
    assert (rows["as_of_ts"] == rows["event_ts"]).all()
