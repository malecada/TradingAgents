"""Uncapped reading list for the reader configuration (Charter 2 draft).

One row per (document, linked asset) for every row of the text store, joined to the cached Flash
typing where the dossier build produced one. The dossier shows at most 25 items per asset-week; this
table keeps every admissible item, so attention counts and the extraction work list do not depend on
that cap. No LLM call and no outcome: the table follows from the text store, the entity dictionary
and the typing cache alone.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import pandas as pd

from tradingagents.dossier.anonymizer import Masker
from tradingagents.dossier.builder import CANONICAL_SEED, MIN_BODY_CHARS, _ROLE_TOKEN
from tradingagents.dossier.entities import Dictionary, Linker
from tradingagents.dossier.llm_text import CACHE, prompt_sha256, scrub_proper_nouns

ITEM_COLUMNS = ["doc_id", "base", "source", "outlet", "event_ts", "as_of_ts", "salience", "typed", "type",
                "novelty", "affected"]
DOC_COLUMNS = ["doc_id", "type", "novelty", "summary", "alias_map", "leaky"]
BODY_CHARS = 6000   # the typing call saw the title and the first 6000 body characters


class FastLinker(Linker):
    """Same matches as ``Linker``: a case-insensitive substring test skips the regex of every absent term."""

    def __init__(self, dictionary: Dictionary):
        super().__init__(dictionary)
        self._lower = [term.lower() for term, _, _, _ in self.patterns]

    def mentions(self, text: str) -> dict[tuple[str, str], int]:
        low = text.lower()
        counts: dict[tuple[str, str], int] = {}
        for (term, role, key, pat), lowered in zip(self.patterns, self._lower):
            if lowered not in low:
                continue
            n = len(pat.findall(text))
            if n:
                counts[(role, key)] = counts.get((role, key), 0) + n
        return counts


def load_typing_cache(path: Path = CACHE) -> dict[str, dict]:
    cache = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            cache[rec["key"]] = rec["value"]
    return cache


def typing_key(masked: str, prompt_hash: str | None = None) -> str:
    return hashlib.sha256(((prompt_hash or prompt_sha256()) + "|" + masked).encode("utf-8")).hexdigest()


def canonical_summary(summary: str, canon: Masker) -> tuple[str, bool]:
    """The dossier's de-identification steps on the canonical aliases: re-mask, scrub residual proper
    nouns, blank role tokens the masker never issued. Returns the text and whether a name still leaks."""
    text = canon.mask_text(summary)
    text, _ = scrub_proper_nouns(text)
    known = canon.mapping()
    text = _ROLE_TOKEN.sub(lambda m: m.group(0) if m.group(0) in known else "[entity]", text)
    return text, bool(canon.verify(text))


def month_rows(rows: pd.DataFrame, dictionary: Dictionary, linker: Linker, cache: dict[str, dict],
               prompt_hash: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(items, docs) for one month file of the store."""
    prompt_hash = prompt_hash or prompt_sha256()
    items, docs = [], []
    for r in rows.itertuples(index=False):
        title, body = r.title or "", r.body or ""
        links = linker.link_assets(title, body)
        if not links:
            continue
        typed = None
        affected: set[str] = set()
        if len(title + body[:BODY_CHARS]) >= MIN_BODY_CHARS or r.source == "reddit":
            canon = Masker(dictionary, pd.Timestamp(r.event_ts), CANONICAL_SEED)
            masked = canon.mask_text(f"{title}\n{body[:BODY_CHARS]}".strip())
            typed = cache.get(typing_key(masked, prompt_hash))
            if typed is not None:
                canon_map = canon.mapping()
                affected = {canon_map.get(a, "").split(":", 1)[-1] for a in typed["affected_aliases"]
                            if canon_map.get(a, "").startswith("asset:")}
                summary, leaky = canonical_summary(typed["summary"], canon)
                used = {alias: key for alias, key in canon.mapping().items()
                        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])", summary)}
                docs.append((r.doc_id, typed["type"], typed["novelty"], summary, json.dumps(used, sort_keys=True), leaky))
        for base, salience in links:
            items.append((r.doc_id, base, r.source, r.outlet, r.event_ts, r.as_of_ts, salience, typed is not None,
                          typed["type"] if typed else None, typed["novelty"] if typed else None, base in affected))
    return pd.DataFrame(items, columns=ITEM_COLUMNS), pd.DataFrame(docs, columns=DOC_COLUMNS)
