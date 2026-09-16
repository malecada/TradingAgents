# Three-year graph panel: source inventory passes, storage needs redesign

September 16, 2026. The fixed metadata audit found one nonempty Parquet object for every date/table pair across 2022–2024: 1,096 dates and 2,192 inventory cells. All six annual listings were nontruncated; all 24 preselected quarterly block/transaction schemas matched the required columns and types. This supports planning a multi-day integrity pilot. It does not establish row completeness, historical availability or predictive value.

The computation bottleneck has shifted. The prior one-day motif operation completed at 2.47 GiB sampled peak, but storing a three-year projected source panel is estimated to require **130.75 GiB**, versus **73.71 GiB free** in the measured filesystem. The present base64 receipt representation increases the estimated payload alone to **174.33 GiB**, before JSON, output vectors, Git and additional working copies. Bulk acquisition under the current layout is not justified.

| Quantity | Bytes | GiB | Evidence |
|---|---:|---:|---|
| All listed complete block/transaction objects | 760,339,599,640 | 708.12 | Exact sum of current listing metadata |
| Selected five block + nine transaction columns | 140,388,550,362 | 130.75 | Extrapolated from fixed quarterly samples |
| Same projected payload encoded as base64 | 187,184,733,816 | 174.33 | Planning arithmetic; excludes other overhead |
| Available local filesystem space | 79,147,524,096 | 73.71 | Snapshot after the audit |

The projection multiplies each quarter-start day's compressed selected-column bytes by the number of days in that calendar quarter, including leap day. It is not a measured full-panel size, confidence bound or worst-case guarantee. Transaction-column samples range from 96,659,471 to 149,438,634 compressed bytes per day; block-column samples range from 912,863 to 1,016,499 bytes. The samples contain 742,785–1,266,656 transaction rows per day, but no new row was decoded. No multi-year RAM or runtime claim is extrapolated from these figures. [Planning evidence](planning-estimate.json) retains each term and the disk observation.

## What is now established

- All 2,192 expected date/table entries and 24 fixed footer samples are retained, without date substitution, pagination or favorable sampling.
- Sampled required schemas match the one-day pipeline. Transaction amounts remain DOUBLE: exact wei, balances and cashflow reconstruction are still excluded.
- Four January 1, 2024 tail/footer receipts were reused only after exact object-identity checks. The audit made 50 new anonymous requests: six listings and 44 conditional range reads, totaling 1,131,565 raw response bytes. No complete new transaction object or column chunk was downloaded.
- All 30 registered lifecycle cells completed with zero unavailable cells and all 111 outputs retained. Runtime was 257.90 seconds, sampled peak RSS 185 MiB, under the retained 8 GiB/two-CPU/no-elapsed-kill guard.
- Independent raw XML, calendar, response, footer and arithmetic reconciliation passed. The [import manifest](import-manifest.json) binds 116 exact files totaling 2,734,318 bytes; both execution and coordinator structural checks pass. [Independent closure](CLOSURE_REVIEW.md) states the limits.

## Midnight handling is ready for a pilot

The synthetic-tested adapter assigns a motif to the day of its final event. For target interval [D,E) and inclusive one-hour span, subtract Local40 counts in [D−3600,D) from those in [D−3600,E), aligning vectors over the full overlapping address universe. This retains cross-midnight motifs exactly once and does not use events at or after E.

An address seen only before midnight can still participate in a triangle completed afterward; filtering to addresses active in the target day would lose that role. Target-day activity and the motif address universe therefore remain separate. Integer subtraction occurs before any normalization or concentration calculation. Coverage parameters supplied to the adapter are assertions, not proof that data exist.

The 29 focused tests passed in preparation, independent review and the isolated runtime. Boundary tests enumerate every three-event directed topology at five boundary arrangements, compare 60 invented event sets at four spans, and check future invariance, adjacent-window additivity, invalid identities and missing overlap. Independent review also checked 100 separate synthetic event sets. No new real multi-day motif panel has been counted.

## What still prevents a credible forecasting claim

All sampled objects report September 30, 2025 modification dates, including those representing 2022–2024. This establishes the retrieved archive vintage, not when the underlying public-chain events first became observable. It neither proves look-ahead contamination nor verifies a historical data-delivery service. The AWS registry describes daily delivery, but does not supply historical publication timestamps for these objects. [Official dataset description](https://registry.opendata.aws/aws-public-blockchain/).

A retrospective information-content study remains possible under an explicit finality/publication/computation-lag assumption. It must be labelled conditional; no historically executable or live-feed claim follows. Full row-level block linkage, duplicate detection, normalization, canonicality and complete-day boundaries still need checking on every admitted partition. The first January 1, 2022 day additionally needs an unaudited December 31, 2021 prefix; it cannot silently use zero history.

The next bounded engineering step is a fixed consecutive-day integrity and boundary pilot, using immutable binary captures and a compact daily feature table. Its purpose is to measure cross-day correctness, storage representation and processing overhead before committing to bulk history. Original receipts and failed attempts must remain untouched. A three-year run needs a viable retained-data location and backup plan; no deletion, new disk, paid storage or account access has been performed or authorized by this result.

Only then should a separate frozen comparison evaluate M0 market features, M1 ordinary on-chain activity and M2 local motif distributions on matched dates. Feature timing, chronological folds, past-only transformations, model capacity, uncertainty and financial evaluation remain separate gates. No price file, target, forecast, return or strategy outcome was opened in this stage.

## Reproducibility and cumulative history

Execution identity `eth-panel-readiness-20260916`, fixed source `76558b095ceed78c09a5101a44ccf4bfbb2afd64`, preserved checkout `/home/malecada/master_thesis/TradingAgents-onchain-panel`. The reviewed source was remotely verified before the claim. [Charter](CHARTER.md), [gate](gates.json), [pre-execution review](PRE_EXECUTION_REVIEW.md), [resource receipt](resource.json) and independent evidence retain exact bindings. Execution is terminal; do not relaunch or move its HEAD.

The one downstream readiness allowance imports the exact four earlier source/prototype/motif claims once and consumes cumulative 5/5. It does not reuse the prior motif amendment or alter old family limits. The coordination root now contains 42 local claims, not 42 independent hypotheses. The original specification, raw stores, failed 2 GiB attempt and successful 8 GiB benchmark remain preserved. No unrelated active research, paid service, provider contact, trading operation or background schedule was changed.
