# One-day temporal motifs complete with the 8 GiB allowance

September 16, 2026. The user-authorized resource-only successor completed all five registered engineering cells and retained all 44 outputs. The same one-day computation is feasible in the tested environment: sampled peak process-tree RSS 2,648,379,392 bytes (2.4665 GiB), below the 8 GiB allowance. The original 2 GiB attempt remains failed and unchanged. The higher allowance is a cap, not a reservation or a measured requirement of 8 GiB.

| Measurement | Result |
|---|---:|
| Raw transaction rows | 1,101,465 |
| Eligible ordered events | 547,332 |
| Incident addresses / directed pairs | 381,191 / 443,937 |
| Nodes with any nonzero Local40 role | 20,831 (5.46%) |
| Whole guarded execution | 640.806 seconds |
| Decode/validate/order phase | 456.940 seconds |
| Bounded-oracle phase | 3.993 seconds |
| Graph-build phase | 1.412 seconds |
| Local-motif phase | 10.805 seconds |
| Export/summary phase | 155.165 seconds |
| Sampled peak / cap | 2.4665 / 8 GiB |
| Complete cells / retained outputs | 5 / 44 |

The phase timers include lifecycle publication and repeated provenance checks. In particular, the local-motif phase lasting 10.805 seconds starts before publication of graph-build.json, so it is not an isolated Raphtory call benchmark. Most elapsed time belongs to input/provenance and export processing. The guard interval of 640.806 seconds also includes lifecycle start/finish outside the execute interval of 628.315 seconds. Sampling every nominal 20 ms can miss brief peaks; no peak-RSS minimal-memory claim follows. Two logical CPUs and no elapsed/CPU-duration kill were retained.

The graph uses the same retained January 1, 2024 UTC Ethereum native positive-value successful transfers, exact 777 sentinel exclusions, integer Unix-second timestamps and explicit block/transaction event ordering. All three motif events must fall inside that day; the inclusive maximum span is 3600 seconds. No cross-midnight context, token/internal transfers, exact-wei data, new chain requests, price outcomes or financial evaluation were added.

The retained Local40 vectors contain 80,215,753 star occurrences, 104,736,340 two-node occurrences and 14,135 triangle occurrences: 184,966,228 unique ordered three-event occurrences. The 289,730,838 local role participations count two-node and triangle occurrences at multiple endpoints and are not another unique-motif total. Local roles are highly concentrated: one address contributes 90.39% of one star-role counter. These are engineering/data-description results, not significance or predictive evidence. Address roles are not entity identities.

All 39 vector shards are retained with ordered row fingerprint `c5d53b59076e5179a053867c41c9ebfd1fa2d67670ff08e240da805d228dcd26`. Input/order/pair fingerprints match the original attempt. The [import manifest](import-manifest.json) binds 50 byte-identical imported files: 46 run members (claim, complete receipt and 44 outputs) plus four runtime/preflight/resource records. Both execution and imported structural verifiers report complete, five cells, zero unavailable cells and 44 outputs.

Execution identity is `eth-temporal-motifs-8gib-20260916`, fixed source `713501b48a952d46c71d283fb6879baf601db4a7`, preserved detached checkout `/home/malecada/master_thesis/TradingAgents-onchain-motifs8gib`. The computation, dependency versions and 128 inputs are unchanged from the failed parent. The family retains prior_attempts 2 / original cap 3 and consumes its one reviewed +1, effective 4/4. The consolidated inventory now contains 41 local claims, not 41 independent hypotheses. No further attempt is implied.

The initial 8 GiB preparation failed metadata admission before any claim. Its original gate/certificate/review remain preserved. Version 2 corrects only amendment-policy scoping: every historical claim remains source-bound and contributes exposure history; strict single-amendment checks apply to the current mechanism, whose prior inventory, failed parent and no-chaining rule remain intact. Independent preparation passed 46 amendment/guard tests; isolated execution passed 17 motif/guard tests. The preceding 57 graph/guard tests and broad 2,060 tests + 81 subtests were inherited for unchanged components.

This establishes computational completion for one fixed day. Full-history scalability, historical availability/canonicality, useful features, incremental predictive value over ordinary activity, robust statistical validation and trading returns remain untested. The next research question is whether a causally available multi-day graph panel adds information beyond matched market/activity baselines; that requires separate dataset and evaluation admission, not extrapolation from this engineering success.

Independent [closure review](CLOSURE_REVIEW.md) and [machine-readable checks](independent-check.json) passed. The separate checker reconstructed all raw/order identities and six bounded subsets, reconciled every exported vector and summary, and independently recounted every full-day two-node vector. It did not repeat the production Local40 calculation. Full-day star and triangle counts retain the narrower synthetic/subset and role-conservation validation. Review took 26.96 seconds with 615,976,960 bytes sampled peak under the same 8 GiB/two-CPU/no-elapsed-kill guard.
