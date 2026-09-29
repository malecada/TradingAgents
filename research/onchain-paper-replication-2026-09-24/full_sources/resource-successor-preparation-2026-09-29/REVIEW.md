# Independent review — prospective largest-week successor

September 29, 2026; engineering base `c0b3f244b4e4faa4434014dd065be8ebf0831dde`. Reviewed the draft charter, budget proposal, graph/job plans, schema, cells, seven daily source manifests and added storage preflight. Reconstruction used compact historical metadata, source inspection, hashes and the old SQLite file's stat only. No body, array or SQLite content was read; no test suite, admission, empirical job or network operation was run. Only this report was written.

**No material arithmetic or source-plan inconsistency was found. This is reviewable preparation, not an admissible or released experiment.** The identified release gaps are real and correctly disclosed by the draft.

## Budget and preserved scope

The proposed previous-allocation hash matches `full_sources/prices-coinmetrics-01/budget-allocation.proposed.json`. Its accepted allocation provides 12 pending body batches and 15 pending financial batches after the consumed source/resource/price claims. Current compact lifecycle reconstruction still finds seven current-program claims, all terminal with matching terminal-to-claim hashes. Combined with the preserved 17 historical attempts this is 24 consumed; the prospective identity has no claim.

The proposal's original family object equals the pilot02 claim's family. Its arithmetic is exactly **24 consumed + 12 body + 15 fit + 1 new resource = 52**. It adds one claim to the old ceiling of 51, reclaims no failure and creates no new scientific lane or fit. The existing fit allocation independently contains 15 batches and 1,420 distinct cells, comprising 1,400 paper fits and 20 diagnostics. The draft preserves the original nine-week/109-cell resource requirement and does not treat this eight-cell stage as full resource-pilot or paper completion.

`admission.py:214–217` currently requires equality between the proposed family and every prior same-mechanism claim. Raising the budget field to 52 would therefore fail, exactly as disclosed. This report does not approve a budget-extension mechanism or make the allocation effective. Old gates, claims, family/history objects and all exposed samples must remain immutable when such a mechanism is designed and independently verified.

## Sources and execution contract

All seven daily manifests contain exactly their corresponding original `pilot_successor_02/source-index.json` member. Current mapping hashes equal both the original source-index hashes and original claim inputs. The schema equals the original expected schema. Intervals partition `[2022-07-25, 2022-08-01)` into seven contiguous days; daily rows sum to 8,841,688. `status: complete` here describes the declared source inventory, not a new successful decode or retrospective completion of the failed parent's source cells.

The largest-training-week selection was independently reconstructed from the original, hash-bound fullpanel plan's daily metadata: among 104 complete Monday weeks in the ETH2024 training interval `[2022-01-01, 2024-01-01)`, 2022-07-25 has the highest declared count, 8,841,688. This qualifier matters: 2024-03-11, in the test-year pilot sample, has 8,848,144 rows. The draft correctly says largest **training** week and inherits the frozen selection; it does not claim the largest graph or peak memory workload across all nine dates.

Static comparison with `graph_production.py` confirms the graph plan's exact fields, ETH decoder schema input, Monday coverage, expected-week list and seven unique source-input names. `cells.json` matches the producer's generated ordered denominator: `source-000000` through `source-000006`, then `graph-2022-07-25`. The generic job's exact schema, `kind: graphs`, `payload.plan_input` and resource fields agree with `job.py`. Actual admission still needs registered windows covering the week and named input bindings for `graph_config`, `eth_schema`, `graph_plan`, `source_00` through `source_06`, `environment` and `execution_job`.

The current producer exhausts each daily decoder and verifies its mapping again before emitting a retained `SourceBoundary`. It creates a new exclusive aggregation/output owner, uses one transaction-identity ledger for the supplied stream and preserves unavailable source/graph dispositions. Nothing in the draft opens the old interrupted SQLite or rebuilds the two already complete pilot graphs. The prior terminal and closure evidence identify the July graph as unfinished; new admission must preserve that ancestry rather than relabeling it unattempted.

## Resource and storage arithmetic

The job's 6 GiB memory maximum, 5 GiB high threshold, 3 GiB reserve, 9 GiB startup requirement, 20 GiB disk floor and 28,800-second limit satisfy the generic static policy inequalities. The generic launcher supplies zero swap and uses up to the first two available affinity CPUs with per-thread readback. This is not evidence that the current host has the required startup capacity or that ancestor pressure cannot terminate the workload.

The added `storage-preflight.json` is appropriately insufficient for release:

- All seven stored-span sums, projected-range sums and unions of covered 4,096-byte pages were independently reconstructed from mapping metadata. Maximum projected page coverage is 215,748,608 bytes. This is a page-coverage calculation, not a guarantee of filesystem allocation, metadata overhead or concurrent scratch residency.
- With N = 8,841,688 raw rows, at most 2N distinct ETH addresses and N edges give the stated saved-array payload bound: `2N × (42 × 4 + 4 × 8) + N × (2 × 8 + 2 × 8 + 2 × 8) = 448N = 3,961,076,224` bytes. This matches the current Unicode address and numeric array representations. It excludes headers, JSON, Python objects, graph construction copies and SQLite/sort/index costs, as disclosed.
- The old SQLite stat matches 3,755,212,800 logical bytes and 3,755,302,912 allocated bytes. It is existing occupied space, with unknown committed row count and no admitted recovery prefix; it supplies neither a new scratch upper bound nor additional free capacity.
- The saved free-space observation leaves 12,006,404,096 bytes above the 20 GiB floor. It is an as-of observation; the charter's earlier approximate headroom is not an execution-time guarantee. The new SQLite/index/sort peak remains null, so `release_sufficient: false` is correct.

## Concrete release prerequisites still missing

1. An explicit, independently verified cumulative-extension mechanism and accepted allocation that preserve every prior family/history/claim object; merely editing the budget or changing mechanism names is insufficient.
2. A reviewed and committed final charter/gate containing the unchanged failed parent experiment record, exact new identity, exposed-window semantics, all source/configuration/plan/closure inputs and the eight cells. The generic source job requires output names `cell-ledger.json`, `source-summary.json` and `artifact-index.json`.
3. A bound current execution-environment inventory, runtime hashes and complete current package/source closure required by `job.required_sources()`. The referenced environment is not yet supplied. The active offline verification result must close on those reviewed source bytes before release attribution.
4. A quantitative full-lifecycle storage assessment covering new retained SQLite, transaction/index pages, sort/temp growth, projected Parquet materialization, graph arrays, metadata, failure retention and any peak overlap; the existing old database remains occupied. RAM feasibility remains uncertain despite the proposed larger cgroup ceiling.
5. Fresh admission, unchanged-input/source checks, adequate host/disk capacity and live-owner/exclusive-path checks. Planned outputs belong under the new identity's source-artifact directory and generic job/guard ownership paths, never the original pilot directory. The resource guard is a stop mechanism, not proof that the calculation fits.
6. At execution, full mapping/body/schema/timestamp/count verification and complete retained dispositions; after execution, bounded graph-content verification and independent closure before any graph is admitted to a population or downstream fit. No wider global uniqueness, historical vintage or economic claim follows from this single-week job.

No gate, admission or launch is supplied by the reviewed draft. The absence of those items is correctly presented, not hidden readiness. This report authorizes no execution and reduces no study requirement.

## Reviewed draft identities

| File | SHA-256 |
| --- | --- |
| CHARTER.draft.md | `c904833537fff22b98af78071bfeb352d189bade1c7eb4acbb3a09cce14a45b2` |
| budget-extension.proposed.json | `4ea32bb359f4568d26b672a04657b7f1b5f11031a7c9ecbea3b50fdcec58405f` |
| cells.json | `eb6a07c3f0d472e90e0c5823db408e1b2e8e78c103944de2a7c444812e24c793` |
| eth-schema.json | `424f4855a105cb3c9c428a4027d880bf8e1849d2da3ffdbe8550c13ffa64b9b2` |
| execution-job.draft.json | `93c5b1b8671e85e21b99a64193cf1dfb6718f13b8032bf95968cbb5e925cfa86` |
| graph-plan.draft.json | `87a91731c13572612cbd704a32ee1fdeddb476509f6156e3a0e7a0db2528349b` |
| source-00.json | `34d21111720fa1c843718c502ea1c32ae813565f6277bd5e504257937231e6ca` |
| source-01.json | `a92d86612601c71e688be3acc6d3cfa1a82061482b316578efc0f9787997e09b` |
| source-02.json | `edfdb3192c5eb009e7d5475e6b20630e58ac2acb0ee9946c5c509502151c2985` |
| source-03.json | `8e741eb2a5890176b5707bcaed561886a2f9faeca7bc4734c2f45d3bc6c6916f` |
| source-04.json | `914bb1b676327b24dd17ee83a3ddcbaf80967bc2f6417eabec3318fb4f42e5b5` |
| source-05.json | `745d1c174895186134af41b5e296b9a24de1f29dc8d79230c3f619a47b01b446` |
| source-06.json | `3fc52bafbbb317e9c1e723990988bbd29c14645921bfa5465fd963c7cba84ffa` |
| storage-preflight.json | `3ca809e1d2e7949ca2f6f1786730c631efc128b2d671d04a9445e3b28e6433c8` |
