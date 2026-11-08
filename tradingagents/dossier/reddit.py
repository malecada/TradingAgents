"""Reddit posts via the Arctic Shift API (plan §6.1); as_of = created time.

Disclosure: the archive is retrieved after the fact, so deleted posts are
missing and scores reflect the retrieval date, not the decision date. Only
``created_utc``, title and body are used as point-in-time facts.
"""
from __future__ import annotations

import time

import pandas as pd
import requests

API = "https://arctic-shift.photon-reddit.com/api/posts/search"
USER_AGENT = "master-thesis-research-bot/0.1 (academic research; contact: malecekadam1@gmail.com)"
FIELDS = "id,created_utc,title,selftext,score,num_comments,author,link_flair_text,url,subreddit"
INTERVAL_S = 2.5
PAGE = 100
SUBREDDITS = ("CryptoCurrency", "Bitcoin", "ethereum")


def fetch_day(subreddit: str, day: pd.Timestamp, session=None, sleep=time.sleep) -> pd.DataFrame:
    """All posts created on ``day`` (UTC), paged by created_utc."""
    session = session or requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    start = int(pd.Timestamp(day).tz_convert("UTC").normalize().timestamp()) if pd.Timestamp(day).tzinfo \
        else int(pd.Timestamp(day, tz="UTC").normalize().timestamp())
    end = start + 86400
    after, rows = start, []
    while True:
        params = {"subreddit": subreddit, "after": after, "before": end, "limit": PAGE,
                  "sort": "asc", "fields": FIELDS}
        for attempt in range(1, 9):
            try:
                r = session.get(API, params=params, timeout=60)
            except requests.RequestException:
                r = None
            if r is not None and r.status_code == 200:
                break
            # 422 "Timeout. Maybe slow down a bit" is the API's soft rate limit: short pause, not exponential
            sleep(4.0 if (r is not None and r.status_code == 422) else min(5 * 2 ** (attempt - 1), 60))
        else:
            raise RuntimeError(f"Arctic Shift failed for {subreddit} {day}")
        data = r.json().get("data") or []
        rows.extend(data)
        sleep(INTERVAL_S)
        if len(data) < PAGE:
            break
        after = max(int(x["created_utc"]) for x in data) + 1
    return pd.DataFrame(rows)


def to_store_rows(posts: pd.DataFrame) -> pd.DataFrame:
    from tradingagents.dossier.store import COLUMNS, doc_id, extra_json
    if posts.empty:
        return pd.DataFrame(columns=COLUMNS)
    ts = pd.to_datetime(posts["created_utc"].astype(int), unit="s", utc=True)
    body = posts.get("selftext", pd.Series([""] * len(posts))).fillna("").astype(str)
    body = body.where(~body.isin(["[removed]", "[deleted]"]), "")
    out = pd.DataFrame({
        "doc_id": posts["id"].map(lambda i: doc_id("reddit", str(i))),
        "event_ts": ts, "as_of_ts": ts, "source": "reddit",
        "outlet": posts["subreddit"].astype(str).str.lower(),
        "url": "https://www.reddit.com/comments/" + posts["id"].astype(str),
        "title": posts["title"].fillna("").astype(str), "body": body, "lang": "en",
        "author": posts.get("author", pd.Series([""] * len(posts))).fillna("").astype(str),
        "extra": [extra_json(score=int(s) if pd.notna(s) else None,
                             num_comments=int(c) if pd.notna(c) else None, flair=f)
                  for s, c, f in zip(posts.get("score", [None] * len(posts)),
                                     posts.get("num_comments", [None] * len(posts)),
                                     posts.get("link_flair_text", [None] * len(posts)))],
    })
    return out[COLUMNS]
