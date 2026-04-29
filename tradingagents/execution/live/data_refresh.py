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


def refresh_ohlcv(coin: str, cache_root: Path) -> None:
    df = fetch_binance_daily(symbol=f"{coin}USDT", days=2)
    if df.empty:
        logger.warning("Binance OHLCV returned 0 rows for %s", coin)
        return
    append_ohlcv(df, coin, cache_root)
    logger.info("OHLCV: appended %d rows for %s", len(df), coin)


def _yesterday_utc() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
