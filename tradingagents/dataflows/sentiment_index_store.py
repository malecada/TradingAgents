"""Bitemporal daily sentiment-index store, one root per scoring engine.

Reuses the on-chain long schema so backtests enforce as_of_ts <= trade_date.
Layout: data/sentiment/index/{engine}/{year}/{month:02d}.parquet
"""
from __future__ import annotations

import glob
import os
from pathlib import Path

import pandas as pd

from tradingagents.dataflows import onchain_store

BASE_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", "data")) / "sentiment" / "index"
ENGINES = ("llm", "bert")


def index_root(engine: str) -> Path:
    if engine not in ENGINES:
        raise ValueError(f"unknown engine {engine!r}, expected one of {ENGINES}")
    return BASE_ROOT / engine


def upsert_index_rows(df: pd.DataFrame, engine: str) -> int:
    return onchain_store.upsert_rows(df, root=index_root(engine))


def load_index(engine: str, coins: list[str], start: str, end: str) -> pd.DataFrame:
    files = glob.glob(str(index_root(engine) / "*" / "*.parquet"))
    if not files:
        return pd.DataFrame(columns=onchain_store.SCHEMA_COLS)
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    m = df["coin"].isin(coins) & (df["event_ts"] >= pd.Timestamp(start, tz="UTC")) \
        & (df["event_ts"] <= pd.Timestamp(end, tz="UTC"))
    return df.loc[m].sort_values(["coin", "metric", "event_ts"]).reset_index(drop=True)
