"""Wayback Machine discovery and fetch for crypto news outlets (plan §6.1).

Discovery uses the CDX API per outlet section and month; the first capture
timestamp of a canonical URL is the as_of bound (the text was observable from
that capture onward). Fetch pulls the raw capture (``id_`` flag) and extracts
title, publication date and body with trafilatura. Politeness: one request per
``FETCH_INTERVAL_S`` seconds with an identifying user agent.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
import time
from urllib.parse import urlsplit, urlunsplit

import pandas as pd
import requests

CDX = "http://web.archive.org/cdx/search/cdx"
USER_AGENT = "master-thesis-research-bot/0.1 (academic research; contact: malecekadam1@gmail.com)"
FETCH_INTERVAL_S = 2.5
CDX_INTERVAL_S = 2.0
TIMEOUT_S = 90

# outlet -> (cdx url pattern with {ym} where applicable, article regex on canonical url, dated_path)
OUTLETS = {
    "coindesk": {
        "patterns": ["coindesk.com/markets/{y}/{m}/*", "coindesk.com/policy/{y}/{m}/*",
                     "coindesk.com/tech/{y}/{m}/*", "coindesk.com/business/{y}/{m}/*",
                     "coindesk.com/web3/{y}/{m}/*", "coindesk.com/layer2/{y}/{m}/*",
                     "coindesk.com/finance/{y}/{m}/*", "coindesk.com/consensus-magazine/{y}/{m}/*"],
        "article": re.compile(r"^https://www\.coindesk\.com/[a-z0-9-]+/\d{4}/\d{2}/\d{2}/[a-z0-9-]+/?$"),
        "dated_path": True,
    },
    "cointelegraph": {
        "patterns": ["cointelegraph.com/news/*"],
        "article": re.compile(r"^https://cointelegraph\.com/news/[a-z0-9-]+/?$"),
        "dated_path": False,
    },
    "theblock": {
        "patterns": ["theblock.co/post/*"],
        "article": re.compile(r"^https://www\.theblock\.co/post/\d+/[a-z0-9-]+/?$"),
        "dated_path": False,
    },
}
_AMP = re.compile(r"/amp/?$")


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    host = parts.netloc.lower()
    if host in ("coindesk.com", "theblock.co"):
        host = "www." + host
    if host == "www.cointelegraph.com":
        host = "cointelegraph.com"
    path = _AMP.sub("/", parts.path)
    path = re.sub(r"/+", "/", path)
    if not path.endswith("/"):
        path += "/"
    return urlunsplit(("https", host, path.lower(), "", ""))


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def discover(outlet: str, year: int, month: int, session=None, sleep=time.sleep) -> pd.DataFrame:
    """Canonical article URLs first captured in ``year-month`` for ``outlet``.

    Dated-path outlets are queried by path; undated outlets by capture window
    (``from``/``to``), which catches articles at or shortly after publication.
    Returns columns: outlet, url, first_ts (UTC), digest.
    """
    spec = OUTLETS[outlet]
    session = session or _session()
    ym = f"{year:04d}{month:02d}"
    frames = []
    for pattern in spec["patterns"]:
        params = {"url": pattern.format(y=f"{year:04d}", m=f"{month:02d}"), "output": "json",
                  "filter": "statuscode:200", "collapse": "urlkey",
                  "fl": "timestamp,original,digest", "limit": 20000}
        if not spec["dated_path"]:
            params.update({"from": ym, "to": ym})
        for attempt in range(1, 6):
            try:
                r = session.get(CDX, params=params, timeout=TIMEOUT_S)
            except requests.RequestException:
                r = None
            if r is not None and r.status_code == 200:
                break
            sleep(min(10 * 2 ** (attempt - 1), 120))
        else:
            raise RuntimeError(f"CDX failed for {pattern} {ym}")
        rows = r.json() if r.text.strip() else []
        if rows:
            frames.append(pd.DataFrame(rows[1:], columns=rows[0]))
        sleep(CDX_INTERVAL_S)
    if not frames:
        return pd.DataFrame(columns=["outlet", "url", "first_ts", "digest"])
    df = pd.concat(frames, ignore_index=True)
    df["url"] = df["original"].map(canonical_url)
    df = df[df["url"].map(lambda u: bool(spec["article"].match(u)))]
    df["first_ts"] = pd.to_datetime(df["timestamp"], format="%Y%m%d%H%M%S", utc=True)
    df = df.sort_values("first_ts").drop_duplicates("url", keep="first")
    df["outlet"] = outlet
    return df[["outlet", "url", "first_ts", "digest"]].reset_index(drop=True)


@dataclass
class Fetched:
    url: str
    capture_ts: pd.Timestamp
    status: int
    title: str | None
    date: str | None
    author: str | None
    text: str | None


def fetch_capture(url: str, capture_ts: pd.Timestamp, session=None) -> Fetched:
    import trafilatura
    session = session or _session()
    ts = pd.Timestamp(capture_ts).strftime("%Y%m%d%H%M%S")
    r = session.get(f"https://web.archive.org/web/{ts}id_/{url}", timeout=TIMEOUT_S)
    if r.status_code != 200:
        return Fetched(url, capture_ts, r.status_code, None, None, None, None)
    meta = trafilatura.extract(r.text, output_format="json", with_metadata=True,
                               include_comments=False, favor_precision=True)
    m = json.loads(meta) if meta else {}
    return Fetched(url, capture_ts, 200, m.get("title"), m.get("date"), m.get("author"),
                   m.get("text"))


def date_from_url(url: str):
    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def to_store_row(outlet: str, f: Fetched) -> dict | None:
    """Store row or None when the capture holds no usable article text."""
    from tradingagents.dossier.store import doc_id, extra_json
    if f.status != 200 or not f.text or len(f.text) < 200:
        return None
    pub = f.date or date_from_url(f.url)
    if pub is None:
        return None
    event_ts = pd.Timestamp(pub, tz="UTC")
    as_of = pd.Timestamp(f.capture_ts)
    if as_of < event_ts - pd.Timedelta(days=2):
        # metadata date later than the capture: untrustworthy, keep the capture time
        event_ts = as_of
    return {"doc_id": doc_id("wayback", f.url), "event_ts": event_ts, "as_of_ts": as_of,
            "source": "wayback", "outlet": outlet, "url": f.url, "title": f.title or "",
            "body": f.text, "lang": "en", "author": f.author or "",
            "extra": extra_json(capture_ts=str(as_of))}
