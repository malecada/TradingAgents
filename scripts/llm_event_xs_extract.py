"""llm_c1_event_xs — typed-event extractor (frozen prompt v1).

Modes:
  --sample          extract on data/llm_event_xs/p0_sample.parquet (300 articles)
  --sample-anon     anonymized re-extraction of the 50-article spot-check subset
  (full-corpus sweep mode added only if P0 passes)

Model: gpt-5.4-mini, temp 0, disk-cached (idempotent). Two-stage:
headline+summary first; content appended only when ambiguous=true (1 retry).
Every event requires a verbatim evidence span; spans not found in the
supplied text are dropped and counted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

OUTDIR = Path("data/llm_event_xs")
CACHE = OUTDIR / "extract_cache.json"
MODEL = "gpt-5.4-mini"

CLASSES = ["hack", "regulatory", "listing_delisting", "unlock_emission",
           "upgrade_partnership", "insolvency_halt"]

PROMPT = """You extract typed crypto events from a news article. Classes:
- hack: exploit, breach, funds stolen or drained from a protocol/venue
- regulatory: government/agency action — lawsuit, charge, settlement, ban,
  license grant/revocation, emergency order
- listing_delisting: an exchange lists or delists a specific asset
- unlock_emission: token unlock, vesting cliff, or emission-schedule news
  for a specific asset
- upgrade_partnership: protocol upgrade, mainnet launch, hard fork, or a
  concrete named partnership/acquisition involving the asset
- insolvency_halt: insolvency, bankruptcy, withdrawal halt or suspension,
  depeg, collapse of a venue/fund/stablecoin

Rules:
- Only report events the article itself asserts as fact or formal action
  (not speculation, price commentary, or opinion).
- asset = the primarily affected crypto asset or protocol token (use its
  common name or ticker). If the event affects a venue (exchange/fund) with
  no single asset, use the venue name.
- severity from IN-ARTICLE facts only: 3 = >$100M or >5% of supply or a
  top-20 venue/asset directly hit; 2 = >$10M or a top-100 asset directly
  hit; 1 = otherwise material but minor.
- evidence = verbatim quote from the given text supporting class+severity.
- If the given text is insufficient to decide, set "ambiguous": true.
- No knowledge of later events; judge only the given text.

Return ONLY a JSON object: {{"events": [{{"asset": str, "class": str,
"severity": 1|2|3, "evidence": str}}], "ambiguous": bool}}
Empty list if no qualifying event.

Article:
{text}"""

ENTITY_MASK = [
    r"FTX|Alameda", r"Terra|LUNA|UST\b", r"Celsius", r"Three Arrows|3AC",
    r"Voyager", r"BlockFi", r"Genesis", r"Silvergate", r"Signature Bank",
    r"Silicon Valley Bank|SVB", r"USDC|Circle", r"Tether|USDT", r"Binance",
    r"Coinbase", r"Kraken", r"Bitfinex", r"Huobi", r"OKX|OKEx", r"Gemini",
    r"Sam Bankman-Fried|SBF", r"Do Kwon", r"Changpeng Zhao|CZ\b",
    r"Bitcoin|BTC\b", r"Ethereum|ETH\b", r"Solana|SOL\b", r"Ripple|XRP\b",
]
DATE_MASK = (r"\b(?:January|February|March|April|May|June|July|August|"
             r"September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|"
             r"Aug|Sep|Sept|Oct|Nov|Dec)\.? ?\d{0,2},? ?(?:20\d{2})?\b"
             r"|\b20\d{2}\b")


def anonymize(text: str) -> str:
    for i, pat in enumerate(ENTITY_MASK):
        text = re.sub(pat, f"ENTITY_{i}", text, flags=re.IGNORECASE)
    return re.sub(DATE_MASK, "DATE", text)


def article_text(row, stage: int) -> str:
    parts = [str(row["headline"] or "")]
    if row.get("summary"):
        parts.append(str(row["summary"]))
    if stage == 2 and row.get("content"):
        parts.append(str(row["content"])[:4000])
    return "\n".join(p for p in parts if p)


def call_llm(client, text: str, cache: dict, tag: str) -> dict:
    key = tag + "|" + hashlib.sha256(text.encode()).hexdigest()[:16]
    if key in cache:
        return cache[key]
    r = client.chat.completions.create(
        model=MODEL, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": PROMPT.format(text=text)}])
    try:
        out = json.loads(r.choices[0].message.content)
    except (json.JSONDecodeError, TypeError):
        out = {"events": [], "ambiguous": True, "parse_error": True}
    cache[key] = out
    return out


def validate_spans(events: list, text: str) -> tuple:
    """Drop events whose evidence is not a (loose) substring of the text."""
    def norm(s):
        return re.sub(r"\s+", " ", s).strip().lower()
    kept, dropped = [], 0
    nt = norm(text)
    for e in events:
        ev = norm(str(e.get("evidence", "")))
        if ev and (ev in nt or ev[:80] in nt):
            kept.append(e)
        else:
            dropped += 1
    return kept, dropped


def extract_row(client, row, cache, anon: bool = False) -> dict:
    tag = "anon" if anon else "v1"
    t1 = article_text(row, 1)
    if anon:
        t1 = anonymize(t1)
    out = call_llm(client, t1, cache, tag)
    used_text = t1
    if out.get("ambiguous") and row.get("content"):
        t2 = article_text(row, 2)
        if anon:
            t2 = anonymize(t2)
        out = call_llm(client, t2, cache, tag)
        used_text = t2
    events, dropped = validate_spans(out.get("events", []), used_text)
    return {"events": events, "ambiguous": bool(out.get("ambiguous")),
            "spans_dropped": dropped}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--sample-anon", action="store_true")
    args = ap.parse_args()

    from dotenv import load_dotenv
    load_dotenv(Path(".env"))
    from openai import OpenAI
    client = OpenAI()

    sample = pd.read_parquet(OUTDIR / "p0_sample.parquet")
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    if args.sample:
        out_path = OUTDIR / "p0_extractor_labels.json"
        rows = sample.to_dict("records")
        anon = False
    elif args.sample_anon:
        out_path = OUTDIR / "p0_extractor_labels_anon.json"
        rng_rows = sample.sample(n=50, random_state=20260813)
        rows = rng_rows.to_dict("records")
        anon = True
    else:
        print("choose --sample or --sample-anon")
        return 1
    if out_path.exists():
        print(f"{out_path} exists — refusing to overwrite")
        return 1

    results = {}
    for i, row in enumerate(rows):
        res = extract_row(client, row, cache, anon=anon)
        results[str(row["sample_idx"])] = {
            "store": row["store"], "id": str(row["id"]),
            "headline": row["headline"], **res}
        if i % 20 == 0:
            CACHE.write_text(json.dumps(cache))
            print(f"{i+1}/{len(rows)}", flush=True)
    CACHE.write_text(json.dumps(cache))
    out_path.write_text(json.dumps(results, indent=1))
    n_ev = sum(len(r["events"]) for r in results.values())
    print(f"done: {len(results)} articles, {n_ev} events -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
