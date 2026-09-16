# One-day temporal-motif feasibility result

September 16, 2026. **The full-day Raphtory Local40 benchmark exceeded the tested 2 GiB process-memory budget.** This is a measured implementation/resource failure, not evidence against the usefulness of temporal motifs. No full-day motif counts, concentration result or forecast result were produced.

The captured January 1, 2024 Ethereum day was successfully reconstructed into 547,332 eligible events, 443,937 distinct directed pairs and 381,191 incident addresses. Every transaction was revalidated against the retained blocks, the exact 777 missing-recipient sentinels remained excluded, and the static pair fingerprint matched the prior independently checked graph. Explicit event IDs preserved repeated transfers and transaction order without changing integer-second durations.

| Registered stage | Retained evidence |
|---|---|
| Input semantics | Full 1,101,465-row reconciliation and original exclusions matched |
| Ordered events | Canonical block/index ordering and ordered-event fingerprint retained |
| Bounded independent oracle | Six 30-event induced samples matched exhaustive Local40 counts |
| Full-day local motifs, inclusive one-hour span | Unavailable: memory guard terminated computation |
| Complete local-vector export | Unavailable: no local shards or full-day summary were published |

The run published three of 44 declared output files: `integrity.json`, `bounded-oracle.json` and `graph-build.json`. The absent 39 local-vector shards, summary and timings remain absent; they are not zero counts or successful cells. The original five-cell denominator remains in the claim. Bounded sample counts concern their explicitly selected event subsets and cannot substitute for full-day counts.

The stopped process initially left no lifecycle terminal receipt. Independently reviewed failure-only recovery appended `failed.json` once, with the original claim and three output hashes unchanged. No calculation was replayed. The separate five-cell progress record is explanatory; it does not turn the failed attempt into a completed run.

The two-CPU guard observed 2,656,620,544 bytes of process-tree RSS (2.47 GiB) against its 2,147,483,648-byte limit and sent SIGTERM. The child exit code is -15. The whole guarded execution lasted 219.66 seconds. There was no elapsed-time kill. The graph-build receipt preceded termination, while no local result was exported. Whole-run time includes repeated source/admission checks for retained input reads and cannot be presented as motif-computation time. No phase-timing output survived. RSS was sampled, so 2.47 GiB is an observed point before termination, not the required memory for successful completion or a worst-case bound.

The frozen operation used Raphtory0.17.0, all three-edge up-to-three-node Local40 roles, inclusive `last_time − first_time ≤ 3600` seconds, integer Unix timestamps and explicit chain-order event IDs. All events were confined to the captured UTC day; cross-midnight motifs were outside coverage. The library's star-center, two-node endpoint and triangle roles were checked independently on small synthetic examples before the run. Neither historical publication timing nor a source feature panel was admitted.

## Feasibility implication

The preceding static graph fits comfortably in the measured environment, and repeated-event representation and bounded motif correctness are feasible. The complete local-motif calculation adds a material memory constraint under this implementation. It would be unjustified to extrapolate the 14.4-second static reconstruction to full motif extraction, or to start building a multi-year feature panel from this result.

The next engineering question is memory attribution and whether a declared implementation change or larger resource envelope can complete the same fixed operation. Candidate approaches require measurement: profiling graph/counter/output allocations, evaluating a genuinely bounded counter implementation, or testing a separately justified memory budget. This run does not establish that 4 GiB, 8 GiB or another specific amount would suffice. A smaller graph, a shorter observation window or changed motif family would change the benchmark and must be labelled accordingly. No such follow-up was run, and no budget is silently extended.

Predictive value remains entirely open. A later matched comparison of market features, ordinary on-chain activity and graph features still requires source availability, historical coverage and temporal-feature admission before forecasting outcomes. This resource failure neither validates nor rejects that hypothesis. Zero strategies are validated.

## Preservation and verification

Execution source `82b92974606cedd43f787df4d4cfb86434232792` was committed and remotely verified before the attempt. The detached `/home/malecada/master_thesis/TradingAgents-onchain-motifs` checkout keeps that HEAD. The [charter](CHARTER.md), [gate](gates.json), [pre-execution review](PRE_EXECUTION_REVIEW.md), [guard receipt](resource.json), [failure closure](failure-closure.json), [import manifest](import-manifest.json) and [independent closure review](CLOSURE_REVIEW.md) preserve the boundary and evidence.

Preparation passed 117 graph/lifecycle tests; independent review also passed 117. The isolated checkout passed all 49 graph tests with its own locked Python3.13.13 runtime. The prior broad unchanged-core result of 2,060 tests and 81 subtests was inherited under review. Raphtory was added as a pinned optional dependency without changing existing dependency versions. Synthetic success does not override the observed real-data memory failure.

The source allowance1/1 and original prototype allowance2/2 remain unchanged, including the original 117-complete/2-unavailable prototype result. The motif attempt consumes its newly authorized cumulative3/3 allowance, importing the two prior distinct source/prototype claims once. No retry, new chain acquisition, price/model evaluation, paid resource, account action or background schedule occurred.
