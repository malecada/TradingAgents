# Quant-First Redirection: Sentiment Index Feature + Prediction-Model Improvements — Design

Date: 2026-07-03. Status: approved direction from supervisor/user; implementation pending.

## 1. Direction change

Previous framing: hybrid/LLM system tries to match and beat the quant baseline.
New framing: **the quant system (V5 MIX) is the main actor** — preferred for determinism. LLMs are demoted to an optional support role (position-size modulation on coins where it is validated to help). The goal is the best-performing system overall, not LLM-vs-quant comparison.

Two workstreams:

- **A. Sentiment index as a quant feature** — build a daily numeric news-sentiment index (full-text corpus, per supervisor's `News_fulltext/` template methodology) and inject it into the LightGBM feature matrix. This is genuinely new: verified that **no sentiment-derived number has ever entered the LGB matrix** (grep across `tradingagents/models/`, `strategies/`, live `retrain.py`/`predict.py`: zero hits for sentiment/fng/news). All prior sentiment work fed LLM agents only.
- **B. Prediction-model analysis + improvements** — evidence-ranked experiments on the LGB pipeline itself, plus ship decisions for already-validated wins.

Plans: `docs/superpowers/plans/2026-07-03-sentiment-index-feature.md` (A) and `docs/superpowers/plans/2026-07-03-model-improvement-experiments.md` (B).

## 2. Current model — factual map (verified 2026-07-03)

- **Model**: `lgb.LGBMRegressor` (n_estimators=500, lr=0.05, num_leaves=31, min_child_samples=20, seed=42), MinMaxScaler per fit, pooled across coins with `coin_int` categorical. Predicts **raw price level** at h=7 and h=14 (`prices_h{h} = prices.shift(-h)`); direction = prediction vs `ref_price`. h=1/h=3 computed but unused (noise).
- **Features**: 78f canonical (OHLCV-derived + `ti_*` stockstats + `xa_*` cross-asset + `oc_funding_rate`/`oc_tvl_delta`/`oc_stable_delta` + lags + calendar) routed to BTC/BNB/XRP/DOGE/TRX; 193f extended (+`oc_*` PIT on-chain + Coinglass derivatives + DVOL) routed to ETH/SOL/ADA. Routing = one flag `add_onchain_pit` in `build_pooled_dataset` (`model_utils.py:374-527`).
- **Sizing (where ~90% of the alpha lives, per BT11/`validate_v5_mix.py` attribution)**: h7+h14 asymmetric term-structure consensus → confidence (`|pred−ref|/ref` scaled by `confidence_ref=0.05`) → 0.5-Kelly × vol-target (0.10 backtest; live V5.1 = 0.07) → conditional leverage ≤3× → min-hold 7 + early-exit → trend filter (×2.0 aligned / ÷2.0 against, SMA20 — V5.1 live values) → core/satellite weights (15%/10%) → 3% price stop, 15% portfolio circuit breaker.
- **Validation harness**: walk-forward (`walkforward_v2.py`), CPCV+PBO (`cpcv_v2.py`, `validate_v5_robustness.py`), stationary-bootstrap ΔSR CI (`bootstrap_sharpe.py`), DSR + random-entry placebo (`validate_v5_mix.py`). Experiments = standalone scripts with top-of-file constant dicts; no config registry.
- **PIT store**: long bitemporal schema `[event_ts, as_of_ts, coin, metric, value, source, status]` (`onchain_store.py`), merge_asof-backward join in `build_pit_onchain_features`, global 1-day shift in `data_transform` so all features originate t−1.
- **Baselines to beat**: 4-coin V5 MIX SR 3.18 (drifted from published 3.25; use 3.18), 8-coin SR 3.97 (4.5-yr WF, backtest only). Live: Hetzner `live-v2.6.2`, quant healthy, hybrid A/B line running.

## 3. Workstream A — sentiment index design

### 3.1 What the supervisor's template provides (`News_fulltext/`)

Extracted recipe (traffic/econ/athlete projects, same skeleton):
1. Multi-source ingestion (GDELT DOC 2.0 + Scrapy/Newspaper3k full-text, Google News, Reddit, NewsAPI, Event Registry) → unified `[url, title, seendate, body, source]`.
2. **Engine A**: GPT-4o relevance filter + sentiment scoring, output contract `"Relevant. [summary], Index: N"` with **integer 0–4 scale** (0=very negative … 4=very positive), regex-parsed (`re.findall` after `split('Index')`).
3. **Engine B**: HuggingFace classifier per article (confidence as index).
4. Daily numeric aggregation is **absent from the template** — must be designed here.
5. `gdelt_project/keywords.py` already contains a ready `crypto` keyword group.

### 3.2 Corpus decision (research verified 2026-07-03)

| Source | Full text | Coverage | Cost | Role |
|---|---|---|---|---|
| **Existing Alpaca store** `data/sentiment/alpaca/` | yes (`content`, mean ~2.9k chars) | 13,644 articles 2021-03→2026-04, dense 2023-10+ (~400-550/mo BTC) | $0, on disk | **Primary** (BTC/ETH), tail-refresh to current date |
| **HF `edaschau/bitcoin_news`** | yes (`article_text`, minute UTC timestamps) | 210,832 rows 2011-06→2025-06 | $0, re-ingest script exists (`ingest_hf_bitcoin_news.py`) | **Primary long-history BTC**; enables 2021+ index |
| HF `edaschau/financial_news` | yes | Yahoo Finance general; keyword-filter ETH/alts | $0 | Optional ETH history top-up |
| GDELT DOC → trafilatura scrape → Wayback rescue | scrape (~60-75% alive, ~85-90% after Wayback) | 2017+ any coin | $0, 1-2 wk effort | **Deferred fallback** for alt-coin breadth (Phase 2) |
| CryptoPanic / CoinDesk Data API / Tiingo / NewsAPI | — | — | free tiers dead or 1-3 mo depth | Rejected |

Phase-1 scope: **BTC + ETH per-coin indices + one global crypto-market index**. The global index is stored as `coin="global"` so every coin's feature row can consume it (same mechanism as F&G/DEX-vol). Alt-coin per-coin indices deferred until the GDELT scrape fallback is justified by Phase-1 results.

### 3.3 Scoring engines (dual, mirrors template + thesis narrative)

- **Engine A (LLM)**: `gpt-4o-mini`, crypto-adapted version of the supervisor's verbatim prompt structure (STEP 1 relevance / STEP 2 relevant-or-not + ≤500-token summary / STEP 3 index 0–4; identical output contract so the template parser carries over). SQLite cache keyed `(model_id, content_sha)` — same pattern as the existing `scorer_cache.sqlite`. Cost estimate: Alpaca 13.6k articles ≈ $4-8; HF 2023-10+ slice (~50k) ≈ $15-25. **Constraint: LLM-scored index is only PIT-honest from 2023-10** (gpt-4o-mini knowledge cutoff; scoring pre-cutoff articles with a model that knows the outcome = memory look-ahead, per `feedback_llm_cutoff_constraint` and Glasserman & Lin distraction/look-ahead results). Ticker anonymization (existing `sentiment/anonymize.py`) is a cheap extra guard — apply it.
- **Engine B (CryptoBERT)**: `ElKulako/cryptobert` via existing `tradingagents/sentiment/scorers.py` (`score_polarity_mean` = p_bull − p_bear, sqlite-cached). Deterministic, free, **no knowledge-cutoff problem** → covers full 2021+ history. Known weakness: trained on social posts, not news; that is what the A/B is for.
- Primary A/B window **2023-10-01 → 2026-05-26** (both engines valid, dense Alpaca coverage). Secondary BTC-only long window 2021-07+ with Engine B to test history value.

### 3.4 Daily aggregation → features (the part the template omits)

Per coin (btc, eth) and global, per UTC day, from articles with `as_of_ts ≤ end-of-day`:

- `snt_idx_mean` — mean of per-article scores mapped to [−1, +1] (Engine A: (idx−2)/2; Engine B: polarity already in [−1,1]).
- `snt_idx_ewm3` — EWMA of `snt_idx_mean`, half-life 3 days (event half-life 2-5d per literature).
- `snt_cnt_z30` — z-score of daily article count over 30d (attention volume — Liu-Tsyvinski: volume > polarity).
- `snt_neg_share_7d` — 7d rolling share of articles with score < 0 (negative-attention proxy).
- `snt_disp_7d` — 7d rolling std of article scores (disagreement).
- Plus free wins from data already on disk (2018+, full coverage): `fng_level`, `fng_ema_168d`, `fng_dev` (level − EMA; the literature supports the *level/EMA*, explicitly not ΔF&G).

No-news days: features carry forward via EWMA/rolling windows; `snt_idx_mean` NaN→0 (neutral) only inside the rolling constructions, and a `snt_cnt_z30` of strongly negative value already encodes "quiet day". Keep the new column count small (≈10) — the 78f route is deliberately lean and prior evidence (§17) says indiscriminate feature addition hurts BTC-class coins.

### 3.5 Integration decision

- **New store** `data/sentiment/index/` with the canonical long schema (copy-adapt `onchain_store.py`) — do not contaminate the on-chain store.
- **New feature builder** `tradingagents/dataflows/sentiment_features.py::build_sentiment_features` mirroring `build_pit_onchain_features` (merge_asof backward, calendar reindex).
- **New flag** `add_sentiment: bool = False` in `build_pooled_dataset` — NOT a widening of the existing 78f/193f sets. This creates route variants `78f+s` / `193f+s`, keeps every existing checkpoint and result comparable, and turns sentiment into a third per-coin routing axis, consistent with the V5 MIX philosophy (feature routing is coin-specific).
- The global t−1 shift in `data_transform` already guarantees the model only sees yesterday's index; article `as_of_ts = event_ts + 1h` mirrors existing store conventions.
- Live parity: `test_predict_feature_parity.py` forces the flag to be wired symmetrically into `execution/live/retrain.py` and `predict.py` — done only for coins that pass acceptance (conditional ship task).

### 3.6 Validation & acceptance (do-no-harm, per-coin)

Regenerate predictions per route variant with `evaluate_models_multi.py` on the A/B window, run `baseline_v5_mix.py` portfolio, then per coin:

- ΔSR vs same-window baseline with stationary-bootstrap 95% CI (`bootstrap_sharpe.py`, block 21).
- Ship a coin to the `+s` route only if: **p_pos ≥ 0.90** (bootstrap P(ΔSR>0)), **MaxDD not worse by >1pp**, and CPCV fold-consistency does not degrade. Same three-gate pattern that rejected market-analyst-v2 — symmetric standards.
- DSR guard: we will test ~8 configurations (2 engines × per-coin) — report Deflated Sharpe with that trial count.
- Expected outcome honestly stated: prior project evidence is that *sentiment-as-LLM-input* was noise or harmful (§10.3 GDELT hurt BTC; §23.11 LOO sentiment=noise; §23.12 v3 hurt ETH). This experiment is materially different (numeric feature, LGB can down-weight it, gain-importance is observable), and the literature ceiling is ΔSR +0.10–0.30. A clean null is an acceptable thesis result; gates prevent shipping a null.

### 3.7 Risks

1. **Coverage asymmetry**: alt coins have thin Benzinga coverage (~10-18/mo BNB) — global index only for them in Phase 1.
2. **LLM look-ahead**: bounded by 2023-10 window start + anonymization; Engine B cross-check on the same window quantifies residual LLM-memory effect.
3. **78f schema drift**: avoided by flag-based route variants; canonical checkpoints untouched.
4. **Multiple testing**: DSR with declared trial count; pre-registered gates above.

## 4. Workstream B — model analysis findings & improvement candidates

Ranked by (evidence strength × effort). Full recipes in plan B.

| # | Candidate | Evidence | Status/expectation |
|---|---|---|---|
| B0 | Trend-mult 2.0, SMA 20, target_vol 0.07 (V5.1) | SR 3.18→3.51, 6/6 yrs | **Already shipped** on `feature/trend-mult-v51-hybrid-routing` (live config verified). No action beyond monitoring. |
| B1 | **Return-space target**: predict `log(P_{t+h}/P_t)` instead of raw price level | Structural: trees cannot extrapolate above the trained price range → systematic downward bias at new ATHs; MinMaxScaler on levels drifts in expanding window. Cheap A/B. | New experiment; plausibly the highest-upside signal fix. |
| B2 | **Training-window-staggered prediction ensemble** (average preds from train-end offsets 0/−21/−42d) | PIT/vintage audit: training-window instability = 100% of WF non-reproducibility (16% signal flip per 3-wk shift); seed-ensemble was negative but targets a *different* variance source | New experiment; success metric = flip-rate ↓ without SR ↓. |
| B3 | **Quantile-LGB confidence** (q10/q50/q90 → spread-based confidence replacing `confidence_ref=0.05` heuristic) | 90% of alpha is sizing; confidence is the sizing input; current scaling is an uncalibrated constant | New experiment; medium effort. |
| B4 | **Carry sleeve @20% blend** | Validated: SR 3.178→3.287, DD 4.9→4.0%, corr +0.003 (repo §32, 23 tests, committed) | **Ship decision only** (live wiring task). |
| B5 | V4-heuristic regime overlay | SR-neutral, DD reducer (BTC 6.7→4.4%) | Optional live risk add; decide after B4. |
| B6 | Satellite routing sweep (XRP/DOGE/TRX on 193f; all coins on `+s` variants) | ada→193f won in 8-coin expansion; routing is the proven lever | Cheap harness reuse; fold into A's validation matrix where possible. |
| B7 | LLM support role (new doctrine): modulator only where validated — BNB (+1.41 SR, P=.99), ETH (with drop-market variant) | Full-year hybrid A/B | Mostly wired on V5.1 branch (per-coin hybrid routing); pending modprompt v1/v2 ETH A/B already queued. Keep as-is; no new build. |

Explicitly **not** pursued (documented negatives): V3 architecture re-attempts (NH-HMM/VPIN/multi-horizon stacking — systematic negative), seed ensembles, intraday SL/TP changes (price-axis 3% stands), weight optimization vs 1/N, sentiment analyst revival on ETH/BTC.

## 5. Open questions (flagged, non-blocking — defaults chosen)

1. Engine A model: default `gpt-4o-mini` (cost policy). Upgrade to a newer mini-tier only if Engine A wins gates and marginal-cost analysis justifies re-scoring.
2. ETH history top-up from `financial_news` keyword filter: attempt in Phase 1 only if ETH Alpaca-only A/B is underpowered (< ~800 scored articles/yr).
3. Alt-coin GDELT scrape (supervisor's Scrapy template adapted with `keywords.py` crypto group): Phase 2, only if Phase 1 ships at least one coin.
4. Where LLM-support (B7) lands long-term is outside this spec; the hybrid A/B line continues unchanged.
