"""Bitemporal sentiment store backed by Parquet + DuckDB.

Layout: data/sentiment/alpaca/{year}/{month:02d}.parquet.
Every row has (event_ts, as_of_ts) so backtests can enforce
as_of_ts <= trade_date to avoid look-ahead bias.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd

from .vintages import (with_availability, merge_vintages, write_preserving_vintage,
                       parquet_view, require_known_availability)

DEFAULT_ROOT = Path("data/sentiment/alpaca")

COIN_TO_SYMBOL: dict[str, str] = {
    "bitcoin": "BTCUSD",
    "ethereum": "ETHUSD",
    "binancecoin": "BNBUSD",
    "solana": "SOLUSD",
    "dogecoin": "DOGEUSD",
    "cardano": "ADAUSD",
}

SCHEMA_COLS = [
    "event_ts", "as_of_ts", "id", "headline", "content",
    "summary", "symbols", "source", "author", "url",
]


def _month_path(root: Path, year: int, month: int) -> Path:
    return Path(root) / str(year) / f"{month:02d}.parquet"


def upsert_alpaca_rows(df: pd.DataFrame, year: int, month: int,
                       root: Path = DEFAULT_ROOT) -> int:
    """Preserve distinct retrieval versions; reject conflicting same-key contents."""
    if df.empty:
        return 0
    missing = set(SCHEMA_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"upsert missing columns: {sorted(missing)}")
    target = _month_path(root, year, month)
    incoming = with_availability(df)
    existing = pd.read_parquet(target) if target.exists() else incoming.iloc[:0]
    combined = merge_vintages(existing, incoming, ["id", "as_of_ts"])
    write_preserving_vintage(combined, target)
    return len(combined)


def query_news(coin: str, ts_start: datetime, ts_end: datetime,
               as_of: datetime, limit: int = 50,
               root: Path = DEFAULT_ROOT, strict_pit: bool = True,
               all_vintages: bool = False) -> pd.DataFrame:
    """Return rows where event_ts in [ts_start, ts_end] AND as_of_ts <= as_of,
    filtered to the coin's symbol, latest eligible version per article.
    all_vintages=True exposes preserved history for explicit diagnostics."""
    symbol = COIN_TO_SYMBOL.get(coin.lower())
    if symbol is None:
        raise ValueError(f"Unsupported coin for sentiment store: {coin!r}")
    glob = f"{root}/*/*.parquet"
    con = duckdb.connect(":memory:")
    try:
        try:
            parquet_view(con, "news", glob)
        except duckdb.IOException:
            return pd.DataFrame(columns=SCHEMA_COLS)
        vintage_filter = "" if all_vintages else (
            "QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY as_of_ts DESC) = 1"
        )
        sql = f"""
        SELECT event_ts, as_of_ts, id, headline, content, summary,
               symbols, source, author, url, availability_basis
        FROM news
        WHERE event_ts BETWEEN ? AND ?
          AND as_of_ts <= ?
          AND list_contains(string_split(symbols, ','), ?)
        {vintage_filter}
        ORDER BY event_ts DESC, id ASC
        LIMIT ?
        """
        return require_known_availability(con.execute(
            sql,
            [ts_start, ts_end, as_of, symbol, limit],
        ).fetchdf(), strict_pit)
    finally:
        con.close()
