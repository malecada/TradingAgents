# Phase-1 Tier-0 report — baseline loss reference (2026-07-30)

Registered battery `predlab_p1_classical`, dev origins 2021-01-01 → 2025-03-31
(earlier bars burn-in only). Baselines are the null: NO gates evaluated at
Tier 0. Every later tier is measured against these numbers (registered loss per
target: T1 SE on log-returns, T2 Brier, T3 QLIKE on variance, T4 MASE on log
dollar volume, T6 SE).

## Best Tier-0 model per cell (the number to beat)

| Cell | n | Best t0 model | Loss |
|---|---:|---|---:|
| BTC 1h T1_ret | 37,201 | rw_zero | 4.5238e-05 |
| BTC 1h T2_dir | 37,201 | base_rate | 0.249991 |
| BTC 1h T3_rv | 37,200 | ewma_0.94 | 0.621823 |
| BTC 1h T4_vol | 37,200 | persistence | 0.743836 |
| BTC 24h T1_ret | 1,551 | rw_zero | 1.03847e-03 |
| BTC 24h T2_dir | 1,551 | base_rate | 0.251395 |
| BTC 24h T3_rv | 1,551 | ewma_0.94 | 0.438717 |
| BTC 24h T4_vol | 1,551 | seasonal_naive_m7 | 0.903588 |
| BTC 7d T1_ret | 1,545 | rw_zero | 7.26584e-03 |
| BTC 7d T2_dir | 1,545 | base_rate | 0.253418 |
| BTC 7d T3_rv | 1,545 | ewma_0.94 | 0.315928 |
| BTC 7d T4_vol | 1,545 | seasonal_naive_m1 | 3.70903 |
| BTC 8h T6_fund | 4,651 | persistence | 1.57281e-08 |
| BTC 24h T6_fund | 1,551 | persistence | 1.01358e-07 |
| ETH 1h T1_ret | 37,201 | rw_zero | 7.39166e-05 |
| ETH 1h T2_dir | 37,201 | base_rate | 0.249979 |
| ETH 1h T3_rv | 37,200 | ewma_0.94 | 0.577591 |
| ETH 1h T4_vol | 37,200 | persistence | 0.769365 |
| ETH 24h T1_ret | 1,551 | rw_zero | 1.76628e-03 |
| ETH 24h T2_dir | 1,551 | base_rate | 0.250347 |
| ETH 24h T3_rv | 1,551 | ewma_0.94 | 0.456798 |
| ETH 24h T4_vol | 1,551 | persistence | 0.696034 |
| ETH 7d T1_ret | 1,545 | rw_zero | 1.19128e-02 |
| ETH 7d T2_dir | 1,545 | base_rate | 0.2537 |
| ETH 7d T3_rv | 1,545 | ewma_0.94 | 0.362999 |
| ETH 7d T4_vol | 1,545 | seasonal_naive_m1 | 3.09698 |
| ETH 8h T6_fund | 4,651 | persistence | 3.50391e-08 |
| ETH 24h T6_fund | 1,551 | persistence | 2.30593e-07 |

Full per-model numbers: `data/predlab/cards/predlab_p1_classical/*.json` (tier "t0").

## Structure checks (expected patterns, all as literature predicts)

- T1 returns: rw_zero beats hist_mean and persistence everywhere — no naive
  return predictability, as expected.
- T3 vol: EWMA dominates persistence and hist_mean in all 6 cells — vol
  persistence is real; HAR (Tier 1) is the registered strong bar.
- T4 volume: at 1h, PERSISTENCE beats seasonal-naive-24 (both symbols) — hourly
  volume is more persistent than one-day-seasonal; at 24h seasonal-naive-m7
  wins for BTC, persistence for ETH. Tier-1 seasonal-AR combines both terms.
- T6 funding: persistence has tiny MSE (clamped, sticky series) — AR(1) is the
  registered strong baseline arriving in Tier 1.
- T2 Brier ≈ 0.25 everywhere (base rates 0.50–0.53).

## Protocol notes (recorded before any gate evaluation)

1. **eval_start fix.** First t0 run evaluated origins from `min_train` onward,
   which reaches before the registered dev-window start (1h cells included
   2020 origins). Fixed: runner now filters origins to `dev_window[0]`
   (2021-01-01); earlier bars are burn-in/training only. Pinned by
   `test_runner_eval_start_filters_origins`. Pre-fix ledger rows have distinct
   config hashes (no `eval_start` key) and remain in the ledger as history.
2. **Tier-0 comparison base ≠ registered strong baseline** for T3 (har_levels)
   and T6 (ar1) — those models ship with Tier 1; at t0 the comparison base is
   the best available honest null (ewma_0.94 / persistence). Cards record the
   base used per tier. No gate content changed.
3. Funding parquets for BTC/ETH copied from the shared xsect store into
   `data/predlab/funding/` (one-time read; predlab never writes outside its
   namespace).
