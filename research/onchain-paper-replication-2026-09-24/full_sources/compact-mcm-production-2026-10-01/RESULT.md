# Compact required-graph MCM production — verification result

The current-owner compact dictionary now produces the exact required graph's
row-major float32 MCM using the unchanged admitted array kernel, compact pair
matching and durable score stream. Output publication and saved-byte admission
run under the same owner transition lock. Actual dictionary, graph, node order,
motif order, matching configuration, policy and source identities are bound.

Failure handling independently attempts owned cleanup once, propagates unresolved
cleanup as a fatal BaseException, retains the primary cause, poisons the owner,
and releases the transition lock. Ambiguous descriptors are never retried.
Partial attempts and all failed test evidence remain preserved.

| Evidence | Closed result |
|---|---|
| red01.log | 1 missing-module failure, 8 deselected, 47.05s |
| check01.log | 9 passed, 499.50s; original integration before cleanup corrections |
| publication-check01.log | 3 passed, 3 deselected, 79.54s; public wrapper regression |
| red02.log | 8 cleanup failures, 1.03s |
| cleanup-check01.log | 45 passed, 4.97s |
| check02.log | 3 passed, 7 deselected, 188.46s; positive, primary failure, nested fatal cleanup |
| red03.log | 6 failures, 18 deselected, 123.92s; PairLog and final producer descriptor |
| cleanup-check02.log | 59 passed, 1.44s; final primitive cleanup sources |
| check03.log | 4 passed, 9 deselected, 258.46s; final positive MCM, two final-descriptor failures, fatal log propagation |

All sessions are terminal. Source/test snapshots retain intermediate bytes.
No combined final-source 13-case producer suite is claimed. Synthetic fixtures
use tiny graphs, fresh temporary registrations and mocked guard surfaces. They
establish neither full-scale resource feasibility nor empirical model accuracy.
The output payload cap excludes parent graphs, dictionary/sample matrices,
matching/stream scratch, Python overhead and mapped-page RSS. Whole-workflow
physical accounting, graph feature publication, full calendar/exclusions,
representation closure, native handoff and empirical release remain pending.
Resource coverage remains 77/109; all 1,420 financial fits remain pending.
