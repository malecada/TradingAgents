"""Bitemporal on-chain metric store (Parquet + DuckDB).

Long-format storage so heterogeneous sources (CoinMetrics, DefiLlama,
beaconcha.in, mempool.space) coexist in one layout. Every row carries
(event_ts, as_of_ts) so backtests can enforce as_of_ts <= trade_date
to avoid look-ahead bias.

Layout: data/onchain/{year}/{month:02d}.parquet.
Schema:
  event_ts      timestamp   UTC day or intraday event time
  as_of_ts      timestamp   when the value became available to a PIT caller
  coin          string      lowercase symbol (btc, eth, bnb)
  metric        string      source-namespaced metric name (e.g. cm.CapMVRVCur)
  value         double
  source        string      vendor tag (coinmetrics_community, defillama, ...)
  status        string      "final" | "flash" (CM flash = revisable)
"""
from __future__ import annotations

import os as _os
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import duckdb
import pandas as pd

from .vintages import (with_availability, merge_vintages, write_preserving_vintage,
                       parquet_view, require_known_availability)

_DATA_ROOT_ENV = _os.environ.get("TRADINGAGENTS_DATA_ROOT", "data")
DEFAULT_ROOT = Path(_DATA_ROOT_ENV) / "onchain"

SCHEMA_COLS = [
    "event_ts", "as_of_ts", "coin", "metric", "value", "source", "status",
]

DEDUPE_KEYS = ["event_ts", "coin", "metric", "source", "as_of_ts"]


def _month_path(root: Path, year: int, month: int) -> Path:
    return Path(root) / str(year) / f"{month:02d}.parquet"


def upsert_rows(df: pd.DataFrame, root: Path = DEFAULT_ROOT) -> int:
    """Write rows to monthly Parquet shards keyed by event_ts month.

    Dedupes on (event_ts, coin, metric, source, as_of_ts). Returns
    total rows written across all touched months.
    """
    if df.empty:
        return 0
    missing = set(SCHEMA_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"upsert missing columns: {sorted(missing)}")
    df = with_availability(df)
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    df["as_of_ts"] = pd.to_datetime(df["as_of_ts"], utc=True)
    df["_year"] = df["event_ts"].dt.year
    df["_month"] = df["event_ts"].dt.month
    total_written = 0
    for (year, month), chunk in df.groupby(["_year", "_month"], sort=False):
        target = _month_path(root, int(year), int(month))
        body = chunk.drop(columns=["_year", "_month"])
        existing = pd.read_parquet(target) if target.exists() else body.iloc[:0]
        combined = merge_vintages(existing, body, DEDUPE_KEYS)
        write_preserving_vintage(combined, target)
        total_written += len(combined)
    return total_written


def query_metrics(
    coin: str,
    ts_start: datetime,
    ts_end: datetime,
    as_of: datetime,
    metrics: Optional[Iterable[str]] = None,
    root: Path = DEFAULT_ROOT,
    strict_pit: bool = True,
    all_vintages: bool = False,
) -> pd.DataFrame:
    """Return rows where event_ts in [ts_start, ts_end] AND as_of_ts <= as_of,
    filtered to the given coin. Enforces the PIT rule.

    If `metrics` is None, returns every metric available for the coin.
    Output is the latest eligible vintage per event/coin/metric/source.
    all_vintages=True exposes preserved history for explicit diagnostics.
    """
    glob = f"{root}/*/*.parquet"
    con = duckdb.connect(":memory:")
    try:
        try:
            parquet_view(con, "onchain", glob)
        except duckdb.IOException:
            return pd.DataFrame(columns=SCHEMA_COLS)
        sql = """
        SELECT event_ts, as_of_ts, coin, metric, value, source, status, availability_basis
        FROM onchain
        WHERE coin = ?
          AND event_ts BETWEEN ? AND ?
          AND as_of_ts <= ?
        """
        args: list = [coin.lower(), ts_start, ts_end, as_of]
        if metrics is not None:
            metric_list = list(metrics)
            placeholders = ",".join(["?"] * len(metric_list))
            sql += f" AND metric IN ({placeholders})"
            args.extend(metric_list)
        if not all_vintages:
            sql += (" QUALIFY ROW_NUMBER() OVER (PARTITION BY event_ts, coin, metric, source "
                    "ORDER BY as_of_ts DESC) = 1")
        sql += " ORDER BY event_ts ASC, metric ASC"
        return require_known_availability(con.execute(sql, args).fetchdf(), strict_pit)
    finally:
        con.close()


def latest_snapshot(
    coin: str,
    as_of: datetime,
    metrics: Optional[Iterable[str]] = None,
    root: Path = DEFAULT_ROOT,
    strict_pit: bool = True,
) -> pd.DataFrame:
    """Return the most recent PIT-valid row per metric for `coin` as of `as_of`.

    One row per metric with its latest value, event time, source, and status.
    """
    glob = f"{root}/*/*.parquet"
    con = duckdb.connect(":memory:")
    try:
        try:
            parquet_view(con, "onchain", glob)
        except duckdb.IOException:
            return pd.DataFrame(columns=["metric", "event_ts", "value", "source", "status"])
        sql = """
        WITH filtered AS (
            SELECT *
            FROM onchain
            WHERE coin = ? AND as_of_ts <= ?
        ),
        ranked AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY metric
                       ORDER BY event_ts DESC, as_of_ts DESC
                   ) AS rk
            FROM filtered
        )
        SELECT metric, event_ts, value, source, status, availability_basis
        FROM ranked
        WHERE rk = 1
        """
        args: list = [coin.lower(), as_of]
        if metrics is not None:
            metric_list = list(metrics)
            placeholders = ",".join(["?"] * len(metric_list))
            sql += f" AND metric IN ({placeholders})"
            args.extend(metric_list)
        sql += " ORDER BY metric ASC"
        return require_known_availability(con.execute(sql, args).fetchdf(), strict_pit)
    finally:
        con.close()
