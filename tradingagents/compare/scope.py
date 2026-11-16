"""Scope of the archive material and the pilot weeks (Charter 5).

Typed are the archive documents with a primary link to a universe asset other than BTC or ETH inside the
seven-day window before the decision time of a test week in which that asset is in the universe. Archive
documents whose main subject is BTC or ETH are left out: they are four times as many as the rest, and the
present material already fills the BTC and ETH dossiers. The rule reads the link table and the universe
alone: no model call, no outcome.
"""
from __future__ import annotations

import random

import pandas as pd

from tradingagents.dossier.anonymizer import Masker
from tradingagents.dossier.builder import CANONICAL_SEED, MIN_BODY_CHARS
from tradingagents.dossier.entities import Dictionary
from tradingagents.reader.items import BODY_CHARS
from tradingagents.reader.reading import DECISION_OFFSET

from .dossier import WINDOW_DAYS

EXCLUDED = ("BTC", "ETH")
PILOT_SEED = 20261115
PILOT_WEEKS = 3


def typing_scope(items: pd.DataFrame, top: pd.DataFrame, fridays=None) -> pd.DataFrame:
    """(doc_id, event_ts) of the archive documents to type, in document order. ``items`` is the archive link
    table, ``top`` the universe; ``fridays`` restricts the weeks."""
    weeks = top if fridays is None else top[top["date"].isin(set(fridays))]
    rows = items[(items["salience"] == "primary") & ~items["base"].isin(EXCLUDED)]
    parts = []
    for friday, week in weeks.groupby("date"):
        decision = pd.Timestamp(friday) + DECISION_OFFSET
        win = rows[(rows["event_ts"] >= decision - pd.Timedelta(days=WINDOW_DAYS)) & (rows["event_ts"] <= decision)
                   & (rows["as_of_ts"] <= decision) & rows["base"].isin(set(week["base"]))]
        parts.append(win[["doc_id", "event_ts"]])
    out = pd.concat(parts, ignore_index=True).drop_duplicates("doc_id")
    return out.sort_values("doc_id").reset_index(drop=True)


def typing_text(title, body, event_ts, dictionary: Dictionary) -> str | None:
    """The masked text the typing call sees, by the rule of ``reader.items.month_rows`` (so the rebuilt link
    table finds the typing under the same key). None when the document is too short to type."""
    title, body = title or "", body or ""
    if len(title + body[:BODY_CHARS]) < MIN_BODY_CHARS:
        return None
    canon = Masker(dictionary, pd.Timestamp(event_ts), CANONICAL_SEED)
    return canon.mask_text(f"{title}\n{body[:BODY_CHARS]}".strip())


def pilot_weeks(fridays, n: int = PILOT_WEEKS, seed: int = PILOT_SEED) -> list:
    """The pilot weeks: a seeded draw from the test weeks, fixed before any model call."""
    return sorted(random.Random(seed).sample(sorted(fridays), n))
