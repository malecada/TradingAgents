"""Fetch realized perpetual funding rates (Binance USDT-M public history) for the symbols that appear in the
weekly decision universe, into data/dossier/funding/<SYMBOL>.parquet (fundingTime, fundingRate). Realized
funding over the held week is a cost of the rule-twin book (charter §5); the card panel only carries the
trailing PIT mean. Resumable: a symbol whose file already reaches the end date is skipped.
Usage: dossier_funding_fetch.py --start 2021-12-01 --end 2026-11-01 [--symbols BTCUSDT,ETHUSDT]
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dossier.universe import weekly_top  # noqa: E402

OUT = Path("data/dossier/funding")
URL = "https://fapi.binance.com/fapi/v1/fundingRate"


def fetch_symbol(sym: str, start: pd.Timestamp, end: pd.Timestamp, session: requests.Session) -> pd.DataFrame:
    rows, t = [], int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    while t < end_ms:
        r = session.get(URL, params={"symbol": sym, "startTime": t, "endTime": end_ms, "limit": 1000}, timeout=30)
        if r.status_code == 429:
            time.sleep(60)
            continue
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        t = int(batch[-1]["fundingTime"]) + 1
        time.sleep(0.25)
        if len(batch) < 1000:
            break
    if not rows:
        return pd.DataFrame(columns=["fundingTime", "fundingRate"])
    df = pd.DataFrame(rows)[["fundingTime", "fundingRate"]]
    df["fundingTime"] = pd.to_datetime(df["fundingTime"].astype("int64"), unit="ms", utc=True)
    df["fundingRate"] = df["fundingRate"].astype(float)
    return df.drop_duplicates("fundingTime").sort_values("fundingTime").reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-12-01")
    ap.add_argument("--end", default=None, help="default: today")
    ap.add_argument("--symbols", default=None, help="comma list; default: every symbol in the weekly top-50 universe")
    ap.add_argument("--top", type=int, default=50)
    args = ap.parse_args()
    start = pd.Timestamp(args.start, tz="UTC")
    end = pd.Timestamp(args.end, tz="UTC") if args.end else pd.Timestamp.now(tz="UTC").normalize()
    if args.symbols:
        symbols = args.symbols.split(",")
    else:
        cards = pd.read_parquet("data/llm_rank_xs/cards.parquet")
        cards["date"] = pd.to_datetime(cards["date"], utc=True)
        symbols = sorted(weekly_top(cards, args.top, start=start)["symbol"].unique())
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    done = 0
    for sym in symbols:
        path = OUT / f"{sym}.parquet"
        if path.exists():
            old = pd.read_parquet(path)
            if len(old) and old["fundingTime"].max() >= end - pd.Timedelta(days=2):
                done += 1
                continue
        df = fetch_symbol(sym, start, end, session)
        df.to_parquet(path, index=False)
        done += 1
        print(f"{sym}: {len(df)} rates {df['fundingTime'].min() if len(df) else '-'} -> {df['fundingTime'].max() if len(df) else '-'} ({done}/{len(symbols)})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
