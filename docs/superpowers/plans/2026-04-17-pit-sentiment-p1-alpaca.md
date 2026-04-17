# PIT Sentiment P1 (Alpaca News) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a point-in-time sentiment data layer backed by Alpaca News, stored as DuckDB-queryable Parquet with bitemporal `(event_ts, as_of_ts)` columns, wired into the existing `crypto_sentiment` analyst via vendor routing, then validated by re-running the 2026-01-16→2026-04-15 BTC+ETH backtest with the analyst enabled.

**Architecture:** DuckDB + Parquet (`data/sentiment/alpaca/{year}/{month}.parquet`). A new `crypto_sentiment_pit` vendor is registered against the existing `get_crypto_google_news` method in `dataflows/interface.py`; `data_vendors["crypto_sentiment"]` selects between the live and PIT implementations. Agent tool names stay the same so the `crypto_sentiment_analyst` prompt needs no changes.

**Tech Stack:** Python 3.10+, DuckDB, pandas, requests (Alpaca REST), pytest, LangChain tool-calling, existing TradingAgents plumbing.

**Spec:** [docs/superpowers/specs/2026-04-17-pit-sentiment-p1-alpaca-design.md](../specs/2026-04-17-pit-sentiment-p1-alpaca-design.md)

**Refinement from spec:** The spec proposed a new `config["sentiment_mode"]` key. This plan implements the same behavior via the existing `data_vendors["crypto_sentiment"]` vendor-routing mechanism — adding a `crypto_sentiment_pit` vendor rather than a parallel flag. Same observable behavior, reuses existing code, no new routing path. Backtest scripts override `config["data_vendors"]["crypto_sentiment"] = "crypto_sentiment_pit"`.

---

## File structure

**Create:**
- `tradingagents/dataflows/sentiment_store.py` — DuckDB-backed bitemporal store (connect, upsert, PIT query)
- `tradingagents/dataflows/crypto_sentiment_pit.py` — PIT vendor impls: `get_crypto_news_pit`, `get_reddit_posts_pit_stub`
- `scripts/backfill_alpaca_news.py` — one-shot CLI for Alpaca News backfill
- `tests/dataflows/__init__.py` — (empty) makes `tests/dataflows/` a package
- `tests/dataflows/test_sentiment_store.py` — unit tests for store
- `tests/dataflows/test_crypto_sentiment_pit.py` — unit tests for PIT tool

**Modify:**
- `pyproject.toml:11-44` — add `duckdb>=1.0.0`, `pyarrow>=14.0.0`
- `tradingagents/dataflows/interface.py:39-42,96-103,105-111,182-185` — import & register PIT vendor
- `tradingagents/default_config.py:34-43` — no change to defaults (live stays default); document override in comment
- `scripts/generate_agent_signals.py:30-48,54-65` — add `--sentiment-mode` flag and `crypto_sentiment` analyst eligibility
- `THESIS_FINDINGS.md` — append new section with rerun results (only after validation)

---

## Prerequisites

- [ ] **Prereq 1: Alpaca account + API key**

Alpaca's News API (Benzinga-sourced) is free with any Alpaca account — no funding required. Go to https://alpaca.markets, create a paper trading account, generate API keys, and add to `.env` in the TradingAgents project root:

```bash
# Append to /home/malecada/master_thesis/TradingAgents/.env
ALPACA_API_KEY_ID=your-key-here
ALPACA_API_SECRET_KEY=your-secret-here
```

Verify manually:
```bash
cd /home/malecada/master_thesis/TradingAgents
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
r = requests.get(
    'https://data.alpaca.markets/v1beta1/news',
    headers={
        'APCA-API-KEY-ID': os.environ['ALPACA_API_KEY_ID'],
        'APCA-API-SECRET-KEY': os.environ['ALPACA_API_SECRET_KEY'],
    },
    params={'symbols': 'BTCUSD', 'limit': 1},
    timeout=30,
)
print(r.status_code, r.json().get('news', [])[:1])
"
```
Expected: `200` and one news item printed.

---

## Phase A — Foundation (sentiment_store)

### Task A1: Add DuckDB and pyarrow dependencies

**Files:**
- Modify: `pyproject.toml:11-44`

- [ ] **Step 1: Add deps**

Edit [pyproject.toml](../../pyproject.toml), adding after the `numpy>=1.24.0` line (around line 42):
```toml
    "duckdb>=1.0.0",
    "pyarrow>=14.0.0",
```

- [ ] **Step 2: Install**

```bash
cd /home/malecada/master_thesis/TradingAgents
pip install -e .
```
Expected: no errors; `duckdb` and `pyarrow` installed.

- [ ] **Step 3: Smoke-verify**

```bash
python -c "import duckdb, pyarrow; print(duckdb.__version__, pyarrow.__version__)"
```
Expected: version numbers printed, no ImportError.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore(deps): add duckdb and pyarrow for PIT sentiment store"
```

---

### Task A2: Write failing test — sentiment store round-trip

**Files:**
- Create: `tests/dataflows/__init__.py`
- Create: `tests/dataflows/test_sentiment_store.py`

- [ ] **Step 1: Create test package**

```bash
mkdir -p /home/malecada/master_thesis/TradingAgents/tests/dataflows
touch /home/malecada/master_thesis/TradingAgents/tests/dataflows/__init__.py
```

- [ ] **Step 2: Write the failing round-trip test**

Create `tests/dataflows/test_sentiment_store.py`:
```python
"""Unit tests for tradingagents.dataflows.sentiment_store."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from tradingagents.dataflows import sentiment_store


def _row(ts: datetime, article_id: int, symbols: str = "BTCUSD",
         headline: str = "Example", content: str = "", source: str = "Benzinga") -> dict:
    return {
        "event_ts": ts,
        "as_of_ts": ts,
        "id": article_id,
        "headline": headline,
        "content": content,
        "summary": "",
        "symbols": symbols,
        "source": source,
        "author": "",
        "url": f"https://example.com/{article_id}",
    }


def test_roundtrip_single_month(tmp_path):
    """Ingest 3 rows, query the window containing them, get them back."""
    base = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
    rows = pd.DataFrame([
        _row(base.replace(day=10), 1, headline="Article 1"),
        _row(base.replace(day=15), 2, headline="Article 2"),
        _row(base.replace(day=20), 3, headline="Article 3"),
    ])

    sentiment_store.upsert_alpaca_rows(rows, year=2024, month=1, root=tmp_path)

    out = sentiment_store.query_news(
        coin="bitcoin",
        ts_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ts_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
        as_of=datetime(2024, 2, 1, tzinfo=timezone.utc),
        root=tmp_path,
    )
    assert len(out) == 3
    assert sorted(out["headline"].tolist()) == ["Article 1", "Article 2", "Article 3"]
```

- [ ] **Step 3: Run and verify failure**

```bash
cd /home/malecada/master_thesis/TradingAgents
pytest tests/dataflows/test_sentiment_store.py::test_roundtrip_single_month -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.dataflows.sentiment_store'` (or `ImportError`).

---

### Task A3: Implement sentiment_store (minimum to pass round-trip)

**Files:**
- Create: `tradingagents/dataflows/sentiment_store.py`

- [ ] **Step 1: Write the module**

Create `tradingagents/dataflows/sentiment_store.py`:
```python
"""Bitemporal sentiment store backed by Parquet + DuckDB.

Layout: data/sentiment/alpaca/{year}/{month:02d}.parquet.
Every row has (event_ts, as_of_ts) so backtests can enforce
as_of_ts <= trade_date to avoid look-ahead bias.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd

DEFAULT_ROOT = Path("data/sentiment/alpaca")

COIN_TO_SYMBOL: dict[str, str] = {
    "bitcoin": "BTCUSD",
    "ethereum": "ETHUSD",
}

SCHEMA_COLS = [
    "event_ts", "as_of_ts", "id", "headline", "content",
    "summary", "symbols", "source", "author", "url",
]


def _month_path(root: Path, year: int, month: int) -> Path:
    return Path(root) / str(year) / f"{month:02d}.parquet"


def upsert_alpaca_rows(df: pd.DataFrame, year: int, month: int,
                       root: Path = DEFAULT_ROOT) -> int:
    """Merge rows into the month Parquet, deduping by `id`. Returns rows written."""
    if df.empty:
        return 0
    missing = set(SCHEMA_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"upsert missing columns: {sorted(missing)}")
    target = _month_path(root, year, month)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing = pd.read_parquet(target)
        combined = pd.concat([existing, df[SCHEMA_COLS]], ignore_index=True)
        combined = combined.drop_duplicates(subset=["id"], keep="last")
    else:
        combined = df[SCHEMA_COLS].drop_duplicates(subset=["id"], keep="last")
    combined.to_parquet(target, index=False)
    return len(combined)


def query_news(coin: str, ts_start: datetime, ts_end: datetime,
               as_of: datetime, limit: int = 50,
               root: Path = DEFAULT_ROOT) -> pd.DataFrame:
    """Return rows where event_ts in [ts_start, ts_end] AND as_of_ts <= as_of,
    filtered to the coin's symbol. Enforces the PIT rule."""
    symbol = COIN_TO_SYMBOL.get(coin.lower())
    if symbol is None:
        raise ValueError(f"Unsupported coin for sentiment store: {coin!r}")
    glob = f"{root}/*/*.parquet"
    con = duckdb.connect(":memory:")
    try:
        try:
            con.execute(f"CREATE VIEW news AS SELECT * FROM read_parquet('{glob}')")
        except duckdb.IOException:
            # No files yet
            return pd.DataFrame(columns=SCHEMA_COLS)
        sql = """
        SELECT event_ts, as_of_ts, id, headline, content, summary,
               symbols, source, author, url
        FROM news
        WHERE event_ts BETWEEN ? AND ?
          AND as_of_ts <= ?
          AND symbols LIKE ?
        ORDER BY event_ts DESC
        LIMIT ?
        """
        return con.execute(
            sql,
            [ts_start, ts_end, as_of, f"%{symbol}%", limit],
        ).fetchdf()
    finally:
        con.close()
```

- [ ] **Step 2: Run round-trip test**

```bash
pytest tests/dataflows/test_sentiment_store.py::test_roundtrip_single_month -v
```
Expected: PASS.

---

### Task A4: Add PIT-enforcement test (the critical one)

**Files:**
- Modify: `tests/dataflows/test_sentiment_store.py`

- [ ] **Step 1: Append the test**

Add to `tests/dataflows/test_sentiment_store.py`:
```python
def test_pit_filter_excludes_future_observations(tmp_path):
    """A row whose event_ts is before as_of but whose as_of_ts is AFTER
    must be excluded — this is the PIT rule."""
    rows = pd.DataFrame([
        # event ts in Jan; observed in Jan (visible at Feb 1)
        _row(datetime(2024, 1, 10, tzinfo=timezone.utc), 1, headline="Known early"),
        # event ts in Jan but only entered the store in March (NOT visible at Feb 1)
        {
            "event_ts": datetime(2024, 1, 25, tzinfo=timezone.utc),
            "as_of_ts": datetime(2024, 3, 5, tzinfo=timezone.utc),
            "id": 2, "headline": "Late ingest", "content": "",
            "summary": "", "symbols": "BTCUSD", "source": "x", "author": "", "url": "",
        },
    ])
    sentiment_store.upsert_alpaca_rows(rows, year=2024, month=1, root=tmp_path)

    out = sentiment_store.query_news(
        coin="bitcoin",
        ts_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ts_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
        as_of=datetime(2024, 2, 1, tzinfo=timezone.utc),
        root=tmp_path,
    )
    ids = out["id"].tolist()
    assert 1 in ids, "row observed before as_of should be visible"
    assert 2 not in ids, "row ingested after as_of must be filtered out"


def test_symbol_filter_isolates_coin(tmp_path):
    """bitcoin query must not return rows tagged only with ETHUSD."""
    rows = pd.DataFrame([
        _row(datetime(2024, 1, 10, tzinfo=timezone.utc), 1, symbols="BTCUSD"),
        _row(datetime(2024, 1, 11, tzinfo=timezone.utc), 2, symbols="ETHUSD"),
        _row(datetime(2024, 1, 12, tzinfo=timezone.utc), 3, symbols="BTCUSD,ETHUSD"),
        _row(datetime(2024, 1, 13, tzinfo=timezone.utc), 4, symbols="SOLUSD"),
    ])
    sentiment_store.upsert_alpaca_rows(rows, year=2024, month=1, root=tmp_path)

    btc = sentiment_store.query_news(
        coin="bitcoin",
        ts_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ts_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
        as_of=datetime(2024, 2, 1, tzinfo=timezone.utc),
        root=tmp_path,
    )
    assert sorted(btc["id"].tolist()) == [1, 3]

    eth = sentiment_store.query_news(
        coin="ethereum",
        ts_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ts_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
        as_of=datetime(2024, 2, 1, tzinfo=timezone.utc),
        root=tmp_path,
    )
    assert sorted(eth["id"].tolist()) == [2, 3]
```

- [ ] **Step 2: Run the full test file**

```bash
pytest tests/dataflows/test_sentiment_store.py -v
```
Expected: all 3 tests PASS.

- [ ] **Step 3: Commit Phase A**

```bash
git add tradingagents/dataflows/sentiment_store.py tests/dataflows/
git commit -m "feat(sentiment): add bitemporal DuckDB+Parquet sentiment store"
```

---

## Phase B — Alpaca backfill script

### Task B1: Write backfill_alpaca_news.py

**Files:**
- Create: `scripts/backfill_alpaca_news.py`

- [ ] **Step 1: Write the script**

Create `scripts/backfill_alpaca_news.py`:
```python
#!/usr/bin/env python
"""Backfill Alpaca News (Benzinga-sourced) into the bitemporal sentiment store.

Usage:
    python scripts/backfill_alpaca_news.py \\
        --start 2023-10-01 --end 2026-04-15 \\
        --symbols BTCUSD ETHUSD

Environment:
    ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY must be set in .env
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.dataflows import sentiment_store  # noqa: E402

ALPACA_NEWS_URL = "https://data.alpaca.markets/v1beta1/news"
INGEST_LAG_SECONDS = 60
HTML_TAG_RE = re.compile(r"<[^>]+>")

log = logging.getLogger("backfill_alpaca_news")


def parse_args():
    p = argparse.ArgumentParser(
        description="Backfill Alpaca News into the PIT sentiment store.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--start", required=True, help="Start date YYYY-MM-DD (UTC)")
    p.add_argument("--end", required=True, help="End date YYYY-MM-DD (UTC, exclusive)")
    p.add_argument("--symbols", nargs="+", default=["BTCUSD", "ETHUSD"])
    p.add_argument("--out-dir", default="data/sentiment/alpaca")
    p.add_argument("--batch-days", type=int, default=7,
                   help="Fetch window in days per Alpaca request")
    p.add_argument("--limit", type=int, default=50,
                   help="Alpaca API page size (max 50)")
    return p.parse_args()


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    return HTML_TAG_RE.sub("", text).strip()


def _headers() -> dict:
    key = os.environ.get("ALPACA_API_KEY_ID")
    sec = os.environ.get("ALPACA_API_SECRET_KEY")
    if not key or not sec:
        raise RuntimeError(
            "ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY missing. "
            "Add them to .env (see prerequisites in the plan)."
        )
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec}


def fetch_window(symbols: list[str], start: datetime, end: datetime,
                 limit: int = 50) -> Iterable[dict]:
    """Yield raw Alpaca news items within [start, end), paginating via next_page_token."""
    params = {
        "symbols": ",".join(symbols),
        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": limit,
        "include_content": "true",
        "sort": "asc",
    }
    backoff = 1.0
    while True:
        resp = requests.get(ALPACA_NEWS_URL, headers=_headers(),
                            params=params, timeout=30)
        if resp.status_code == 429:
            log.warning("429 rate limit — sleeping %.1fs", backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60.0)
            continue
        resp.raise_for_status()
        backoff = 1.0
        payload = resp.json()
        for item in payload.get("news", []) or []:
            yield item
        tok = payload.get("next_page_token")
        if not tok:
            return
        params["page_token"] = tok
        time.sleep(0.35)  # stay well under 200 req/min


def normalize(item: dict) -> dict:
    created = pd.to_datetime(item["created_at"], utc=True).to_pydatetime()
    symbols = ",".join(item.get("symbols") or [])
    return {
        "event_ts": created,
        "as_of_ts": created + timedelta(seconds=INGEST_LAG_SECONDS),
        "id": int(item["id"]),
        "headline": item.get("headline") or "",
        "content": strip_html(item.get("content")),
        "summary": strip_html(item.get("summary")),
        "symbols": symbols,
        "source": item.get("source") or "",
        "author": item.get("author") or "",
        "url": item.get("url") or "",
    }


def daterange(start: datetime, end: datetime, step_days: int):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=step_days), end)
        yield cur, nxt
        cur = nxt


def main():
    load_dotenv()
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    out_dir = Path(args.out_dir)

    total = 0
    by_month: dict[tuple[int, int], list[dict]] = {}
    for window_start, window_end in daterange(start, end, args.batch_days):
        log.info("Fetching %s → %s", window_start.date(), window_end.date())
        for item in fetch_window(args.symbols, window_start, window_end, args.limit):
            row = normalize(item)
            key = (row["event_ts"].year, row["event_ts"].month)
            by_month.setdefault(key, []).append(row)
            total += 1
        for (y, m), rows in list(by_month.items()):
            if len(rows) >= 500:
                sentiment_store.upsert_alpaca_rows(
                    pd.DataFrame(rows), year=y, month=m, root=out_dir)
                log.info("Flushed %d rows to %d-%02d.parquet", len(rows), y, m)
                by_month.pop(key, None)

    for (y, m), rows in by_month.items():
        if rows:
            sentiment_store.upsert_alpaca_rows(
                pd.DataFrame(rows), year=y, month=m, root=out_dir)
            log.info("Flushed %d rows to %d-%02d.parquet", len(rows), y, m)

    log.info("Backfill complete: %d articles", total)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable and syntax-check**

```bash
chmod +x scripts/backfill_alpaca_news.py
python -m py_compile scripts/backfill_alpaca_news.py
```
Expected: no output, exit code 0.

- [ ] **Step 3: Dry smoke — 1 day backfill**

```bash
python scripts/backfill_alpaca_news.py \
  --start 2024-01-02 --end 2024-01-03 \
  --symbols BTCUSD ETHUSD \
  --out-dir data/sentiment/alpaca_smoke
```
Expected: log lines fetching the window, "Backfill complete: N articles" with N > 0.

- [ ] **Step 4: Verify the Parquet**

```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/sentiment/alpaca_smoke/2024/01.parquet')
print(df.shape, df.columns.tolist())
print(df[['event_ts','as_of_ts','headline','symbols']].head())
"
```
Expected: non-empty DataFrame with all SCHEMA_COLS present.

- [ ] **Step 5: Clean smoke output and commit**

```bash
rm -rf data/sentiment/alpaca_smoke
git add scripts/backfill_alpaca_news.py
git commit -m "feat(sentiment): add Alpaca News backfill script"
```

---

## Phase C — PIT tool + vendor routing

### Task C1: Write failing test — PIT news tool

**Files:**
- Create: `tests/dataflows/test_crypto_sentiment_pit.py`

- [ ] **Step 1: Write tests**

Create `tests/dataflows/test_crypto_sentiment_pit.py`:
```python
"""Tests for the PIT crypto sentiment tool wrappers."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from tradingagents.dataflows import sentiment_store, crypto_sentiment_pit


def _row(ts, article_id, symbols="BTCUSD", headline="H", content="body"):
    return {
        "event_ts": ts, "as_of_ts": ts, "id": article_id,
        "headline": headline, "content": content, "summary": "",
        "symbols": symbols, "source": "Benzinga", "author": "", "url": "",
    }


def test_get_crypto_news_pit_returns_formatted_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(sentiment_store, "DEFAULT_ROOT", tmp_path)
    rows = pd.DataFrame([
        _row(datetime(2024, 1, 10, tzinfo=timezone.utc), 1,
             headline="BTC surges on ETF approval"),
        _row(datetime(2024, 1, 12, tzinfo=timezone.utc), 2,
             headline="SEC hints at stricter enforcement"),
    ])
    sentiment_store.upsert_alpaca_rows(rows, year=2024, month=1, root=tmp_path)

    out = crypto_sentiment_pit.get_crypto_news_pit(
        coin_name="bitcoin",
        trade_date="2024-01-15",
        lookback_days=7,
    )
    assert "Alpaca" in out or "Benzinga" in out
    assert "BTC surges on ETF approval" in out
    assert "SEC hints at stricter enforcement" in out


def test_get_crypto_news_pit_respects_pit_cutoff(tmp_path, monkeypatch):
    """An article whose event_ts falls inside the window but whose as_of_ts is AFTER
    the trade_date must not appear in the report."""
    monkeypatch.setattr(sentiment_store, "DEFAULT_ROOT", tmp_path)
    rows = pd.DataFrame([
        _row(datetime(2024, 1, 10, tzinfo=timezone.utc), 1, headline="visible"),
        {
            "event_ts": datetime(2024, 1, 12, tzinfo=timezone.utc),
            "as_of_ts": datetime(2024, 3, 1, tzinfo=timezone.utc),
            "id": 2, "headline": "leaked future", "content": "",
            "summary": "", "symbols": "BTCUSD", "source": "x", "author": "", "url": "",
        },
    ])
    sentiment_store.upsert_alpaca_rows(rows, year=2024, month=1, root=tmp_path)

    out = crypto_sentiment_pit.get_crypto_news_pit(
        coin_name="bitcoin", trade_date="2024-01-15", lookback_days=7,
    )
    assert "visible" in out
    assert "leaked future" not in out


def test_get_crypto_news_pit_empty_returns_notice(tmp_path, monkeypatch):
    monkeypatch.setattr(sentiment_store, "DEFAULT_ROOT", tmp_path)
    out = crypto_sentiment_pit.get_crypto_news_pit(
        coin_name="bitcoin", trade_date="2024-01-15", lookback_days=7,
    )
    assert "No" in out  # "No Alpaca articles found" or "No cached sentiment"


def test_get_reddit_posts_pit_stub_returns_disabled_message():
    """P1 does not implement Reddit PIT; stub must explicitly say so
    rather than silently fall back to live data."""
    out = crypto_sentiment_pit.get_reddit_posts_pit_stub(
        coin_name="bitcoin", start_date="2024-01-01", end_date="2024-01-10",
    )
    assert "not available" in out.lower() or "disabled" in out.lower()
```

- [ ] **Step 2: Run — confirm failure**

```bash
pytest tests/dataflows/test_crypto_sentiment_pit.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.dataflows.crypto_sentiment_pit'`.

---

### Task C2: Implement crypto_sentiment_pit

**Files:**
- Create: `tradingagents/dataflows/crypto_sentiment_pit.py`

- [ ] **Step 1: Write the module**

Create `tradingagents/dataflows/crypto_sentiment_pit.py`:
```python
"""PIT-enforced crypto sentiment tool implementations.

Registered as vendor 'crypto_sentiment_pit' in dataflows.interface.
When data_vendors['crypto_sentiment'] = 'crypto_sentiment_pit', agent tool
calls route here instead of the today-relative live implementations.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from tradingagents.dataflows import sentiment_store


def get_crypto_news_pit(
    coin_name: Annotated[str, "Cryptocurrency name (e.g., 'Bitcoin', 'Ethereum')"],
    trade_date: Annotated[str, "Point-in-time date in yyyy-mm-dd format; no data after this date is returned"],
    lookback_days: Annotated[int, "How many days back from trade_date to fetch"] = 7,
) -> str:
    """Fetch Alpaca News articles with strict PIT enforcement.

    Returns raw headlines and article content for the LLM analyst to
    interpret sentiment. Every row's as_of_ts <= trade_date, so there
    is no look-ahead.
    """
    coin = coin_name.lower()
    try:
        trade_dt = datetime.strptime(trade_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return f"Invalid trade_date format: {trade_date!r} (expected yyyy-mm-dd)."

    ts_end = trade_dt
    ts_start = trade_dt - timedelta(days=lookback_days)

    try:
        df = sentiment_store.query_news(
            coin=coin, ts_start=ts_start, ts_end=ts_end, as_of=trade_dt, limit=50,
        )
    except ValueError as e:
        return f"Sentiment store error: {e}"

    if df.empty:
        return (
            f"No Alpaca articles found for {coin_name} in the "
            f"{lookback_days}-day window before {trade_date}. "
            f"(Ensure backfill_alpaca_news.py ran for this range.)"
        )

    lines: list[str] = [
        f"# Alpaca News (Benzinga): {coin_name}",
        f"# Window: {ts_start.date()} → {trade_date}",
        f"# Articles: {len(df)}",
        "",
    ]
    for i, row in enumerate(df.itertuples(index=False), 1):
        lines.append(f"### Article {i} — {row.source}")
        lines.append(f"**Date:** {row.event_ts}")
        lines.append(f"**Headline:** {row.headline}")
        if row.summary:
            lines.append(f"**Summary:** {row.summary}")
        elif row.content:
            # Truncate to keep prompt size reasonable
            body = (row.content or "")[:800]
            lines.append(f"**Content:** {body}")
        if row.url:
            lines.append(f"**URL:** {row.url}")
        lines.append("")
    return "\n".join(lines)


def get_reddit_posts_pit_stub(
    coin_name: Annotated[str, "Cryptocurrency name"],
    start_date: Annotated[str, "Start date yyyy-mm-dd"],
    end_date: Annotated[str, "End date yyyy-mm-dd"],
) -> str:
    """P1 stub: Reddit PIT data is not available (Phase 3).

    Returning an explicit message (instead of no impl) prevents the vendor
    router from silently falling back to the today-relative live Reddit tool.
    """
    return (
        f"Reddit PIT data is not available in P1 (no Arctic Shift/Pushshift ingest yet). "
        f"Sentiment analysis should rely on Alpaca News for {coin_name}."
    )
```

- [ ] **Step 2: Run tests**

```bash
pytest tests/dataflows/test_crypto_sentiment_pit.py -v
```
Expected: all 4 tests PASS.

---

### Task C3: Register PIT vendor in interface.py

**Files:**
- Modify: `tradingagents/dataflows/interface.py:39-42,105-111,179-185`

- [ ] **Step 1: Add import**

Edit [tradingagents/dataflows/interface.py:39-42](../../tradingagents/dataflows/interface.py#L39-L42). After the `from .crypto_sentiment import (...)` block, add:
```python
from .crypto_sentiment_pit import (
    get_crypto_news_pit as get_crypto_news_pit_impl,
    get_reddit_posts_pit_stub as get_reddit_posts_pit_impl,
)
```

- [ ] **Step 2: Add vendor to VENDOR_LIST**

Edit the `VENDOR_LIST` (around line 105-111). Add `"crypto_sentiment_pit"`:
```python
VENDOR_LIST = [
    "yfinance",
    "alpha_vantage",
    "coingecko_binance",
    "onchain",
    "crypto_sentiment",
    "crypto_sentiment_pit",
]
```

- [ ] **Step 3: Register implementations in VENDOR_METHODS**

Edit the `# Crypto sentiment` block of `VENDOR_METHODS` (around line 178-185):
```python
    # Crypto sentiment
    "get_reddit_posts": {
        "crypto_sentiment": get_crypto_reddit_posts,
        "crypto_sentiment_pit": get_reddit_posts_pit_impl,
    },
    "get_crypto_google_news": {
        "crypto_sentiment": get_crypto_google_news_impl,
        "crypto_sentiment_pit": get_crypto_news_pit_impl,
    },
```

- [ ] **Step 4: Sanity-check routing**

```bash
python -c "
from tradingagents.dataflows.interface import VENDOR_METHODS, VENDOR_LIST
assert 'crypto_sentiment_pit' in VENDOR_LIST
assert 'crypto_sentiment_pit' in VENDOR_METHODS['get_crypto_google_news']
assert 'crypto_sentiment_pit' in VENDOR_METHODS['get_reddit_posts']
print('OK')
"
```
Expected: `OK`.

- [ ] **Step 5: Test routing with config override**

```bash
python -c "
from tradingagents.dataflows.config import set_config, DEFAULT_CONFIG
from tradingagents.dataflows.interface import route_to_vendor
cfg = DEFAULT_CONFIG.copy()
cfg['data_vendors'] = dict(cfg['data_vendors'])
cfg['data_vendors']['crypto_sentiment'] = 'crypto_sentiment_pit'
set_config(cfg)
out = route_to_vendor('get_crypto_google_news', 'bitcoin', '2024-01-15', 7)
print(out[:200])
"
```
Expected: text beginning with `No Alpaca articles found for bitcoin ...` (or similar — no real data yet).

- [ ] **Step 6: Run the full test suite sanity pass**

```bash
pytest tests/ -x -q
```
Expected: all green (no regressions).

- [ ] **Step 7: Commit Phase C**

```bash
git add tradingagents/dataflows/crypto_sentiment_pit.py tradingagents/dataflows/interface.py tests/dataflows/test_crypto_sentiment_pit.py
git commit -m "feat(sentiment): add PIT Alpaca tool + vendor routing"
```

---

## Phase D — Integration & validation rerun

### Task D1: Add --sentiment-mode flag to generate_agent_signals.py

**Files:**
- Modify: `scripts/generate_agent_signals.py:30-48,54-65`

- [ ] **Step 1: Add CLI flag**

In `parse_args()` (around line 30-48), after the `--analysts` line add:
```python
    p.add_argument("--sentiment-mode", choices=["live", "pit"], default="live",
                    help="Select sentiment vendor: 'live' (today-relative) or 'pit' (Alpaca PIT).")
```

- [ ] **Step 2: Apply to config**

In `main()` (around line 54-65), after the `config["replay_cache"] = True` line add:
```python
    if args.sentiment_mode == "pit":
        config["data_vendors"] = dict(config.get("data_vendors", {}))
        config["data_vendors"]["crypto_sentiment"] = "crypto_sentiment_pit"
```

- [ ] **Step 3: Echo selection in banner**

In the banner print block, after `LLM       : {args.deep_think} / {args.quick_think}` add:
```python
    print(f"  Sentiment : {args.sentiment_mode}")
```

- [ ] **Step 4: Syntax-check**

```bash
python -m py_compile scripts/generate_agent_signals.py
python scripts/generate_agent_signals.py --help | grep sentiment-mode
```
Expected: `--sentiment-mode` appears in help output.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_agent_signals.py
git commit -m "feat(cli): add --sentiment-mode flag to generate_agent_signals"
```

---

### Task D2: Live smoke test — single-day propagate with PIT sentiment

**Purpose:** Verify the end-to-end glue works before committing to the expensive full backfill.

- [ ] **Step 1: Backfill 7 days of real Alpaca data**

```bash
python scripts/backfill_alpaca_news.py \
  --start 2024-01-08 --end 2024-01-15 \
  --symbols BTCUSD ETHUSD
```
Expected: log shows "Backfill complete: N articles" with N > 0.

- [ ] **Step 2: Propagate one day with PIT sentiment enabled**

```bash
python -c "
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = dict(DEFAULT_CONFIG)
config['data_vendors'] = dict(config['data_vendors'])
config['data_vendors']['crypto_sentiment'] = 'crypto_sentiment_pit'
config['asset_class'] = 'crypto'
config['deep_think_llm'] = 'gpt-4o-mini'
config['quick_think_llm'] = 'gpt-4o-mini'
config['replay_cache'] = True

ta = TradingAgentsGraph(
    selected_analysts=['crypto_sentiment'],
    debug=False, config=config,
)
state, signal = ta.propagate('bitcoin', '2024-01-15')
report = state.get('sentiment_report', '')
print('---SIGNAL:', signal)
print('---REPORT HEAD:')
print(report[:2000])
"
```
Expected: a non-empty `sentiment_report` that mentions Alpaca/Benzinga content and references articles from the 2024-01-08→2024-01-15 window.

- [ ] **Step 3: Verify no look-ahead leak**

The report must not mention anything that happened AFTER 2024-01-15 (e.g. the Bitcoin spot ETF spike on 2024-01-10 can appear; anything post 2024-01-15 must not).

Inspect the report manually; if it references dates or events after 2024-01-15, the PIT filter has a bug — stop and investigate `sentiment_store.query_news`.

- [ ] **Step 4: Commit (documentation only)**

No new files to commit. If the smoke was successful, move on to D3.

---

### Task D3: Full backfill 2023-10 → today

**Purpose:** Populate the store for the full rerun window (and a bit before, for lookback).

- [ ] **Step 1: Run full backfill**

```bash
python scripts/backfill_alpaca_news.py \
  --start 2023-10-01 --end 2026-04-17 \
  --symbols BTCUSD ETHUSD \
  --batch-days 14
```
Expected runtime: ~30-60 min (depends on article density and Alpaca's server responsiveness). Monitor logs for any non-429 errors.

- [ ] **Step 2: Verify coverage**

```bash
python -c "
import duckdb, glob
files = sorted(glob.glob('data/sentiment/alpaca/*/*.parquet'))
print(f'Monthly files: {len(files)}')
con = duckdb.connect(':memory:')
con.execute(\"CREATE VIEW n AS SELECT * FROM read_parquet('data/sentiment/alpaca/*/*.parquet')\")
for row in con.execute('''
    SELECT strftime(event_ts, '%Y-%m') AS ym, COUNT(*) AS n
    FROM n GROUP BY ym ORDER BY ym
''').fetchall():
    print(row)
"
```
Expected: monthly counts from 2023-10 through 2026-04, each with N > 0 (article volume varies, but no month should be empty).

---

### Task D4: Rerun 90-day backtest with PIT sentiment

**Purpose:** Compare against the baseline signal distribution (BTC 67 SELL / 18 BUY, ETH 59/23) to see whether sentiment flips the bearish bias.

- [ ] **Step 1: Generate signals**

```bash
python scripts/generate_agent_signals.py \
  --coins bitcoin ethereum \
  --start 2026-01-16 --end 2026-04-15 \
  --analysts market onchain prediction crypto_sentiment \
  --deep-think gpt-4o-mini --quick-think gpt-4o-mini \
  --sentiment-mode pit \
  --output-dir data/agent_signals_pit
```
Expected runtime: several hours (4 analysts × ~90 days × LLM calls, but most hit replay_cache after first pass). Log the start time.

- [ ] **Step 2: Run the backtest**

```bash
python scripts/backtest_system_v2.py \
  --coins bitcoin ethereum \
  --start 2026-01-16 --end 2026-04-15 \
  --signals-dir data/agent_signals_pit \
  --output-dir data/agent_backtest_v2_pit
```

If `backtest_system_v2.py` does not already accept `--signals-dir` / `--output-dir`, inspect the script and either (a) add the flags or (b) temporarily symlink `data/agent_signals_pit/*.csv` to the path it expects. Do NOT overwrite the baseline CSVs in `data/agent_signals/`.

Expected: a new `data/agent_backtest_v2_pit/agent_v2_metrics_*.json` and equity plot.

- [ ] **Step 3: Summarize results**

```bash
python -c "
import json, pandas as pd, glob
meta = json.load(open(glob.glob('data/agent_backtest_v2_pit/agent_v2_metrics_*.json')[0]))
print(json.dumps(meta, indent=2, default=str))
for csv in sorted(glob.glob('data/agent_signals_pit/*.csv')):
    df = pd.read_csv(csv)
    coin = csv.split('/')[-1].split('_')[0]
    print(coin, df['signal'].value_counts().to_dict())
"
```

Expected: metrics JSON and signal distributions printed. Compare to baseline in THESIS_FINDINGS.md:
- Baseline BTC: 67 SELL / 18 BUY, 46.4% win rate, -4.95% return, Sharpe -1.64
- Baseline ETH: 59 SELL / 23 BUY, 43.5% win rate, +0.44% return, Sharpe -0.11

---

### Task D5: Update THESIS_FINDINGS.md

**Files:**
- Modify: `THESIS_FINDINGS.md`

- [ ] **Step 1: Append findings**

Read current THESIS_FINDINGS.md; append a new section. Use this template (fill `<...>` with real values from Task D4 Step 3):

```markdown
## PIT Sentiment — Phase 1 (Alpaca News) — 2026-04-17

**Setup:**
- Data source: Alpaca News API (Benzinga), PIT-enforced via bitemporal Parquet store
- Window: 2026-01-16 → 2026-04-15 (same as baseline 90-day run)
- Models: GPT-4o-mini (deep + quick), replay_cache on
- Analysts: market + onchain + prediction + **crypto_sentiment (PIT)**

**Results vs. 3-analyst baseline:**

| | Baseline (3-analyst) | +PIT Sentiment | Δ |
|---|---|---|---|
| BTC return | -4.95% | <..>% | <..> |
| BTC Sharpe | -1.64 | <..> | <..> |
| BTC win rate | 46.4% | <..>% | <..> |
| BTC BUY / SELL signals | 18 / 67 | <..> / <..> | <..> |
| ETH return | +0.44% | <..>% | <..> |
| ETH Sharpe | -0.11 | <..> | <..> |
| ETH win rate | 43.5% | <..>% | <..> |
| ETH BUY / SELL signals | 23 / 59 | <..> / <..> | <..> |
| Portfolio return | -2.26% | <..>% | <..> |
| Portfolio Sharpe | -0.89 | <..> | <..> |

**Takeaway:** <one sentence — did sentiment flip the bearish bias, sharpen it, or have no effect?>

**Artifacts:**
- Signals: `data/agent_signals_pit/`
- Backtest output: `data/agent_backtest_v2_pit/`
- Spec: [docs/superpowers/specs/2026-04-17-pit-sentiment-p1-alpaca-design.md](docs/superpowers/specs/2026-04-17-pit-sentiment-p1-alpaca-design.md)
- Plan: [docs/superpowers/plans/2026-04-17-pit-sentiment-p1-alpaca.md](docs/superpowers/plans/2026-04-17-pit-sentiment-p1-alpaca.md)
```

- [ ] **Step 2: Commit**

```bash
git add THESIS_FINDINGS.md
git commit -m "docs(thesis): record P1 PIT Alpaca sentiment rerun findings"
```

---

## Out of scope (deferred, not in P1)

- GDELT 2.0 ingestion (Phase 2)
- HuggingFace `edaschau/bitcoin_news` Parquet corpus (Phase 2)
- alternative.me F&G daily snapshots (Phase 2)
- Arctic Shift / Pushshift Reddit dumps (Phase 3 — and likely unnecessary given post-2023 viable window)
- CryptoBERT or learned sentiment scoring (later — prediction-model feature)
- Live-mode replacement (live keeps today-relative tools, per design)
- Multi-year 2020–2023 validation (dropped; LLM cutoff constraint)
- Twitter/X archives

---

## Self-review (completed during plan writing)

**Spec coverage:** Every section of the spec has tasks — store (A2-A4), backfill (B1), PIT tool (C1-C2), vendor routing (C3), CLI flag (D1), validation rerun (D2-D5). ✓

**Placeholder scan:** Every step contains actual code or specific commands. The only `<..>` placeholders are in the THESIS_FINDINGS.md template — those are values the engineer fills from Task D4 Step 3 output, which is the correct pattern. ✓

**Type consistency:** `upsert_alpaca_rows(df, year, month, root)` and `query_news(coin, ts_start, ts_end, as_of, limit, root)` signatures are consistent across tests, the store implementation, and the PIT tool. `COIN_TO_SYMBOL` and `SCHEMA_COLS` names are reused. ✓

**Refinement from spec:** Changed the `config["sentiment_mode"]` key to vendor-routing (`data_vendors["crypto_sentiment"] = "crypto_sentiment_pit"`) — documented at the top of this plan. Behavior is identical; routing reuses the existing mechanism.
