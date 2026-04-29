"""Daily incremental data refresh for the live trading cycle.

All three sources are append-only into Parquet stores keyed on
(metric, coin, valid_from). Re-running the same date is a no-op due to
dedupe keys in the on-chain store and a date-level deduplication on the
OHLCV cache.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from tradingagents.dataflows.onchain import (
    fetch_coinmetrics_incremental,
    fetch_defillama_incremental,
)
from tradingagents.dataflows.coingecko_binance import fetch_binance_daily
from tradingagents.execution.live.config import to_binance_symbol

logger = logging.getLogger(__name__)


def upsert_onchain_rows(df: pd.DataFrame, root: Path) -> int:
    """Wrapper around the on-chain store upsert function.

    Defined on this module so tests can patch it directly. Delegates to
    ``tradingagents.dataflows.onchain_store.upsert_rows``.
    """
    from tradingagents.dataflows import onchain_store
    return onchain_store.upsert_rows(df, root=root)


def append_ohlcv(df: pd.DataFrame, coin: str, cache_root: Path) -> None:
    """Append rows to the per-coin OHLCV cache, deduping on the date column."""
    cache_root = Path(cache_root)
    cache_root.mkdir(parents=True, exist_ok=True)
    out = cache_root / f"{coin}USDT_1d.parquet"
    if out.exists():
        existing = pd.read_parquet(out)
        merged = pd.concat([existing, df]).drop_duplicates(
            subset=["date"], keep="last"
        )
    else:
        merged = df
    merged.to_parquet(out, index=False)


def refresh_coinmetrics(coins: list[str], store_root: Path) -> None:
    df = fetch_coinmetrics_incremental(coins=coins, since=_yesterday_utc())
    if df.empty:
        logger.warning("CoinMetrics returned 0 rows")
        return
    n = upsert_onchain_rows(df, store_root)
    logger.info("CoinMetrics: upserted %d rows", n)


def refresh_defillama(coins: list[str], store_root: Path) -> None:
    df = fetch_defillama_incremental(coins=coins, since=_yesterday_utc())
    if df.empty:
        logger.warning("DefiLlama returned 0 rows")
        return
    n = upsert_onchain_rows(df, store_root)
    logger.info("DefiLlama: upserted %d rows", n)


def refresh_ohlcv(coin: str, cache_root: Path, min_history: int = 60) -> None:
    """Refresh OHLCV cache for ``coin`` (CoinGecko id or Binance base).

    Cold-start backfill: when the cache is missing or shorter than
    ``min_history`` rows, fetch ``min_history`` days; otherwise the cheap
    incremental 2-day fetch. The 60-day default ensures the first cycle
    after a fresh deploy has enough history for vol_lookback=20 and
    SMA30 computations.
    """
    cache_root = Path(cache_root)
    cache_root.mkdir(parents=True, exist_ok=True)
    symbol = to_binance_symbol(coin)
    out = cache_root / f"{symbol}_1d.parquet"
    existing_rows = 0
    if out.exists():
        try:
            existing_rows = len(pd.read_parquet(out))
        except Exception:
            existing_rows = 0
    days = min_history if existing_rows < min_history else 2
    df = fetch_binance_daily(symbol=symbol, days=days)
    if df.empty:
        logger.warning("Binance OHLCV returned 0 rows for %s", symbol)
        return
    append_ohlcv(df, symbol.replace("USDT", ""), cache_root)
    logger.info(
        "OHLCV: appended %d rows for %s (cache had %d)",
        len(df), symbol, existing_rows,
    )


def _yesterday_utc() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
