# Phase-5 report — MCS champion freeze + sealed-holdout one-shots (2026-07-31)

Registration `predlab_p5` (frozen before any MCS computation). Holdout
2025-04-01 → 2026-07-01 (15 months, 457 daily / 10,945 hourly origins),
sealed since program kickoff with **zero prior spends**. One evaluation per
frozen champion, spend rule enforced in code (verdicts file blocks re-runs).
Champion + strong baseline recomputed **causally** on the holdout (training
windows may include dev — legitimate walk-forward; nothing from the holdout
ever fed a modeling choice). Config-parity with the dev batteries was
verified against the battery source before the spend; three would-be
mismatches were caught in review (logit refit cadence, a hidden dev-end clip
in the T4 feature builder, a T2 alignment bug) — none touched holdout data.

U4 criteria (registered): DM p<0.05 vs the cell's strong baseline AND
holdout effect ≥ 0.5 × dev effect AND same sign; T2 additionally accuracy
edge ≥ 1.0pp; T7: |IC| ≥ 0.02 with |NW-t| ≥ 2 and dev sign.

## Verdicts — 7/10 PASS

| Cell | Champion | Baseline | Dev eff | Floor | Holdout eff | DM p | Verdict |
|---|---|---|---|---|---|---|---|
| BTC 1h T3 (rv) | harq | har_levels | +11.5% | 5.7% | **+15.1%** | 3e-81 | **PASS** |
| BTC 24h T3 (rv) | harq | har_levels | +11.5% | 5.8% | **+22.6%** | 5.5e-11 | **PASS** |
| ETH 1h T3 (rv) | egarch11 | har_levels | +21.4% | 10.7% | +7.4% | 2.2e-11 | FAIL |
| BTC 1h T4 (volume) | lgb | seasonal_naive | +41.9% | 20.9% | **+44.8%** | ~0 | **PASS** |
| ETH 1h T4 (volume) | lgb | seasonal_naive | +40.4% | 20.2% | **+42.3%** | ~0 | **PASS** |
| BTC 24h T4 (volume) | lgb | seasonal_naive | +22.1% | 11.1% | **+26.6%** | 8.3e-12 | **PASS** |
| ETH 24h T4 (volume) | lgb | seasonal_naive | +30.0% | 15.0% | **+30.1%** | 4.3e-14 | **PASS** |
| BTC 1h T2 (direction) | logit_lags5 | base_rate | +0.83% | 0.41% | +0.21% (edge +2.51pp) | 0.103 | FAIL |
| ETH 1h T2 (direction) | logit_lags5 | base_rate | +0.74% | 0.37% | +0.05% (edge +1.69pp) | 0.369 | FAIL |
| T7 xs-rank 24h | park_5 | — | IC −0.089 | |IC|≥0.02 | **IC −0.083, NW-t −11.5** | — | **PASS** |

Effect = % loss improvement vs baseline (QLIKE / MASE / Brier). T2 edge =
accuracy − holdout majority-class rate (0.5026/0.5027).

## Reading

- **Volume is the program's flagship**: LGB beats the seasonal champion in
  all four cells with holdout effects at or ABOVE dev (+26.6…+44.8%),
  cross-symbol × cross-grid, DM p ≤ 8e-12. U1–U4 fully met.
- **BTC realized vol (HARQ) confirms on both grids**, holdout effects
  larger than dev (+15.1%/+22.6% vs +11.5%). The quarticity channel is
  real out-of-sample. U1–U4 met.
- **T7 cross-sectional low-vol rank signal replicates almost exactly**
  (IC −0.083 holdout vs −0.089 dev, share-positive 31%, NW-t −11.5).
  Within-day permutation null (5 seeds): |IC| ≤ 0.008, mixed signs —
  the real IC is 10× the strongest null draw.
- **ETH vol FAILS the effect floor honestly**: +7.4% is highly significant
  (DM p 2e-11) but under the registered ≥10.7% bar. Dev overstated the
  edge — exactly the baseline-fragility profile flagged in Phase 1 (ETH
  T3 was "predictable-vs-weak-only"). Real but attenuated skill; the
  registered criteria treat "attenuated below half" as failure, so it
  fails. No re-litigation.
- **Direction skill degrades in probability space but survives in sign
  space**: both logit cells keep accuracy edges above the +1pp bar
  (+2.51pp BTC, +1.69pp ETH — PT-style sign skill), yet the Brier
  improvement collapses to +0.21%/+0.05% and loses DM significance. The
  dev finding was calibration-fragile. Verdict FAIL per registered
  criteria (both DM gate and floor missed). A sign-only claim was NOT
  registered, so none is made.
- CW note: T3/T2 cw_p values are large because Clark-West targets nested
  MSPE comparisons; QLIKE/Brier DM is the registered primary. T4 cw_p
  confirms (≤1e-26).

## Forensics on passes (registered: 5-seed permute-y + sub-periods)

Permute-y nulls re-run champion + baseline on the holdout with the target
permuted (marginal preserved, dynamics destroyed; exog kept real — the
Phase-2 permute-y-only pattern; champion/baseline pairs are same-collapse).

| Cell | Real eff | Null effs (5 seeds) | Sub-periods + |
|---|---|---|---|
| BTC 1h T3 | +15.1% | +0.02, 0.00, +0.07, 0.00, −0.00 | **6/6** quarters |
| BTC 24h T3 | +22.6% | −0.05, −0.31, −0.04, −0.09, +0.10 | 5/6 quarters |
| BTC 1h T4 | +44.8% | −0.33, −0.43, −0.64, −0.49, −0.43 † | 5/6 quarters |
| ETH 1h T4 | +42.3% | −0.61, −0.75, −0.49, −0.91, −0.62 † | **6/6** quarters |
| BTC 24h T4 | +26.6% | −7.55, −9.01, −6.68, −6.32, −7.21 † | 5/6 quarters |
| ETH 24h T4 | +30.1% | −11.65, −10.14, −12.54, −10.38, −11.68 † | 5/6 quarters |

† T4 nulls are the CORRECTED same-collapse pairing (permuted-y LGB vs
HistMean). The naive pairing (permuted-y LGB vs seasonal-naive) produced a
deterministic +30.05% artifact (3 seeds observed, then aborted): under
permutation a regression collapses to the unconditional center while a
seasonal lag predicts a random draw — the Phase-1 collapse-class lesson
reproduced at holdout. The artifact is disclosed in the forensics JSON
(`t4_naive_pair_null_note`); the corrected nulls are all NEGATIVE (LGB
never beats even the center-collapse floor on permuted data), so the real
+26.6…+44.8% advantages cannot come from collapse-class asymmetry.

T7 within-day shuffle null (5 seeds): mean IC in [−0.0063, +0.0077], all
|IC| < 0.008 vs real −0.083 (`data/predlab/p5_t7_permute_null.json`).

## U1–U5 status

- U1 (beats strong baseline, DM p<0.05): met for the 7 passes.
- U2 (effect floor): met (floors are 0.5×dev; all passes ≥ floor).
- U3 (multiplicity): champions came through per-cell MCS (α=0.10) or the
  registered T7 rule; family-level honesty note — 10 one-shots at p<0.05
  with the observed p-values (≤8e-11 for every pass) survive any standard
  correction by orders of magnitude.
- U4 (sealed holdout one-shot): **met — this report.**
- U5 (stability): sub-period table below; T7 share_positive 31% with
  negative IC = consistent direction.

## Artifacts

- `data/predlab/p5_holdout_verdicts.json` (the spend record)
- `data/predlab/forecasts/predlab_p5_holdout/` (stored holdout forecasts)
- `data/predlab/p5_holdout_forensics.json`, `p5_t7_permute_null.json`
- Ledger rows: experiment `predlab_p5` phase `holdout_oneshot` (+ runner
  rows under `predlab_p5_holdout`)
