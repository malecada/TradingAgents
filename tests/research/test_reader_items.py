from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.dossier.anonymizer import Masker  # noqa: E402
from tradingagents.dossier.builder import CANONICAL_SEED  # noqa: E402
from tradingagents.dossier.entities import Linker, build_dictionary  # noqa: E402
from tradingagents.reader.items import DOC_COLUMNS, ITEM_COLUMNS, FastLinker, load_typing_cache, month_rows, typing_key  # noqa: E402

BASES = ["BTC", "ETH", "SOL", "OP", "PEPE"]
TEXTS = [
    ("Solana outage drags SOL lower", "Traders rotated into ether. Bitcoin held. bitcoin ETF flows rose."),
    ("Op-ed: the op is over", "nothing"),
    ("$OP unlock next week", "Optimism releases tokens. Optimism holders watch. PEPE and pepe mentioned once."),
    ("", "binance lists a coin; the SEC responds; ETH, Ether and ethereum all count."),
]


def _row(doc_id, source, title, body, ts="2023-06-10 12:00"):
    t = pd.Timestamp(ts, tz="UTC")
    return {"doc_id": doc_id, "event_ts": t, "as_of_ts": t + pd.Timedelta(hours=6), "source": source, "outlet": "x", "url": "u",
            "title": title, "body": body, "lang": "en", "author": None, "extra": None}


def test_fast_linker_equals_linker():
    d = build_dictionary(BASES)
    slow, fast = Linker(d), FastLinker(d)
    for title, body in TEXTS:
        assert fast.link_assets(title, body) == slow.link_assets(title, body)
        assert fast.mentions(f"{title} {body}") == slow.mentions(f"{title} {body}")


def test_month_rows_joins_typing_and_keeps_untyped_links(tmp_path):
    d = build_dictionary(BASES)
    title = "Solana validators halt the network after a bug"
    body = "Solana stopped producing blocks for several hours. Bitcoin was unaffected. " + "Filler sentence. " * 10
    rows = pd.DataFrame([
        _row("d1", "wayback", title, body),
        _row("d2", "wayback", "Bitcoin steady", "Short."),                     # linked, never typed: below the length floor
        _row("d3", "wayback", "Weather report", "Nothing about any asset. " * 10),   # no link: dropped
        _row("d4", "wayback", "Ethereum upgrade ships", "Ethereum developers shipped the upgrade. " * 6),   # typed call missing from cache
    ])
    canon = Masker(d, rows.event_ts[0], CANONICAL_SEED)
    masked = canon.mask_text(f"{title}\n{body[:6000]}".strip())
    sol, btc = canon.alias("asset", "SOL"), canon.alias("asset", "BTC")
    value = {"type": "event", "summary": f"{sol} halted block production for several hours after a software bug.",
             "novelty": "new_information", "affected_aliases": [sol, "Asset_ZZ"]}
    cache_file = tmp_path / "cache.jsonl"
    cache_file.write_text(json.dumps({"key": typing_key(masked, "h"), "value": value}) + "\n\n")
    cache = load_typing_cache(cache_file)

    items, docs = month_rows(rows, d, FastLinker(d), cache, prompt_hash="h")
    assert list(items.columns) == ITEM_COLUMNS and list(docs.columns) == DOC_COLUMNS
    got = {(r.doc_id, r.base): r for r in items.itertuples(index=False)}
    assert set(got) == {("d1", "SOL"), ("d1", "BTC"), ("d2", "BTC"), ("d4", "ETH")}
    assert got[("d1", "SOL")].typed and got[("d1", "SOL")].affected and got[("d1", "SOL")].salience == "primary"
    assert got[("d1", "SOL")].type == "event" and got[("d1", "SOL")].novelty == "new_information"
    assert got[("d1", "BTC")].typed and not got[("d1", "BTC")].affected and got[("d1", "BTC")].salience == "mentioned"
    assert not got[("d2", "BTC")].typed and pd.isna(got[("d2", "BTC")].type)
    assert not got[("d4", "ETH")].typed

    assert list(docs.doc_id) == ["d1"]
    doc = docs.iloc[0]
    assert sol in doc.summary and "Solana" not in doc.summary and not doc.leaky
    assert json.loads(doc.alias_map) == {sol: "asset:SOL"} and btc not in doc.summary


def test_month_rows_flags_and_blanks_leaks(tmp_path):
    d = build_dictionary(BASES)
    title, body = "Bitcoin miners sell reserves", "Bitcoin miners sold a large part of their reserves this week. " * 3
    rows = pd.DataFrame([_row("d1", "reddit", title, body)])
    canon = Masker(d, rows.event_ts[0], CANONICAL_SEED)
    masked = canon.mask_text(f"{title}\n{body[:6000]}".strip())
    btc = canon.alias("asset", "BTC")
    value = {"type": "event", "summary": f"Bitcoin miners sold reserves of {btc}; Asset_ZZ and Glassnode were cited.",
             "novelty": "new_information", "affected_aliases": [btc]}
    items, docs = month_rows(rows, d, FastLinker(d), {typing_key(masked, "h"): value}, prompt_hash="h")
    summary = docs.iloc[0].summary
    assert "Bitcoin" not in summary and "Asset_ZZ" not in summary and "[entity]" in summary and "Glassnode" not in summary
    assert items.iloc[0].affected and not docs.iloc[0].leaky
