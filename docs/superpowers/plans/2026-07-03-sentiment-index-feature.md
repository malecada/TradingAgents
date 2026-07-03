# Sentiment Index as Quant Feature — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a PIT-safe daily news-sentiment index (BTC, ETH, global) from full-text corpora, inject it into the LightGBM feature matrix as route variants `78f+s`/`193f+s`, and A/B-validate per coin with do-no-harm gates against the V5 MIX baseline.

**Architecture:** Corpus (existing Alpaca full-text store + re-ingested HF `edaschau/bitcoin_news`) → dual scoring engines (Engine A: gpt-4o-mini 0–4 index with the supervisor-template prompt contract; Engine B: CryptoBERT polarity) → per-article score parquets → daily aggregation into a bitemporal long store (`data/sentiment/index/{engine}/`) → new `build_sentiment_features` PIT builder → `add_sentiment` flag in `build_pooled_dataset` → prediction regen + bootstrap/CPCV validation.

**Tech Stack:** Python 3.13 (uv), pandas, DuckDB/Parquet, LightGBM, transformers (CryptoBERT), openai (gpt-4o-mini), pytest.

**Design doc:** `docs/superpowers/specs/2026-07-03-quant-first-sentiment-and-model-improvements-design.md` — read it first; it carries the rationale and the acceptance gates.

## Global Constraints

- Repo: `/home/malecada/master_thesis/TradingAgents`. Work in a **git worktree** on new branch `feature/sentiment-index-quant` cut from `feature/trend-mult-v51-hybrid-routing` HEAD (`f979683` at plan time). The main checkout has the user's uncommitted modulator-A/B changes — do not touch them.
- Data lives only in the main checkout: run everything with `export TRADINGAGENTS_DATA_ROOT=/home/malecada/master_thesis/TradingAgents/data` (the store modules honour this env var; default is relative `data`).
- Env setup: `uv sync --all-extras --python 3.13.13` (487+ tests green baseline). API keys: `.env` in repo root (`OPENAI_API_KEY`, `ALPACA_API_KEY_ID`, `ALPACA_API_SECRET_KEY`).
- LLM scoring model: `gpt-4o-mini` (cost policy). Never score pre-2023-10-01 articles with Engine A (knowledge-cutoff look-ahead).
- A/B window (pre-registered): **2023-10-01 → 2026-05-26**. Long-history BTC window (Engine B only): 2021-07-01 → 2026-05-26.
- Baselines (same-window, regenerated — never compare against the published 4.5-yr numbers): regenerate baseline predictions on the A/B window with identical settings minus the flag.
- Acceptance gates (per coin, pre-registered): bootstrap `p_pos ≥ 0.90` for ΔSR>0 AND MaxDD not worse by >1pp AND CPCV fold-consistency not degraded. Trial count for DSR: 8.
- New feature columns are exactly: `snt_idx_mean, snt_idx_ewm3, snt_cnt_z30, snt_neg_share_7d, snt_disp_7d` (per-coin), `snt_g_idx_ewm3, snt_g_cnt_z30` (global), `fng_level, fng_ema_168d, fng_dev` (global) — 10 columns. No additions without updating the spec.
- Commit after every task; conventional-commit messages.

---

### Task 1: Worktree, branch, environment sanity

**Files:** none created in-repo (worktree setup).

- [ ] **Step 1: Create worktree + branch**

```bash
cd /home/malecada/master_thesis/TradingAgents
git worktree add ../TradingAgents-sentiment -b feature/sentiment-index-quant f979683
cd ../TradingAgents-sentiment
```

- [ ] **Step 2: Environment + data root**

```bash
uv sync --all-extras --python 3.13.13
export TRADINGAGENTS_DATA_ROOT=/home/malecada/master_thesis/TradingAgents/data
cp /home/malecada/master_thesis/TradingAgents/.env .env  # keys
```

- [ ] **Step 3: Baseline test run**

Run: `uv run pytest -x -q`
Expected: all pass (≈487+). If failures exist at HEAD, record them now — they are pre-existing, not yours.

- [ ] **Step 4: Verify data visibility**

```bash
uv run python -c "
import os, pandas as pd, glob
root = os.environ['TRADINGAGENTS_DATA_ROOT']
files = glob.glob(f'{root}/sentiment/alpaca/*/*.parquet')
print('alpaca shards:', len(files))
df = pd.read_parquet(files[-1]); print(df.columns.tolist()); print(len(df))"
```
Expected: 41+ shards; columns include `event_ts, as_of_ts, headline, content, summary, symbols`.

---

### Task 2: Port the sentiment scorer module from the research fork

**Files:**
- Create: `tradingagents/sentiment/__init__.py`
- Create: `tradingagents/sentiment/scorers.py` (copy from `/home/malecada/master_thesis/TradingAgents-research/tradingagents/sentiment/scorers.py`)
- Create: `tradingagents/sentiment/anonymize.py` (copy from research fork, same dir)
- Test: `tests/sentiment/test_scorers_cache.py`

**Interfaces:**
- Produces: `CryptoBertScorer().score_polarity_mean(texts: list[str]) -> float` and per-text `score(texts) -> np.ndarray (n,3)` with sqlite cache at `data/sentiment/scorer_cache.sqlite` keyed `(model_id, content_sha)`. `anonymize(text: str) -> str` replaces tickers/entity names.

- [ ] **Step 1: Copy files verbatim** (they are self-contained; check imports resolve against this repo).

```bash
mkdir -p tradingagents/sentiment tests/sentiment
cp /home/malecada/master_thesis/TradingAgents-research/tradingagents/sentiment/{__init__.py,scorers.py,anonymize.py} tradingagents/sentiment/
```

- [ ] **Step 2: Write cache unit test (no model download — subclass with fake inference)**

```python
# tests/sentiment/test_scorers_cache.py
import numpy as np
from tradingagents.sentiment import scorers

class FakeScorer(scorers._BertScorer):
    MODEL_ID = "fake/model"
    calls = 0
    def _infer(self, texts):  # match the real private inference hook name — adapt if different
        FakeScorer.calls += len(texts)
        return np.tile(np.array([[0.2, 0.3, 0.5]]), (len(texts), 1))

def test_cache_hit_avoids_reinference(tmp_path, monkeypatch):
    monkeypatch.setattr(scorers, "CACHE_PATH", tmp_path / "cache.sqlite")
    s = FakeScorer()
    r1 = s.score(["hello world"])
    n = FakeScorer.calls
    s2 = FakeScorer()
    r2 = s2.score(["hello world"])
    assert FakeScorer.calls == n          # served from cache
    assert np.allclose(r1, r2)

def test_polarity_mean_is_bull_minus_bear(tmp_path, monkeypatch):
    monkeypatch.setattr(scorers, "CACHE_PATH", tmp_path / "cache.sqlite")
    s = FakeScorer()
    assert abs(s.score_polarity_mean(["x"]) - (0.5 - 0.2)) < 1e-9
```

Note: read `scorers.py` first — if the inference hook is named differently (e.g. `_score_uncached`), adapt the subclass; the two behaviors under test (cache hit, p_bull−p_bear) are the contract.

- [ ] **Step 3: Run tests** — `uv run pytest tests/sentiment/ -v` → PASS.
- [ ] **Step 4: Commit** — `git commit -m "feat(sentiment): port CryptoBERT scorer + anonymizer from research fork"`

---

### Task 3: Sentiment index store (bitemporal, engine-namespaced)

**Files:**
- Create: `tradingagents/dataflows/sentiment_index_store.py`
- Test: `tests/dataflows/test_sentiment_index_store.py`

**Interfaces:**
- Produces: `index_root(engine: str) -> Path`; `upsert_index_rows(df, engine) -> int`; `load_index(engine, coins, start, end) -> pd.DataFrame` (long schema). Reuses `onchain_store.upsert_rows(df, root=...)` — same 7-column schema, dedupe keys, monthly shards.

- [ ] **Step 1: Write failing test**

```python
# tests/dataflows/test_sentiment_index_store.py
import pandas as pd
from tradingagents.dataflows import sentiment_index_store as sis

def _rows():
    return pd.DataFrame({
        "event_ts": pd.to_datetime(["2024-01-01", "2024-01-02"], utc=True),
        "as_of_ts": pd.to_datetime(["2024-01-01 01:00", "2024-01-02 01:00"], utc=True),
        "coin": ["btc", "btc"],
        "metric": ["snt_idx_mean", "snt_idx_mean"],
        "value": [0.25, -0.5],
        "source": ["sentiment_index", "sentiment_index"],
        "status": ["final", "final"],
    })

def test_upsert_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(sis, "BASE_ROOT", tmp_path)
    sis.upsert_index_rows(_rows(), engine="llm")
    out = sis.load_index("llm", coins=["btc"], start="2024-01-01", end="2024-01-31")
    assert len(out) == 2 and set(out.metric) == {"snt_idx_mean"}

def test_engines_are_isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(sis, "BASE_ROOT", tmp_path)
    sis.upsert_index_rows(_rows(), engine="llm")
    assert sis.load_index("bert", coins=["btc"], start="2024-01-01", end="2024-01-31").empty
```

- [ ] **Step 2: Run** — `uv run pytest tests/dataflows/test_sentiment_index_store.py -v` → FAIL (module missing).
- [ ] **Step 3: Implement**

```python
# tradingagents/dataflows/sentiment_index_store.py
"""Bitemporal daily sentiment-index store, one root per scoring engine.

Reuses the on-chain long schema so backtests enforce as_of_ts <= trade_date.
Layout: data/sentiment/index/{engine}/{year}/{month:02d}.parquet
"""
from __future__ import annotations
import glob
import os
from pathlib import Path
import pandas as pd
from tradingagents.dataflows import onchain_store

BASE_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", "data")) / "sentiment" / "index"
ENGINES = ("llm", "bert")

def index_root(engine: str) -> Path:
    if engine not in ENGINES:
        raise ValueError(f"unknown engine {engine!r}, expected one of {ENGINES}")
    return BASE_ROOT / engine

def upsert_index_rows(df: pd.DataFrame, engine: str) -> int:
    return onchain_store.upsert_rows(df, root=index_root(engine))

def load_index(engine: str, coins: list[str], start: str, end: str) -> pd.DataFrame:
    files = glob.glob(str(index_root(engine) / "*" / "*.parquet"))
    if not files:
        return pd.DataFrame(columns=onchain_store.SCHEMA_COLS)
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    m = df["coin"].isin(coins) & (df["event_ts"] >= pd.Timestamp(start, tz="UTC")) \
        & (df["event_ts"] <= pd.Timestamp(end, tz="UTC"))
    return df.loc[m].sort_values(["coin", "metric", "event_ts"]).reset_index(drop=True)
```

- [ ] **Step 4: Run tests** → PASS. **Step 5: Commit** `feat(dataflows): bitemporal sentiment-index store`.

---

### Task 4: Refresh corpora (Alpaca tail + HF bitcoin_news re-ingest)

**Files:** none new — run existing scripts `scripts/backfill_alpaca_news.py`, `scripts/ingest_hf_bitcoin_news.py`. Read each script's `--help`/header first for exact flags.

- [ ] **Step 1: Alpaca tail** (store currently ends 2026-04-18)

```bash
uv run python scripts/backfill_alpaca_news.py --start 2026-04-01 --end 2026-07-03
```
Expected: new monthly shards under `data/sentiment/alpaca/2026/`; rerun the Task-1 Step-4 snippet — shard count grows, max `event_ts` ≥ 2026-06.

- [ ] **Step 2: HF corpus re-ingest** (dir `data/sentiment/hf_btc/` is currently absent; dataset now has 210,832 rows to 2025-06)

```bash
HF_TOKEN=$(cat /home/malecada/master_thesis/hf_token.txt) uv run python scripts/ingest_hf_bitcoin_news.py
```
Expected: `data/sentiment/hf_btc/` populated; sanity-check row count ≥ 200k, `article_text` non-null share > 90%, timestamps span 2011→2025-06.

- [ ] **Step 3: Record counts** in a scratch note (feeds Task 10's report) and commit any script fixes needed (`fix(scripts): ...`) — data itself is gitignored.

---

### Task 5: Engine A — LLM 0–4 index scorer

**Files:**
- Create: `tradingagents/sentiment/llm_index_scorer.py`
- Test: `tests/sentiment/test_llm_index_scorer.py`

**Interfaces:**
- Produces: `SCORING_PROMPT: str`; `parse_index(answer: str) -> int | None` (None = not relevant / unparseable); `LlmIndexScorer(model="gpt-4o-mini").score_article(text: str, coin: str) -> dict(relevant: bool, idx: int | None, raw: str)` with sqlite cache table `llm_scores(model_id, content_sha, coin, relevant, idx, raw)` at `data/sentiment/llm_score_cache.sqlite`. Truncate input to 12,000 chars. `score_norm = (idx - 2) / 2`.

- [ ] **Step 1: Failing tests for the parser (the template contract)**

```python
# tests/sentiment/test_llm_index_scorer.py
from tradingagents.sentiment.llm_index_scorer import parse_index

def test_parses_relevant_with_index():
    assert parse_index("Relevant. BTC ETF inflows surge, Index: 3") == 3

def test_parses_index_with_label_suffix():
    assert parse_index("Relevant. Exchange hacked. Index: 0 (Very Negative)") == 0

def test_not_relevant_returns_none():
    assert parse_index("Not relevant. Article is about equities.") is None

def test_garbage_returns_none():
    assert parse_index("I cannot determine this.") is None

def test_out_of_range_clamped_to_none():
    assert parse_index("Relevant. Something, Index: 7") is None
```

- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**

```python
# tradingagents/sentiment/llm_index_scorer.py
"""LLM relevance filter + 0-4 sentiment index (supervisor-template contract).

Prompt structure and the "Relevant. [summary], Index: N" output contract are
adapted verbatim from News_fulltext/sentiment_index_tariff.py so the parser
carries over. Scale: 0 very negative ... 4 very positive for the coin's price.
"""
from __future__ import annotations
import hashlib
import os
import re
import sqlite3
from pathlib import Path

CACHE_PATH = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", "data")) / "sentiment" / "llm_score_cache.sqlite"
MAX_CHARS = 12_000

SCORING_PROMPT = """You are a cryptocurrency market analyst evaluating news articles for their relevance to {coin_name} ({symbol}) market conditions. Additionally, you will assess the sentiment of relevant articles based on their potential impact on {coin_name} price over the next days to weeks. Follow these steps:
STEP 1:

Examine the article and determine if it is relevant to understanding or predicting {coin_name} price, adoption, regulation, security incidents, exchange flows, macro conditions affecting crypto markets, or major protocol/network developments.
The article is relevant if it is about {coin_name} directly, or about the broader crypto market in a way that clearly affects {coin_name}.
The article is for example not relevant if it is about an unrelated small-cap token, general stock-market news without crypto linkage, or product advertising.

STEP 2:

    If the article is relevant:
        Respond with: "Relevant" and provide a concise summary of the content, ensuring the summary does not exceed 500 tokens.
        Proceed to Step 3 to create the sentiment index.
    If the article is not relevant:
        Respond with: "Not relevant" and provide reasons why.

STEP 3:

For relevant articles, create a sentiment index using the following scale based on how the article impacts {coin_name} price expectations:

    0 (Very Negative): The article highlights factors or events that severely worsen the price outlook (e.g. exchange collapse, hack, ban).
    1 (Negative): The article discusses elements that negatively impact the outlook, but not to an extreme degree.
    2 (Neutral): The article is balanced, with no strong positive or negative impact.
    3 (Positive): The article emphasizes factors that improve the outlook.
    4 (Very Positive): The article discusses elements that greatly enhance the outlook (e.g. ETF approval, major adoption).

Format your responses as follows:

    For relevant articles: "Relevant. [Your summary], Index: [sentiment_index]"
    For non-relevant articles: "Not relevant. [Your explanation]"

Ensure your evaluations are clear, concise, and consistent.
article text: {article}"""

_IDX_RE = re.compile(r"Index:\s*(\d)")

def parse_index(answer: str) -> int | None:
    low = answer.lower()
    if "not relevant" in low or "relevant" not in low:
        return None
    m = _IDX_RE.search(answer)
    if not m:
        tail = answer.split("Index")[-1]
        digits = re.findall(r"\d", tail)
        if not digits:
            return None
        m_val = int(digits[0])
    else:
        m_val = int(m.group(1))
    return m_val if 0 <= m_val <= 4 else None

def _sha(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()

class LlmIndexScorer:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(CACHE_PATH)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS llm_scores ("
            "model_id TEXT, content_sha TEXT, coin TEXT, relevant INT, idx INT, raw TEXT,"
            " PRIMARY KEY (model_id, content_sha, coin))")
        self._client = None

    def _chat(self, prompt: str) -> str:
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        resp = self._client.chat.completions.create(
            model=self.model, temperature=0,
            messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content or ""

    def score_article(self, text: str, coin: str, coin_name: str, symbol: str) -> dict:
        sha = _sha(text[:MAX_CHARS])
        row = self._conn.execute(
            "SELECT relevant, idx, raw FROM llm_scores WHERE model_id=? AND content_sha=? AND coin=?",
            (self.model, sha, coin)).fetchone()
        if row:
            return {"relevant": bool(row[0]), "idx": row[1], "raw": row[2]}
        answer = self._chat(SCORING_PROMPT.format(
            coin_name=coin_name, symbol=symbol, article=text[:MAX_CHARS]))
        idx = parse_index(answer)
        rec = {"relevant": idx is not None, "idx": idx, "raw": answer}
        self._conn.execute(
            "INSERT OR REPLACE INTO llm_scores VALUES (?,?,?,?,?,?)",
            (self.model, sha, coin, int(rec["relevant"]), idx, answer))
        self._conn.commit()
        return rec
```

- [ ] **Step 4: Run parser tests** → PASS. Add a cache test with a monkeypatched `_chat` (return fixed string, assert second call does not invoke `_chat`) — same pattern as Task 2 Step 2.
- [ ] **Step 5: Commit** `feat(sentiment): LLM 0-4 index scorer with template output contract`.

---

### Task 6: Corpus scoring runner

**Files:**
- Create: `scripts/score_sentiment_corpus.py`
- Test: `tests/sentiment/test_score_corpus_helpers.py` (coin-mapping + normalization helpers only; network runs are manual)

**Interfaces:**
- Consumes: Alpaca shards (`data/sentiment/alpaca/*/*.parquet`, cols `event_ts, as_of_ts, headline, content, summary, symbols`), HF store (`data/sentiment/hf_btc/`), `LlmIndexScorer`, `CryptoBertScorer`, `anonymize`.
- Produces: per-article score parquets `data/sentiment/scores/{engine}/{source}/{year}.parquet` with cols `[event_ts, as_of_ts, coin, engine, score_norm, relevant, content_sha]`. Coin mapping: Alpaca `symbols` contains `BTCUSD`→`btc`, `ETHUSD`→`eth`; an article may emit one row per matched coin plus one `global` row (any crypto match). HF corpus → `btc` + `global`.

Key behaviors to implement (CLI: `--engine {llm,bert} --source {alpaca,hf_btc} --coins btc,eth --start --end --limit N --est-only`):
- Engine A path: `anonymize(headline + "\n\n" + (content or summary))` → `score_article`; `score_norm=(idx-2)/2`; drop non-relevant.
- Engine B path: `score_polarity_mean` per article (headline+summary is enough for BERT's 256-token window); `relevant=True` always (BERT has no relevance filter — the daily count features absorb this).
- `--est-only`: print article count × est. 1.4k tokens in / 160 out × model price, exit. Abort real runs if estimate > $40 unless `--yes`.
- Idempotent: sqlite caches make re-runs cheap; parquet write is overwrite-per-year after dedupe on `content_sha, coin`.

- [ ] **Step 1: Write helper tests** (symbols→coins mapping incl. `global`, score_norm mapping, year-partition writer round-trip on tmpdir).
- [ ] **Step 2: Implement script.** **Step 3: Helpers green.**
- [ ] **Step 4: Estimate then run Engine A** (window start clamps to 2023-10-01 in code when engine=llm — hard guard, not just convention):

```bash
uv run python scripts/score_sentiment_corpus.py --engine llm --source alpaca --coins btc,eth --start 2023-10-01 --end 2026-05-26 --est-only
uv run python scripts/score_sentiment_corpus.py --engine llm --source alpaca --coins btc,eth --start 2023-10-01 --end 2026-05-26
```
Expected: ≈11-13k scored articles, cost single-digit $; relevant-share printed (expect 0.6-0.9; investigate if <0.3).

- [ ] **Step 5: Run Engine B over both sources and the full window**

```bash
uv run python scripts/score_sentiment_corpus.py --engine bert --source alpaca --coins btc,eth --start 2021-07-01 --end 2026-05-26
uv run python scripts/score_sentiment_corpus.py --engine bert --source hf_btc --coins btc --start 2021-07-01 --end 2025-06-30
```
Expected: CPU-hours scale run (~200k texts); cache makes it resumable. Sanity: mean |score_norm| in (0.05, 0.6).

- [ ] **Step 6: (optional, budget-gated) Engine A over HF 2023-10+ slice** — only if `--est-only` ≤ $25.
- [ ] **Step 7: Commit** script + tests.

---

### Task 7: Daily aggregation → index store

**Files:**
- Create: `scripts/build_sentiment_index.py`
- Create: `tradingagents/sentiment/daily_index.py` (pure functions, tested)
- Test: `tests/sentiment/test_daily_index.py`

**Interfaces:**
- Produces: `daily_index.aggregate(scores: pd.DataFrame) -> pd.DataFrame` — input per-article rows, output long-store rows for metrics `snt_idx_mean, snt_idx_ewm3, snt_cnt_z30, snt_neg_share_7d, snt_disp_7d` per `coin` (incl. `global`), `source="sentiment_index"`, `status="final"`, `as_of_ts = event_ts(day end) + 1h`. Script pipes Task-6 parquets → `upsert_index_rows(df, engine)`.

Formulas (exact):

```python
day = scores.groupby(["coin", scores.event_ts.dt.floor("D")])
base = day.agg(snt_idx_mean=("score_norm", "mean"),
               snt_cnt=("score_norm", "size"),
               snt_disp_7d_raw=("score_norm", "std"),
               snt_neg=("score_norm", lambda s: (s < 0).mean()))
# reindex each coin to the full calendar; days with no articles: snt_idx_mean=0, snt_cnt=0
per_coin["snt_idx_ewm3"]     = per_coin.snt_idx_mean.ewm(halflife=3).mean()
per_coin["snt_cnt_z30"]      = (per_coin.snt_cnt - per_coin.snt_cnt.rolling(30, min_periods=10).mean()) / per_coin.snt_cnt.rolling(30, min_periods=10).std()
per_coin["snt_neg_share_7d"] = per_coin.snt_neg.rolling(7, min_periods=3).mean()
per_coin["snt_disp_7d"]      = per_coin.snt_disp_7d_raw.rolling(7, min_periods=3).mean()
```

- [ ] **Step 1: TDD `aggregate`** — synthetic 40-day frame, assert: no-news day yields cnt 0 and carried EWMA; z-score NaN before min_periods; output passes `onchain_store` schema check (`upsert_rows` on tmp root).
- [ ] **Step 2: Implement.** **Step 3: Green.**
- [ ] **Step 4: Run for both engines**

```bash
uv run python scripts/build_sentiment_index.py --engine llm
uv run python scripts/build_sentiment_index.py --engine bert
```
Expected: `data/sentiment/index/llm/` (2023-10→2026-05, coins btc/eth/global) and `.../bert/` (2021-07→2026-05). Print row counts per coin/metric.

- [ ] **Step 5: Eyeball sanity plot** (matplotlib PNG to `data/sentiment/index/preview_{engine}.png`): `snt_idx_ewm3` for btc vs BTC close — known events should align (spot-check 2024-01 ETF approval positive, any 2025 crash negative). Not a test; attach to report.
- [ ] **Step 6: Commit.**

---

### Task 8: PIT feature builder + `add_sentiment` flag

**Files:**
- Create: `tradingagents/dataflows/sentiment_features.py`
- Modify: `tradingagents/models/model_utils.py:374-527` (`build_pooled_dataset` — new params `add_sentiment: bool = False, sentiment_engine: str = "llm"`; join block after the `add_onchain_pit` block)
- Test: `tests/dataflows/test_sentiment_features.py`

**Interfaces:**
- Produces: `build_sentiment_features(coin: str, dates: pd.DatetimeIndex, engine: str) -> pd.DataFrame` — columns exactly the 10 from Global Constraints; per-coin metrics from `coin` rows, `snt_g_*` from `global` rows, `fng_*` computed from `data/sentiment/fng/fng.parquet` (`fng_level`=value, `fng_ema_168d`=EWM halflife-84d of value, `fng_dev`=level−ema). PIT rule: `merge_asof(direction="backward")` on `as_of_ts <= date` — copy the `_pit_align` pattern from `onchain_features.py:90-119`.
- `build_pooled_dataset` join: same shape as the `add_onchain_pit` block (`model_utils.py:477+`): tz-normalize to calendar day, left-join on date index per coin, `fillna(0.0)` for all `snt_*`/`fng_*` cols. The existing global t−1 shift in `data_transform` then applies — no extra lag.

- [ ] **Step 1: TDD** — build tmp index store with known rows (via Task-3 store), synthetic fng parquet; assert: (a) a value with `as_of_ts` = day D 01:00 appears on day D and not D−1; (b) coins without per-coin rows still get `snt_g_*`/`fng_*`; (c) `build_pooled_dataset(..., add_sentiment=True)` output contains exactly the 10 new columns and `add_sentiment=False` output is byte-identical to before the change (regression guard — reuse `tests/regression/test_v2_unchanged.py` fixtures if applicable).
- [ ] **Step 2: Implement.** **Step 3: Green + full suite** `uv run pytest -x -q` (watch `tests/execution/live/test_predict_feature_parity.py` — it must still pass because the default flag is False).
- [ ] **Step 4: Commit** `feat(models): add_sentiment flag joins PIT sentiment-index features`.

---

### Task 9: Prediction regeneration (A/B routes)

**Files:**
- Modify: `scripts/evaluate_models_multi.py` — add `--add-sentiment` / `--sentiment-engine` CLI flags passed through to `build_pooled_dataset` (read the script header first; follow its existing flag pattern).
- Output dirs (convention from `baseline_v5_mix.py:DEFAULT_ROUTING`): `data/eval_multi_sent_{engine}/{78f|pit}/...`

- [ ] **Step 1: Wire flags** (small diff; keep default off). Commit.
- [ ] **Step 2: Regenerate BASELINE predictions on the A/B window** (flag off) for all 4 route dirs used by BTC/ETH (78f pool and pit pool) — 2023-10-01→2026-05-26. Record runtime.
- [ ] **Step 3: Regenerate SENTIMENT predictions** — same commands + `--add-sentiment --sentiment-engine llm`, then `--sentiment-engine bert`; plus the long BTC-only Engine-B run 2021-07-01→2026-05-26.
- [ ] **Step 4: Sanity** — each output dir has `preds_lgb_h7.csv` + `preds_lgb_h14.csv`, row counts within 1% of baseline, `ref_price` column present, no NaN predictions.
- [ ] **Step 5: Commit** any script changes (prediction CSVs are gitignored data).

---

### Task 10: A/B validation + gates verdict

**Files:**
- Create: `scripts/validate_sentiment_feature.py` (copy the skeleton of `scripts/validate_v5_mix.py`; keep `v2_sizing` primitives and `baseline_v5_mix._v2_positions` wiring identical — only the preds dirs differ)
- Output: `data/sentiment_feature_ab/{engine}/summary.json` + per-coin equity CSVs.

**Interfaces:**
- Consumes: Task-9 preds dirs; `bootstrap_sharpe.py` block-bootstrap helpers (block 21).
- Produces: per coin {btc, eth} × engine {llm, bert}: `sr_base, sr_sent, delta_sr, ci_low, ci_high, p_pos, maxdd_base, maxdd_sent, verdict` where `verdict = "SHIP" if p_pos >= 0.90 and (maxdd_sent - maxdd_base) <= 0.01 else "NO"`; plus portfolio row; plus DSR with `n_trials=8`.

- [ ] **Step 1:** Implement script; unit-test the gate function with synthetic PnL series (3 cases: clear ship, clear no, DD-fail despite SR-pass).
- [ ] **Step 2:** Run for both engines + the BTC long window. Also run CPCV variant: reuse `scripts/cpcv_v2.py` pattern on the winning engine only (cost control) and record fold-consistency deltas.
- [ ] **Step 3:** Feature-importance readout — load one trained bundle per route (re-fit via `fit_pooled_full` on the A/B window with flag on) and print LGB gain importance ranks of the 10 `snt_*`/`fng_*` columns. If all rank in the bottom decile, say so plainly in the report — that is the "model ignores it" null.
- [ ] **Step 4:** Write results section into `THESIS_FINDINGS.md` (next free §; follow the house format: config table, per-coin table, bootstrap CIs, verdict, negative-results-are-results framing). Commit.

---

### Task 11 (CONDITIONAL — only for coins with verdict SHIP): live wiring

**Files:**
- Modify: `tradingagents/execution/live/config.py:29-40` (`_V5_DEFAULT_ROUTING` — add `"feature_set": "78f+s"` variants), `retrain.py:143` area, `predict.py:183` area (map `+s` → `add_sentiment=True`), plus a daily scoring step in the live runner sequence (score yesterday's Alpaca articles with the SHIPPED engine before retrain).
- Test: extend `tests/execution/live/test_predict_feature_parity.py`, `test_retrain.py`, `test_config_portfolio_weights.py` fixtures.

- [ ] Gate: do not start this task without the Task-10 verdict table. If nothing ships, close the branch with the writeup (a validated null) and skip to Task 12.
- [ ] Follow the V5.1 deploy pattern (`docs/superpowers/plans/2026-05-30-v5-8coin-live-DEPLOY-HANDOFF.md`): tag, parity test on testnet, weekly parity job continues to compare.

---

### Task 12: Merge + handoff

- [ ] Full suite green; `git rebase` onto the integration branch the user designates (ask — main checkout branch is theirs); PR or merge per `superpowers:finishing-a-development-branch`.
- [ ] Summarize: corpora counts, cost actually spent, per-coin verdict table, importance ranks, and the follow-up decision (Phase 2 GDELT alt-coin scrape only if ≥1 coin shipped).

## Self-review notes

- Spec §3.4 formulas == Task 7 formulas; §3.6 gates == Task 10 gate function; 10-column contract repeated in Tasks 7/8/10 — keep in sync if the spec changes.
- Anchor line numbers (`model_utils.py:374`, `config.py:29`) are from 2026-07-03 HEAD `f979683`; verify before editing.
- Known unknowns the executor must resolve in-place: exact CLI of `backfill_alpaca_news.py`/`ingest_hf_bitcoin_news.py` (Task 4), inference-hook name in `scorers.py` (Task 2), flag pattern of `evaluate_models_multi.py` (Task 9). Each task says to read the file first.
