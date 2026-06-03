#!/usr/bin/env python
"""Download 1h OHLCV klines for the 4-coin V5 MIX core and cache to parquet.

One parquet per coin at data/intraday_1h/{coin}.parquet with columns
open_time, open, high, low, close, volume. Incremental: appends only bars
after the last cached open_time. Idempotent.

Usage:
    python scripts/fetch_intraday_1h.py --start 2021-11-07 --end 2026-04-15
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.dataflows.coingecko_binance import fetch_binance_klines_range  # noqa: E402

COIN_SYMBOLS = {
    "bitcoin": "BTCUSDT", "ethereum": "ETHUSDT",
    "binancecoin": "BNBUSDT", "solana": "SOLUSDT",
}


def _to_ms(date_str: str) -> int:
    return int(pd.Timestamp(date_str, tz="UTC").timestamp() * 1000)


def fetch_coin(coin: str, symbol: str, start: str, end: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{coin}.parquet"
    from_ms = _to_ms(start)
    to_ms = _to_ms(end) + 86_400_000  # include the end day's bars

    existing = pd.DataFrame()
    if out_path.exists():
        existing = pd.read_parquet(out_path)
        if not existing.empty:
            last_ms = int(existing["open_time"].max().timestamp() * 1000)
            from_ms = max(from_ms, last_ms + 3_600_000)

    if from_ms >= to_ms:
        print(f"  {coin}: cache up to date ({len(existing)} bars)")
        return out_path

    t0 = time.time()
    fresh = fetch_binance_klines_range(symbol, from_ms, to_ms, interval="1h")
    df = pd.concat([existing, fresh], ignore_index=True) if not existing.empty else fresh
    df = df.drop_duplicates(subset="open_time").sort_values("open_time").reset_index(drop=True)
    df.to_parquet(out_path, index=False)
    print(f"  {coin}: {len(df)} bars (+{len(fresh)} new) in {time.time()-t0:.1f}s → {out_path}")
    return out_path


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", default="2021-11-07")
    p.add_argument("--end", default="2026-04-15")
    p.add_argument("--output-dir", default="data/intraday_1h")
    p.add_argument("--coins", nargs="+", default=list(COIN_SYMBOLS))
    args = p.parse_args()

    out_dir = PROJECT_ROOT / args.output_dir
    for coin in args.coins:
        fetch_coin(coin, COIN_SYMBOLS[coin], args.start, args.end, out_dir)


if __name__ == "__main__":
    main()
