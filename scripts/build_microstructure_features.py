"""Pull Binance aggTrades for a date range, compute daily microstructure features,
write to ``data/microstructure/{coin}.parquet``.

Usage:
    python scripts/build_microstructure_features.py \\
        --coins bitcoin ethereum \\
        --start 2024-05-01 --end 2026-04-15
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tradingagents.strategies.v3.features.microstructure import (  # noqa: E402
    build_daily_microstructure_features,
    fetch_aggtrades,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_COIN_TO_SYMBOL = {
    "bitcoin": "BTCUSDT",
    "ethereum": "ETHUSDT",
    "binancecoin": "BNBUSDT",
    "solana": "SOLUSDT",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coins", nargs="+", default=["bitcoin", "ethereum"])
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--cache-dir", default="data/microstructure_raw")
    parser.add_argument("--out-dir", default="data/microstructure")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    dates = pd.date_range(args.start, args.end, freq="D", tz="UTC")
    for coin in args.coins:
        symbol = _COIN_TO_SYMBOL[coin]
        logger.info("Fetching %s for %d days", symbol, len(dates))
        all_trades = []
        for d in dates:
            try:
                day_df = fetch_aggtrades(symbol=symbol, date=d, cache_dir=cache_dir)
                all_trades.append(day_df)
            except Exception:
                logger.exception("Failed %s %s", symbol, d.strftime("%Y-%m-%d"))
        if not all_trades:
            continue
        trades = pd.concat(all_trades).sort_index()
        features = build_daily_microstructure_features(
            trades, as_of=trades.index.max()
        )
        out_file = out_dir / f"{coin}.parquet"
        features.to_parquet(out_file)
        logger.info("Wrote %s (%d rows)", out_file, len(features))


if __name__ == "__main__":
    main()
