# Phase-1 Tier-1 report — 7d cells, direct aggregation (2026-07-30)

Battery `predlab_p1_classical`, tier t1, 8 cells {BTC,ETH} × 7d × {T1,T2,T3,T4},
overlapping daily-grid targets (h=7 purge + HAC lag 6 throughout), dev origins
2021-01-01 → 2025-03-31 (n = 1,545). Iterated-ARIMA variant deferred (direct is
the registered protocol; helper `iterated.py` exists, tested).

| Cell | Baseline (loss) | Best challenger (loss) | DM p | Verdict |
|---|---|---|---:|---|
| BTC 7d T1 | rw_zero 7.27e-3 | arima 1.24e-2 (worse) | 1.0 | NO-SKILL |
| ETH 7d T1 | rw_zero 1.19e-2 | arima 2.07e-2 (worse) | 1.0 | NO-SKILL |
| BTC 7d T2 | base_rate 0.253 | logit 0.374 (worse) | 1.0 | NO-SKILL |
| ETH 7d T2 | base_rate 0.254 | logit 0.351 (worse) | 1.0 | NO-SKILL |
| BTC 7d T3 | har_levels 0.267 | garch11 0.306 (worse) | 0.82 | BASELINE-WINS |
| ETH 7d T3 | har_levels 0.275 | harq 0.330 (worse) | 0.91 | BASELINE-WINS |
| BTC 7d T4 | seasonal_naive_m1 3.891 | seasonal_ar 3.878 | 0.204 | BASELINE-WINS |
| ETH 7d T4 | seasonal_naive_m1 3.145 | seasonal_ar 3.131 | 0.165 | BASELINE-WINS |

## Readings

1. **Skill is horizon-local.** The daily HARQ edge does NOT extend to 7d — at
   weekly aggregation plain HAR-levels beats every challenger including HARQ
   (BTC 0.267 vs 0.331; ETH 0.275 vs 0.330). The rq-interaction corrects
   measurement noise in the 1-day lag; aggregated targets wash that out.
2. **The overlapping-sum trap degrades fitted models.** T1 ARIMA/ETS are not
   merely equal to RW — they are ~1.7–2× WORSE, and T2 logit is badly harmful:
   overlapping 7d sums have strong MA(6) autocorrelation that small fitted
   models mistake for signal. The honest protocol (h=7 purge, HAC lag 6)
   scores this correctly; the models themselves still degrade. Matches the
   RESEARCH.md pitfall list (overlapping-horizon autocorrelation).
3. Sanity: seasonal_naive_m1 ≡ persistence bit-identical (3.89119/3.14512
   both) — loader/model wiring confirmed; hist_mean catastrophic on trending
   log-volume (11.9/14.3) as expected.
4. ARIMA MLE on overlapping sums is ~4s/fit (select_once already frozen the
   order) — 7d battery cost ≈ 110 CPU-min, dominated by two T1 cells.

Cards: `data/predlab/cards/predlab_p1_classical/*_7d_*.json` (tier t1).
