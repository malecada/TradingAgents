# Phase-1 Tier-1 report — 1h cells (2026-07-31)

Battery `predlab_p1_classical`, tier t1, 8 cells {BTC,ETH} × 1h × {T1,T2,T3,T4},
dev origins 2021-01-01 → 2025-03-31 (n = 37,201 hourly), declared amendment
(arima/ets/garch conditioning capped at 4320 bars), ARIMA order-frozen after
first AIC pick + extend-cache, ETS lfilter paths. DM one-sided vs registered
strong baseline; pairwise strongest-baseline DMs from stored forecasts.

## Verdict table

| Cell | Champion | Loss (vs baseline) | DM p | Strongest-alt pairwise | Verdict |
|---|---|---|---:|---|---|
| BTC 1h T1 | — (rw_zero) | 4.524e-5 | all ≥ 0.96 | — | NO-SKILL |
| ETH 1h T1 | — (rw_zero) | 7.392e-5 | all ≥ 0.95 | — | NO-SKILL |
| BTC 1h T2 | logit_lags5 | Brier 0.24816 vs 0.24999 | **9.0e-16** | edge **+2.86pp** ≥ 2.00 floor | **SKILL-CANDIDATE** |
| ETH 1h T2 | logit_lags5 | Brier 0.24847 vs 0.24998 | **4.9e-12** | edge **+2.59pp** ≥ 2.00 floor | **SKILL-CANDIDATE** |
| BTC 1h T3 | harq | QLIKE 0.5370 vs 0.6068 (Δ11.5%) | **3.3e-83** | vs egarch +6.1% p 4.3e-7; vs garch +8.1% p 4.2e-16 | **SKILL-CANDIDATE** |
| ETH 1h T3 | gjr11/egarch11 (family) | QLIKE 0.5467 vs 0.6610 (Δ17.3%) | **8.7e-58** | gjr ≡ egarch (p 0.50); vs EWMA +5.4% p 0.003 | **SKILL-CANDIDATE (family)** |
| BTC 1h T4 | seasonal_ar_m24 | MASE 0.6723 vs 1.0939 (Δ38.5%) | ~0 | vs persistence +9.6% p 2.4e-293 | **SKILL-CANDIDATE** |
| ETH 1h T4 | seasonal_ar_m24 | MASE 0.6903 vs 1.0775 (Δ35.9%) | ~0 | vs persistence +10.3% p ≈ 0 | **SKILL-CANDIDATE** |

## Readings

1. **The 1h horizon is where classical predictability lives.** Six of eight
   cells are skill-candidates (vs one of eight daily, zero of eight 7d).
   Statistical power (37k origins) + genuine short-horizon structure.
2. **First-ever direction skill (T2), cross-symbol replicated.** Five sign
   lags in a logistic regression beat the base rate by 2.86pp (BTC) / 2.59pp
   (ETH) accuracy — above the registered 2pp floor — with Brier DM p ≈ 1e-16 /
   1e-12. Consistent with the intraday momentum/reversal literature
   (RESEARCH.md §1); every earlier daily/7d direction attempt in this program
   and its predecessors was null.
3. **T3 model ranking flips across symbols — and HARQ is bimodal.** BTC: HARQ
   dominates all six alternatives. ETH: HARQ catastrophically destabilizes
   (QLIKE 8.19 — near-zero variance forecasts from the levels-OLS + rq
   interaction under ETH's outliers, exactly the fragility flagged in the
   daily forensics, amplified) while the GARCH family wins as a group.
   Verdict for ETH is FAMILY-level; single-champion selection deferred to
   Phase-5 MCS. HARQ needs a variance-floor guard before any deployment-like
   use; recorded as a model-robustness finding, not patched post-hoc.
4. **T4 volume is the strongest, most robust effect in the map** — ΔMASE
   35–39% vs seasonal-naive AND ~10% vs persistence at p beyond floating-point,
   replicated across symbols and consistent with the daily result.
5. GARCH conditioning matters intraday (beats HAR-class on ETH, beats
   har_levels on BTC too) — unlike daily, where GARCH never beat HAR.

## Forensics status

- Leak channels: pinned by A2 alignment audit, truncation-equivalence tests,
  and the train-on-future canary (DM p 5.6e-15) — all pre-battery.
- Shuffled equality-vs-hist_mean nulls for the 1h champions: launched
  post-battery (results appended to `data/predlab/forensics_shuffled_null.json`).
- Sub-period stability: per-cell `sub_periods` in cards
  (`data/predlab/cards/predlab_p1_classical/*_1h_*.json`); roll-up (P1-08)
  applies the ≥2/3 right-signed criterion.
- Multiplicity: all 1h results enter the registry-wide BH-FDR (q=0.10) at
  roll-up; within-cell SPA/MCS reserved for Phase 5 per registration.

## Shuffled-null addendum (completed post-report)

Champions vs hist_mean equality on row-shuffled data: logit BTC/ETH p 0.998/0.939
PASS; seasonal_ar BTC/ETH p 0.9999/0.994 PASS; gjr11 ETH p 0.977 PASS. The only
non-pass is BTC harq (p 5.9e-8) — expected and mechanism-confirming: harq reads
the within-row (time-lagged, legitimate) rq feature, which row-shuffling
preserves, while every history-only model (including gjr, whose ret exog enters
via x_hist) nulls out exactly as an honest model should. The dichotomy
history-users-pass / row-feature-user-"fails" is itself evidence the harness
distinguishes information channels correctly.
