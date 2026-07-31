# Phase P — Profitability Mapping of the Holdout-Validated Prediction Models

Date: 2026-07-31. Status: registered (gates key `predlab_pp`) BEFORE any
strategy backtest result. Follows the house pre-registration standard
(trial ledger, frozen gates, one-shot, forensic verification of any pass).

## Question

The Prediction Lab produced 7 U1–U4 usable forecast models (THESIS §57).
Forecast skill ≠ tradability. Phase P asks, per model family: does the
validated forecast translate into net economic value after costs — and
answers PASS/FAIL with the same discipline as the forecast claims.

## Inputs (frozen — no model retraining, no re-tuning)

- Stored dev forecasts (2021-01-01 → 2025-03-31) and stored causal
  holdout forecasts (2025-04-01 → 2026-07-01) for every champion +
  baseline, exactly as generated in P5. Models are NEVER refit in Phase P.
- T7 panels (799-sym survivorship-safe store) + monthly top-200 universe.
- Funding store (2019-09 → 2026-07-03) for carry costs.

## Window discipline

- **Strategy-dev window = 2021-01 → 2025-03.** All strategy design
  iteration happens here, on dev-period forecasts only.
- **Strategy-holdout = 2025-04 → 2026-07, one-shot.** One frozen config
  per candidate, evaluated once on the stored holdout forecasts. The
  forecast models are frozen artifacts, so reusing the P5 holdout window
  for the STRATEGY one-shot introduces no model-selection leakage; the
  strategy layer sees this window exactly once.

## Registered candidates

### S1 — T7 low-vol rank long-short (the only direct return play)
- Signal: park_5 (5-day mean Parkinson vol, shifted 1 day), daily
  cross-sectional rank on the monthly top-200 PIT universe.
- Portfolio family (dev may pick ONE config): long bottom-signal
  quintile / short top-signal quintile, equal- or rank-weighted;
  optional 2-5 day holding smoothing. ≤ 6 configs total on dev.
- Costs: taker 5 bp per side (Binance USDT-perp taker tier, no
  discounts), plus realized funding carry per leg where funding data
  exists (else 0 — disclosed). Turnover accounted per rebalance.
- Prior: guarded — §43/§46/§47 XS strategies died on costs; this IC is
  ~4× stronger.

### S2 — BTC HARQ vol-targeting overlay (sizing value, not alpha)
- Base: long-only BTC daily, position = target_vol / σ̂_t, σ̂ from (a)
  HARQ (champion), (b) HAR (strong baseline), (c) trailing 20-day
  realized vol (naive). Target vol 20% ann.; leverage cap 3×; costs 5 bp
  on position changes.
- Claim: HARQ sizing beats baselines on realized-vol tracking error to
  target, with SR/MaxDD not worse.

### S3 (exploratory, disclosed) — hourly sign filter
- BTC 1h logit sign edge (+2.51pp holdout accuracy edge; Brier verdict
  FAIL) as long/flat filter on 1h BTC. Exploratory ONLY: the underlying
  forecast claim failed its registered criteria; any positive result here
  is hypothesis-generating, cannot graduate past dev in this cycle.

Out of scope: volume-model monetization (execution/slippage support role;
needs an intraday execution simulator — not testable in this harness).

## Gates (frozen)

Dev gate per candidate (all must hold to earn the holdout spend):
1. Net SR ≥ 1.0 (house floor) on strategy-dev window (S2: tracking-error
   reduction ≥ 15% vs BOTH baselines with bootstrap p < 0.05, SR and
   MaxDD not worse than either baseline).
2. Dual-family placebo p < 0.05 (time-shuffled signal + sign-flip
   families — house §45 pattern) for S1/S3.
3. DSR > 0.5 at n_trials = total registered configs across Phase P
   (≤ 13: 6 S1 + 3 S2 + 4 S3).
4. Positive net mean in ≥ half of dev sub-periods (2021-22, 2023-24,
   2025Q1).

Holdout one-shot criteria (U-P): net SR ≥ 0.5 × dev net SR AND same
sign AND placebo family p < 0.10 on holdout (S2: tracking-error
improvement ≥ 0.5 × dev improvement). One evaluation per candidate,
PASS/FAIL recorded, no second look, spend rule enforced in code.

## Stop rules

Candidates/configs fixed at registration; no additions after first dev
result. Failing dev gate = candidate dead this cycle (revival needs new
registered cycle on fresh data). Ledger row per config evaluated.

## Deliverables

Engine `tradingagents/predlab/pp/` + `scripts/predlab_pp*.py`, reports
`docs/predlab/reports/pp_*.md`, THESIS §58+, verdicts JSON with
code-enforced spend rule.
