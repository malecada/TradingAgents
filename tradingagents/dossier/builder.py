"""Assemble one immutable, anonymized dossier per (symbol, decision Friday) (plan §6.2).

Decision time is Saturday 00:00 UTC after the Friday card date: cards use data through
Friday, text must satisfy as_of_ts <= decision time, and the position is held the
following week. Steps: numeric block -> text retrieval -> entity linking -> masking ->
typing/summaries -> selection within a token budget -> verification -> hash.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import pandas as pd

from tradingagents.dossier import store
from tradingagents.dossier.anonymizer import Masker
from tradingagents.dossier.calendar import render_calendar
from tradingagents.dossier.entities import Dictionary, Linker
from tradingagents.dossier.llm_text import TextLLMError
from tradingagents.dossier.numeric_card import numeric_block, render_numeric, weekly_path
from tradingagents.dossier.universe import base_symbol

BUILDER_VERSION = "dossier-v2.2"
TEXT_LOOKBACK_DAYS = 30
TOKEN_BUDGET = 9000           # approximate tokens for the text section (chars / 4)
CLASSIFY_WORKERS = 4
REDDIT_SHOWN_CAP = 8           # community posts among shown items
REDDIT_CAP = 25               # community posts per dossier, ranked by comment count (retrieval-time; disclosed)
_LINK_CACHE: dict[str, dict] = {}   # doc_id -> {base: salience}; rows repeat across the 50 symbols of a week
MAX_ITEMS = 25
MIN_BODY_CHARS = 120
OUT = Path("data/dossier/dossiers")
TYPE_PRIORITY = {"event": 0, "analysis_opinion": 1, "price_recap": 3, "promotional": 9, "unrelated": 9}


def decision_time(friday: pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(friday).normalize() + pd.Timedelta(days=1)


def _tokens(text: str) -> int:
    return max(1, len(text) // 4)


@dataclass
class Dossier:
    symbol: str
    base: str
    friday: pd.Timestamp
    decision_ts: pd.Timestamp
    alias: str
    numeric: dict
    items: list[dict]
    counts: dict
    alias_map: dict
    leaks: list[str]
    text: str
    sha256: str

    def to_json(self) -> dict:
        return {"builder_version": BUILDER_VERSION, "symbol": self.symbol, "base": self.base,
                "friday": self.friday.isoformat(), "decision_ts": self.decision_ts.isoformat(),
                "alias": self.alias, "numeric": self.numeric, "items": self.items, "counts": self.counts,
                "alias_map": self.alias_map, "leaks": self.leaks, "text": self.text, "sha256": self.sha256}


def _links_for(row, linker: Linker) -> dict:
    cached = _LINK_CACHE.get(row.doc_id)
    if cached is None:
        if len(_LINK_CACHE) > 300_000:
            _LINK_CACHE.clear()
        cached = dict(linker.link_assets(row.title, row.body))
        _LINK_CACHE[row.doc_id] = cached
    return cached


def _comments(extra: str) -> int:
    try:
        return int(json.loads(extra or "{}").get("num_comments") or 0)
    except (ValueError, TypeError):
        return 0


def retrieve_text(base: str, linker: Linker, decision_ts: pd.Timestamp, root=store.DEFAULT_ROOT,
                  lookback_days: int = TEXT_LOOKBACK_DAYS, reddit_cap: int = REDDIT_CAP) -> pd.DataFrame:
    """Store rows in the lookback window, observable at decision time, linked to ``base``.
    News rows are all kept; community posts are capped at ``reddit_cap`` per dossier, taking the
    most-commented posts where the asset is the primary subject."""
    rows = store.query(decision_ts - pd.Timedelta(days=lookback_days), decision_ts, decision_ts, root=root)
    if rows.empty:
        return rows.assign(salience=pd.Series(dtype=str))
    salience = [_links_for(r, linker).get(base) for r in rows.itertuples(index=False)]
    rows = rows.assign(salience=salience)
    rows = rows[rows["salience"].notna()]
    news = rows[rows["source"] != "reddit"]
    reddit = rows[(rows["source"] == "reddit") & (rows["salience"] == "primary")].copy()
    if len(reddit) > reddit_cap:
        reddit["_c"] = reddit["extra"].map(_comments)
        reddit = reddit.sort_values("_c", ascending=False).head(reddit_cap).drop(columns="_c")
    return pd.concat([news, reddit]).sort_values("event_ts").reset_index(drop=True)


def select_items(classified: list[dict], budget_tokens: int = TOKEN_BUDGET, max_items: int = MAX_ITEMS) -> list[dict]:
    """Events first, then analysis; new information before follow-ups; newer before older;
    primary-salience before mentioned. Price recaps are counted, not included."""
    keep = [c for c in classified if c["type"] in ("event", "analysis_opinion")]
    keep.sort(key=lambda c: (TYPE_PRIORITY[c["type"]], 0 if c["salience"] == "primary" else 1,
                             0 if c["novelty"] == "new_information" else 1, -c["event_ts"].value))
    out, used, reddit_shown = [], 0, 0
    for c in keep:
        cost = _tokens(c["summary"]) + 12
        if used + cost > budget_tokens or len(out) >= max_items:
            break
        if c["source"] == "reddit":
            if reddit_shown >= REDDIT_SHOWN_CAP:
                continue
            reddit_shown += 1
        out.append(c)
        used += cost
    out.sort(key=lambda c: c["event_ts"])
    return out


def render(alias: str, numeric_text: str, items: list[dict], counts: dict, decision_ts: pd.Timestamp,
           calendar_text: str = "") -> str:
    lines = [f"# Dossier for {alias}", "", "## Numeric profile (relative to this week's universe)", numeric_text, "",
             calendar_text,
             f"## News and discussion, last {TEXT_LOOKBACK_DAYS} days",
             f"Items retrieved: {counts['retrieved']}; events {counts['event']}, analysis {counts['analysis_opinion']}, "
             f"price recaps {counts['price_recap']} (omitted), promotional/unrelated {counts['promotional'] + counts['unrelated']} (omitted); "
             f"shown: {len(items)}.", ""]
    for n, it in enumerate(items, 1):
        days = (decision_ts.normalize() - it["event_ts"].normalize()).days
        when = "today" if days == 0 else f"{days} days ago"
        src = "community post" if it["source"] == "reddit" else "news"
        lines.append(f"- [t{n}] [{when}, {src}, {it['type']}, {it['novelty']}] {it['summary']}")
    if not items:
        lines.append("- No qualifying items.")
    return "\n".join(lines) + "\n"


def build(symbol: str, friday: pd.Timestamp, cards: pd.DataFrame, dictionary: Dictionary, linker: Linker,
          text_llm, seed: int, store_root=store.DEFAULT_ROOT, klines_dir=None, out_dir: Path | None = OUT) -> Dossier:
    friday = pd.Timestamp(friday)
    decision_ts = decision_time(friday)
    base = base_symbol(symbol)
    masker = Masker(dictionary, decision_ts, seed, focus_asset=base)
    alias = masker.alias("asset", base)
    path = weekly_path(symbol, friday, **({"klines_dir": klines_dir} if klines_dir else {}))
    numeric = numeric_block(cards, symbol, friday, path)
    numeric_text = masker.mask_text(render_numeric(numeric))
    rows = retrieve_text(base, linker, decision_ts, root=store_root)
    counts = {k: 0 for k in TYPE_PRIORITY}
    counts["retrieved"] = int(len(rows))
    counts["failed"] = 0
    counts["leaky"] = 0
    classified = []
    candidates = []
    for r in rows.itertuples(index=False):
        body = (r.body or "")[:6000]
        if len((r.title or "") + body) < MIN_BODY_CHARS and r.source != "reddit":
            continue
        candidates.append((r, masker.mask_text(f"{r.title}\n{body}".strip())))

    def classify(pair):
        r, masked = pair
        try:
            return r, text_llm.classify(masked)
        except TextLLMError:
            return r, None

    with ThreadPoolExecutor(max_workers=CLASSIFY_WORKERS) as pool:
        for r, out in pool.map(classify, candidates):
            if out is None:                  # one bad article must not sink the dossier; counted and disclosed
                counts["failed"] += 1
                continue
            counts[out["type"]] += 1
            if alias not in out["affected_aliases"] and r.salience != "primary":
                continue
            summary = masker.mask_text(out["summary"])       # the model may re-derive names from context
            if masker.verify(summary):
                counts["leaky"] += 1
                continue
            classified.append({"doc_id": r.doc_id, "source": r.source, "outlet": r.outlet, "event_ts": pd.Timestamp(r.event_ts),
                               "as_of_ts": pd.Timestamp(r.as_of_ts), "salience": r.salience, "type": out["type"],
                               "novelty": out["novelty"], "summary": summary})
    items = select_items(classified)
    text = render(alias, numeric_text, items, counts, decision_ts, render_calendar(decision_ts, numeric))
    leaks = masker.verify(text)
    payload = {"builder_version": BUILDER_VERSION, "symbol": symbol, "friday": friday.isoformat(),
               "text": text, "numeric": numeric}
    sha = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    items_json = [{**it, "event_ts": it["event_ts"].isoformat(), "as_of_ts": it["as_of_ts"].isoformat()} for it in items]
    d = Dossier(symbol, base, friday, decision_ts, alias, numeric, items_json, counts, masker.mapping(), leaks, text, sha)
    if out_dir is not None:
        target = Path(out_dir) / friday.strftime("%Y-%m-%d") / f"{symbol}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(d.to_json(), indent=1, default=str))
    return d
