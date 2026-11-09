"""Fill the asset-category attribute (coarse family) for the weekly universe from CoinGecko's public coin pages,
where the card panel (DefiLlama protocol categories) has none. Categories are a stable, non-dated attribute;
the current label is used for all weeks (disclosed: a coin that pivoted carries its present category).
Writes data/dossier/categories.json {symbol: {"id":..., "categories":[...]}}. Resumable.
Usage: dossier_categories_fetch.py [--top 50] [--start 2022-01-01]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dossier.universe import base_symbol, weekly_top  # noqa: E402

OUT = Path("data/dossier/categories.json")
CACHE = Path("data/dossier/coingecko_markets_top1000.json")
API = "https://api.coingecko.com/api/v3"


def coin_ids_by_symbol(session) -> dict[str, list[str]]:
    by = {}
    for x in json.loads(CACHE.read_text())["coins"]:           # top-1000 first: market rank disambiguates
        by.setdefault(x["symbol"].upper(), []).append(x["id"])
    r = session.get(f"{API}/coins/list", timeout=60)
    r.raise_for_status()
    full = {}
    for x in r.json():
        full.setdefault(x["symbol"].upper(), []).append(x["id"])
    return by, full


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=50)
    ap.add_argument("--start", default="2022-01-01")
    args = ap.parse_args()
    cards = pd.read_parquet("data/llm_rank_xs/cards.parquet")
    cards["date"] = pd.to_datetime(cards["date"], utc=True)
    symbols = sorted(weekly_top(cards, args.top, start=args.start)["symbol"].unique())
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    session = requests.Session()
    top, full = coin_ids_by_symbol(session)
    for sym in symbols:
        if sym in out:
            continue
        base = base_symbol(sym).upper()
        ids = top.get(base) or full.get(base) or []
        if len(ids) != 1:
            out[sym] = {"id": None, "categories": [], "note": f"{len(ids)} candidate ids"}
            continue
        while True:
            r = session.get(f"{API}/coins/{ids[0]}", params={"localization": "false", "tickers": "false", "market_data": "false",
                                                           "community_data": "false", "developer_data": "false"}, timeout=30)
            if r.status_code == 429:
                time.sleep(65)
                continue
            break
        cats = r.json().get("categories", []) if r.status_code == 200 else []
        out[sym] = {"id": ids[0], "categories": [c for c in cats if c]}
        OUT.write_text(json.dumps(out, indent=0, sort_keys=True))
        print(f"{sym}: {out[sym]['categories'][:3]}", flush=True)
        time.sleep(2.5)
    OUT.write_text(json.dumps(out, indent=0, sort_keys=True))
    print("done", len(out), "symbols;", sum(1 for v in out.values() if v["categories"]), "with categories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
