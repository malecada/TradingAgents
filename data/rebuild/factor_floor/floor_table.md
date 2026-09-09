# Factor floor — 18 pre-registered model-free configs

Window: 2021-11-07 .. 2025-03-31 (dev). Coins: bitcoin + ethereum, equal weight.
Shared causal sizing path (target_vol=0.10, kelly=0.5, max_lev=3.0, min_hold=7, early_exit=0.015, vol_lookback=20, vol_cap=0.95, price_stop=3%). Sorted by portfolio Sharpe (desc).

**Halt-latch transparency** (adjudicated Critical finding, 2026-07-09): `run_coin_backtest`'s max_portfolio_dd=0.15 circuit breaker is a PERMANENT per-coin latch — once tripped it never resets, and every later bar for that coin is a flat 0.0. The halt is kept as-is (it is the live-system circuit breaker, applied identically to every config, so full-series SR stays a fair gate metric), but is now surfaced for transparency: `sr_active` is the portfolio Sharpe computed only up to the last nonzero portfolio return (trailing post-halt zero tail excluded) — diagnostic only, never used for BEST selection, which remains max full-series `sr`. `halts` lists the first date each coin's returns went permanently to zero. `n_trailing_zero_bars` is the portfolio-level trailing zero-bar count.

| rank | config | sr | sr_active | total_return | maxDD | halts | n_trailing_zero_bars | n_bars |
|-----:|--------|-----:|-----:|-------------:|------:|-------|---------------------:|-------:|
| 1 | macross_10_50_ls | +0.632 | +1.016 | +36.7% | -12.7% | ETH 2022-07-19; BTC 2023-03-04 | 759 | 1240 |
| 2 | xsmom_btc_eth_30d | +0.290 | +0.473 | +8.6% | -7.6% | ETH 2023-02-17; BTC 2022-07-20 | 774 | 1240 |
| 3 | tsmom_k30_ls | +0.232 | +0.335 | +9.5% | -13.3% | ETH 2023-06-27; BTC 2023-01-07 | 644 | 1240 |
| 4 | donchian_n55_ls | +0.227 | +0.329 | +7.6% | -14.9% | ETH 2022-04-19; BTC 2023-06-21 | 650 | 1240 |
| 5 | tsmom_k14_ls | +0.225 | +0.334 | +8.2% | -14.2% | ETH 2023-05-25; BTC 2022-10-18 | 677 | 1240 |
| 6 | tsmom_k7_ls | +0.029 | +0.054 | -0.2% | -15.2% | ETH 2022-10-23; BTC 2022-08-10 | 891 | 1240 |
| 7 | donchian_n20_ls | -0.058 | -0.109 | -1.9% | -13.1% | ETH 2022-05-02; BTC 2022-10-28 | 886 | 1240 |
| 8 | tsmom_k90_ls | -0.453 | -1.226 | -12.3% | -14.7% | ETH 2022-04-14; BTC 2022-04-26 | 1071 | 1240 |
| 9 | macross_20_100_ls | -0.564 | -1.530 | -12.3% | -15.2% | ETH 2022-04-22; BTC 2022-04-26 | 1071 | 1240 |
| 10 | tsmom_k14_lo | -0.770 | -1.836 | -15.1% | -15.1% | ETH 2022-06-15; BTC 2022-06-16 | 1020 | 1240 |
| 11 | tsmom_k7_lo | -0.805 | -2.106 | -14.3% | -14.5% | ETH 2022-03-07; BTC 2022-05-10 | 1057 | 1240 |
| 12 | macross_50_200_ls | -0.821 | -2.488 | -13.2% | -15.0% | ETH 2022-01-28; BTC 2022-03-25 | 1103 | 1240 |
| 13 | tsmom_k90_lo | -0.903 | -2.387 | -13.3% | -15.1% | ETH 2022-01-28; BTC 2022-05-07 | 1060 | 1240 |
| 14 | macross_20_100_lo | -0.903 | -2.387 | -13.3% | -15.1% | ETH 2022-01-28; BTC 2022-05-07 | 1060 | 1240 |
| 15 | macross_50_200_lo | -0.903 | -2.387 | -13.3% | -15.1% | ETH 2022-01-28; BTC 2022-05-07 | 1060 | 1240 |
| 16 | macross_10_50_lo | -0.979 | -2.451 | -13.0% | -14.2% | ETH 2022-01-28; BTC 2022-05-28 | 1039 | 1240 |
| 17 | tsmom_k180_ls | -1.197 | -4.825 | -13.2% | -14.9% | ETH 2022-01-28; BTC 2022-01-29 | 1158 | 1240 |
| 18 | tsmom_k30_lo | -1.214 | -2.910 | -13.7% | -14.9% | ETH 2022-01-28; BTC 2022-06-17 | 1019 | 1240 |

**Best config: `macross_10_50_ls`** — portfolio SR +0.632 (active-period SR +1.016), total return +36.7%, maxDD -12.7%, halts: ETH 2022-07-19; BTC 2023-03-04. Selection remains max full-series SR (`sr`); `sr_active` is diagnostic only — see Halt-latch transparency note above.
