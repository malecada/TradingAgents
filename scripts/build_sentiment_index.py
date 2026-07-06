#!/usr/bin/env python
"""Daily sentiment-index builder — Task 7.

Consumes the per-article score parquets produced by
`scripts/score_sentiment_corpus.py` (Task 6) at
`{DATA_ROOT}/sentiment/scores/{engine}/{source}/{year}.parquet`
(cols `event_ts, as_of_ts, coin, engine, score_norm, relevant, content_sha`),
concatenates whichever of `--sources` (default: alpaca + hf_btc, whichever
exist on disk) have shards for the requested engine, dedupes overlapping
articles between sources on `[content_sha, coin]` (keep='first' — the two
corpora rarely but occasionally cover the same article), and rolls the
result up into the daily sentiment-index long store via
`tradingagents.sentiment.daily_index.aggregate` +
`tradingagents.dataflows.sentiment_index_store.upsert_index_rows`.

Data root is determined by the `TRADINGAGENTS_DATA_ROOT` environment variable
(defaults to `data` in the current directory if unset). This env var governs
both score read paths and index write paths, ensuring consistency.

Usage:
    python scripts/build_sentiment_index.py --engine llm
    python scripts/build_sentiment_index.py --engine bert --sources alpaca,hf_btc
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.dataflows.sentiment_index_store import upsert_index_rows  # noqa: E402
from tradingagents.sentiment.daily_index import aggregate  # noqa: E402

SCORE_COLS = [
    "event_ts", "as_of_ts", "coin", "engine", "score_norm", "relevant", "content_sha",
]

SOURCES = ("alpaca", "hf_btc")


def _data_root() -> Path:
    return Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", "data"))


def _scores_glob(data_root: Path, engine: str, source: str) -> str:
    return str(data_root / "sentiment" / "scores" / engine / source / "*.parquet")


def load_scores(engine: str, sources: list[str], data_root: Optional[Path] = None) -> pd.DataFrame:
    """Load + concat all per-article score parquets for `engine` across
    `sources` (sources with no shards on disk are silently skipped), then
    dedupe on `[content_sha, coin]` keeping the first-seen row — this is the
    only place two sources' rows for the same article/coin could collide
    (rare cross-corpus overlap between Alpaca and the HF BTC corpus).

    If `data_root` is not provided, defaults to the value of the
    `TRADINGAGENTS_DATA_ROOT` environment variable (or "data" if unset)."""
    if data_root is None:
        data_root = _data_root()
    frames = []
    for source in sources:
        for f in sorted(glob.glob(_scores_glob(data_root, engine, source))):
            frames.append(pd.read_parquet(f))
    if not frames:
        return pd.DataFrame(columns=SCORE_COLS)
    df = pd.concat(frames, ignore_index=True)
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    df["as_of_ts"] = pd.to_datetime(df["as_of_ts"], utc=True)
    df = df.drop_duplicates(subset=["content_sha", "coin"], keep="first")
    return df.reset_index(drop=True)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Aggregate per-article sentiment scores into the daily index store.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--engine", choices=["llm", "bert"], required=True)
    p.add_argument("--sources", default=None,
                   help="comma-separated subset of alpaca,hf_btc (default: both, whichever exist)")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    sources = [s.strip() for s in args.sources.split(",") if s.strip()] if args.sources else list(SOURCES)

    scores = load_scores(args.engine, sources)
    data_root = _data_root()
    if scores.empty:
        print(f"No score parquets found for engine={args.engine} sources={sources} "
              f"under {data_root}. Nothing to do.")
        return 0

    rows = aggregate(scores)
    if rows.empty:
        print("aggregate() produced no rows — nothing to upsert.")
        return 0

    written = upsert_index_rows(rows, engine=args.engine)

    print("--- Summary ---")
    print(f"Engine: {args.engine}  Sources: {sources}")
    print(f"Input per-article score rows (post-dedupe): {len(scores)}")
    print(f"Output index rows produced this run: {len(rows)}")
    print(f"Store rows after upsert (existing + new, deduped): {written}")
    counts = rows.groupby(["coin", "metric"]).size().sort_index()
    for (coin, metric), n in counts.items():
        print(f"  {coin:8s} {metric:20s} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
