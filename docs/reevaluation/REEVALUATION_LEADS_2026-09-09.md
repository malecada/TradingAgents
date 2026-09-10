# Lead reevaluation after the September 9 repairs

**September 10 qualification:** Later recovered-data and lifecycle evidence changes the accounting interpretation to **two conditional measured failures and 22 unavailable cases**. Threshold 3.5 / 24h held LUNA through its closure and is no longer a complete executable negative. The historical results below are preserved; the [September 10 recovery report](../data-recovery/DATA_RECOVERY_2026-09-10.md) takes precedence for current accounting counts and qualifications.

The preregistered reevaluation completed all 26 cases. No strategy was validated or promoted. The most consequential finding is that 21 accounting cases remain unjudgeable with the registered data; they must not be counted as confirmed kills.

The registered correction covers 26 fixed cases across five materially affected families. The accounting runs reveal a material distinction: 21 cases are unavailable because a held position cannot be marked from the registered data; three liquidation-fade cases are measurable and fail their original gates. The corrected pair selector still fails its historical conditional comparison, with complete-panel inference unavailable. The DEX composite passes its descriptive ranking test but fails the economic gate. These findings do not establish an absence of weaker effects or of possible strategies outside the tested constructions.

## Scope and controls

Registration preceded results in commits `e3c0d63`, `e4e60d7`, and `4fe113b`. Reviewed source was frozen in `49fb9e47c4d9e40b9c3f1b7de475041ec63aac76`; 171 integrated offline tests passed in 19.03 seconds before execution. The repaired base had previously passed 779 offline tests. Source, gate and correction policy remained fixed throughout the empirical runs. Original worktrees, data and results were preserved.

The original development interval is January 2021–March 2025. Momentum and carry retain the original January 5 first accrual; PRX retains its original 50 months ending February 2025. NLST4 retains 3,981 development-created pools and only their already cached settlement observations, including those extending into April 2025. No April-created pool, new holdout cohort, forecast-model refit, strategy parameter search or live deployment is part of this correction. PRX necessarily recomputes its original rolling formation regressions.

All 31 previous predlab registrations are unchanged. Original accounting DSR denominators remain 74/87/100 for momentum/carry/liquidation fade; the additional current-policy comparison uses 150 fixed accounting trial identities. Missing cells remain in the declared denominator. No winner is selected, no acceptance threshold is lowered, and spent holdouts remain spent.

## Family outcomes

| Family | Registered cases | Corrected disposition |
| --- | ---: | --- |
| Weekly cross-sectional momentum | 12 | All unavailable: held positions encounter contract price tails. No corrected full-window Sharpe or gate failure is claimed. |
| Cross-sectional carry | 6 | All unavailable at the LUNAUSDT price tail. Funding continuation does not establish a settlement price. |
| Liquidation fade | 6 | Three measured failures; three unavailable due to internal hourly gaps. P0/P1/P2 pass at family level; only three of six P2 cells have complete event windows. |
| Pair persistence / PRX | 1 | Original conditional comparison fails. All 50 months are retained; six unavailable selected-pair outcomes prevent complete-panel inference. |
| New-pool ranking / NLST4 | 1 | Ranking T1 passes; economics T2 fails. 2,718 of 2,776 new-set pools are scoreable; the global top-quintile comparison remains retrospective. |

## Accounting: actual failures and unavailable books

The original stored Sharpes below are invalidated historical comparators, not alternative usable estimates. Corrected values use simple returns, actual held exposures and turnover, complete calendars, initial capital and compounded hourly NAV.

| Liquidation-fade case | Original stored SR | Corrected SR | Maximum drawdown | DSR, original n=100 | DSR, current n=150 |
| --- | ---: | ---: | ---: | ---: | ---: |
| threshold 2.5 / hold 6h | 0.3562 | 0.1657 | 70.97% | 0.0143 | 0.0099 |
| threshold 3.5 / hold 6h | 0.9612 | 0.8154 | 16.60% | 0.3060 | 0.2589 |
| threshold 3.5 / hold 24h | 1.1205 | 0.9813 | 43.00% | 0.2330 | 0.1926 |

Each measured series has all 1,551 development days. Each fails both the SR≥1 and original-denominator DSR≥0.9 requirements. The near-threshold SR of the 24h case is therefore not a failure attributable only to a small cost difference. Even at zero transaction fees, the three DSR values are 0.1058, 0.5462 and 0.2928, all below 0.9. The corresponding zero-fee Sharpes are 0.6193, 1.0169 and 1.0937; doubled-fee Sharpes are −0.2898, 0.6089 and 0.8680. These are fixed forensic counterfactuals, not additional candidates. The original liquidation-fade model excludes funding, so these figures are not executable all-in net returns.

The invalid log-PnL counterfactual is −0.1294 for threshold 3.5/6h. For the other two measured cases the engine rejects a log value below −1 during the May 2022 crash: it cannot be admitted as an arithmetic simple return. That diagnostic is explicitly unavailable, not silently altered to produce a number. Expensive remaining placebo performance tests are not run after a primary gate failure; the original shared RNG stream is nevertheless advanced as preregistered.

| Cases unavailable | First blocking observation | Evidence requirement |
| --- | --- | --- |
| Nine momentum cases: all L7/L14 cells, plus L28/skip1/K20 | BZRXUSDT, 2021-12-20 | Verified perpetual contract closure and settlement accounting. |
| Three momentum cases: L28/skip0/K10, L28/skip0/K20, L28/skip1/K10 | BNXUSDT, 2025-03-18 | Verified contract closure/settlement; a successor ticker cannot be substituted by name. |
| All six carry cells | LUNAUSDT, 2022-05-13 | Verified terminal contract cashflow and funding cutoff. |
| Liquidation fade threshold 2.5/24h | TRXUSDT, 2022-02-26 00:00 UTC | Recover the missing internal hourly observations from verifiable records. |
| Liquidation fade threshold 2.5/48h | FILUSDT and LTCUSDT, 2022-02-26 00:00 UTC | Same internal coverage issue. |
| Liquidation fade threshold 3.5/48h | FILUSDT, 2022-04-01 00:00 UTC | Same internal coverage issue. |

The momentum benchmark is also unavailable at BZRX. Its failure does not hide candidate measurements: all 12 real books were attempted separately and each encountered its own held-mark failure. A first blocking observation is not an exhaustive list of later gaps. Previous full-window results cannot validate the corrected holdings contract.

The local contract-tail evidence is specific. BZRX hourly trading ends December 19, 2021 with a zero-volume terminal bar; BNX has 336 frozen zero-volume hourly bars during March 18–31, 2025; LUNA has seven frozen zero-volume bars on May 13, 2022. The daily source fetcher trims trailing zero-volume rows. Funding data continue after some trading tails, and FORM begins later in the local store, but neither fact supplies the missing terminal cashflow. This supports a contract-lifecycle explanation; no official settlement record has been reconstructed in this cycle.

The TRX/FIL/LTC issue is different: all three hourly stores omit February 26–28, 2022 (72 hours) and April 1–2, 2022 (48 hours), despite bars on either side and active daily bars on inspected dates. Their missing-month metadata do not flag these internal gaps. Alternative minute and aggregate-hour files exist but are also 120 hours short by row count; their existence does not establish recoverability. No interpolated, zero-filled or substituted observation was used.

## Pair selection

The corrected Engle–Granger formation test produces a mean monthly selected-pair persistence rate of 10.9611%, against 11.3000% for the fixed random comparator. The ratio is 0.9700 versus the required 1.5; the original one-sided paired Wilcoxon p-value is 0.8128 versus the required <0.05. The original stored ratio was 0.9427. The formation correction does not reverse this conditional rejection.

Every one of the original 50 months remains present. There are 931 selected pairs and 925 scoreable selected outcomes; six are unavailable: two TOMO-related pairs in November 2023, three RNDR-related pairs in August 2024 and one MATIC-related pair in September 2024. Thus 47 months have complete selected-pair coverage. The random arm preserves its seed, 1,305 attempts and 1,000 scoreable outcomes; its monthly rates exactly match the original comparator. Repeated/reversed random draws remain disclosed.

The registered stationary-bootstrap sensitivity is unavailable because the observation panel is incomplete. No 47-month substitute, confidence interval or bootstrap probability was manufactured. The historical Wilcoxon comparison remains conditional and has dependence limitations from overlapping formation windows and shared names. No pair-trading P1 simulation was run; this is not a claim about trading profitability or all possible pair constructions.

## DEX cohort

All 3,981 frozen pools are retained: 1,205 prior-history pools and 2,776 new-set pools. Events and seven-day returns are available for every new-set pool; 2,718 have a score and return, while 58 remain explicitly unavailable because feature availability or causal normalization is insufficient. All 17 quarters remain represented. The old result used 2,770 scoreable new-set pools, so the comparison is not a paired estimate on an identical sample. Independent identity checks find 52 formerly scoreable rows now unavailable and no newly scoreable rows.

| NLST4 diagnostic | Original stored result, qualified | Corrected result |
| --- | ---: | ---: |
| Scoreable new-set pools | 2,770 | 2,718 of 2,776 requested |
| Rank IC | 0.09191 | 0.14236 |
| Quarter-bootstrap fifth percentile | 0.02899 | 0.08322 |
| Top-quintile pools | 554 | 544 |
| Mean seven-day return, $1,000 model | 6.50% | 19.10% |
| One-sided NW p-value | 0.40186 | 0.22802 |
| Mean excluding largest absolute return | −12.38% | 0.044% |
| Median seven-day return | −68.38% | −64.95% |
| Largest absolute return / total absolute returns | 14.75% | 13.90% |
| Mean seven-day return, $5,000 stress | −29.22% | −21.42% |

The ranking criterion T1 passes with all 1,000 registered bootstrap draws finite and a positive fifth percentile. The economics criterion T2 fails its p<0.05 requirement and positive $5,000 stress condition. The mean at $1,000 is positive, but the median is a severe loss and the mean excluding the largest absolute return is only about four basis points. No threshold was changed to exploit the improved rank correlation or positive arithmetic mean.

This result retains an association between the corrected available-feature composite and later outcomes in the scoreable historical cohort. It does not establish a profitable entry policy, identify which repair caused the metric change, isolate the contribution of any component, or provide a new out-of-sample confirmation. The old features and the corrected features differ, and coverage also changes. The global q80 threshold is computed over the full evaluated new sample, so the top-quintile comparison is explicitly retrospective. No P1 or holdout was executed.

Missingness is material rather than cosmetic. Ownership is unverified for every new pool and remains NaN. No new-set deployer-performance feature is identifiable under the complete-history requirement; only 14 have an identifiable deployer count. Unknown earlier deployer identities cannot silently become a smaller known history. The original signs and minimum six observed standardized features remain fixed. The ranking result therefore must not be described as validation of all ten component features.

The rebuilt features use strictly earlier observations for within-quarter normalization, preserve independently known creation/deployer records, and admit completed outcomes only after both the nominal seven-day horizon and actual selected exit time. Actual entry clocks, strictly prior feature blocks and completed five-minute ETH quotes are enforced. Creation timestamps remain interpolated. Original LP/gas assumptions exclude MEV and are not observations of live execution. The previous recorded artifact is preserved separately as `original-nlst4-p0.json` with its source checksum for this reporting comparison.

## What deserves the next correction

The strongest immediate priority is market-data and instrument accounting: verified terminal settlement events for discontinued contracts, a point-in-time identity map that distinguishes contracts from successor tickers, and explicit internal bar-gap recovery with source receipts. These are prerequisites for the 21 unavailable books and relevant pair-coverage gaps. Recovery must preserve the original sample and produce a separately registered replay. Filling missing held returns with zero, deleting affected coins, renaming contracts, or shortening the window would change the evidence.

The present cycle does not repeat S2/S3 or the 16 saved ENet diagnostics already corrected earlier on September 9. OFLOW's sign fix was already applied before its economic failure. The passive-fill overlay and execution-cost forecast study need separate holdings/measurement repairs before a valid comparison. Classic factor/V2 and duplicate-fee overlays have concrete but separately scoped accounting work; they were not silently added after these outcomes. Historical news/on-chain vintages that were never retained cannot be recreated by changing availability timestamps. Full triage and exclusions are retained in the three triage documents beside this report.

A measured negative result, an unavailable measurement, a conditional historical diagnostic and a validated strategy are separate conclusions. No closure is converted into proof of universal absence of alpha, and no corrected development result restores an untouched holdout.

## Reproducibility and verification

The five immutable results and their complete cell metrics are under `data/predlab/audit_reevaluation_2026_09_09/`. Every family process exited successfully; process completion is separate from a research PASS. The ledger preserves every prior byte and appends exactly 26 rows with 26 unique trial identities. The original S2/S3/ENet correction artifact is unchanged. All 31 previous registrations are unchanged.

The verification manifest records 13,217 distinct input paths, ten hashed ancillary outputs, all five result hashes and execution timestamps. Independent accounting, PRX and DEX reviews are stored beside this report. Original data files were hashed before use and checked again at completion; independent reviewers also verify the input and output hashes. No source, gate, policy or HEAD changed during the runs. The DEX reconstruction completed in about 31 minutes 48 seconds; its existing wallet-history implementation dominates the runtime.

| Result | SHA256 |
| --- | --- |
| momentum | `cd8edbcbc36638b87dfab722526ff715590e78016b5be7ca8d091a11a63b7b7b` |
| carry | `b2def83b0c8b13b418963b0d1df6008d178c12f114d6efb37d05400eaa1512ab` |
| liquidation fade | `30a8629fa9214ac031d8a642f719bccdff60c6f1a0b473b365e699dd79f6837a` |
| PRX | `799662b5ec8307aa9ca4008aef0b3d219a79c40a37dddebcbb0f8606cffba3ce` |
| NLST4 | `613cc7a1321eaaf3b5ac2613cbed10c7f7db0ce955f6e7ce56e39ac7e7449c53` |

Executed source: `49fb9e47c4d9e40b9c3f1b7de475041ec63aac76`. Gate SHA256: `b74efa4273a38339cab652cb140b0aa64df1778a1f7f8bcb015e49c3f357e894`. Pre-run correction-policy SHA256: `fba631d9bb458decc4b278c1b224a2441d97b75d7a328dffa0850c9799619a4d`. Completion is recorded afterward in the append-only correction register; the frozen gate retains its pre-run state.

Reproduction and review files: `execution.md`, `verification/manifest.json`, `verification/final-integration.log`, `accounting-artifact-review.md`, `prx-result-review.md`, and `nlst4-result-review.md`. Full original/corrected accounting cells and every unavailable reason are retained in the immutable JSON files, including diagnostics that could not be computed. THESIS_FINDINGS §89 records the current interpretation. The current thesis already withdraws the legacy causal and strategy-validation claims; this cycle adds research evidence and does not change the manuscript or deployment.
