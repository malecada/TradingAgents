# Independent completed-run accounting audit

The fixed factor-floor run under source `27640882822d812c6d0478340495e033a11d3915` was reviewed from its completed saved outputs. The registered gate and correction-policy hashes were independently compared with that historical Git revision. No strategy function, signal builder, fitted model or backtest runner was invoked. This review reconstructed accounting identities and reporting metrics from saved Parquet traces and returns only. Original data, outputs, source, registrations and ledgers were not changed; only this note and its companion JSON were written.

## Disposition and integrity

**All reviewed checks passed; no material accounting discrepancy was found.** All18 primary records are qualified benchmark measurements; all90 registered book/index variants and18 frozen-log diagnostics are available. None is a strategy-validation decision. The result's `holdout_evaluated=False`, `models_refit=False` and `validated_strategies=0` flags are consistent with the reviewed artifacts.

- Result SHA-256: `a6886a55966f78d8e9bb36f694212fa626484a3088104bd53c48589a27b4309d`.
- Companion audit JSON SHA-256: `848236df067d3d762a883593b8f79c4927f0aeabbf14e2e4fda994030b4d643a`.
- All289 declared output-payload hashes were verified before and after inspection; the namespace contains those files plus `result.json`.
- All16 registered pinned input/archive/charter files matched their declared hashes. This verifies the consumed saved artifacts, not otherwise missing July acquisition lineage.
- The central ledger's original730-row/428150-byte prefix exactly matches SHA-256 `710a4f087325bfb408ed8d051963a473e8d8a47b445ffae0238c565aff6dc791`. There are exactly18 unique new rows in registered source order, matching configuration identities, nested variant records, diagnostics, source and result hash. Final748-row ledger SHA-256 is `4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601`. The reviewer did not write it.

## Reconciliation and clocks

All36 target artifacts contain the complete1241-day valuation calendar, November7,2021–March31,2025. Every one of90 return-index files,144 corrected sleeve traces and18 shadow files contains the exact1240-day midnight return calendar, November8,2021–March31,2025. There are178560 corrected trace rows. All saved return values are finite; no cash-tail or missing-date rows were silently removed.

Every corrected trace was checked independently for its10000 initial NAV, exact NAV continuity and persisted alias equality; NAV change equal to gross plus signed funding minus fee and impact; gross equal to pretrade exposure times effective marked return; funding at the declared signed assumed daily rate; entry turnover against the prior marked holding; one-way entry/exit fees; quadratic impact using each leg's NAV; exact component subdivisions; final/exit marked notionals; saved requested targets before halt and zero exposure after it; return-to-NAV agreement; exact halt dates/counts and monotone latch behavior; and disclosed assumed stop fills relative to each saved day's OHLC. Zero-execution and zero-funding controls have exactly zero corresponding charges. All144 traces have zero flagged fills outside the admitted OHLC envelopes, which does not prove intrabar market-order execution fidelity.

All reported primary, variant-index, sleeve and shadow metrics were recomputed from saved return arrays: sqrt365 and sqrt252 Sharpes, compounded return, initial-NAV drawdown, row counts, trailing cash rows and active-only diagnostic Sharpe. Maximum discrepancy was exactly0 for the reported metrics. The maximum dollar accounting residual was `5.8548721426632255e-12`, within1e-9. All90 aggregate streams exactly equal the two-sleeve mean. Exact post-halt rows carry zero exposure, holdings, cashflows and returns with unchanged NAV.

All18 legacy scalar comparisons match the archived original definitions at tolerance1e-10; maximum absolute difference is `1.1102230246251565e-16`. The original four compared scalars are sqrt252/no-cash-hurdle Sharpe, compounded return, original no-initial-NAV drawdown and row count. The separately archived historical BEST two-sleeve stream matches at rtol0/atol1e-10 on the exact index. This supports numerical reconstruction on the saved references. It does not retroactively establish clean July execution, contemporaneous data receipts or exact-grid pre-result registration.

## Why the30-day long/short momentum measurement changes

The saved index Sharpe changes from legacy **0.279708** to corrected **0.985098** on the same365-day reporting convention. The corresponding original252-day values are0.232412 and0.818528, so annualization does not explain the difference. The saved index compounded return changes from9.466398% to65.325008%.

The largest observed difference is a change in the permanent BTC halt. Its legacy stream's final nonzero date is January6,2023; the archived January7 halt date denotes the first zero-tail row. The corrected BTC book instead halts August5,2024 and records577 additional nonzero return days. At the legacy final nonzero date, corrected BTC NAV is **10391.79**, compared with the legacy final NAV **9735.91**, a difference of **655.88**. Corrected BTC subsequently gains **10426.25** to finish at **20818.03**. The later interval reconciles directly to saved gross **+11614.39**, signed funding **-506.37**, execution fees **−661.08** and impact **−20.70**. This accounts for most of the **11082.12** final BTC dollar difference.

ETH's legacy last nonzero day is June26,2023, followed by its June27 zero-tail marker. Corrected ETH halts June30, adding four nonzero days. It has an **807.73** advantage by the legacy last nonzero day, then loses **214.29** during the extension, leaving a **593.45** final difference.

These are time-segment identities on already saved books, not newly simulated conditional variants. They show how small earlier NAV differences can change a permanent stopping boundary and expose the corrected book to much more of the subsequent price path. The historical engine has no saved daily fee/funding trace, so an exact separate causal allocation of the legacy-to-primary change among fee convention, signed funding, drifted turnover and risk-exit charges is not established here. Sharpe differences are not additively decomposable into those terms.

The registered controls qualify a fee-only explanation: k30 zero-execution Sharpe is **1.070207**, double-execution **0.906936**, and zero-funding **1.010040**. Each control independently applies the same halt rule, so these are complete cost/funding sensitivity measurements with potentially different exposure durations. They do not identify isolated causal effects under a shared stop schedule, and the favorable variant is not selected.

## Frozen-log and stopped-tail limits

For every shadow, the saved primary aggregate plus frozen exposure times `log1p(effective_return) - effective_return` reproduces the diagnostic, with maximum absolute residual `1.3877787807814457e-17`. Primary funding and execution-charge fractions and the primary stop schedule are unchanged. All18 shadows are finite and explicitly labeled invalid frozen-exposure diagnostics. They do not describe a feasible alternative trading account and cannot support promotion.

All36 primary sleeves eventually trip the permanent halt. Aggregate trailing exact-zero rows range from238 to1157 of1240 return days, and k30's aggregate tail falls from644 legacy rows to238 corrected rows. Full-clock metrics correctly retain those rows; active-only metrics remain diagnostic. The observed halted paths do not establish an ongoing strategy that can simply be resumed or restarted. The original holdout remains spent, the original factor-floor registration supplies no standalone adoption gate, and the aggregate is a two-sleeve benchmark index with unmodeled pooled-account transfers and costs. Proxy prices, assumed funding and threshold-stop fills remain qualifications even when numerical legacy parity passes.

## Complete frozen grid, without selection

The table retains registration order. All values are365-day full-clock Sharpe, except the final column. The log column is an invalid frozen-exposure diagnostic. These are qualified benchmark measurements, not18 passes of a strategy gate.

| Configuration | Legacy | Corrected | Zero execution | Double execution | Zero funding | Invalid log shadow | Corrected zero-tail rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| tsmom_k7_ls | 0.034621 | 0.151295 | 0.243534 | 0.070722 | 0.123086 | 0.249939 | 889 |
| tsmom_k14_ls | 0.271060 | 0.336140 | 0.421911 | 0.293567 | 0.351327 | 0.400183 | 650 |
| tsmom_k30_ls | 0.279708 | 0.985098 | 1.070207 | 0.906936 | 1.010040 | 0.975064 | 238 |
| tsmom_k90_ls | -0.544870 | -0.522876 | -0.518068 | -0.543050 | -0.522547 | -0.446339 | 1065 |
| tsmom_k7_lo | -0.968833 | -0.862231 | -0.841777 | -1.086680 | -0.829690 | -0.985146 | 1055 |
| tsmom_k14_lo | -0.927162 | -0.943819 | -0.922904 | -0.959625 | -0.929167 | -1.056514 | 1019 |
| tsmom_k30_lo | -1.460912 | -1.275786 | -0.929114 | -1.469124 | -1.113774 | -1.408628 | 1019 |
| tsmom_k90_lo | -1.086608 | -0.934554 | -0.759496 | -1.088863 | -0.870511 | -1.050802 | 1060 |
| tsmom_k180_ls | -1.440269 | -1.450072 | -1.436519 | -1.471245 | -1.441491 | -1.495246 | 1157 |
| macross_10_50_ls | 0.760875 | 0.858507 | 0.895914 | 0.821087 | 0.851473 | 0.931352 | 759 |
| macross_20_100_ls | -0.678651 | -0.020635 | 0.002860 | -0.149509 | -0.048346 | 0.069505 | 591 |
| macross_50_200_ls | -0.987570 | -0.966855 | -0.106932 | -0.986621 | -0.990514 | -0.947620 | 1100 |
| macross_10_50_lo | -1.178287 | -1.028438 | -0.758636 | -1.215575 | -0.877543 | -1.153257 | 1039 |
| macross_20_100_lo | -1.086608 | -0.934554 | -0.759496 | -1.088863 | -0.870511 | -1.050802 | 1060 |
| macross_50_200_lo | -1.086608 | -0.934554 | -0.759496 | -1.088863 | -0.870511 | -1.050802 | 1060 |
| donchian_n20_ls | -0.070262 | 0.288407 | 0.320712 | -0.010139 | 0.004368 | 0.403591 | 886 |
| donchian_n55_ls | 0.273073 | 0.360765 | 0.386031 | 0.331601 | 0.353302 | 0.425346 | 649 |
| xsmom_btc_eth_30d | 0.348787 | 0.446214 | 0.521306 | 0.389163 | 0.422285 | 0.465575 | 770 |

The companion JSON retains full-precision metrics, per-sleeve halt dates, arithmetic residuals and the k30 saved-output decomposition. The earlier `accounting-results-part1.md` remains a preserved review of the first two completed configurations; this completed-run note extends its coverage to the entire fixed slate.

## Final report numerical cross-check

All54 data rows in the main report's three18-row tables were checked against saved result JSON at the report's displayed precision: historical/current metrics, execution/funding/log sensitivities, halt dates and stop counts. Summary counts also match:16 improved common-365 Sharpes, seven positive corrected versus six positive legacy measurements, and the historical10/50 MA index changing from0.760875 to0.858507. The k30 halt explanation matches the saved-output decomposition above. No numerical reporting defect was found. Reviewed main-report SHA-256: `423fcb1d4eb7c4fed9220f93015131554116283f26688600e9c08bf1ab7dadb9`. These sign/ranking summaries remain descriptive; they do not supply an adoption gate.
