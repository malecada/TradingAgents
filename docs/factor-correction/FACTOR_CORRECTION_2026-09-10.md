# Fixed factor-floor correction — 2026-09-10

All **18 configurations, 90 registered two-sleeve evaluations and 18 invalid-log shadow diagnostics** completed. The old engine reproduces all eighteen saved July scalar summaries within1e-10 and the sole saved BEST daily stream within1e-10. Sixteen configurations improve on a common365-day Sharpe basis; seven have positive primary development Sharpe, versus six in the old-engine replay. **No strategy is validated or selected for deployment.**

The largest primary Sharpe is **30-day long/short momentum:0.985**, versus0.280 under the preserved old engine on the same inputs and365-day reporting basis. Its corrected benchmark return is65.33%, maximum drawdown12.13%, doubled-execution-cost Sharpe0.907 and zero-assumed-funding Sharpe1.010. The historical10/50 MA benchmark improves from0.761 to0.859. These are development measurements; the original BEST artifact is unchanged.

The large30-day momentum improvement is mainly a consequence of different halt timing. BTC has577 additional nonzero return days after the old engine stops on2023-01-06, continuing until2024-08-05. Of the$11,082 difference between the separately simulated BTC final NAVs,$10,426 arises after the old halt. This is not a pure annualization effect: the before/after Sharpe comparison uses365 days on both sides. Changing fees and funding can move a permanent halt and therefore change years of subsequent exposure. The registered controls reapply the same rule; they do not establish independent additive fee/funding contributions.

Every primary coin sleeve eventually trips the original permanent15% drawdown halt: **36/36 sleeves**. Every benchmark then has a post-halt cash tail, ranging from238 to1157 of1240 return days. These zero-return days remain in every primary statistic. The correction preserves the original halt/reentry policy; it does not establish how a production strategy should resume after a halt.

## Complete before/after comparison

Window:2021-11-07..2025-03-31; first return2021-11-08. Columns distinguish original252-day reporting from365-day reporting. Sizing still uses the original252-day volatility convention so quantities are not silently changed. Drawdown below includes initial NAV and is expressed as a loss magnitude. Configurations retain the registered order; no new champion is selected.

| Configuration | July SR252 | Old replay SR365 | Corrected SR365 | Corrected return | Max DD | Cash-tail days |
|---|---:|---:|---:|---:|---:|---:|
| tsmom_k7_ls | +0.029 | +0.035 | +0.151 | +3.30% | 14.98% | 889 |
| tsmom_k14_ls | +0.225 | +0.271 | +0.336 | +11.57% | 14.70% | 650 |
| tsmom_k30_ls | +0.232 | +0.280 | +0.985 | +65.33% | 12.13% | 238 |
| tsmom_k90_ls | -0.453 | -0.545 | -0.523 | -12.01% | 14.99% | 1065 |
| tsmom_k7_lo | -0.805 | -0.969 | -0.862 | -14.58% | 14.86% | 1055 |
| tsmom_k14_lo | -0.770 | -0.927 | -0.944 | -15.34% | 15.34% | 1019 |
| tsmom_k30_lo | -1.214 | -1.461 | -1.276 | -13.49% | 14.65% | 1019 |
| tsmom_k90_lo | -0.903 | -1.087 | -0.935 | -13.17% | 14.96% | 1060 |
| tsmom_k180_ls | -1.197 | -1.440 | -1.450 | -13.22% | 15.01% | 1157 |
| macross_10_50_ls | +0.632 | +0.761 | +0.859 | +42.91% | 11.79% | 759 |
| macross_20_100_ls | -0.564 | -0.679 | -0.021 | -1.99% | 14.62% | 591 |
| macross_50_200_ls | -0.821 | -0.988 | -0.967 | -12.97% | 14.77% | 1100 |
| macross_10_50_lo | -0.979 | -1.178 | -1.028 | -12.80% | 13.97% | 1039 |
| macross_20_100_lo | -0.903 | -1.087 | -0.935 | -13.17% | 14.96% | 1060 |
| macross_50_200_lo | -0.903 | -1.087 | -0.935 | -13.17% | 14.96% | 1060 |
| donchian_n20_ls | -0.058 | -0.070 | +0.288 | +7.64% | 15.03% | 886 |
| donchian_n55_ls | +0.227 | +0.273 | +0.361 | +10.72% | 14.38% | 649 |
| xsmom_btc_eth_30d | +0.290 | +0.349 | +0.446 | +11.32% | 7.46% | 770 |

## All fixed sensitivity results

Execution sensitivity scales fee, slippage, spread and quadratic turnover impact together. Funding is unchanged in those variants. The zero-funding diagnostic preserves primary execution costs. Each variant reapplies the same risk rule; changed NAV can change halt dates. None replaces the primary result. The log column is invalid arithmetic on frozen primary exposure, costs, funding and stop decisions; it is solely a convention check.

| Configuration | Primary SR365 | Zero execution | Double execution | Zero funding | Invalid-log shadow |
|---|---:|---:|---:|---:|---:|
| tsmom_k7_ls | +0.151 | +0.244 | +0.071 | +0.123 | +0.250 |
| tsmom_k14_ls | +0.336 | +0.422 | +0.294 | +0.351 | +0.400 |
| tsmom_k30_ls | +0.985 | +1.070 | +0.907 | +1.010 | +0.975 |
| tsmom_k90_ls | -0.523 | -0.518 | -0.543 | -0.523 | -0.446 |
| tsmom_k7_lo | -0.862 | -0.842 | -1.087 | -0.830 | -0.985 |
| tsmom_k14_lo | -0.944 | -0.923 | -0.960 | -0.929 | -1.057 |
| tsmom_k30_lo | -1.276 | -0.929 | -1.469 | -1.114 | -1.409 |
| tsmom_k90_lo | -0.935 | -0.759 | -1.089 | -0.871 | -1.051 |
| tsmom_k180_ls | -1.450 | -1.437 | -1.471 | -1.441 | -1.495 |
| macross_10_50_ls | +0.859 | +0.896 | +0.821 | +0.851 | +0.931 |
| macross_20_100_ls | -0.021 | +0.003 | -0.150 | -0.048 | +0.070 |
| macross_50_200_ls | -0.967 | -0.107 | -0.987 | -0.991 | -0.948 |
| macross_10_50_lo | -1.028 | -0.759 | -1.216 | -0.878 | -1.153 |
| macross_20_100_lo | -0.935 | -0.759 | -1.089 | -0.871 | -1.051 |
| macross_50_200_lo | -0.935 | -0.759 | -1.089 | -0.871 | -1.051 |
| donchian_n20_ls | +0.288 | +0.321 | -0.010 | +0.004 | +0.404 |
| donchian_n55_ls | +0.361 | +0.386 | +0.332 | +0.353 | +0.425 |
| xsmom_btc_eth_30d | +0.446 | +0.521 | +0.389 | +0.422 | +0.466 |

The20-day Donchian positive result is fragile: primary0.288 falls to−0.010 at doubled execution costs and0.004 without assumed funding. The20/100 MA primary remains negative(−0.021); its invalid-log shadow becomes positive(+0.070). That sign change is an accounting warning, not evidence for the strategy. The strongest momentum result remains positive in both registered cost/funding controls. No additional decomposition or parameter sweep was run.

## Halt chronology

The dates below are the actual primary engine halt bars, not the historical first-zero-return proxy. Full traces retain every opening and exit charge, marked notional, price stop and final cash state. No primary threshold fill falls outside its observed daily high/low envelope; the retained stop-level fill and daily funding approximation still do not establish actual intraday execution.

| Configuration | BTC halt | ETH halt | BTC price stops | ETH price stops |
|---|---|---|---:|---:|
| tsmom_k7_ls | 2022-10-21 | 2022-10-24 | 37 | 55 |
| tsmom_k14_ls | 2022-11-08 | 2023-06-20 | 30 | 52 |
| tsmom_k30_ls | 2024-08-05 | 2023-06-30 | 46 | 39 |
| tsmom_k90_ls | 2022-05-01 | 2022-04-23 | 17 | 15 |
| tsmom_k7_lo | 2022-05-11 | 2022-05-09 | 20 | 25 |
| tsmom_k14_lo | 2022-06-16 | 2022-06-15 | 22 | 23 |
| tsmom_k30_lo | 2022-06-16 | 2022-02-24 | 19 | 22 |
| tsmom_k90_lo | 2022-05-06 | 2022-02-24 | 18 | 22 |
| tsmom_k180_ls | 2022-01-29 | 2022-01-28 | 16 | 22 |
| macross_10_50_ls | 2023-03-03 | 2022-07-18 | 19 | 7 |
| macross_20_100_ls | 2023-08-18 | 2022-04-24 | 23 | 13 |
| macross_50_200_ls | 2022-03-27 | 2022-01-31 | 14 | 23 |
| macross_10_50_lo | 2022-05-27 | 2022-02-24 | 14 | 22 |
| macross_20_100_lo | 2022-05-06 | 2022-02-24 | 18 | 22 |
| macross_50_200_lo | 2022-05-06 | 2022-02-24 | 18 | 22 |
| donchian_n20_ls | 2022-10-27 | 2022-09-19 | 18 | 23 |
| donchian_n55_ls | 2023-06-21 | 2022-04-21 | 12 | 4 |
| xsmom_btc_eth_30d | 2022-07-28 | 2023-02-20 | 39 | 41 |

## Evidence and interpretation

- The broad July factor charter was committed, but pre-result commitment of the exact18 grid and clean executed source are not proven. The37 historical factor ledger rows are two runs of the same18 configurations plus one halt note. They are preserved as37 execution records, not37 distinct hypotheses.
- Current cache snapshots contain all available prior history: BTC2179 rows from2019-04-14, ETH2178 rows from2019-04-15, both through2025-03-31. The1241-date development calendars are complete with valid OHLC. Stateful signal warmup uses all prior rows; XS uses the common prior span. Sizing resets inside development exactly as before. No new source, fill, shortened development cohort, network fallback or post-cutoff price parsing occurred.
- Matching the old scalar results and saved daily stream supports numerical reproduction on the current caches. Missing contemporaneous raw receipts and July input hashes still prevent proof of the original data lineage.
- Prices retain the original unverified spot/mixed-provider proxy convention. Funding remains an assumed signed3bp/day, not realized historical perpetual funding. Fee4bp, slippage5bp, spread1bp and quadratic impact0.5bp are the fixed original execution assumptions. Stops retain threshold fills, and funding applies to opening daily exposure even on stop days.
- The aggregate is a daily50/50 index of separately simulated BTC/ETH sleeve returns. It is not a pooled executable account; capital transfers, cross-sleeve rebalancing costs, netting and margin are unmodeled. Per-sleeve dollar traces must not be interpreted as cashflows of a single index account.
- The original factor-floor role was benchmark ranking, with no standalone factor adoption gate. No bootstrap/DSR/holdout pass or fresh out-of-sample claim is inferred. Positive development Sharpe does not reopen the closed program. The spent holdout stays untouched.
- No input/output case was unavailable in this correction. The separate22 settlement-blocked accounting cases remain unavailable; no historical settlement value or successor substitution was added. ENet inference and fee-affected overlays were not run in this cycle.

## Registration, source and verification

Charter/archive commit:acb8c8b. Exact gate and input snapshot commit:9cedcc4. Reviewed runner/trace commit:ce7030f. Executed source: `27640882822d812c6d0478340495e033a11d3915`. One initial invocation was rejected by the clean-source fence while the preservation checker was being saved; it stopped before input loading/output creation. The rejection is preserved separately. The checker was then committed before the single empirical run.

Before execution, **107 synthetic, causality, sizing, accounting and registry tests passed**, plus six preservation selftests. Independent source reviews reproduced and resolved sensitivity-failure masking, diagnostic isolation and trace-schema issues. The optional trace leaves engine arithmetic unchanged. Tests include hand-calculated signed funding, opening/stop-exit fees and impact, positive books, stop gaps, actual halt bars, initial-NAV drawdown, complete clocks and full18/90 failure denominators.

Artifacts: `data/factor-correction/2026-09-10/results/` contains290 files:1start marker,36target frames,144repaired trace frames,90two-sleeve return frames,18shadow frames and1result JSON. All180individual sleeve simulations are represented by the90paired return frames. The central ledger appends18 fixed configuration records with all five variants and the shadow nested; its original730-row/428150-byte prefix is retained.

Independent result arithmetic/provenance reviews and preservation evidence are retained in `docs/factor-correction/verification/`. Preservation checks confirm6,876unchanged baseline files,5,974prior manifest references,all36prior predlab gate objects and224original inputs. The original ledger prefix is intact, with748rows after exactly18appends. Six permitted prior paths are disclosed:the trace source, gate addition, financial ledger, correction ledger, findings and current workspace instructions. Final verification records govern the exact checked counts. Original gate objects, legacy outputs, data caches and prior recovery/funding evidence are preserved. No manuscript, VPS, account, order, paper run or provider message was involved.

Result SHA-256: `a6886a55966f78d8e9bb36f694212fa626484a3088104bd53c48589a27b4309d`. The registered source, gate, correction policy, all16pinned inputs/documents and289pre-result-file output hashes are recorded in the immutable result.
