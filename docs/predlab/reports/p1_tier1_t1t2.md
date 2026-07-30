# Phase-1 Tier-1 report — daily returns (T1) and direction (T2) (2026-07-30)

Battery `predlab_p1_classical`, tier t1, cells {BTC,ETH} × 24h × {T1_ret, T2_dir},
dev origins 2021-01-01 → 2025-03-31 (n = 1,551), refit_every = 5.
DM one-sided vs registered strong baseline (positive = model better); CW for
nested; PT on signs.

## T1_ret vs rw_zero (loss = SE on log-returns)

| Cell | Model | Loss | DM p | CW p | PT p |
|---|---|---:|---:|---:|---:|
| BTC 24h | rw_zero | 1.03847e-03 | — | — | — |
| BTC 24h | arima_aic | 1.04977e-03 | 0.871 | 0.139 | 0.441 |
| BTC 24h | ets_ann | 1.06222e-03 | 0.973 | 0.237 | 0.567 |
| BTC 24h | ets_aan | 1.08696e-03 | 0.999 | 0.258 | 0.313 |
| ETH 24h | rw_zero | 1.76628e-03 | — | — | — |
| ETH 24h | arima_aic | 1.77866e-03 | 0.697 | **0.054** | 0.150 |
| ETH 24h | ets_ann | 1.80724e-03 | 0.974 | 0.331 | 0.653 |
| ETH 24h | ets_aan | 1.85212e-03 | 0.999 | 0.288 | 0.551 |

**Verdict: NO-SKILL (both cells).** Every Tier-1 model has HIGHER loss than the
random walk. The only non-null reading is ETH ARIMA's Clark-West p = 0.054 —
under BH-FDR across the registered battery this is nothing; recorded, not
pursued. Matches the literature prior (RESEARCH.md §1: daily returns
borderline-unpredictable by classical means).

## T2_dir vs base_rate (loss = Brier)

| Cell | Model | Brier | DM p | PT p |
|---|---|---:|---:|---:|
| BTC 24h | base_rate | 0.251395 | — | — |
| BTC 24h | logit_lags5 | 0.251775 | 0.588 | **0.026** |
| ETH 24h | base_rate | 0.250347 | — | — |
| ETH 24h | logit_lags5 | 0.249957 | 0.363 | 0.164 |

**Verdict: NO-SKILL (both cells).** No Brier improvement over climatology.
BTC logit PT p = 0.026 is a marginal sign-association not corroborated by any
probability skill (Brier WORSE than base rate) and far from surviving
multiplicity; recorded as a marginal, not a finding.

## Notes

- Method sanity: the same wrappers detect planted AR(1) structure on synthetic
  data at p < 0.01 (test_tier1.py) — the nulls here are informative, not a
  power failure of the harness. n = 1,551 origins per cell.
- These are the FIRST honest classical return/direction cells in the map;
  Tier-2 ML (taker-imbalance features — the highest-prior T1/T2 feature per
  RESEARCH.md) is the next attempt on these targets in Phase 2.
