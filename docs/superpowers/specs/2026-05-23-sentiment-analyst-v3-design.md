# Sentiment Analyst v3 — Structured Snapshot + Narrow LLM Event Extractor

**Date**: 2026-05-23
**Branch**: `feature/sentiment-analyst-v3` (off `feature/hybrid-modulator`)
**Related research**: `sentiment_analysis_report.md` (project root)
**Related memories**: `project_loo_ablation.md`, `project_pit_sentiment_p2.md`, `project_hybrid_v5_1yr.md`

## Background

Per-analyst leave-one-out ablation (THESIS §23.11) found the current `crypto_sentiment_analyst` is noise on both BTC (drop ΔSR -0.47, P=0.106) and ETH (drop ΔSR +0.10, P=0.556). Earlier PIT P2 results found GDELT hurts BTC and lifts BNB.

The research report `sentiment_analysis_report.md` recommends replacing the free-text LLM "vibe" analyst with a structured event-driven layer (Option C):

- Deterministic `SentimentSnapshot` (Pydantic) built from BERT-family polarity scorers + Liu-Tsyvinski attention proxies + Fear & Greed regime gate + GDELT event flags
- Narrow ticker-anonymized LLM analyst restricted to event extraction, aggregated via Self-MoA (N=5 samples, single strong model)
- Both feed downstream: snapshot fields → V5 hybrid modulator features; LLM text → Researchers/Trader/PM agent chain

This spec defines that v3 architecture for **BTC + ETH only**. BNB/SOL extension is a separate Phase 2 spec.

## Goal

Replace the noisy free-text sentiment analyst with structured + narrow-LLM architecture, validated against the existing 90-bar A/B harness on `feature/hybrid-modulator`.

**Acceptance criteria** (must hold per coin for BTC and ETH on the 2026-01-16 → 2026-04-15 90-bar slice, bootstrap 10k paired CI):

| Variant | Required vs A (pure V5 quant) | Required vs B (legacy sentiment) |
|---|---|---|
| C — structured-only (modulator features, no LLM analyst) | ΔSR ≥ +0.10 | ΔSR ≥ +0.20 |
| D — structured + narrow LLM (full Option C) | ΔSR ≥ +0.10 | ΔSR ≥ +0.20 AND ΔSR(D−C) ≥ +0.05 |

Decision tree:
- D beats both bars → ship D as default
- Only C beats → ship C (drop narrow LLM analyst)
- Neither beats → ship Option A (drop sentiment analyst entirely; controlled negative result)

## Architecture

```
PIT store (data/sentiment/...)
  Alpaca News (Benzinga)  ─┐
  GDELT GKG               ─┤
  F&G level + 24w EMA     ─┤
  Google Trends (NEW)     ─┘
                          │
                          ↓
          tradingagents/sentiment/  (new module)
          ├─ scorers.py     CryptoBERT + FinBERT-Crypto CPU inference,
          │                 cache by sha1(model_id + content)
          ├─ events.py      GDELT V2Themes → CryptoEventType enum;
          │                 ambiguous → gpt-4o-mini structured fallback
          ├─ attention.py   Liu-Tsyvinski features
          │                 (search_z, neg_attention_ratio)
          └─ snapshot.py    build_snapshot(coin, trade_date, horizon)
                            → SentimentSnapshot Pydantic
                          │
            ┌─────────────┴─────────────┐
            ↓                           ↓
  Narrow LLM analyst         V5 hybrid modulator
  (anonymized backtest,      (numeric features:
   Self-MoA N=5,              polarity_news, polarity_event,
   gpt-4o-mini,               attention_z, fng_ema24w_z,
   event-scope only)          fng_extreme_flag, n_events_*)
            ↓
  sentiment_report text
  for Researchers/Trader/PM
```

## Components

### 1. Data layer

**NEW** `tradingagents/dataflows/gtrends_store.py`
- Bitemporal parquet store, partitioned by date
- Rolling-90-day pytrends pulls with re-stitching to handle Google's normalization
- Embargo: queries enforce `as_of_ts < trade_date - 1d`
- Columns: `coin, query, event_ts, as_of_ts, value, value_z90, value_z365`
- Helpers: `ingest_window(coin, start, end)`, `query_attention(coin, trade_date, lookback)`

**EXISTING** `sentiment_store.py`, `fng_store.py` — no changes.

### 2. Feature extraction layer

**NEW** `tradingagents/sentiment/__init__.py` — module exports.

**NEW** `tradingagents/sentiment/snapshot.py`
- `CryptoEventType` enum (regulatory: `SEC_ENFORCEMENT`, `CFTC_ACTION`, `MICA_EU`, `NATIONAL_REG`; market structure: `ETF_FLOW`, `ETF_APPROVAL_DENIAL`, `EXCHANGE_LISTING`, `PROOF_OF_RESERVES`; security: `EXCHANGE_HACK`, `PROTOCOL_EXPLOIT`, `BRIDGE_EXPLOIT`; network: `NETWORK_UPGRADE`, `HALVING`, `HARD_FORK`; on-chain: `WHALE_MOVEMENT`, `EXCHANGE_NETFLOW_EXTREME`; macro: `FED_FOMC`, `CPI_PRINT`, `DXY_EXTREME`; `NONE`)
- `EventFlag` Pydantic model: `event_type, asset, direction_hint(-1/0/+1), severity[0,1], event_ts, as_of_ts, half_life_days, source_url, confidence[0,1]`
- `SentimentSnapshot` Pydantic model — fields per report §4. Numeric vectorizable to `to_modulator_features()`. Markdown serializable to `to_prompt_table()`.
- `build_snapshot(coin: str, trade_date: datetime, horizon_days: int = 14, *, sources: dict | None = None) -> SentimentSnapshot` — orchestrator that queries PIT stores, calls scorers, aggregates events, computes confidence interval via Wilson/bootstrap.

**NEW** `tradingagents/sentiment/scorers.py`
- `CryptoBertScorer` — lazy-load `ElKulako/cryptobert`, batch CPU inference, `score(texts: list[str]) -> np.ndarray[(n, 3)]` returning `(p_bear, p_neutral, p_bull)`
- `FinBertCryptoScorer` — same shape over `ProsusAI/finbert` (FinBERT-Crypto checkpoint TBD; if no public retrained checkpoint, fall back to vanilla FinBERT and document)
- Disk cache at `data/sentiment/scorer_cache.sqlite` keyed by `(model_id, sha1(content))`
- Determinism: temperature=0 equivalent (argmax), seeded numpy, no dropout
- Lazy module-level singletons (avoid reload per snapshot)

**NEW** `tradingagents/sentiment/events.py`
- `THEME_TO_EVENT: dict[str, CryptoEventType]` — GDELT V2Themes mapping
- `classify_event(theme_string, headline, body) -> tuple[CryptoEventType, float]` — rule first; only LLM-fallback when ambiguous (multiple themes match, no obvious winner)
- LLM fallback uses gpt-4o-mini with strict Pydantic output (`EventFlag` schema), cached by `sha1(headline)`
- `extract_events(gdelt_rows: pd.DataFrame, coin: str, as_of: datetime) -> list[EventFlag]`

**NEW** `tradingagents/sentiment/attention.py`
- `compute_attention_features(gtrends_df: pd.DataFrame, coin: str, trade_date: datetime) -> dict`:
  - `google_search_z` (raw "Bitcoin"/"Ethereum" search, z-score over 90d)
  - `google_neg_attention_ratio` ("bitcoin hack" / "bitcoin", raw ratio + z-score)
  - `twitter_volume_z` (stub for future X integration, default 0.0)

### 3. Agent layer

**REWRITE** `tradingagents/agents/analysts/crypto_sentiment_analyst.py`
- Feature flag: `config["sentiment_mode"]` ∈ `{"v3", "legacy"}` (default `legacy` until validation passes)
- v3 path:
  1. `snapshot = build_snapshot(coin, trade_date, horizon)`
  2. Render `snapshot.to_prompt_table()` (compact Markdown ≤ 1500 tokens)
  3. Anonymize: if `config["sentiment_anonymize"]` (default True in backtest, False in live), rewrite `coin → "Asset-A"` in the prompt context, exchange names → `"Exchange-N"`
  4. Self-MoA: N=5 samples from `quick_think_llm` at T=0.7 with structured Pydantic output (`event_summary, key_drivers, risks, overall_label`); majority vote on `overall_label`, mean on numeric fields
  5. Render to `sentiment_report` string for state
- System prompt: narrow scope — events, risks, regime only. Explicit "do not infer polarity from headline tone alone; trust the snapshot polarity fields."
- Cost target: ≤ $0.005 per (coin, trade_date) at gpt-4o-mini rates with prompt caching

**NEW** `tradingagents/sentiment/anonymize.py` — `anonymize_text(text, coin) -> str` with reversible substitution table; tested unit-level.

### 4. Modulator integration

**TOUCH** modulator entry point (currently `tradingagents/strategies/hybrid_modulator.py` or equivalent — locate during impl):
- Append SentimentSnapshot numeric features to modulator's feature vector
- Features: `polarity_news`, `polarity_event`, `polarity_news_n`, `attention_search_z`, `attention_neg_ratio_z`, `fng_level`, `fng_ema24w`, `fng_extreme_flag`, `n_events_regulatory_3d`, `n_events_security_3d`, `n_events_etf_3d`, `agg_signal`
- Backwards-compat path: if `sentiment_mode == "legacy"`, features default to zeros (no feature-vector size change between modes; flag controls source, not schema)

### 5. Backtest harness wiring

**TOUCH** `scripts/backtest_hybrid.py` (or whichever harness drives `feature/hybrid-modulator` runs):
- Accept `--sentiment-mode v3|legacy` flag
- Plumb through to `config["sentiment_mode"]` and `config["sentiment_anonymize"]`
- Cache invalidation: snapshot cache keyed by mode

### 6. Validation harness

**NEW** `scripts/run_sentiment_v3_ab.py`
- 4 variants × 2 coins × 90 bars (BTC+ETH, 2026-01-16 → 2026-04-15):
  - **A** — pure V5 quant baseline (no sentiment analyst)
  - **B** — legacy sentiment analyst (current production)
  - **C** — v3 structured-only (modulator features, no LLM analyst in agent chain)
  - **D** — v3 full (modulator features + narrow LLM analyst)
- Reuse existing V5 quant config (BTC→V2 78f, ETH→V4-B 193f, 25% EW)
- All-`gpt-4o-mini`, replay cache enabled, sequential on Hetzner CX22 isolated worktree (~50h total)
- Output: `data/sentiment_v3_ab/{variant}/signals_{coin}.csv` + bootstrap 10k paired CI vs A and B
- Final summary table written to `data/sentiment_v3_ab/summary.json` and `THESIS_FINDINGS.md` §23.12

## Data flow / PIT discipline

| Source | as_of cutoff | Embargo |
|---|---|---|
| Alpaca/Benzinga | `as_of_ts < trade_date` (end-of-day UTC) | none |
| GDELT GKG | `as_of_ts < trade_date` | none (15-min lag already in `as_of_ts`) |
| Fear & Greed | `event_ts < trade_date` | none |
| Google Trends | `as_of_ts < trade_date - 1d` | **24h** (GT renormalization) |

Polarity scoring is done offline against the PIT store; cached scores are keyed by `(model_id, sha1(content))` and never re-scored at backtest time. Snapshot itself is cached by `(coin, trade_date, sentiment_mode)` for replay determinism.

## Anonymization

Backtest mode (`config["sentiment_anonymize"] = True`):
- Case-insensitive substitution: `Bitcoin|BTC|bitcoin|btc → Asset-A`, `Ethereum|ETH|ethereum|eth → Asset-B`
- Major exchange names → `Exchange-1, Exchange-2, ...` via fixed mapping (also case-insensitive)
- LLM analyst sees only anonymized text

Live mode: `config["sentiment_anonymize"] = False`. Real names — no look-ahead concern at trade time.

Unit-tested: anonymized vs original outputs on a fixed fixture must differ only by the substitution table (no semantic content lost).

## Testing strategy

**Unit**
- Scorer determinism: identical input → identical output
- Pydantic schema validation: out-of-range fields rejected
- PIT cutoff: `as_of_ts == trade_date` rows excluded; `as_of_ts < trade_date` included
- gtrends embargo: queries at `trade_date - 0d` return empty for rows with `as_of_ts >= trade_date - 1d`
- Anonymization roundtrip on fixed fixture

**Integration**
- `build_snapshot()` end-to-end against synthetic PIT fixtures (no live API)
- Narrow LLM analyst with mocked LLM responses (Self-MoA aggregation correctness)
- Modulator feature plumbing: v3 mode adds 12 features, legacy mode zeros

**Golden**
- 5 fixed `(coin, trade_date)` tuples → pinned SentimentSnapshot JSON; CI fails on drift

**Regression**
- All existing PIT P2 tests stay green
- Legacy sentiment analyst tests stay green under `sentiment_mode=legacy`
- V5 quant baseline replay (no sentiment) unchanged

## Migration plan

1. Land sentiment module + tests (no agent or modulator touched yet) — green CI
2. Land modulator feature plumbing under flag — green CI, legacy mode still default
3. Land narrow LLM analyst under flag — green CI
4. Run validation harness on Hetzner CX22 (~50h)
5. Per acceptance criteria: flip `sentiment_mode` default to `v3`, remove legacy path in follow-up PR
6. THESIS §23.12 documents result; memory updated

## Risks

- **CryptoBERT June-2022 cutoff** — may drift on post-FTX, post-spot-ETF discourse. Mitigate via continued pretraining on Alpaca/Benzinga corpus only if v1 underperforms.
- **GDELT BTC noise** (PIT P2 finding) — event-class tagging lets modulator down-weight non-event polarity for BTC. Validation harness will surface if this is sufficient.
- **Liu-Tsyvinski 2011-2018 fit** — post-ETF regime may attenuate alphas; validation reports per-period stability.
- **Google Trends PIT brittleness** — renormalization mid-window can silently change historical values. Mitigated by 24h embargo + as_of_ts logging + 90d rolling re-stitch with explicit pull timestamps.
- **gpt-4o-mini Self-MoA cost** — N=5 × 90 bars × 2 coins × 2 variants (C/D differ here) ≈ $5-15 per run; ~$40 budget for the 4-run harness.
- **FinBERT-Crypto checkpoint availability** — if no public retrained checkpoint exists, fall back to vanilla FinBERT and document the gap (option to retrain on CryptoGDelt2022 corpus as Phase 2).

## Out of scope (Phase 2)

- BNB/SOL coverage — separate spec after BTC/ETH validation passes
- Twitter/X volume features — paid API; revisit if attention_z proves valuable
- Santiment dev-activity — Max tier paywall; revisit only for ETH long-horizon
- FinBERT-Crypto continued pretraining — only if vanilla FinBERT underperforms on validation
- LightGBM modulator with sentiment features as exclusive input — current spec keeps quant features as backbone, sentiment as additive

## File map summary

NEW:
- `docs/superpowers/specs/2026-05-23-sentiment-analyst-v3-design.md` (this file)
- `docs/superpowers/plans/2026-05-23-sentiment-analyst-v3.md` (next step)
- `tradingagents/dataflows/gtrends_store.py`
- `tradingagents/sentiment/__init__.py`
- `tradingagents/sentiment/snapshot.py`
- `tradingagents/sentiment/scorers.py`
- `tradingagents/sentiment/events.py`
- `tradingagents/sentiment/attention.py`
- `tradingagents/sentiment/anonymize.py`
- `tests/sentiment/test_snapshot.py`
- `tests/sentiment/test_scorers.py`
- `tests/sentiment/test_events.py`
- `tests/sentiment/test_attention.py`
- `tests/sentiment/test_anonymize.py`
- `tests/dataflows/test_gtrends_store.py`
- `scripts/run_sentiment_v3_ab.py`

REWRITE:
- `tradingagents/agents/analysts/crypto_sentiment_analyst.py`

TOUCH:
- modulator entry point (locate during impl — likely `tradingagents/strategies/hybrid_modulator.py` or `scripts/backtest_hybrid.py` companion module)
- `scripts/backtest_hybrid.py` (CLI flag plumbing)
- `tradingagents/default_config.py` (new keys: `sentiment_mode`, `sentiment_anonymize`)
- `pyproject.toml` (deps: `transformers`, `torch` CPU build, `pytrends`)
