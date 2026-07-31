# Phase-1 Predictability Map (P1-08 roll-up, 2026-07-31)

Cells: 28 | BH-FDR q=0.10 across cells | verdict downgrades
only via documented overrides (strongest-baseline principle).

| Cell | Champion | Impr% vs base | DM p | FDR | Floor | Stable | Verdict |
|---|---|---:|---:|---|---|---|---|
| BTCUSDT|1h|T1_ret | rw_zero | 0.0 |  | n | — | n | **BASELINE-WINS** |
| BTCUSDT|1h|T2_dir | logit_lags5 | 0.7 | 9e-16 | Y | Y | Y | **SKILL-CANDIDATE** |
| BTCUSDT|1h|T3_rv | harq | 11.5 | 3.3e-83 | Y | Y | Y | **SKILL-CANDIDATE** |
| BTCUSDT|1h|T4_vol | seasonal_ar_m24 | 38.5 | 0 | Y | Y | Y | **SKILL-CANDIDATE** |
| BTCUSDT|24h|T1_ret | rw_zero | 0.0 |  | n | — | n | **BASELINE-WINS** |
| BTCUSDT|24h|T2_dir | base_rate | 0.0 |  | n | n | n | **BASELINE-WINS** |
| BTCUSDT|24h|T3_rv | harq | 11.6 | 0.001 | Y | Y | Y | **SKILL-CANDIDATE** |
| BTCUSDT|24h|T4_vol | seasonal_ar_m7 | 16.5 | 7.5e-18 | Y | Y | Y | **SKILL-CANDIDATE** |
| BTCUSDT|24h|T6_funding | ar1 | 0.0 |  | n | n | n | **BASELINE-WINS** |
| BTCUSDT|7d|T1_ret | rw_zero | 0.0 |  | n | — | n | **BASELINE-WINS** |
| BTCUSDT|7d|T2_dir | base_rate | 0.0 |  | n | n | n | **BASELINE-WINS** |
| BTCUSDT|7d|T3_rv | har_levels | 0.0 |  | n | n | n | **BASELINE-WINS** |
| BTCUSDT|7d|T4_vol | seasonal_ar_m1 | 0.3 | 0.2 | n | n | Y | **NO-SKILL** |
| BTCUSDT|8h|T6_funding | ar1 | 0.0 |  | n | n | n | **BASELINE-WINS** |
| ETHUSDT|1h|T1_ret | rw_zero | 0.0 |  | n | — | n | **BASELINE-WINS** |
| ETHUSDT|1h|T2_dir | logit_lags5 | 0.6 | 4.9e-12 | Y | Y | Y | **SKILL-CANDIDATE** |
| ETHUSDT|1h|T3_rv | gjr11 | 17.3 | 8.7e-58 | Y | Y | Y | **SKILL-CANDIDATE (family)** — gjr11 = egarch11 (pairwise p 0.50); GARCH family beats har_levels (p 8.7e-58) and EWMA (p 0.003); single champion deferred to Phase-5 MCS |
| ETHUSDT|1h|T4_vol | seasonal_ar_m24 | 35.9 | 0 | Y | Y | Y | **SKILL-CANDIDATE** |
| ETHUSDT|24h|T1_ret | rw_zero | 0.0 |  | n | — | n | **BASELINE-WINS** |
| ETHUSDT|24h|T2_dir | logit_lags5 | 0.2 | 0.36 | n | n | Y | **NO-SKILL** |
| ETHUSDT|24h|T3_rv | harq | 15.4 | 4.8e-12 | Y | Y | Y | **PREDICTABLE-VS-WEAK-ONLY** — battery p 4.8e-12 vs har_levels reflects baseline fragility; no significant edge vs log_har (p 0.43) or EWMA (p 0.21) — forensics v2 K3 |
| ETHUSDT|24h|T4_vol | seasonal_ar_m7 | 21.4 | 5.8e-25 | Y | Y | Y | **SKILL-CANDIDATE** |
| ETHUSDT|24h|T6_funding | ar1 | 0.0 |  | n | n | n | **BASELINE-WINS** |
| ETHUSDT|7d|T1_ret | rw_zero | 0.0 |  | n | — | n | **BASELINE-WINS** |
| ETHUSDT|7d|T2_dir | base_rate | 0.0 |  | n | n | n | **BASELINE-WINS** |
| ETHUSDT|7d|T3_rv | har_levels | 0.0 |  | n | n | n | **BASELINE-WINS** |
| ETHUSDT|7d|T4_vol | seasonal_ar_m1 | 0.4 | 0.17 | n | n | Y | **NO-SKILL** |
| ETHUSDT|8h|T6_funding | ar1 | 0.0 |  | n | n | n | **BASELINE-WINS** |

**9 SKILL-CANDIDATE cells.** Ledger trials: 180 unique configs.
