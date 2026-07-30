# Prediction Lab — Research Base (2026-07-30)

Distilled from three research passes (crypto-predictability literature; TS foundation
models; in-repo asset inventory). Full source links at bottom. Informs the charter
(`docs/superpowers/specs/2026-07-30-prediction-lab-charter-design.md`) and the ordering
of `BACKLOG.md`.

## 1. What the literature says is predictable (priors per target)

| Target | Prior | Key evidence | Implication for us |
|---|---|---|---|
| T3 Realized vol | **STRONG** — the genuinely predictable target; daily-RV OOS R² ~0.5–0.7 from persistence alone | HAR (Corsi 2009) transfers to crypto: lowest QLIKE/MSE on majority of 12 coins vs GARCH family (IJFS 2026); ML beats HAR for most coins **except BTC** (APFM 2024); credible ML gains = single-digit-to-low-teens % QLIKE | HAR-RV is the bar; ETH/alts more likely than BTC to show ML skill; HAR-J / HAR-RS variants worth including |
| T4 Volume | **STRONG** — most forecastable after RV | persistent, fat-tailed, 24h/weekly session seasonality (US/Asia); mixture ensembles beat single models (Digital Finance) | seasonal-naive/seasonal-AR is the bar; thin literature = room for a clean result |
| T6 Funding | **MODERATE** — AR-predictable by design (clamped, mean-reverting) | DAR one-step beats no-change on error AND direction (SSRN 5576424); Crypto Carry (Mgmt Sci 2024) | AR(1) is the bar; DAR worth adding to Tier 1 |
| T2 Direction | **WEAK-MODERATE** | daily ML DA on top-100 ≈ **52.9–54.1%** (JFDS 2022); 55%+ intraday claims largely unreplicated; base rate ≠ 50% under drift (always-up beats coin-flip on BTC) | gate vs class base rate, never vs 0.5; 2 pp over base rate is a realistic strong result |
| T1 Return level | **WEAK** | best-replicated family = **order flow**: 1σ lagged aggregate flow ≈ +0.2% daily / +0.9% weekly (J. Fin. Markets 2026); LOB imbalance predicts near-term but **vanishes under daily aggregation** (arXiv 2602.00776); Liu-Tsyvinski momentum post-2018 attenuation contested | taker-imbalance features (we have `taker_buy_quote_volume`) are the highest-prior T1/T2 feature; intraday > daily for flow effects |
| T7 XS rank | **MODERATE** | 40-char × 8-ML study shows significant OOS gains, long-leg-driven, cost-survival contested (IRFA 2024); practitioner daily rank-IC lore 0.01–0.03 | our IC ≥ 0.02 + NW-t ≥ 3 floor sits mid-lore; weekly IC easier than daily |
| T5 Range | proxy of T3 | — | keep secondary |

**Structural warnings adopted:** (i) level-forecast R² is a near-unit-root artifact — the
old Krypto-v0 ARIMA "R² 0.978" is exactly this failure mode; all T1 work is in returns,
never levels. (ii) M6 competition: forecast accuracy and investment performance largely
disconnected (TS/ML teams' average information ratio −3.374) — justifies prediction-first
framing AND warns Phase P is its own problem. (iii) Leakage endemic in crypto-ML papers
(scale-before-split, same-bar execution, LLM memorization) — our canary/kill-test
battery is not optional.

## 2. Significance toolkit (adopted into charter §5)

- **DM (1995) + HLN (1997)** small-sample/h-step correction, HAC variance lag ≥ h−1.
  **Degenerate for nested models** (errors perfectly correlated under null) → use
  **Clark-West (2007)** for nested, or **Giacomini-White (2006)** conditional test
  (valid under nesting with rolling windows — our default scheme; add alongside CW).
- **Pesaran-Timmermann (1992)** direction test assumes independence — breaks under
  serial correlation/overlap and constant-sign forecasts; complement with block
  bootstrap on directional hit series. No maintained PT package → implement + test.
- **QLIKE + MSE are the only vol-proxy-robust losses** (Patton 2011; Hansen-Lunde
  2006); QLIKE higher-powered. Rankings under other losses can flip from proxy noise.
- **Multiplicity:** White reality check → **Hansen SPA (2005)**, StepM, **MCS
  (Hansen-Lunde-Nason 2011)**; plus registry-wide BH-FDR (charter U3) and
  Harvey-Liu-Zhu t > 3 sensibility check.
- **Python:** `arch` (Sheppard) covers GARCH family + **SPA + StepM + MCS + stationary
  bootstrap** — single new dependency for most of the toolkit; `statsmodels` covers
  ARIMA/ETS/OLS-HAC (Newey-West); `dieboldmariano` pkg as dev-only cross-check of our
  DM-HLN implementation; Nixtla `statsforecast`/`utilsforecast` optional later for
  AutoARIMA/MASE at scale.

## 3. Foundation models (Tier 4 roster + leakage classes)

Finance reality check: zero-shot TSFMs ≈ **parity with HAR-class at best** — TTM
narrowly beats Log-HAR (1.3–1.8%, never ejecting HAR from the MCS; arXiv 2607.05291);
zero-shot Chronos/TimesFM lose to GBDTs on stock returns (arXiv 2511.18578). Realistic
Tier-4 goal: parity + ensemble value (TTM+Log-HAR ensemble entered MCS for ~all assets).

Leakage classes (drives per-model evaluation windows, registered at P4-01):

- **Class A — leakage-clean by construction, full dev window usable:**
  TabPFN-TS (synthetic priors only), Toto-2 (observability + synthetic, finance-free).
- **Class B — documented corpora, no crypto found; still restrict to post-release out
  of caution:** Chronos-2 (rel. 2025-10, corpus public, finance <1%), Chronos-Bolt
  (2024-11), TimesFM 2.5 (2025-09; publishes dated cutoffs), Moirai-2 (2025-08;
  **CC-BY-NC weights** — fine for thesis research), TTM r2 (2024-10; 1–5M params,
  CPU-only OK), TiRex/TiRex-2.
- **Class C — unauditable corpus → excluded:** TimeGPT (closed, finance explicitly in
  corpus, no cutoff disclosure).

Contamination is real and large where present (47–184% MSE deflation documented,
arXiv 2510.13654) — the class system is load-bearing, not paranoia.

CPU-first picks for P4: **TTM r2** (tiny, point forecasts), **Chronos-2** (120M,
quantiles, CPU-feasible), **TabPFN-TS** (Class A, quantiles). Fine-tuning: cheap for
TTM; deferred decision otherwise (gains on finance limited/negative per 2511.18578).

## 4. In-repo assets (inventory highlights binding the plan)

- **Stores:** 799-sym daily klines (2019-09→2026-07, `data/xsect/klines/`); 333-file
  1h store **with `taker_buy_quote_volume`** (2020-06→2026-07, `data/xsect/klines_1h/`);
  799-sym funding (8h prints); 8-coin Coinglass daily derivatives; bitemporal on-chain
  PIT store; DVOL (BTC/ETH implied vol, 1,816 d — useful T3 covariate). **No 1m/5m
  kline store and no sub-daily OI store exist on disk** — P1-02 fetches 5m klines
  (Vision monthly zips; `scripts/fetch_xsect_klines_1h.py` is the proven idempotent
  template, `INTERVAL` constant swap); Vision also has 5-min OI metrics from 2021-01
  (reference_data_source_audit_jul30) for P2.
- **Reusable eval code:** `tradingagents/rebuild/ledger.py` (`assert_dev_window`,
  `log_trial` w/ config-hash + git commit, `trial_count`) — predlab wraps with own
  paths; CPCV (`strategies/v3/backtest/cpcv.py`), DSR, stationary bootstrap
  (`rebuild/compare.py`, `xsect/portfolio.py`); dev-harness templates
  (`scripts/liq_fade_dev.py`, `value_xs_dev.py`) for probes→grid→ledger flow.
- **Confirmed gaps predlab must build (P1-01):** DM/HLN, CW, GW, PT, NW mean test,
  QLIKE/MASE/CRPS-pinball, MCS/SPA wiring, rolling-origin splitter (CPCV is
  combinatorial-purged, not rolling-origin), true RV builder (existing
  `compute_realized_vol` is close-to-close, not 5-min RV).
- **Existing models to wrap, not rewrite:** `models/arima_model.py` (SARIMAX + PI),
  `models/lgb_model.py` (`walk_forward_pooled(..., purge_days, target_mode)`),
  feature builders in `models/model_utils.py`, microstructure
  (`ofi_d` taker imbalance), derivatives features. **No GARCH/HAR anywhere** → `arch`
  dependency + ~60-LOC HAR-OLS.
- **Conventions:** package code in `tradingagents/predlab/`; scripts flat
  `scripts/predlab_*.py`; tests `tests/predlab/`; registration unit-tested (pattern:
  `tests/xsect/test_*_registration.py`); THESIS heading `## Section N: Title — Verdict
  (date)`; py3.9-compatible source (`from __future__ import annotations`); pytest
  markers `slow`/`online`; `TRADINGAGENTS_DATA_ROOT` respected.
- **Thesis numbering:** §50 highest on this branch; §51–§53 reserved for
  value/unlock (in flight on another worktree) → **predlab claims §54+**.
- **Env:** py3.13.13 uv venv per worktree; `statsmodels 0.14.6`, `lightgbm 4.6.0`,
  `sklearn 1.9.0`, `scipy`, `pyarrow` present; **add `arch`**; torch absent (Tier 3
  gated anyway).

## 5. Ordering rationale (why the backlog looks like it does)

1. Eval core before data (P1-01): every later item consumes it; DM/QLIKE/PT get
   reference-validated tests once, reused forever.
2. 5m klines + RV store (P1-02) unlocks T3/T4/T5 — the high-prior targets — and 1h/24h
   cells simultaneously.
3. Classical battery before ML: HAR/GARCH/ARIMA set the honest bar cheaply; every
   later tier is measured against them, so they must exist first (charter ordering
   rule).
4. Taker-imbalance features early in Phase 2 (highest-prior T1/T2 feature per §1).
5. Foundation models last among model tiers: parity-at-best prior, leakage windows
   shrink usable data, and their value is ensemble-with-HAR — which needs HAR results
   to exist.

## Sources

Lit survey: J. Fin. Markets 2026 order flow (SSRN 5020002); arXiv 2602.00776 (LOB
imbalance); Shen-Urquhart-Wang FR 2022; JFDS 2022 (52.9–54.1% DA); Liu-Tsyvinski RFS
2021; Liu-Tsyvinski-Wu JF 2022; Cakici et al. IRFA 2024; IJFS 2026 14(4):90 (HAR on 12
coins); APFM 2024 horserace; Corsi 2009; Patton JoE 2011; Hansen-Lunde 2006; M6 IJF
2025; Inan SSRN 5576424 (DAR funding); Crypto Carry Mgmt Sci 2024 / BIS WP1087; DL
review arXiv 2405.11431 (no-baseline critique); arXiv 2512.06932 (LSTM leakage);
arXiv 2412.07031 (LLM lookahead). Tests: Diebold-Mariano 1995; HLN IJF 1997; Clark-West
JoE 2007; Giacomini-White Ecta 2006; Pesaran-Timmermann JBES 1992; Hansen SPA JBES
2005; MCS Ecta 2011; Hyndman-Koehler 2006 (MASE); Politis-Romano 1994.
Foundation models: amazon/chronos-2 (HF); google/timesfm-2.5-200m-pytorch;
Salesforce/moirai-2.0-R-small; Toto-2 (Datadog blog); NX-AI/tirex-2;
ibm-granite/granite-timeseries-ttm-r2; tabpfn-time-series (PyPI); fev-bench arXiv
2509.26468; RV-TSFM arXiv 2607.05291; TSFM-finance arXiv 2511.18578; leakage arXiv
2510.13654; TSFMAudit arXiv 2605.26161; MDPI Forecasting 7(3):48 (crypto TimeGPT).
