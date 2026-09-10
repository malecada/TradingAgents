# Saved forecast reliability and factor risk diagnostics — September 10, 2026

**All sixteen forecast comparisons and thirty-six factor sleeves are complete.** Volume prediction retains a consistent historical improvement over seasonal baselines. The factor traces expose stale sizing and repeated stop/re-entry behavior that warrants a narrowly defined risk-policy investigation. **Zero strategies are validated.** No trading rule, model, original gate or holdout result was changed.

## Scope and reproducibility

The two charters and exact input hashes were registered at `38d9a67e6ff042cb1fd870877b3e0222f40fdc08` before implementation or results. The reviewed executable source was committed as `cd8d9e3f064bb40273ba493e597e371e6f199b66` before both successful, single executions. The existing saved development artifacts end March 31, 2025. No fitting, strategy replay, new data, network request, paid purchase or holdout read occurred. The 22 settlement-blocked cases remain deferred.

| Evidence | Identity |
|---|---|
| [Forecast result](../../data/diagnostics/2026-09-10/forecast/result.json) | SHA-256 `acbe21b51a346211a8c13c9c04ca82844c6fe90b12f9ac5a604b1dca15ef9cdc` |
| [Risk result](../../data/diagnostics/2026-09-10/risk/result.json) | SHA-256 `d37d6f7ab18b307aa12f4b5f57212ee0dbffd7611358ba3a1beaf8638982f9fa` |
| [Forecast charter](forecast-charter.md) | `audit_saved_forecast_inference_2026_09_10`; 16 cells, 35 pins |
| [Factor charter](factor-risk-charter.md) | `audit_factor_risk_2026_09_10`; 18 configurations × 2 assets, 78 pins |

The runners record all 52 identities in separate forensic ledgers. The original financial ledger remains at 748 rows, 569,325 bytes and SHA-256 `4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601`. Source reviews and final test logs are retained under `verification/`: 57 forecast tests and 80 factor tests passed before execution. The [independent result review](verification/result-review.md) and [final preservation record](verification/preservation-final.json) provide completion checks.

## Forecast reliability

Positive percentages below mean lower forecast loss than the declared baseline, not an investment return. Return uses squared error against zero; direction uses Brier loss against the base rate; variance uses normalized QLIKE against HAR; volume uses absolute error on log volume against seasonal naive. The original common MASE scale cancels from the volume ratios. Every scalar comparison reconciles with the prior correction.

The fixed circular stationary bootstrap uses 2,000 draws, 21-day mean blocks and seed 20260910 independently per cell. All 32,000 saved draws have valid denominators. Full physical calendars and fallback observations are retained: the unavailable October 28, 2024 20:00 UTC hour remains unscoreable in both hourly variance and volume comparisons. It is not replaced with a fabricated target or silently removed from bootstrap time.

| Asset | Grid | Target | Relative loss improvement | Conditional 95% interval | Eligible Holm p | Stable periods descriptor |
|---|---|---|---:|---:|---:|---|
| BTC | 1h | Return | -0.37% | [-0.95%, -0.01%] | unavailable | not met |
| BTC | 1h | Direction | 0.16% | [-0.08%, 0.35%] | unavailable | met |
| BTC | 1h | Variance | -35.58% | [-52.21%, -22.63%] | unavailable | not met |
| BTC | 1h | Volume | 38.82% | [36.99%, 40.48%] | 0.007996 | met |
| BTC | 24h | Return | -3.75% | [-8.65%, -0.38%] | unavailable | not met |
| BTC | 24h | Direction | -2.07% | [-4.24%, -0.30%] | unavailable | not met |
| BTC | 24h | Variance | -69.19% | [-127.19%, -19.04%] | unavailable | not met |
| BTC | 24h | Volume | 17.16% | [13.00%, 21.40%] | 0.007996 | met |
| ETH | 1h | Return | -0.03% | [-0.09%, 0.03%] | unavailable | not met |
| ETH | 1h | Direction | 0.25% | [-0.16%, 0.55%] | unavailable | met |
| ETH | 1h | Variance | 10.28% | [0.13%, 18.99%] | unavailable | met |
| ETH | 1h | Volume | 37.15% | [35.22%, 38.74%] | 0.007996 | met |
| ETH | 24h | Return | -0.90% | [-2.09%, -0.20%] | unavailable | not met |
| ETH | 24h | Direction | -2.88% | [-5.50%, -0.46%] | unavailable | not met |
| ETH | 24h | Variance | 5.86% | [-29.71%, 31.57%] | unavailable | met |
| ETH | 24h | Volume | 22.37% | [18.64%, 25.81%] | 0.007996 | met |

**Volume is the most consistent forecast finding.** All four volume comparisons meet the original 5% effect descriptor, improve in each of the three fixed historical periods, and retain Holm-adjusted p=0.007996 across the full 16-slot family. Raw valid prediction coverage is 92.85–97.45%; fallback observations remain included. These are conditional comparisons of saved forecasts against seasonal naive. They do not resolve historical model selection, prove stationarity or establish that ENet is the best model. Earlier saved LightGBM scalar losses were lower; no new competitor comparison or coverage-parity claim was made.

**Directional alpha is not established.** Every mean-return comparison has worse point loss than its zero baseline. Hourly direction accuracy edges are 1.7768 percentage points for BTC and 1.9119 for ETH, below the original 2-point floor; their Brier-loss intervals cross zero improvement. Point AUCs are 0.5314 and 0.5344, but the required AUC interval is absent. Daily direction is worse than its baseline. ETH hourly variance has a favorable conditional interval, while daily ETH variance is uncertain and BTC variance is worse.

Formal primary inference for return, direction and variance remains unavailable because applicability of nested-model tests to these penalized, selected, expanding estimates is unresolved. Those twelve slots enter Holm as one; their conditional intervals do not reverse the original gates. The stability descriptor means positive loss differential in at least two of three fixed periods, with at least thirty observations per period. It is descriptive historical evidence, not fresh validation.

## What the factor traces establish

All 36 sleeves reconcile to the saved accounting: 44,640 daily rows, including 8,873 dates with nonzero applied exposure. The sizing formula sets an entry risk proxy of at most 15% (`0.10 × 0.5 × 3`), subject to the leverage cap. Size is then retained until a raw-target entry or flip. This is entry-time volatility sizing; it does not continuously maintain that risk level. The diagnostic proxy is absolute position weight multiplied by trailing annualized volatility, not realized account volatility.

The applied proxy exceeds its entry reference on 4,458/8,873 active sleeve-dates (50.24%). The 95th-percentile volatility gate is closed on 939 active sleeve-dates; that gate controls builder entries/flips and does not flatten an existing target. No applied or latent target breaches the 3× leverage cap. Counts across configurations describe overlapping sleeve-date observations, not independent experiments or a pooled account.

Of 852 recorded price stops, 726 are followed by same-direction next-day re-entry, all reusing the saved sizing reference; 93 are followed by opposite-direction entry, 25 by permanent halt, and 8 by a flat date. Thus 819/852 stops are followed by immediate renewed exposure. A price stop closes the executed position while the target builder can continue holding its old directional target and size.

The following two configurations were already discussed before this diagnostic; their appearance here is explanatory, not a new selection rule.

| Configuration / asset | Active dates | Applied risk p90 / maximum | Dates above entry reference | Same-direction re-entry / stops | Maximum reused sizing age at re-entry |
|---|---:|---:|---:|---:|---:|
| `tsmom_k30_ls / bitcoin` | 983 | 27.98% / 51.08% | 519/983 | 32/46 | 16 days |
| `tsmom_k30_ls / ethereum` | 581 | 28.92% / 64.44% | 277/581 | 29/39 | 19 days |
| `macross_10_50_ls / bitcoin` | 462 | 48.77% / 80.02% | 234/462 | 19/19 | 32 days |
| `macross_10_50_ls / ethereum` | 234 | 29.60% / 38.56% | 104/234 | 7/7 | 29 days |

All 36 sleeves eventually trip the permanent 15% drawdown latch. In 35 sleeves the threshold is crossed before final exit charges; only ETH 30-day momentum first crosses afterward, from 14.999356% to 15.032114%. The gross market component dominates the peak-to-halt loss in the four examples above. A fee crossing at the boundary is an accounting observation, not proof that removing the fee would improve the full path.

Maintenance turnover is real even when the target weight is unchanged, because holdings and NAV drift. The signed target-change and maintenance components reconcile after retaining their netting term; their absolute values are not additive trade volume. Linear execution charges include the saved fee/slippage/spread assumption, with impact recorded separately. Stop-successor entry charges are a subset of opening charges, so they must not be added a second time. The detailed [risk interpretation](verification/risk-interpretation.md) reports sleeve-specific dollars and disjoint charge categories.

**Cash-tail count addendum:** the earlier factor report stated 238–1,157 days. The preserved traces establish 238–1,158 already-halted cash dates. ETH 180-day long/short momentum halts on January 28, 2022; January 29, 2022 through March 31, 2025 contains 1,158 dates. This corrects the earlier prose only. Its original halt date, return series, metrics and files remain unchanged.

## Next research decision

The clearest engineering follow-up is to specify a consistent contract between signal persistence, current volatility sizing and execution stop state. A bounded future comparison could test refreshing size when exposure is maintained or reopened, while preserving the signal and accounting conventions. The exact alternative, comparison set, costs and fresh validation route must be registered before any new performance calculation. The present observations do not determine the best resizing cadence, justify removing a halt, or show that a changed rule will make a lead pass. Lower Kelly sizing and removal of volatility targeting already appear in the historical record and should not be represented as new discoveries.

Volume forecasts warrant retention as inputs for a narrowly specified execution-cost investigation. The earlier day-start execution-profile test did not establish useful economic savings; a lower volume prediction error alone does not establish them either. A causal mapping from forecast to actual order schedule, with an executable cost comparison, would be a separate registered experiment. Mean-return tuning is not supported by these results. ETH variance retains qualified descriptive evidence but no new formal validation.

Original price-cache provenance, assumed daily funding, threshold stop fills and the separate BTC/ETH sleeve-index construction remain limitations. The spent holdouts stay spent, and the deferred settlement cases are unchanged. These findings provide specific questions for further research; they do not promote a strategy.

## Complete factor denominator

| Configuration / asset | Active dates | Applied risk p90 | Applied risk maximum | Price stops | First halt | Crossing stage |
|---|---:|---:|---:|---:|---|---|
| `tsmom_k7_ls / bitcoin` | 329 | 23.29% | 28.35% | 37 | 2022-10-21 | pre_exit |
| `tsmom_k7_ls / ethereum` | 332 | 22.02% | 25.55% | 55 | 2022-10-24 | pre_exit |
| `tsmom_k14_ls / bitcoin` | 347 | 21.16% | 26.87% | 30 | 2022-11-08 | pre_exit |
| `tsmom_k14_ls / ethereum` | 571 | 24.50% | 37.29% | 52 | 2023-06-20 | pre_exit |
| `tsmom_k30_ls / bitcoin` | 983 | 27.98% | 51.08% | 46 | 2024-08-05 | pre_exit |
| `tsmom_k30_ls / ethereum` | 581 | 28.92% | 64.44% | 39 | 2023-06-30 | post_exit |
| `tsmom_k90_ls / bitcoin` | 156 | 21.38% | 23.28% | 17 | 2022-05-01 | pre_exit |
| `tsmom_k90_ls / ethereum` | 148 | 26.20% | 29.00% | 15 | 2022-04-23 | pre_exit |
| `tsmom_k7_lo / bitcoin` | 151 | 19.98% | 21.24% | 20 | 2022-05-11 | pre_exit |
| `tsmom_k7_lo / ethereum` | 162 | 15.43% | 16.54% | 25 | 2022-05-09 | pre_exit |
| `tsmom_k14_lo / bitcoin` | 137 | 17.76% | 18.29% | 22 | 2022-06-16 | pre_exit |
| `tsmom_k14_lo / ethereum` | 136 | 19.88% | 21.31% | 23 | 2022-06-15 | pre_exit |
| `tsmom_k30_lo / bitcoin` | 122 | 18.78% | 19.32% | 19 | 2022-06-16 | pre_exit |
| `tsmom_k30_lo / ethereum` | 90 | 15.94% | 16.73% | 22 | 2022-02-24 | pre_exit |
| `tsmom_k90_lo / bitcoin` | 161 | 18.09% | 20.20% | 18 | 2022-05-06 | pre_exit |
| `tsmom_k90_lo / ethereum` | 90 | 15.94% | 16.73% | 22 | 2022-02-24 | pre_exit |
| `tsmom_k180_ls / bitcoin` | 64 | 16.09% | 17.28% | 16 | 2022-01-29 | pre_exit |
| `tsmom_k180_ls / ethereum` | 63 | 15.60% | 16.41% | 22 | 2022-01-28 | pre_exit |
| `macross_10_50_ls / bitcoin` | 462 | 48.77% | 80.02% | 19 | 2023-03-03 | pre_exit |
| `macross_10_50_ls / ethereum` | 234 | 29.60% | 38.56% | 7 | 2022-07-18 | pre_exit |
| `macross_20_100_ls / bitcoin` | 630 | 27.39% | 33.42% | 23 | 2023-08-18 | pre_exit |
| `macross_20_100_ls / ethereum` | 149 | 19.96% | 21.19% | 13 | 2022-04-24 | pre_exit |
| `macross_50_200_ls / bitcoin` | 121 | 28.29% | 29.21% | 14 | 2022-03-27 | pre_exit |
| `macross_50_200_ls / ethereum` | 66 | 15.60% | 16.41% | 23 | 2022-01-31 | pre_exit |
| `macross_10_50_lo / bitcoin` | 104 | 24.18% | 24.86% | 14 | 2022-05-27 | pre_exit |
| `macross_10_50_lo / ethereum` | 90 | 15.94% | 16.73% | 22 | 2022-02-24 | pre_exit |
| `macross_20_100_lo / bitcoin` | 161 | 18.09% | 20.20% | 18 | 2022-05-06 | pre_exit |
| `macross_20_100_lo / ethereum` | 90 | 15.94% | 16.73% | 22 | 2022-02-24 | pre_exit |
| `macross_50_200_lo / bitcoin` | 161 | 18.09% | 20.20% | 18 | 2022-05-06 | pre_exit |
| `macross_50_200_lo / ethereum` | 90 | 15.94% | 16.73% | 22 | 2022-02-24 | pre_exit |
| `donchian_n20_ls / bitcoin` | 269 | 24.87% | 31.38% | 18 | 2022-10-27 | pre_exit |
| `donchian_n20_ls / ethereum` | 259 | 27.53% | 36.08% | 23 | 2022-09-19 | pre_exit |
| `donchian_n55_ls / bitcoin` | 564 | 27.64% | 46.74% | 12 | 2023-06-21 | pre_exit |
| `donchian_n55_ls / ethereum` | 105 | 25.85% | 28.19% | 4 | 2022-04-21 | pre_exit |
| `xsmom_btc_eth_30d / bitcoin` | 244 | 18.82% | 20.38% | 39 | 2022-07-28 | pre_exit |
| `xsmom_btc_eth_30d / ethereum` | 451 | 29.87% | 64.44% | 41 | 2023-02-20 | pre_exit |

Every row is a qualified completed diagnostic. Full dated exposures, flags, charge identities, risk denominators and stop events are retained in the immutable Parquets.
