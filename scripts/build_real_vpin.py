"""Download Binance public aggTrades (S3 bulk ZIPs) and compute real VPIN features.

Uses data.binance.vision bulk daily ZIPs instead of the REST API endpoint to
avoid rate-limit pagination issues.  Each daily ZIP is ~10-16 MB compressed.

Output: data/microstructure_real/{coin}.parquet with columns:
    vpin_50, vpin_50_z, ofi_d, ofi_d_w, aggressor_ratio

Usage:
    python scripts/build_real_vpin.py \\
        --coins bitcoin ethereum \\
        --start 2026-01-15 --end 2026-04-15 \\
        --out-dir data/microstructure_real
"""
from __future__ import annotations

import argparse
import io
import logging
import os
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tradingagents.strategies.v3.features.microstructure import (
    build_daily_microstructure_features,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

_BASE_URL = "https://data.binance.vision/data/spot/daily/aggTrades/{symbol}/{symbol}-aggTrades-{date}.zip"

_COIN_TO_SYMBOL = {
    "bitcoin": "BTCUSDT",
    "ethereum": "ETHUSDT",
    "binancecoin": "BNBUSDT",
    "solana": "SOLUSDT",
}

# CSV columns: agg_id, price, qty, first_trade_id, last_trade_id, timestamp_us, is_buyer_maker, is_best_match
# NOTE: Binance public data timestamps are in MICROSECONDS despite the historical "ms" naming
_CSV_COLS = [
    "agg_id",
    "price",
    "qty",
    "first_trade_id",
    "last_trade_id",
    "timestamp_ms",  # actually microseconds in public bulk data
    "is_buyer_maker",
    "is_best_match",
]


def _download_day_zip(
    symbol: str,
    date_str: str,
    cache_dir: Path,
    session: requests.Session,
) -> pd.DataFrame | None:
    """Download and parse one day of aggTrades from Binance S3."""
    cache_file = cache_dir / f"{symbol}_{date_str}.parquet"
    if cache_file.exists():
        logger.debug("Cache hit: %s", cache_file)
        return pd.read_parquet(cache_file)

    url = _BASE_URL.format(symbol=symbol, date=date_str)
    try:
        resp = session.get(url, timeout=60)
        if resp.status_code == 404:
            logger.warning("No data available: %s", url)
            return None
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Download failed %s: %s", url, exc)
        return None

    try:
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        csv_name = zf.namelist()[0]
        with zf.open(csv_name) as f:
            df = pd.read_csv(
                f,
                header=None,
                names=_CSV_COLS,
                dtype={
                    "price": "float64",
                    "qty": "float64",
                    "timestamp_ms": "int64",
                },
            )
    except Exception as exc:
        logger.error("Parse error for %s: %s", date_str, exc)
        return None

    df["is_buyer_maker"] = df["is_buyer_maker"].astype(str).str.lower().isin(
        ["true", "1", "yes"]
    )
    # Binance public data timestamps are in microseconds (not milliseconds)
    ts = pd.to_datetime(df["timestamp_ms"], unit="us", utc=True)
    out = pd.DataFrame(
        {
            "price": df["price"].values,
            "qty": df["qty"].values,
            "is_buyer_maker": df["is_buyer_maker"].values,
        },
        index=ts,
    )
    out.index.name = "ts"
    out = out.sort_index()

    # Cache to disk
    out.to_parquet(cache_file)
    logger.debug("Cached %s (%d rows)", cache_file, len(out))
    return out


def build_features_for_coin(
    coin: str,
    dates: pd.DatetimeIndex,
    cache_dir: Path,
    out_dir: Path,
) -> pd.DataFrame | None:
    symbol = _COIN_TO_SYMBOL.get(coin)
    if symbol is None:
        logger.error("Unknown coin: %s", coin)
        return None

    session = requests.Session()
    all_trades: list[pd.DataFrame] = []
    n_days = len(dates)

    for i, d in enumerate(dates, 1):
        date_str = d.strftime("%Y-%m-%d")
        day_df = _download_day_zip(symbol, date_str, cache_dir, session)
        if day_df is not None and not day_df.empty:
            all_trades.append(day_df)
            logger.info("[%s] %d/%d done: %s (%d trades)", coin, i, n_days, date_str, len(day_df))
        else:
            logger.warning("[%s] %d/%d skipped: %s", coin, i, n_days, date_str)

    if not all_trades:
        logger.error("No trades fetched for %s", coin)
        return None

    logger.info("[%s] Concatenating %d days of trades...", coin, len(all_trades))
    trades = pd.concat(all_trades).sort_index()
    logger.info("[%s] Total trades: %d", coin, len(trades))

    logger.info("[%s] Computing microstructure features...", coin)
    features = build_daily_microstructure_features(
        trades, as_of=trades.index.max()
    )

    out_file = out_dir / f"{coin}.parquet"
    features.to_parquet(out_file)
    logger.info("[%s] Wrote %s (%d rows)", coin, out_file, len(features))
    return features


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coins", nargs="+", default=["bitcoin", "ethereum"])
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--cache-dir", default="data/microstructure_raw_s3")
    parser.add_argument("--out-dir", default="data/microstructure_real")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    dates = pd.date_range(args.start, args.end, freq="D", tz="UTC")
    logger.info("Dates: %s → %s (%d days)", args.start, args.end, len(dates))

    for coin in args.coins:
        logger.info("=== Processing %s ===", coin)
        build_features_for_coin(coin, dates, cache_dir, out_dir)

    logger.info("Done.")


if __name__ == "__main__":
    main()
