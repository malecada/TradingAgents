"""Fetch Reddit posts per subreddit and day via Arctic Shift into the bitemporal store.

Idempotent per (subreddit, day) via data/dossier/reddit/days.jsonl.
Usage: dossier_reddit_fetch.py --start 2022-01-01 --end 2024-12-31 [--subreddits CryptoCurrency,Bitcoin,ethereum]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dossier import store  # noqa: E402
from tradingagents.dossier.reddit import SUBREDDITS, fetch_day, to_store_rows  # noqa: E402

LEDGER = Path("data/dossier/reddit/days.jsonl")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--subreddits", default=",".join(SUBREDDITS))
    args = ap.parse_args()
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if LEDGER.exists():
        done = {(j["subreddit"], j["day"]) for j in map(json.loads, LEDGER.read_text().splitlines()) if j}
    days = pd.date_range(args.start, args.end, freq="D", tz="UTC")
    with LEDGER.open("a") as ledger:
        for sub in args.subreddits.split(","):
            for day in days:
                key = (sub, day.strftime("%Y-%m-%d"))
                if key in done:
                    continue
                posts = fetch_day(sub, day)
                n = store.upsert(to_store_rows(posts)) if len(posts) else 0
                ledger.write(json.dumps({"subreddit": sub, "day": key[1], "posts": int(len(posts))}) + "\n")
                ledger.flush()
                if day.day == 1 or len(posts) == 0:
                    print(f"{sub} {key[1]}: {len(posts)} posts", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
