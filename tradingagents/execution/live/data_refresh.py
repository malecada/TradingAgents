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


def refresh_coinglass(
    coins: list[str],
    derivatives_dir: Path,
    raw_dir: Path,
    api_key: str,
    structured_log: object | None,
) -> None:
    """Daily incremental refresh of Coinglass derivatives parquets.

    Wraps the §13 fetch helpers from ``scripts/fetch_coinglass_history.py``,
    appends new rows to ``{raw_dir}/{SYMBOL}_cg_*.parquet`` and merges
    everything into ``{derivatives_dir}/{coin}.parquet`` for V3/runner_v3 +
    V4-B PIT feature consumers.

    Idempotent: re-running over a date range already present is a no-op for
    the on-disk parquets.
    """
    if not api_key:
        raise RuntimeError("COINGLASS_API_KEY env var missing — required for V5 193f routes")

    # Late import to avoid pulling the heavy scripts package at module import time.
    from scripts.fetch_coinglass_history import (
        COIN_TO_SYMS, ENDPOINTS, fetch_oi_agg, fetch_liq_agg, fetch_ls_ratio,
        fetch_taker_vol, fetch_funding_weighted,
    )

    derivatives_dir = Path(derivatives_dir)
    raw_dir = Path(raw_dir)
    derivatives_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    for coin in coins:
        if coin not in COIN_TO_SYMS:
            if structured_log is not None:
                structured_log.warn("coinglass_coin_unsupported", coin=coin)
            continue
        sym_base, pair = COIN_TO_SYMS[coin]

        # Fetch all 7 endpoints. Empty frames OK — leave the merge step to handle.
        frames = {
            "oi":              fetch_oi_agg(sym_base, api_key),
            "liq":             fetch_liq_agg(sym_base, api_key),
            "ls_global":       fetch_ls_ratio("ls_global", pair, api_key),
            "ls_top_position": fetch_ls_ratio("ls_top_position", pair, api_key),
            "ls_top_account":  fetch_ls_ratio("ls_top_account", pair, api_key),
            "taker":           fetch_taker_vol(pair, api_key),
            "funding_w":       fetch_funding_weighted(sym_base, api_key),
        }

        # Cache raw + merge into daily aggregate (matches fetch_coinglass_history.py logic).
        non_empty = []
        for name, df in frames.items():
            if df.empty:
                continue
            if df.index.tz is None:
                df.index = pd.to_datetime(df.index).tz_localize("UTC")
            else:
                df.index = df.index.tz_convert("UTC")
            raw_path = raw_dir / f"{pair}_cg_{name}.parquet"
            df.to_parquet(raw_path)  # full overwrite — idempotent
            non_empty.append(df)

        if not non_empty:
            continue
        merged_cg = pd.concat(non_empty, axis=1).sort_index()

        daily_file = derivatives_dir / f"{coin}.parquet"
        if daily_file.exists():
            existing = pd.read_parquet(daily_file)
            if existing.index.tz is None:
                existing.index = pd.to_datetime(existing.index).tz_localize("UTC")
            # Drop any pre-existing cg_* prefixed columns to avoid stale double-merge.
            existing = existing.loc[:, ~existing.columns.str.startswith(
                ("oi_", "liq_", "ls_", "taker_", "funding_oiw")
            )]
            out = existing.join(merged_cg, how="outer").sort_index()
        else:
            out = merged_cg
        out.to_parquet(daily_file)
