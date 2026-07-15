# Meta-Labeled Trend System — Design Spec

Date: 2026-07-15
Branch: `feature/meta-labeling` (based on `rebuild/honest-2026-07` @ f789916)
Status: DESIGN — pre-registration artifacts (gates.json, trial ledger) must be committed before any experiment runs.

## 1. Motivation and evidence base

Goal: resurrect the "strategy built around a prediction model" thesis line by changing **what the model predicts** — from unconditional price direction (repeatedly negative) to the conditional success probability of an already-positive model-free signal (meta-labeling, Lopez de Prado).

Evidence that motivated this design:

- Internal: LightGBM on 176 engineered features systematically loses to model-free MA-cross on BTC/ETH 4.5-yr walk-forward under the leak-free harness (§40); V3 architecture sweep negative (BT8/BT11); daily BTC/ETH autocorrelation ≈ 0 post-2021; signal-density diagnosis — daily bars x 2 majors ≈ 3,300 coin-bars starves any per-coin learner.
- External (deep-research pass 2026-07-15, 101-agent adversarially verified): time-series foundation models (Chronos, TimesFM, TimeGPT, Moirai) achieve 50–53% directional accuracy on daily returns and are degraded by fine-tuning; PatchTST/iTransformer show negative IC on a 66-coin daily cross-section; naive baselines beat XGBoost/RF/N-BEATS at 1/7/30-day horizons on 5 majors; 3–10 bps of costs flip every published gross-positive daily/hourly ML strategy negative; the only net-positive published claim found (CryptoGAT) was refuted 0–3 at verification. Two doors left open: exogenous covariates (flagged by the strongest peer-reviewed benchmark as the only credible accuracy route) and alternative targets (meta-labeling / triple-barrier / vol — no verified evidence either way; unexplored, not refuted).

Design consequences: (a) primary directional decision stays model-free; (b) ML consumes exogenous covariates (positioning + on-chain), not price lags; (c) the ML layer can only **remove or shrink** trades, so it reduces turnover and fees rather than adding them — inverting the cost-death mechanism; (d) pooling events across 8 coins attacks the breadth constraint.

## 2. System architecture

Four layers, strictly ordered; each layer frozen before the next is fit.

### 2.1 Primary signal (model-free, FROZEN)

- Universe: live 8-coin set — BTC, ETH, BNB, SOL (core) + XRP, DOGE, ADA, TRX (satellite), per `scripts/baseline_v5_mix.py` CORE_COINS/SATELLITE_COINS.
- Signal: long-flat trend ensemble per coin — equal-weight vote of MA-cross (fast/slow: 5/20, 10/40, 20/60) and Donchian breakout (20d entry / 10d exit), daily bars.
- An **entry event** occurs when the ensemble vote crosses from ≤ 0.5 to > 0.5. Position held while vote > 0.5, exited on vote ≤ 0.5 or barrier touch (below).
- Parameters above are fixed a priori from the literature-standard short-lookback range (5–60d) and are NOT tuned at any point in this project. Freeze contract: this section's parameters are pinned in `freeze.json` committed before the first backtest of the primary.
- Primary must be run once on dev to establish the baseline SR (denominator for G2). This run is also one-shot: no iteration on the primary after seeing its results.

### 2.2 Event and label layer (triple-barrier)

For each entry event at bar t with entry price P_t and vol estimate σ_t (20d EWMA of daily returns):

- Profit-take barrier: P_t · (1 + 2.0 σ_t)
- Stop barrier: P_t · (1 − 1.5 σ_t)
- Vertical barrier: t + 15 trading days
- Label y = 1 if PT touched first; y = 0 if SL or vertical touched first with net return ≤ 0; y = 1 if vertical touched with net return > 0 (sign-of-return at vertical, standard AFML §3.5).
- Barrier constants (2.0 / 1.5 / 15d) fixed a priori to match the primary's natural trade geometry; not tuned.
- Intrabar touch resolution uses the intrabar price-stop replay logic from `tradingagents/rebuild/` (Task 3, commit de2980d): high/low ordering convention, conservative (SL checked before PT when both touched in one bar).
- Overlapping events (same coin, overlapping [t, barrier-touch] windows) get average-uniqueness sample weights (AFML §4.5). Cross-coin events are independent.

### 2.3 Meta-model

- Baselines (must beat to pass G1): (i) constant p = train-set base rate; (ii) L2 logistic regression on the same features.
- Model: LightGBM binary classifier, isotonic calibration fit on a nested split of train only. Conservative fixed hyperparameter grid (≤ 12 combos), selected inside the walk-forward training window via purged 3-fold CV — never on test folds.
- Features, all strictly measurable at bar t close (PIT stores, no revision leakage):
  - Trend context: ensemble vote strength, trend age (bars since cross), distance to 20d high, 20d/60d return.
  - Vol regime: σ_t level and 60d percentile, vol-of-vol.
  - Positioning (Coinglass PIT): funding rate level + 7d z, OI z, liquidation z (long/short), long-short ratio, taker buy/sell imbalance, smart-money divergence.
  - On-chain (CM/DefiLlama PIT store): active-address z, exchange-flow z, TVL delta (where coverage exists; NaN where not — LightGBM native NaN handling).
  - Market context: F&G index, cross-coin breadth (fraction of 8 coins with vote > 0.5), BTC 20d return (for alts).
  - Identity: coin one-hot.
- Pooled training across all 8 coins. Expected event count ~1–2K over the dev window; per-fold minimums asserted (≥ 150 train events; else fold skipped and logged).

### 2.4 Decision layer

- Take the trade iff calibrated p̂ ≥ τ; size multiplier = clip((p̂ − τ) / (0.7 − τ), 0.25, 1.0) applied to the primary's vol-target weight.
- τ selected on dev only, from grid {0.45, 0.50, 0.55, 0.60}, and pre-registered in the ledger before the holdout run.
- Meta layer can only skip or shrink trades. It never adds trades, never flips direction, never levers up beyond the primary weight.

## 3. Evaluation protocol (pre-registered)

- Harness: corrected causal + purged engine lineage (main @ 382d189 fixes + rebuild intrabar stop). Same-bar execution forbidden; signals at close t execute at open t+1.
- Data split: dev = 2021-07-01 … 2025-03-31; **locked holdout = 2025-04-01 … 2026-06-30** — aligned with the pre-existing house lock `HOLDOUT_START = 2025-04-01` in `tradingagents/rebuild/ledger.py` (stricter than the originally drafted 2025-07 boundary; guard code unmodified). Holdout OHLCV/feature files hashed and untouched until G3. Holdout guard from `tradingagents/rebuild/ledger.py` enforces access.
- Walk-forward on dev: expanding window, retrain every 90 days, embargo = 15 trading days (= vertical barrier) after each train window; purge events whose label window overlaps the test block (Lopez de Prado purged K-fold adapted to WF).
- Costs: 10 bps round trip + funding where applicable — identical to rebuild convention.
- Trial ledger: every model fit / config run logged via `tradingagents/rebuild/ledger.py`; gates.json committed BEFORE the first experiment.

### Gates

- **G1 (model quality, dev):** pooled OOS AUC with 95% bootstrap CI excluding 0.5, AND AUC ≥ logistic baseline AUC, AND calibrated Brier ≤ constant-base-rate Brier. Fail → stop, document negative.
- **G2 (economic, dev):** meta-filtered strategy net SR ≥ primary net SR (do-no-harm), ΔSR bootstrap p_pos ≥ 0.90, MaxDD ≤ primary MaxDD × 1.1. Dual SR reporting per halt-latch convention. Fail → stop, document negative.
- **G3 (holdout, one-shot):** frozen pipeline (primary + labeler + model + τ) run once on holdout. Verdict = holdout ΔSR > 0 and no catastrophic degradation (holdout net SR > 0 or > primary's holdout SR). No re-runs regardless of outcome.

Multiple-testing discipline: exactly one primary, one label geometry, one model family + one linear baseline, one τ grid (4 values). Everything else frozen. Any deviation requires a new ledger entry and taints the holdout.

## 4. Deliverables and repo layout

- `tradingagents/metalabel/primary.py` — trend ensemble + event extraction
- `tradingagents/metalabel/labeler.py` — triple-barrier labels + uniqueness weights
- `tradingagents/metalabel/features.py` — PIT feature assembly at event bars
- `tradingagents/metalabel/model.py` — baselines, LGB, calibration
- `tradingagents/metalabel/backtest.py` — meta-filtered replay on top of primary (reuses rebuild engine)
- `scripts/metalabel_run.py` — dev WF + gates; `scripts/metalabel_holdout.py` — G3 one-shot
- `experiments/metalabel/gates.json`, `freeze.json`, ledger entries
- Tests: leak tests (features ≤ t, labels > t), barrier-touch golden fixtures (incl. same-bar PT+SL), purge/embargo correctness, uniqueness weights, calibration monotonicity, holdout-guard denial test.
- THESIS section (§44): method + result, positive or negative.

## 5. Error handling

- Missing Coinglass/on-chain history for early years or small coins → NaN features (LGB native); assert per-feature coverage report logged, no silent zero-fill (CPI zero-fill lesson).
- Coins with < 30 events in dev → included in pooled training, excluded from per-coin reporting.
- Zero-variance SR windows → SR := 0 convention (halt-latch memory).
- Cache files: canonical filenames, no embedded dates (rate-limit lesson).

## 6. Risks and honest expectations

- G1 may fail: trade-outcome predictability given entry may be as absent as unconditional direction. Pre-registered stop honors that.
- Event count (~1–2K) is small; wide CIs expected. Pooling + uniqueness weights mitigate but don't remove this.
- The meta layer cannot raise SR by more than the fraction of bad trades it can identify; realistic upside is filtering the ~50% of trend entries that whipsaw. Even ΔSR ≈ +0.3–0.5 with reduced DD would validate the thesis claim ("a prediction model with sufficient accuracy can improve a trading strategy") in its honest, conditional form.
