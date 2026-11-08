from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.dossier import store  # noqa: E402
from tradingagents.dossier.builder import build, decision_time, select_items  # noqa: E402
from tradingagents.dossier.entities import Linker, build_dictionary  # noqa: E402


class StubLLM:
    def __init__(self):
        self.seen = []

    def classify(self, text):
        self.seen.append(text)
        if "exploit" in text:
            return {"type": "event", "summary": "An exploit drained funds from a Bitcoin lending protocol on Ethereum.",
                    "novelty": "new_information", "affected_aliases": [text.split()[0]]}
        if "price" in text.lower():
            return {"type": "price_recap", "summary": "Prices moved.", "novelty": "none", "affected_aliases": []}
        return {"type": "analysis_opinion", "summary": "Commentary on the asset.", "novelty": "none",
                "affected_aliases": [text.split()[0]]}


def test_build_dossier_end_to_end(tmp_path):
    friday = pd.Timestamp("2024-01-05", tz="UTC")
    cards = pd.DataFrame({"date": [friday] * 2, "symbol": ["BTCUSDT", "ETHUSDT"], "ret_4w": [0.1, 0.2], "ret_12w": [0.5, 0.1],
                          "dist_26w_high": [0, -0.3], "vol_ewma20": [0.5, 0.9], "volvol_20": [0.1, 0.2], "dvol_30d": [3e9, 1e9],
                          "mcap_cm": [1e11, 1e10], "funding_3d": [0.0001, 0.0], "funding_30d": [0.0001] * 2,
                          "d_adract_30d": [0.05, 0.0], "d_txcnt_30d": [0.0, 0.1], "unlock_next30_pct": [np.nan] * 2,
                          "unlock_prev30_pct": [np.nan] * 2, "age_weeks": [400, 300], "category": ["Layer 1"] * 2, "size_rank": [1, 2]})
    rows = pd.DataFrame([
        {"doc_id": "1", "event_ts": "2024-01-03", "as_of_ts": "2024-01-03T02:00", "source": "wayback", "outlet": "coindesk",
         "url": "u1", "title": "Bitcoin lending protocol hit by exploit", "body": "An exploit on a Bitcoin lending protocol drained funds on Wednesday. " * 3, "lang": "en", "author": "", "extra": "{}"},
        {"doc_id": "2", "event_ts": "2024-01-04", "as_of_ts": "2024-01-04", "source": "wayback", "outlet": "coindesk",
         "url": "u2", "title": "Bitcoin price climbs toward $45,000", "body": "Bitcoin price rose 3% on Thursday as traders bought the dip. " * 3, "lang": "en", "author": "", "extra": "{}"},
        {"doc_id": "3", "event_ts": "2024-01-04", "as_of_ts": "2024-01-07", "source": "wayback", "outlet": "coindesk",
         "url": "u3", "title": "Bitcoin ETF decision looms", "body": "Analysts weigh the Bitcoin ETF decision. " * 4, "lang": "en", "author": "", "extra": "{}"},
        {"doc_id": "4", "event_ts": "2024-01-02", "as_of_ts": "2024-01-02", "source": "wayback", "outlet": "coindesk",
         "url": "u4", "title": "Solana outage resolved", "body": "Solana validators restarted the network. " * 4, "lang": "en", "author": "", "extra": "{}"},
    ])
    store.upsert(rows, root=tmp_path / "text")
    d = build_dictionary(["BTC", "ETH", "SOL"])
    llm = StubLLM()
    dossier = build("BTCUSDT", friday, cards, d, Linker(d), llm, seed=1, store_root=tmp_path / "text",
                    klines_dir=tmp_path / "nokl", out_dir=tmp_path / "out")
    assert dossier.decision_ts == decision_time(friday) == pd.Timestamp("2024-01-06", tz="UTC")
    assert dossier.counts["retrieved"] == 2          # ETF item not observable yet; Solana item not linked
    assert dossier.counts["event"] == 1 and dossier.counts["price_recap"] == 1
    assert len(dossier.items) == 1 and dossier.items[0]["type"] == "event"
    assert "Bitcoin" not in dossier.items[0]["summary"] and "Ethereum" not in dossier.items[0]["summary"]
    assert "Bitcoin" not in dossier.text and "$45,000" not in dossier.text and dossier.leaks == []
    assert dossier.text.startswith(f"# Dossier for {dossier.alias}") and dossier.alias.startswith("Asset_")
    assert all("Bitcoin" not in t for t in llm.seen)   # the LLM only ever saw masked text
    assert (tmp_path / "out" / "2024-01-05" / "BTCUSDT.json").exists()


def test_select_items_priority_and_budget():
    ts = pd.Timestamp("2024-01-01", tz="UTC")
    items = [{"type": "analysis_opinion", "salience": "primary", "novelty": "none", "event_ts": ts, "summary": "a" * 40, "source": "wayback"},
             {"type": "event", "salience": "mentioned", "novelty": "follow_up", "event_ts": ts, "summary": "b" * 40, "source": "wayback"},
             {"type": "event", "salience": "primary", "novelty": "new_information", "event_ts": ts + pd.Timedelta(days=1), "summary": "c" * 40, "source": "reddit"},
             {"type": "price_recap", "salience": "primary", "novelty": "none", "event_ts": ts, "summary": "d" * 40, "source": "wayback"}]
    out = select_items(items, budget_tokens=50, max_items=10)
    assert [i["summary"][0] for i in out] == ["b", "c"] or [i["summary"][0] for i in out] == ["c", "b"]
    assert all(i["type"] != "price_recap" for i in select_items(items))


def test_calendar_block_and_item_ids():
    from tradingagents.dossier.calendar import next_fomc_days, render_calendar
    ts = pd.Timestamp("2024-01-06", tz="UTC")
    assert next_fomc_days(ts) == 25
    text = render_calendar(ts, {"unlock_next30_pct_supply": 3.1})
    assert "in 25 days" in text and "3.1%" in text and "2024" not in text


def test_reddit_cap_by_comments(tmp_path):
    from tradingagents.dossier.builder import retrieve_text
    rows = []
    for i in range(40):
        rows.append({"doc_id": f"r{i}", "event_ts": "2024-01-03", "as_of_ts": "2024-01-03", "source": "reddit",
                     "outlet": "cryptocurrency", "url": f"u{i}", "title": f"Bitcoin thought {i}", "body": "", "lang": "en",
                     "author": "", "extra": f'{{"num_comments": {i}}}'})
    rows.append({"doc_id": "n1", "event_ts": "2024-01-03", "as_of_ts": "2024-01-03", "source": "wayback", "outlet": "coindesk",
                 "url": "n", "title": "Bitcoin news", "body": "Bitcoin " * 30, "lang": "en", "author": "", "extra": "{}"})
    store.upsert(pd.DataFrame(rows), root=tmp_path / "t")
    d = build_dictionary(["BTC", "ETH"])
    got = retrieve_text("BTC", Linker(d), pd.Timestamp("2024-01-06", tz="UTC"), root=tmp_path / "t", reddit_cap=5)
    assert (got["source"] == "reddit").sum() == 5 and (got["source"] == "wayback").sum() == 1
    assert set(got[got["source"] == "reddit"]["doc_id"]) == {f"r{i}" for i in range(35, 40)}
