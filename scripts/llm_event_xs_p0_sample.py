"""llm_c1_event_xs P0 — stratified 300-article sample (frozen seed).

Strata: 200 prefilter-positive + 100 prefilter-negative, allocated
proportionally across years 2021-2025 and both stores (min 1 per
non-empty cell). Requires the corpus manifest (freeze discipline);
refuses to overwrite an existing sample.

Prefilter = frozen keyword list (charter §3), matched case-insensitively
on headline+summary+content.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

MANIFEST = Path("data/llm_event_xs/corpus_manifest.json")
OUT = Path("data/llm_event_xs/p0_sample.parquet")
SEED = 20260813

KEYWORDS = [
    "hack", "hacked", "exploit", "exploited", "breach", "stolen", "drained",
    "vulnerability", "insolven", "bankrupt", "withdraw", "halt", "suspend",
    "frozen", "depeg", "collaps", "liquidat", "sec", "cftc", "lawsuit",
    "charge", "settle", "ban", "regulat", "delist", "listing", "lists",
    "launch", "unlock", "vesting", "emission", "airdrop", "upgrade",
    "hard fork", "mainnet", "partnership", "acqui", "merge",
]
# word-boundary for short/ambiguous tokens, substring for stems
_SHORT = {"sec", "cftc", "ban", "lists"}
PATTERN = re.compile("|".join(
    (rf"\b{k}\b" if k in _SHORT else re.escape(k)) for k in KEYWORDS),
    re.IGNORECASE)

STORES = {"alpaca": Path("data/sentiment/alpaca"),
          "gdelt": Path("data/sentiment/gdelt")}
DEV = ("2021-01-01", "2025-03-31")


def load_corpus() -> pd.DataFrame:
    frames = []
    for store, root in STORES.items():
        for f in sorted(root.rglob("*.parquet")):
            df = pd.read_parquet(
                f, columns=["event_ts", "id", "headline", "summary",
                            "content", "symbols", "url"])
            df["store"] = store
            frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)
    df = df[(df["event_ts"] >= pd.Timestamp(DEV[0], tz="UTC")) &
            (df["event_ts"] <= pd.Timestamp(DEV[1] + " 23:59:59", tz="UTC"))]
    df = df.dropna(subset=["headline"])
    df = df.drop_duplicates(subset=["store", "id"])
    text = (df["headline"].fillna("") + " " + df["summary"].fillna("") +
            " " + df["content"].fillna(""))
    df["prefilter"] = text.str.contains(PATTERN).to_numpy()
    df["year"] = df["event_ts"].dt.year
    return df


def stratified(df: pd.DataFrame, n_target: int, rng) -> pd.DataFrame:
    cells = df.groupby(["store", "year"])
    sizes = cells.size()
    alloc = (sizes / sizes.sum() * n_target).round().astype(int).clip(lower=1)
    while alloc.sum() != n_target:
        # adjust largest cells
        key = alloc.idxmax() if alloc.sum() > n_target else sizes.idxmax()
        alloc[key] += -1 if alloc.sum() > n_target else 1
    picks = []
    for key, k in alloc.items():
        sub = cells.get_group(key)
        picks.append(sub.sample(n=min(int(k), len(sub)),
                                random_state=rng.integers(2**31)))
    return pd.concat(picks)


def main() -> int:
    if OUT.exists():
        print(f"sample exists ({OUT}) — refusing to overwrite (stop rule)")
        return 1
    if not MANIFEST.exists():
        print("corpus manifest missing — freeze the corpus first")
        return 1
    rng = np.random.default_rng(SEED)
    df = load_corpus()
    pos, neg = df[df["prefilter"]], df[~df["prefilter"]]
    print(f"corpus dev-window: {len(df)} articles "
          f"({len(pos)} prefilter-pos, {len(neg)} prefilter-neg)")
    sample = pd.concat([stratified(pos, 200, rng), stratified(neg, 100, rng)])
    sample = sample.sample(frac=1.0, random_state=SEED)  # shuffle order
    sample["sample_idx"] = range(len(sample))
    sample.to_parquet(OUT, index=False)
    print(f"sample written: {len(sample)} articles -> {OUT}")
    print(sample.groupby(["store", "year", "prefilter"]).size())
    return 0


if __name__ == "__main__":
    sys.exit(main())
