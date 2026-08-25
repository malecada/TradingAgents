# rviv_p0 — RV-forecast vs IV-implied forecast (Deribit DVOL variance-premium lead, P0 probe)

Registered 2026-08-25, BEFORE any results. Scope approved by user: **P0 forecast
probe only** — dev-window evaluation, no holdout touch, no strategy layer, $0
external cost. Successor context: research program closed 2026-08-24 with zero
validated strategies; this is the single unfalsified vol-monetization channel
(state memory `state-aug24-research-closed`).

## Claim (falsifiable)

A point-in-time realized-volatility forecast beats the option market's implied
forecast — **debiased DVOL** — at predicting next-30-day realized volatility of
BTC and ETH, out-of-sample within the dev window.

Rationale for the bar: raw DVOL is a *biased-high* RV forecast by construction
(variance risk premium), so beating raw IV at a proper loss is uninformative.
The honest market benchmark is DVOL passed through a PIT debiasing regression.

## Data (all on-disk, no network)

| Series | Source | Coverage | Vintage note |
|---|---|---|---|
| Daily log return `ret`, 5m-RV `rv` | `data/predlab/rv_1d/{BTCUSDT,ETHUSDT}.parquet` | 2020-01-02 → 2026-07-30 | built from Binance 5m klines |
| DVOL OHLC (30d annualized IV, %) | `data/options/{btc,eth}_dvol.parquet` | 2021-06-01 → 2026-05-26 | Deribit public API, fetched 2026-05 |

Daily **simple** return: `r_t = exp(ret_t) − 1` (Aug-24 house rule: simple
returns are the primary convention everywhere; log variant appears only as the
convention-swap kill-test).

## Definitions (pinned)

- **Target** `RV30(t)` = sqrt( 365 × mean(r_s², s ∈ t+1 … t+30 calendar days) ),
  uncentered. Requires ≥25 non-NaN daily returns in the window, else NaN.
- **Predictor** `iv(t)` = `dvol_close(t) / 100` (annualized vol units).
- **Trailing RV_k(t)** = sqrt( 365 × mean(r_s², s ∈ t−k+1 … t) ), calendar days,
  ≥⌈0.8k⌉ non-NaN required.
- **PIT training-pair rule**: any regression fitted at day t may use pairs
  (features(s), RV30(s)) only where s + 30 calendar days ≤ t (target window
  completed). Refit daily, expanding window, OLS, min 365 pairs.

## Baselines (frozen)

- **B0** raw DVOL: `σ̂ = iv(t)` — disclosure only (bias-inflated).
- **B1 debiased DVOL (THE BAR)**: expanding PIT OLS `RV30(s) ~ a + b·iv(s)`,
  prediction `max(â + b̂·iv(t), 0.01)`.
- **B2** trailing RV20: `σ̂ = RV_20(t)` — sanity floor.

## Candidates (frozen, ≤4)

- **C1** EWMA-20: pandas `ewm(span=20)` mean of daily simple r², sqrt, ×√365,
  constant projection to 30d. Secondary, disclosure only.
- **C2 HAR-30 — PRIMARY**: expanding PIT OLS
  `RV30(s) ~ a + b1·RV_1(s) + b2·RV_5(s) + b3·RV_30(s)`, prediction floored at
  0.01. (RV_1 = sqrt(365·r_t²).)
- **C3** HAR-30 + DVOL: C2 regressors + `iv(s)`. Encompassing **diagnostic
  only** (nests B1 information; never a claim). Question answered: does
  realized-side info add anything on top of IV, and vice versa.

No other candidates, no tuning, no lag/span sweeps. Single run per frozen spec.

## Evaluation

- **Eval days**: t ∈ 2022-06-01 … 2025-03-31 (inside predlab dev convention
  2021-01→2025-03; first year of DVOL burns in the debiasing regression;
  target windows end ≤ 2025-04-30 < any holdout claim window — and this cycle
  makes **no holdout claims** regardless).
- **Loss (primary)**: QLIKE on variance,
  `L = σ²_true/σ²_pred − ln(σ²_true/σ²_pred) − 1`. Secondary: MSE on vol level.
- **Test**: Diebold-Mariano on per-day loss differential (candidate − B1),
  HAC/Newey-West lag 30 (overlapping 30d targets), two-sided, normal approx.
- **PASS (primary claim)**: C2 vs B1 — relative QLIKE improvement ≥ **3%** AND
  DM p < 0.05, with improvement (not degradation), on **both** BTC and ETH.
  Both-or-fail; no per-asset cherry-pick. This is a single pre-named test
  evaluated jointly on two assets — conservative, no FDR needed for the
  primary. All other comparisons (C1, C3, B0, B2, MSE) are disclosure.
- Effective independence: ~1,035 eval days / 30d overlap ≈ 34 independent
  windows per asset — power is modest; the 3% floor reflects that.

## Pre-registered descriptive output (thesis content either way)

Annual variance risk premium per asset: mean(iv² − RV30²) and mean(iv − RV30)
per calendar year 2021-2026 (full DVOL coverage, descriptive only, no gate).

## Forensics (mandatory before verdict)

1. **F1 convention-swap kill-test** (house rule
   `feedback_never_log_returns_as_pnl`): recompute target from log returns;
   verdict must not flip. If it flips → investigate before any verdict.
2. **F2 shuffled-IV probe**: circular-shift DVOL by ≥180d; B1 must degrade to
   ≈B2 level and C3 must collapse to ≈C2. If shuffled B1 still "beats" things,
   the harness is broken.
3. **F3 PIT audit**: unit test asserting the training-pair rule (no pair with
   s + 30d > t) and that forecasts at t use no data after t.
4. **F4 annualization sanity**: mean RV30 and mean iv within [0.2, 1.5]
   annualized for both assets; same units confirmed.

## Stop rule

- FAIL → lead CLOSED; RV-vs-IV stays thesis future-work, program remains
  closed. No re-tuning, no candidate additions, no window changes.
- PASS → stop-and-decide with user. Known constraints for any next tier,
  recorded now: the 2025-04→2026-07 predlab holdout is spent/contaminated for
  this family; virgin data accrues from 2026-07-02 (~8 weeks as of
  registration — too short); any economic layer needs a tradable-instrument
  design (DVOL is an index, not a price).

## Mechanics

Branch `research/prediction-lab`, worktree TradingAgents-predlab.
Script `scripts/predlab_rviv_p0.py`, tests `tests/test_rviv_p0.py`,
outputs `data/predlab/rviv/`, gates key `predlab_rviv_p0` (registered in the
same commit as this charter, before results), ledger rows appended to the
predlab trial ledger.
