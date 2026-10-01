# Compact complete-calendar admission

Actual compact_training.Training is now joined to the registered calendar and
coverage inputs selected identically in the job and producer plan. The existing
source-admitted denominator validator retains every included/excluded date and
checks the required graph union, fold clocks and per-input graph availability.
Original graph, fold and example content is rechecked after live callbacks.
No sampling, numerical fitting, graph artifact publication or empirical job is
performed. Price-based exclusions remain recorded rather than independently
recomputed; full representation and price admission remain separate.

Independent review found CDEN1: configured lookback could expand date metadata
before an inconsistent row length was rejected. The corrected adapter checks
both admitted partitions are nonempty and every row's input date, price, graph
and availability length equals the requested lookback before the validator runs.
This interface accepts actual nonempty Training only; exclusion-only manifests
cannot bypass that preflight. Existing supplied rows and outer process bounds
remain prerequisites; this is not a full RSS or metadata-object budget.

| Retained log | Closed result |
|---|---|
| red01.log | 1 missing-module failure, 4 deselected, 15.81s |
| check01.log | 5 passed, 96.22s; original source before lookback correction |
| red02.log | 1 failure, 5 deselected, 21.35s; safe allocation-boundary trap reproduced CDEN1 |
| check02.log | 2 passed, 1 failed, 4 deselected, 60.65s; corrected positive/lookback pass; mutation fixture attempted a read-only write |
| check03.log | 1 passed, 1 failed, 5 deselected, 40.86s; read-only backing also rejected setflags before intended mutation |
| check04.log | 2 passed, 5 deselected, 41.52s; explicit original graph replacement detected at first and final callback |

Original source and test snapshots preserve all evidence. The first-callback
passes in check01/check03 alone are not evidence of actual graph mutation;
check04 supplies that coverage. No combined final seven-case run is claimed.
The final source's normal admission and bounded lookback behavior passed check02;
its original and final callback mutation checks passed check04. The synthetic
fixture accounts for 20 calendar days: two train, two test and 16 excluded dates.
Independent prices, complete feature/representation publication, native handoff,
whole-workflow resource accounting and committed resource release remain pending.
Coverage remains 77/109; all 1,420 financial fits remain pending.
