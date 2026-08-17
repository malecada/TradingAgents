"""llm_c3_rank_xs — LLM ranking runner (frozen prompt, charter §3).

Partition-rank-average: per week, seeded partition into batches of 25
anonymized cards; LLM orders each batch by expected 5-day forward return;
score = mean normalized in-batch rank over R=2 independent partitions.
All calls disk-cached; temp 0; gpt-5.4-mini.

Modes:
  --weeks W1,W2,...   run specific ISO dates (P0)
  --shuffle           batch-order-shuffled variant (P0 probe; same partition)
  --named             named cards (P1 only)
  --dev               full dev window anonymous run (P2)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("data/llm_rank_xs")
CACHE = OUT / "rank_call_cache.json"
MODEL = "gpt-5.4-mini"
BATCH = 25
ROUNDS = 2
DEV_END = pd.Timestamp("2025-03-31", tz="UTC")

FIELDS = ["ret_4w", "ret_12w", "dist_26w_high", "vol_ewma20", "volvol_20",
          "dvol_rank", "mcap_cm", "funding_3d", "funding_30d",
          "d_adract_30d", "d_txcnt_30d", "unlock_next30_pct",
          "unlock_prev30_pct", "age_weeks", "category"]

PROMPT = """You are ranking crypto perpetual-futures assets by expected 5-day
forward return (best first). Each asset is a card of point-in-time numeric
facts (null = not available). Fields: ret_4w/ret_12w = 4/12-week log
returns; dist_26w_high = log distance from 26-week high; vol_ewma20 =
annualized vol; volvol_20 = vol of vol; dvol_rank = dollar-volume
percentile; mcap_cm = market cap USD; funding_3d/30d = mean daily funding
(positive = longs pay); d_adract_30d/d_txcnt_30d = 30d change in active
addresses / tx count; unlock_next30_pct / unlock_prev30_pct = scheduled
token unlocks next/past 30d as fraction of supply; age_weeks = weeks since
listing; category = protocol category.

Rank ALL assets in the list. Use only the given numbers; consider
interactions (e.g. crowded funding + imminent unlocks + weak activity).
Return ONLY JSON: {{"ranking": ["<tag>", "<tag>", ...]}} best-first,
containing every tag exactly once.

Assets:
{cards}"""


def round3(x):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return None
    return float(f"{x:.3g}") if isinstance(x, (int, float, np.floating)) else x


def card_text(row, tag):
    kv = []
    for f in FIELDS:
        v = row.get(f)
        v = round3(v) if not isinstance(v, str) else v
        kv.append(f"{f}={v if v is not None else 'null'}")
    return f"{tag}: " + ", ".join(kv)


def call_rank(client, cards_block, tags, cache, tag_prefix):
    key = tag_prefix + "|" + hashlib.sha256(cards_block.encode()).hexdigest()[:16]
    if key in cache:
        ranking = cache[key]
    else:
        r = client.chat.completions.create(
            model=MODEL, temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "user",
                       "content": PROMPT.format(cards=cards_block)}])
        try:
            ranking = json.loads(r.choices[0].message.content).get("ranking", [])
        except (json.JSONDecodeError, TypeError):
            ranking = []
        cache[key] = ranking
    seen = [t for t in ranking if t in set(tags)]
    missing = [t for t in tags if t not in set(seen)]
    return seen + missing  # unranked tags appended (counted by caller)


def rank_week(client, wk_cards, cache, seed, named=False, shuffle=False,
              tag_prefix="anon"):
    """Return per-symbol score (0=best..1=worst) for one week."""
    rng = np.random.default_rng(seed)
    syms = wk_cards["symbol"].tolist()
    scores = {s: [] for s in syms}
    for rnd in range(ROUNDS):
        perm = rng.permutation(len(syms))
        order = [syms[i] for i in perm]
        if named:
            tags = {s: s for s in syms}
        else:
            shuffled = rng.permutation(len(syms))
            tags = {s: f"ASSET_{i:03d}" for s, i in zip(syms, shuffled)}
        for b0 in range(0, len(order), BATCH):
            batch = order[b0:b0 + BATCH]
            if shuffle:
                batch = [batch[i] for i in rng.permutation(len(batch))]
            rows = wk_cards.set_index("symbol").loc[batch]
            block = "\n".join(card_text(rows.loc[s], tags[s]) for s in batch)
            ranked_tags = call_rank(client, block, [tags[s] for s in batch],
                                    cache, tag_prefix)
            inv = {tags[s]: s for s in batch}
            n = len(batch)
            for pos, t in enumerate(ranked_tags):
                if t in inv:
                    scores[inv[t]].append(pos / max(1, n - 1))
    return pd.Series({s: float(np.mean(v)) if v else np.nan
                      for s, v in scores.items()})


def week_seed(date, variant):
    h = hashlib.sha256(f"{date.date()}|{variant}|20260814".encode()).hexdigest()
    return int(h[:8], 16)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weeks", type=str, default=None)
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--named", action="store_true")
    ap.add_argument("--shuffle", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from dotenv import load_dotenv
    load_dotenv(".env")
    from openai import OpenAI
    client = OpenAI()

    cards = pd.read_parquet(OUT / "cards.parquet")
    cards["date"] = pd.to_datetime(cards["date"], utc=True)
    cards = cards[cards["date"] <= DEV_END]  # dev clip: holdout never ranked here
    if args.weeks:
        want = {pd.Timestamp(w, tz="UTC") for w in args.weeks.split(",")}
        cards = cards[cards["date"].isin(want)]

    variant = ("named" if args.named else "anon") + ("-shuf" if args.shuffle else "")
    out_path = OUT / args.out
    if out_path.exists():
        print(f"{out_path} exists — refusing to overwrite (stop rule)")
        return 1
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    results = []
    dates = sorted(cards["date"].unique())
    for i, d in enumerate(dates):
        wk = cards[cards["date"] == d]
        s = rank_week(client, wk, cache, week_seed(pd.Timestamp(d), "base"),
                      named=args.named, shuffle=args.shuffle,
                      tag_prefix=variant)
        for sym, v in s.items():
            results.append({"date": d, "symbol": sym, "score": v})
        CACHE.write_text(json.dumps(cache))
        print(f"{pd.Timestamp(d).date()} ({i+1}/{len(dates)}): {len(s)} ranked",
              flush=True)
    pd.DataFrame(results).to_parquet(out_path, index=False)
    print(f"written {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
