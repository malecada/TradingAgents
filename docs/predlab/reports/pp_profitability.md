# Phase-P report — profitability mapping of the validated models (2026-07-31)

Registration `predlab_pp` frozen before any strategy result (spec:
`2026-07-31-phase-p-profitability-design.md`). Inputs = STORED P5
forecasts/panels only; models never refit. Strategy dev 2021-01→2025-03,
strategy holdout 2025-04→2026-07 one-shot (spend rule enforced in code).

## Dev gates (13 registered configs, one ledger row each)

| Candidate | Result | Gate verdict |
|---|---|---|
| **S1 T7 low-vol long-short** | all 6 configs net SR 1.11–1.48 (gross 1.41–1.88), 5bp+funding costs | **PASS all 4 gates**: floor ≥1.0; placebos p=.010/.005; DSR 0.70 (corrected¹); subs 3/3 |
| S2 HARQ vol-target overlay | TE reduction +21.5%/+26.2% vs HAR/naive (bootstrap p≈0) but SR +0.20 < both baselines (+0.34/+0.45), MaxDD worse than HAR | **FAIL** (frozen do-no-harm guard); dead this cycle |
| S3 sign filter (exploratory) | all 4 configs net SR −2.69…−0.08 | dead; +2.5pp accuracy edge does not survive 5bp/flip at 1h |

¹ DSR units bug disclosed: first computation converted hourly S3 trial SRs
at the daily factor (wrong by √24), inflating cross-trial variance → 0.052.
Corrected per-frequency conversion → 0.698. Both retained in
`pp_dev_results.json`.

Frozen config: `eq_h1` — equal-weight quintiles (long lowest-vol 40,
short highest-vol 40 of top-200), daily rebalance, no smoothing.

## Strategy-holdout one-shot (S1 only): PASS

| Metric | Dev | Holdout (2025-04→2026-07) | Criterion |
|---|---|---|---|
| Net SR | +1.48 | **+2.20** | ≥ 0.74 ✓ |
| Gross SR | +1.88 | +3.31 | — |
| Placebo (shift / xshuffle) | .010 / .005 | **.025 / .005** | both < 0.10 ✓ |
| MaxDD | 42.5% | 32.0% | not gated (disclosed) |
| Turnover /day | 0.67 | 0.57 | — |

Quarters (bp/day net): 2025Q2 −2.6, then +14.9, +42.6, +67.2, +54.8
(2026Q3 = 1 day, excluded). 4/5 positive, strengthening.

## Reading

- **The park_5 forecast survives economic translation**: net of 5 bp taker
  per side and realized funding carry, the low-vol rank book earns SR +2.2
  out-of-sample. Consistent with the forecast-level replication (IC −0.083
  holdout vs −0.089 dev) — signal did not decay; the earlier §43/§46/§47
  XS failures were weak signals, not an untradeable market.
- **Caveats, disclosed**: gross-2 unlevered book with 32-42% MaxDD — raw
  overlay, no vol targeting/stops (adding any would be a NEW registered
  cycle); 5 bp assumes taker fills on top-200 perps (plausible for small
  size; capacity untested); funding panel covers listed history, gaps=0
  disclosed; short leg concentrated in high-vol names — borrow/liquidity
  risk beyond fee model.
- **S2 lesson**: better vol *forecasting* provably improves vol *tracking*
  (+21-26%, p≈0) but did not improve SR on dev BTC — sizing-value claim
  failed its own do-no-harm guard. Honest kill; revival = new cycle.
- Verdicts: `data/predlab/pp_holdout_verdicts.json` (blocks re-runs);
  ledger rows under `predlab_pp`.
