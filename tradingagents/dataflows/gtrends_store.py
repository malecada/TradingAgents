"""Bitemporal Google Trends store.

Schema (parquet, one file per (coin, as_of_date)):
    coin: str
    query: str
    event_ts: datetime64[ns, UTC]
    as_of_ts: datetime64[ns, UTC]
    value: float
    value_z90: float
    value_z365: float

PIT discipline: queries enforce as_of_ts < trade_date - embargo (default 24h)
to defend against Google Trends mid-window renormalization.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

DEFAULT_ROOT = Path("data/sentiment/gtrends")
SCHEMA_COLS = ["coin", "query", "event_ts", "as_of_ts",
               "value", "value_z90", "value_z365"]
EMBARGO_HOURS = 24


def _file_for(root: Path, coin: str, as_of_date: pd.Timestamp) -> Path:
    return Path(root) / coin / f"as_of={as_of_date.strftime('%Y-%m-%d')}.parquet"


def write_rows(df: pd.DataFrame, *, root: Path = DEFAULT_ROOT) -> None:
    """Append rows to the store, partitioned by (coin, as_of_date)."""
    if df.empty:
        return
    missing = set(SCHEMA_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    df = df.copy()
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    df["as_of_ts"] = pd.to_datetime(df["as_of_ts"], utc=True)
    for (coin, as_of_date), group in df.groupby(
        ["coin", df["as_of_ts"].dt.floor("D")]
    ):
        target = _file_for(Path(root), coin, as_of_date)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            existing = pd.read_parquet(target)
            combined = pd.concat([existing, group], ignore_index=True)
            combined = combined.drop_duplicates(
                subset=["coin", "query", "event_ts", "as_of_ts"],
                keep="last",
            )
        else:
            combined = group
        combined.to_parquet(target, index=False)


def query_attention(
    coin: str,
    trade_date: datetime,
    lookback_days: int,
    *,
    root: Path = DEFAULT_ROOT,
    embargo_hours: int = EMBARGO_HOURS,
) -> pd.DataFrame:
    """Return rows for `coin` with event_ts in [trade_date - lookback, trade_date)
    and as_of_ts < trade_date - embargo_hours."""
    root = Path(root)
    coin_dir = root / coin
    if not coin_dir.exists():
        return pd.DataFrame(columns=SCHEMA_COLS)
    cutoff = pd.Timestamp(trade_date).tz_convert("UTC") - pd.Timedelta(hours=embargo_hours)
    start = pd.Timestamp(trade_date).tz_convert("UTC") - pd.Timedelta(days=lookback_days)
    parts = []
    for f in coin_dir.glob("as_of=*.parquet"):
        df = pd.read_parquet(f)
        df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
        df["as_of_ts"] = pd.to_datetime(df["as_of_ts"], utc=True)
        df = df[
            (df["as_of_ts"] < cutoff)
            & (df["event_ts"] >= start)
            & (df["event_ts"] < pd.Timestamp(trade_date).tz_convert("UTC"))
        ]
        if not df.empty:
            parts.append(df)
    if not parts:
        return pd.DataFrame(columns=SCHEMA_COLS)
    out = pd.concat(parts, ignore_index=True)
    out = out.sort_values("event_ts").drop_duplicates(
        subset=["coin", "query", "event_ts"], keep="last"
    )
    return out
