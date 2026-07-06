#!/usr/bin/env python
"""Corpus sentiment scoring runner — Engine A (LLM 0-4 index) + Engine B (CryptoBERT).

Consumes the bitemporal news corpora written by `backfill_alpaca_news.py`
(`{DATA_ROOT}/sentiment/alpaca/{year}/{MM}.parquet`) and
`ingest_hf_bitcoin_news.py` (`{DATA_ROOT}/sentiment/hf_btc/**/*.parquet`),
both sharing the schema
`[event_ts, as_of_ts, id, headline, content, summary, symbols, source,
author, url]`.

Produces per-article score rows at
`{DATA_ROOT}/sentiment/scores/{engine}/{source}/{year}.parquet` with columns
`[event_ts, as_of_ts, coin, engine, score_norm, relevant, content_sha]`
(see `SCORE_COLS`), one row per matched coin plus one extra `global` row
reusing whichever matched coin's score was computed first (see
`resolve_coins_for_article`). Consumed downstream by
`scripts/build_sentiment_index.py` (Task 7).

Coin mapping:
    Alpaca `symbols` field containing the substring "BTCUSD"/"ETHUSD" (list
    or comma-joined / stringified-list — matched via plain substring
    containment, so any representation works) maps to coin "btc"/"eth",
    filtered to the coins requested via `--coins`. The HF BTC-only corpus
    ignores `symbols` entirely and always maps to "btc" (if requested).

Engine A (LLM 0-4 index, `tradingagents.sentiment.llm_index_scorer`):
    Text = `anonymize_text(headline + "\\n\\n" + (content or summary), coin)`.
    The anonymizer substitutes a fixed per-coin alias ("Asset-A" for btc,
    "Asset-B" for eth) for the coin's real name/ticker; `coin_alias()`
    derives this token generically (via `anonymize_text` itself) and MUST be
    used as the `coin_name`/`symbol` fed into `score_article`'s prompt, or
    the prompt and the anonymized article text would reference different
    tokens and the model could never find "the coin" in scope.
    `score_norm = (idx - 2) / 2` (this formula's home; see `llm_score_norm`).
    Non-relevant articles and `__error__:`-prefixed API failures are
    skipped (no row written); errors are counted and reported.

Engine B (CryptoBERT, `tradingagents.sentiment.scorers.CryptoBertScorer`):
    Text = `headline + ". " + summary` (fits the 256-token window; full
    `content` is NOT used). `score_norm = p_bull - p_bear` per article.
    `relevant` is always True (BERT has no relevance filter). Scored in
    batches (default 64 texts) since model load is lazy+slow and per-article
    calls to `.score()` would be pathological.

Knowledge-cutoff guard: when `--engine llm`, the effective start date is
clamped to `max(--start, 2023-10-01)` (gpt-4o-mini's knowledge cutoff) to
avoid look-ahead bias from the model's memorized training-time knowledge of
"future" (relative to the article) price history. This is a hard guard in
code, not just an operational convention — see `clamp_llm_start`.

Usage:
    python scripts/score_sentiment_corpus.py --engine llm --source alpaca \\
        --coins btc,eth --start 2023-10-01 --end 2026-05-26 --est-only
    python scripts/score_sentiment_corpus.py --engine llm --source alpaca \\
        --coins btc,eth --start 2023-10-01 --end 2026-05-26 --yes
    python scripts/score_sentiment_corpus.py --engine bert --source hf_btc \\
        --coins btc --start 2021-07-01 --end 2025-06-30
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.sentiment.anonymize import anonymize_text  # noqa: E402
from tradingagents.sentiment.llm_index_scorer import LlmIndexScorer  # noqa: E402
from tradingagents.sentiment.scorers import get_cryptobert  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CORPUS_COLS = [
    "event_ts", "as_of_ts", "id", "headline", "content",
    "summary", "symbols", "source", "author", "url",
]

SCORE_COLS = [
    "event_ts", "as_of_ts", "coin", "engine", "score_norm", "relevant", "content_sha",
]

# Only coins the anonymizer knows about (Asset-A / Asset-B aliases exist for
# these two only) are supported end to end.
SYMBOL_SUBSTR = {"btc": "BTCUSD", "eth": "ETHUSD"}
SUPPORTED_COINS = tuple(SYMBOL_SUBSTR)

LLM_CUTOFF_DATE = date(2023, 10, 1)  # gpt-4o-mini knowledge-cutoff guard

BERT_BATCH_SIZE = 64
PROGRESS_EVERY = 500

# --est-only pricing model: gpt-4o-mini $0.15/1M input + $0.60/1M output.
EST_TOKENS_IN = 1_400
EST_TOKENS_OUT = 160
EST_PRICE_IN_PER_M = 0.15
EST_PRICE_OUT_PER_M = 0.60
COST_ABORT_THRESHOLD = 40.0


# ---------------------------------------------------------------------------
# Coin mapping (incl. "global") — pure, unit tested
# ---------------------------------------------------------------------------

def validate_coins(coins: list[str]) -> None:
    """Raise ValueError if any requested coin isn't in SUPPORTED_COINS."""
    unsupported = [c for c in coins if c not in SUPPORTED_COINS]
    if unsupported:
        raise ValueError(
            f"Unsupported coin(s) {unsupported!r}; supported: {SUPPORTED_COINS!r}"
        )


def symbols_to_coins(symbols, requested_coins: list[str]) -> list[str]:
    """Map an article's `symbols` field (list, comma-string, or stringified
    list — any representation) to matched coin codes, filtered to
    `requested_coins` and returned in `requested_coins` order."""
    text = str(symbols)
    return [c for c in requested_coins if SYMBOL_SUBSTR.get(c) and SYMBOL_SUBSTR[c] in text]


def resolve_coins_for_article(symbols, requested_coins: list[str], *, source: str) -> list[str]:
    """Return the list of coin codes to emit a score row for, with a
    trailing "global" entry when at least one requested coin matched.

    HF BTC corpus ignores `symbols` and always maps to "btc" (source is
    BTC-only by construction). Returns [] if nothing matched (no rows at
    all, not even "global").
    """
    if source == "hf_btc":
        matched = ["btc"] if "btc" in requested_coins else []
    else:
        matched = symbols_to_coins(symbols, requested_coins)
    if not matched:
        return []
    return matched + ["global"]


# ---------------------------------------------------------------------------
# score_norm mappings — pure, unit tested
# ---------------------------------------------------------------------------

def llm_score_norm(idx: int) -> float:
    """Engine A: map the 0-4 sentiment index to [-1, +1]."""
    return (idx - 2) / 2


def bert_score_norms(probs: np.ndarray) -> np.ndarray:
    """Engine B: per-row p_bull - p_bear, vectorized over an (n, 3) array."""
    if probs.shape[0] == 0:
        return np.zeros((0,), dtype=np.float64)
    return probs[:, 2] - probs[:, 0]


# ---------------------------------------------------------------------------
# Anonymization alias — pure, unit tested
# ---------------------------------------------------------------------------

def coin_alias(coin: str) -> str:
    """The placeholder token `anonymize_text` substitutes for `coin`.

    Derived generically (rather than hardcoded) so the prompt's
    `{coin_name}`/`{symbol}` can never drift out of sync with what the
    anonymizer actually emits into the article text.
    """
    token = coin.upper()
    return anonymize_text(token, coin)


# ---------------------------------------------------------------------------
# Text builders
# ---------------------------------------------------------------------------

def build_llm_text(headline: str, content: Optional[str], summary: Optional[str], coin: str) -> str:
    """Engine A scoring text: anonymized headline + (content or summary)."""
    body = content or summary or ""
    raw = f"{headline}\n\n{body}"
    return anonymize_text(raw, coin)


def build_bert_text(headline: str, summary: Optional[str]) -> str:
    """Engine B scoring text: headline + summary (fits the 256-token window)."""
    return f"{headline}. {summary or ''}"


# ---------------------------------------------------------------------------
# Misc pure helpers
# ---------------------------------------------------------------------------

def sha1_of(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()


def clamp_llm_start(start: date, engine: str, cutoff: date = LLM_CUTOFF_DATE) -> tuple[date, bool]:
    """Hard guard: engine=llm never scores articles before `cutoff` (the
    model's knowledge cutoff), to avoid look-ahead bias from memorized
    "future" price history relative to the article's publish date.

    Returns (effective_start, was_clamped).
    """
    if engine == "llm" and start < cutoff:
        return cutoff, True
    return start, False


def estimate_cost(
    n_articles: int,
    *,
    tokens_in: int = EST_TOKENS_IN,
    tokens_out: int = EST_TOKENS_OUT,
    price_in_per_m: float = EST_PRICE_IN_PER_M,
    price_out_per_m: float = EST_PRICE_OUT_PER_M,
) -> float:
    """Rough cost estimate for `--est-only`: n_articles * (in-token + out-token cost).

    Note: this counts articles that matched >=1 requested coin (i.e. would
    trigger at least one `score_article` call), not raw corpus rows. It does
    not separately account for the rare case of an article matching >1
    requested coin (which triggers >1 LLM call) — a documented
    simplification, not a precision cost model.
    """
    per_article = tokens_in * price_in_per_m / 1e6 + tokens_out * price_out_per_m / 1e6
    return n_articles * per_article


# ---------------------------------------------------------------------------
# Year-partition writer — round-trip + dedupe, unit tested
# ---------------------------------------------------------------------------

def _scores_path(data_root: Path, engine: str, source: str, year: int) -> Path:
    return Path(data_root) / "sentiment" / "scores" / engine / source / f"{year}.parquet"


def write_scores(rows: pd.DataFrame, *, engine: str, source: str, data_root: Path) -> dict[int, int]:
    """Merge `rows` into per-year Parquet shards, deduping on
    (content_sha, coin) keep='last'. Overwrites the touched year files.

    Returns {year: row_count_after_write} for touched years.
    """
    if rows.empty:
        return {}
    missing = set(SCORE_COLS) - set(rows.columns)
    if missing:
        raise ValueError(f"write_scores missing columns: {sorted(missing)}")
    rows = rows[SCORE_COLS].copy()
    rows["event_ts"] = pd.to_datetime(rows["event_ts"], utc=True)
    rows["as_of_ts"] = pd.to_datetime(rows["as_of_ts"], utc=True)
    years = rows["event_ts"].dt.year
    written: dict[int, int] = {}
    for year, chunk in rows.groupby(years):
        year = int(year)
        target = _scores_path(data_root, engine, source, year)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            existing = pd.read_parquet(target)
            combined = pd.concat([existing, chunk], ignore_index=True)
        else:
            combined = chunk.reset_index(drop=True)
        combined = combined.drop_duplicates(subset=["content_sha", "coin"], keep="last")
        combined.to_parquet(target, index=False)
        written[year] = len(combined)
    return written


# ---------------------------------------------------------------------------
# Corpus loading (I/O — not unit tested per brief scope, kept small/simple)
# ---------------------------------------------------------------------------

def _corpus_glob(source: str, data_root: Path) -> str:
    if source == "alpaca":
        return str(Path(data_root) / "sentiment" / "alpaca" / "*" / "*.parquet")
    if source == "hf_btc":
        return str(Path(data_root) / "sentiment" / "hf_btc" / "**" / "*.parquet")
    raise ValueError(f"unknown source {source!r}")


def load_corpus(source: str, start: date, end: date, data_root: Path) -> pd.DataFrame:
    """Load and concat all shards for `source`, filtered to event_ts in [start, end]."""
    pattern = _corpus_glob(source, data_root)
    files = glob.glob(pattern, recursive=True)
    if not files:
        return pd.DataFrame(columns=CORPUS_COLS)
    frames = [pd.read_parquet(f) for f in files]
    df = pd.concat(frames, ignore_index=True)
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    df["as_of_ts"] = pd.to_datetime(df["as_of_ts"], utc=True)
    for col in ("headline", "content", "summary"):
        if col in df.columns:
            df[col] = df[col].fillna("")
    ts_start = pd.Timestamp(start, tz="UTC")
    ts_end = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)  # end date inclusive
    mask = (df["event_ts"] >= ts_start) & (df["event_ts"] < ts_end)
    return df.loc[mask].sort_values("event_ts").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Engine runners (I/O + external calls — not unit tested per brief scope)
# ---------------------------------------------------------------------------

def _first_matched_row(matched_rows: dict[str, dict], matched_order: list[str]) -> Optional[dict]:
    for coin in matched_order:
        if coin in matched_rows:
            return matched_rows[coin]
    return None


def run_llm_engine(matched_df: pd.DataFrame, scorer: Optional[LlmIndexScorer] = None) -> tuple[pd.DataFrame, dict]:
    """Score every row of `matched_df` (must already carry a `matched_coins`
    column, see main()) via Engine A. Returns (rows_df, stats)."""
    scorer = scorer or LlmIndexScorer(model="gpt-4o-mini")
    rows: list[dict] = []
    n_relevant = 0
    n_errors = 0
    n_processed = 0
    for article in matched_df.itertuples(index=False):
        matched = list(article.matched_coins)
        real_coins = [c for c in matched if c != "global"]
        per_coin_rows: dict[str, dict] = {}
        for coin in real_coins:
            text = build_llm_text(article.headline, article.content, article.summary, coin)
            alias = coin_alias(coin)
            result = scorer.score_article(text, coin, coin_name=alias, symbol=alias)
            if isinstance(result.get("raw"), str) and result["raw"].startswith("__error__:"):
                n_errors += 1
                continue
            if not result["relevant"] or result["idx"] is None:
                continue
            row = {
                "event_ts": article.event_ts,
                "as_of_ts": article.as_of_ts,
                "coin": coin,
                "engine": "llm",
                "score_norm": llm_score_norm(result["idx"]),
                "relevant": True,
                "content_sha": sha1_of(text),
            }
            per_coin_rows[coin] = row
            rows.append(row)
            n_relevant += 1
        if "global" in matched:
            source_row = _first_matched_row(per_coin_rows, real_coins)
            if source_row is not None:
                rows.append({**source_row, "coin": "global"})
        n_processed += 1
        if n_processed % PROGRESS_EVERY == 0:
            print(f"  ... {n_processed} articles processed "
                  f"(relevant={n_relevant}, errors={n_errors})")
    stats = {
        "engine": "llm",
        "n_articles": n_processed,
        "n_rows": len(rows),
        "n_relevant": n_relevant,
        "n_errors": n_errors,
        "relevant_share": (n_relevant / n_processed) if n_processed else 0.0,
    }
    return pd.DataFrame(rows, columns=SCORE_COLS), stats


def run_bert_engine(matched_df: pd.DataFrame, scorer=None,
                    batch_size: int = BERT_BATCH_SIZE) -> tuple[pd.DataFrame, dict]:
    """Score every row of `matched_df` via Engine B (CryptoBERT), batched.
    Returns (rows_df, stats)."""
    scorer = scorer or get_cryptobert()
    rows: list[dict] = []
    n_processed = 0
    n = len(matched_df)
    for start in range(0, n, batch_size):
        chunk = matched_df.iloc[start:start + batch_size]
        texts = [build_bert_text(h, s) for h, s in zip(chunk["headline"], chunk["summary"])]
        probs = scorer.score(texts)
        norms = bert_score_norms(np.asarray(probs))
        for i, article in enumerate(chunk.itertuples(index=False)):
            sha = sha1_of(texts[i])
            score_norm = float(norms[i])
            for coin in article.matched_coins:
                rows.append({
                    "event_ts": article.event_ts,
                    "as_of_ts": article.as_of_ts,
                    "coin": coin,
                    "engine": "bert",
                    "score_norm": score_norm,
                    "relevant": True,
                    "content_sha": sha,
                })
            n_processed += 1
            if n_processed % PROGRESS_EVERY == 0:
                print(f"  ... {n_processed} articles processed")
    stats = {
        "engine": "bert",
        "n_articles": n_processed,
        "n_rows": len(rows),
        "n_relevant": n_processed,
        "n_errors": 0,
        "relevant_share": 1.0 if n_processed else 0.0,
    }
    return pd.DataFrame(rows, columns=SCORE_COLS), stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Score a news corpus with Engine A (LLM) or Engine B (CryptoBERT).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--engine", choices=["llm", "bert"], required=True)
    p.add_argument("--source", choices=["alpaca", "hf_btc"], required=True)
    p.add_argument("--coins", required=True, help="comma-separated, e.g. btc,eth")
    p.add_argument("--start", required=True, help="YYYY-MM-DD (UTC, inclusive)")
    p.add_argument("--end", required=True, help="YYYY-MM-DD (UTC, inclusive)")
    p.add_argument("--limit", type=int, default=None,
                   help="cap the number of matched articles processed (smoke testing)")
    p.add_argument("--est-only", action="store_true",
                   help="print article count + cost estimate, then exit")
    p.add_argument("--yes", action="store_true",
                   help="proceed with a real LLM run even if estimated cost > $%.0f" % COST_ABORT_THRESHOLD)
    p.add_argument("--data-root", default=None,
                   help="override TRADINGAGENTS_DATA_ROOT for this run")
    return p.parse_args(argv)


def _data_root(args: argparse.Namespace) -> Path:
    if args.data_root:
        return Path(args.data_root)
    return Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", "data"))


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    coins = [c.strip().lower() for c in args.coins.split(",") if c.strip()]
    validate_coins(coins)

    data_root = _data_root(args)
    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()

    start, was_clamped = clamp_llm_start(start, args.engine)
    if was_clamped:
        print(f"WARNING: engine=llm clamps --start to {LLM_CUTOFF_DATE} "
              f"(knowledge-cutoff look-ahead guard); requested start was earlier.")

    df = load_corpus(args.source, start, end, data_root)
    df = df.assign(matched_coins=[
        resolve_coins_for_article(s, coins, source=args.source) for s in df["symbols"]
    ])
    matched_df = df[df["matched_coins"].map(len) > 0].reset_index(drop=True)
    if args.limit is not None:
        matched_df = matched_df.head(args.limit)

    n_articles = len(matched_df)
    cost = estimate_cost(n_articles)

    if args.est_only:
        print(f"Articles matching --coins {coins} in window "
              f"[{start} .. {end}]: {n_articles}")
        print(f"Estimated cost (gpt-4o-mini @ {EST_TOKENS_IN}in/{EST_TOKENS_OUT}out "
              f"tokens/article): ${cost:.2f}")
        return 0

    if args.engine == "llm" and cost > COST_ABORT_THRESHOLD and not args.yes:
        print(f"ABORT: estimated cost ${cost:.2f} exceeds ${COST_ABORT_THRESHOLD:.0f} guard. "
              f"Re-run with --yes to proceed anyway.")
        return 1

    if n_articles == 0:
        print("No matching articles in window — nothing to score.")
        return 0

    if args.engine == "llm":
        rows, stats = run_llm_engine(matched_df)
    else:
        rows, stats = run_bert_engine(matched_df)

    written = write_scores(rows, engine=args.engine, source=args.source, data_root=data_root)

    print("--- Summary ---")
    print(f"Engine: {stats['engine']}  Source: {args.source}  Coins: {coins}")
    print(f"Articles processed (cost-relevant): {stats['n_articles']}")
    print(f"Score rows written: {stats['n_rows']}")
    print(f"Relevant share: {stats['relevant_share']:.2%}")
    print(f"Errors (skipped): {stats['n_errors']}")
    print(f"Years written: {sorted(written)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
