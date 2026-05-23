"""One-off pytrends ingestion driver.

Pulls daily Google Trends interest-over-time for BTC and ETH (plus the
'<coin> hack' negative-attention query) in rolling 90-day windows,
stores into the bitemporal store with the pull timestamp as as_of_ts.

Usage:
    python scripts/ingest_gtrends.py --coins bitcoin ethereum \
        --start 2024-01-01 --end 2026-05-23
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd

from tradingagents.dataflows.gtrends_store import write_rows, DEFAULT_ROOT

logger = logging.getLogger(__name__)

QUERIES = {
    "bitcoin": ["bitcoin", "bitcoin hack"],
    "ethereum": ["ethereum", "ethereum hack"],
}


def _zscore(series: pd.Series, window: int) -> pd.Series:
    roll = series.rolling(window=window, min_periods=window // 2)
    return (series - roll.mean()) / roll.std(ddof=0).replace(0, 1)


def fetch_window(coin: str, query: str, start: datetime, end: datetime) -> pd.DataFrame:
    from pytrends.request import TrendReq
    pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 30))
    tf = f"{start.strftime('%Y-%m-%d')} {end.strftime('%Y-%m-%d')}"
    pytrends.build_payload([query], cat=0, timeframe=tf, geo="", gprop="")
    df = pytrends.interest_over_time()
    if df.empty:
        return pd.DataFrame()
    df = df.reset_index().rename(columns={"date": "event_ts", query: "value"})
    df["coin"] = coin
    df["query"] = query
    return df[["coin", "query", "event_ts", "value"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coins", nargs="+", default=["bitcoin", "ethereum"])
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--window-days", type=int, default=90)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)
    as_of = datetime.now(timezone.utc)

    cursor = start
    accum = []
    while cursor < end:
        nxt = min(cursor + timedelta(days=args.window_days), end)
        for coin in args.coins:
            for q in QUERIES.get(coin, [coin]):
                logger.info("Fetch %s '%s' %s → %s", coin, q, cursor.date(), nxt.date())
                df = fetch_window(coin, q, cursor, nxt)
                if df.empty:
                    continue
                df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
                df["as_of_ts"] = as_of
                df["value_z90"] = _zscore(df["value"], 90)
                df["value_z365"] = _zscore(df["value"], 365)
                df = df.fillna({"value_z90": 0.0, "value_z365": 0.0})
                accum.append(df)
        cursor = nxt

    if accum:
        big = pd.concat(accum, ignore_index=True)
        write_rows(big)
        logger.info("Wrote %d rows to gtrends store", len(big))
    else:
        logger.warning("No rows ingested")


if __name__ == "__main__":
    main()
