# Factor floor — 18 pre-registered model-free configs

Window: 2021-11-07 .. 2025-03-31 (dev). Coins: bitcoin + ethereum, equal weight.
Shared causal sizing path (target_vol=0.10, kelly=0.5, max_lev=3.0, min_hold=7, early_exit=0.015, vol_lookback=20, vol_cap=0.95, price_stop=3%). Sorted by portfolio Sharpe (desc).

| rank | config | portfolio SR | total_return | maxDD | n_bars |
|-----:|--------|-------------:|-------------:|------:|-------:|
| 1 | macross_10_50_ls | +0.632 | +36.7% | -12.7% | 1240 |
| 2 | xsmom_btc_eth_30d | +0.290 | +8.6% | -7.6% | 1240 |
| 3 | tsmom_k30_ls | +0.232 | +9.5% | -13.3% | 1240 |
| 4 | donchian_n55_ls | +0.227 | +7.6% | -14.9% | 1240 |
| 5 | tsmom_k14_ls | +0.225 | +8.2% | -14.2% | 1240 |
| 6 | tsmom_k7_ls | +0.029 | -0.2% | -15.2% | 1240 |
| 7 | donchian_n20_ls | -0.058 | -1.9% | -13.1% | 1240 |
| 8 | tsmom_k90_ls | -0.453 | -12.3% | -14.7% | 1240 |
| 9 | macross_20_100_ls | -0.564 | -12.3% | -15.2% | 1240 |
| 10 | tsmom_k14_lo | -0.770 | -15.1% | -15.1% | 1240 |
| 11 | tsmom_k7_lo | -0.805 | -14.3% | -14.5% | 1240 |
| 12 | macross_50_200_ls | -0.821 | -13.2% | -15.0% | 1240 |
| 13 | tsmom_k90_lo | -0.903 | -13.3% | -15.1% | 1240 |
| 14 | macross_20_100_lo | -0.903 | -13.3% | -15.1% | 1240 |
| 15 | macross_50_200_lo | -0.903 | -13.3% | -15.1% | 1240 |
| 16 | macross_10_50_lo | -0.979 | -13.0% | -14.2% | 1240 |
| 17 | tsmom_k180_ls | -1.197 | -13.2% | -14.9% | 1240 |
| 18 | tsmom_k30_lo | -1.214 | -13.7% | -14.9% | 1240 |

**Best config: `macross_10_50_ls`** — portfolio SR +0.632, total return +36.7%, maxDD -12.7%.
