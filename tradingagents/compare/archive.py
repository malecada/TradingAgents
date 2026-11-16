"""Public news archive as a second text source of the direct-comparison configuration (Charter 5).

The archive is a dump of an aggregated crypto news feed (Hugging Face dataset
``maryamfakhari/crypto-news-coindesk-2020-2025``, CoinDesk Data feed, CC-BY-NC-4.0). One row is one article
of one outlet: a feed id, a publication time in Iran local time, a title and a short excerpt. This module
turns the rows into rows of the bitemporal text store (``tradingagents.dossier.store``) under the source
``ccnews``. Outlets the present store already holds are left out. No outcome is read and no model is called.

Availability. The archive carries no capture time (``last_update`` is a re-index time on six days between
December 2024 and February 2025). The feed id is assigned in ingestion order, which gives a clock: the
running maximum of the median publication time of the 50 articles ingested before an article. An article
published no more than one hour before that clock was ingested live and is taken as observable one hour
after its publication. Every other article was ingested late (a backfill of an outlet's history) and is
taken as observable 24 hours after the clock, which covers the lag of the clock behind the feed. The feed
went live in July 2022; everything published earlier is backfill and observable only from then on.
"""
from __future__ import annotations

import html
import re

import numpy as np
import pandas as pd

from tradingagents.dossier import store

SOURCE = "ccnews"
FEED_TZ = "Asia/Tehran"
PRESENT_OUTLETS = ("cointelegraph", "coindesk", "theblock")   # already in the store through the page archive
AVAIL_WINDOW = 50
AVAIL_MIN_HISTORY = 10
LIVE_TOLERANCE = pd.Timedelta(hours=1)   # published at most this long before the feed clock: ingested live
LIVE_MARGIN = pd.Timedelta(hours=1)      # a live article is observable this long after publication
LATE_MARGIN = pd.Timedelta(hours=24)     # a late article is observable this long after the feed clock
RAW_COLUMNS = ["id", "published_on", "title", "body", "url", "categories", "source"]
_EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
# feed boilerplate at the end of an excerpt: "The post <title> appeared first on <outlet> ."
_BOILER = re.compile(r"\s*The post\s.{1,400}?\sappeared first on\s[^.]{1,80}?\s?\.?\s*$", re.S)


def to_utc(published_on: pd.Series) -> pd.Series:
    """Publication times of the feed (Iran local time, no offset) as UTC; ambiguous clock times become NaT."""
    local = pd.to_datetime(published_on, errors="coerce")
    return local.dt.tz_localize(FEED_TZ, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")


def clean(text) -> str:
    """HTML entities resolved, the feed boilerplate cut, whitespace collapsed."""
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return ""
    return " ".join(_BOILER.sub("", html.unescape(str(text))).split())


def feed_clock(event_ts: pd.Series, feed_id: pd.Series, window: int = AVAIL_WINDOW) -> pd.Series:
    """Running maximum, in feed order, of the median publication time of the ``window`` preceding articles
    (seconds since the epoch; missing for the first articles). Index of ``event_ts`` is kept."""
    order = np.argsort(feed_id.to_numpy(), kind="stable")
    secs = pd.Series((event_ts.iloc[order] - _EPOCH).dt.total_seconds().to_numpy())
    clock = secs.rolling(window, min_periods=AVAIL_MIN_HISTORY).median().shift(1).cummax()
    out = np.empty(len(secs))
    out[order] = clock.to_numpy()
    return pd.Series(out, index=event_ts.index)


def availability(event_ts: pd.Series, feed_id: pd.Series, window: int = AVAIL_WINDOW) -> pd.Series:
    """Observable-from time of every article (see the module text). Index of ``event_ts`` is kept."""
    clock = feed_clock(event_ts, feed_id, window)
    secs = (event_ts - _EPOCH).dt.total_seconds()
    late = secs < clock - LIVE_TOLERANCE.total_seconds()             # False where the clock is still missing
    seen = np.where(late, clock + LATE_MARGIN.total_seconds(), secs + LIVE_MARGIN.total_seconds())
    return pd.to_datetime(pd.Series(seen, index=event_ts.index), unit="s", utc=True).dt.round("s")


def store_rows(raw: pd.DataFrame, start: str = "2022-01-01", end: str = "2025-01-01") -> tuple[pd.DataFrame, dict]:
    """Store rows of the archive's new outlets with ``start <= event_ts < end`` and the count of every exclusion.

    The availability rule runs on the whole feed before any exclusion, so the neighbours of an article are
    its true neighbours in the feed.
    """
    missing = set(RAW_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"archive rows missing columns: {sorted(missing)}")
    feed = raw[RAW_COLUMNS].copy()
    feed["event_ts"] = to_utc(feed["published_on"])
    counts = {"rows": len(feed), "no_time": int(feed["event_ts"].isna().sum())}
    feed = feed[feed["event_ts"].notna()]
    feed["as_of_ts"] = availability(feed["event_ts"], feed["id"])
    lo, hi = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    feed = feed[(feed["event_ts"] >= lo) & (feed["event_ts"] < hi)]
    counts["in_window"] = len(feed)
    present = feed["source"].isin(PRESENT_OUTLETS)
    counts["present_outlets"] = int(present.sum())
    feed = feed[~present].sort_values("id")
    dup = feed["url"].duplicated(keep="first") & feed["url"].notna()
    counts["duplicate_url"] = int(dup.sum())
    feed = feed[~dup]
    out = pd.DataFrame({
        "doc_id": [store.doc_id(SOURCE, str(i)) for i in feed["id"]],
        "event_ts": feed["event_ts"].dt.round("s").to_numpy(), "as_of_ts": feed["as_of_ts"].to_numpy(),
        "source": SOURCE, "outlet": feed["source"].astype(str).to_numpy(),
        "url": feed["url"].fillna("").astype(str).to_numpy(),
        "title": [clean(t) for t in feed["title"]], "body": [clean(b) for b in feed["body"]],
        "lang": "en", "author": "",
        "extra": [store.extra_json(feed_id=int(i), categories="" if pd.isna(c) else str(c))
                  for i, c in zip(feed["id"], feed["categories"])]})
    empty = (out["title"].str.len() + out["body"].str.len()) == 0
    counts["empty"] = int(empty.sum())
    out = out[~empty].reset_index(drop=True)
    counts["stored"] = len(out)
    counts["late"] = int(((out["as_of_ts"] - out["event_ts"]) > LIVE_MARGIN + pd.Timedelta(seconds=1)).sum())
    return store.normalize(out), counts
