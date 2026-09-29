# Independent review of graph-production corrections

Status: **P1 and P2 resolved in the inspected source; no new critical defect
identified in this correction delta.** This closes the two implementation
findings in `REVIEW.md`, whose original contents and initial source identities
remain unchanged. This is not empirical release or full-suite verification.

All seven source/test SHA256 values were independently recomputed and match
`source-bindings.json`. The corrected producer is
`ef5ee5e2c8f6438e4e334d1a468397ad6f60e176d157e7849b7132737c7c85e8`;
the current producer test file is
`a7ee4c9a34119b6fb6f34c552637fb99a4293f2b62c18d3c069327244cd49bf7`.
The other five reviewed implementation/test files retain their initial hashes.

## Finding closure

**P1 — complete source coverage:** resolved.
`graph_production.py:67–108` reads registered source manifests before decoding.
ETH member intervals must cover their source interval, their declared counts
must reconcile, and each member must lie within planned coverage. BTC partitions
contribute their declared full UTC day. The combined member interval union must
cover every planned interval. Therefore the original counterexample—one source
day per week with the other twelve days missing—fails before any graph is built.
The caught failure still generates the complete registered unavailable-cell
denominator. The positive BTC fixture now supplies fourteen daily partitions,
including twelve explicit zero-row files, rather than silently omitting those
days. The negative test retains one populated day in each week and checks that
both assets are refused for insufficient coverage.

**P2 — exact reused week and publication boundary:** resolved.
`graph_production.py:179–185` requires the graph end to equal the registered
Monday start plus seven days and publication to be at least one day after the
end. The original short-week counterexample is rejected despite consistent
graph and array hashes. Later publication is accepted without rewriting either
the graph or its metadata. The regression asserts an interval-specific rejection
for a shortened graph and an early publication, and preserves an independent
valid weekly cell. Long-week and delayed-publication cases are not explicitly
executed by the inspected tests; the equality/lower-bound checks establish their
intended behavior by inspection.

## Coverage-proof follow-through

Build output now includes a separate immutable `coverage.json` whose membership
contains every overlapping admitted source interval, including zero-row
members. It binds asset, exact graph period, configuration, graph manifest,
original claim and plan hashes. The complete graph disposition carries the
coverage file's path and SHA256. Publication occurs before the complete cell is
recorded, so failure to seal the proof does not admit that graph cell.

Reuse requires `coverage_input` as a registered, hash-checked input. The validator
at `graph_production.py:112–138` rejects the wrong graph identity, missing coverage,
duplicate source hashes, invalid intervals/counts, or a graph event-source hash
absent from the proof. This preserves the distinction between event-bearing
`graph.source_hashes` and the complete source calendar. A zero-row source is
therefore retained in the coverage proof even though it contributes no graph
event hash. Decoder sentinels remain in the actual reuse tests.

The proof is admitted provenance, not an independent audit of original provider
completeness. Its claim/plan hashes are structurally checked; the reuse validator
does not itself reopen and audit the originating claim, source manifests or raw
data. Legacy pilot graphs without this proof require separately reviewed
admission evidence. Subsequent population admission remains separate; this
delta does not add mandatory coverage-proof verification to the population
producer. No broader downstream or canonical-chain guarantee is asserted.

## Saved regression evidence

The reviewer read the four guard terminals and child logs without executing any
tests. `review-red01` retains four failing counterexamples; `review-green01`
retains sixteen passing tests. `coverage-red01` retains two failures for absent
coverage output; `coverage-green01` retains twenty-two passing tests. Both green
guards record child exit zero, verified cleanup and no memory events. Both red
guards record expected child exit one and verified cleanup.

The current test source expands reuse across `coverage_fault=None`, `gap` and
`wrong_graph` for both assets: twenty producer cases plus six aggregation cases,
twenty-six total. The twenty-two-test `coverage-green01` log therefore does not
prove execution of all current cases. Its result is retained as evidence for the
earlier focused snapshot; the active `offline02` run was not operated or judged
by this review. No full-suite pass is claimed here.

No tests, real raw reads, array loads, empirical decoding, network calls,
financial experiments, registrations or ledger writes were performed by the
reviewer. Source files and `REVIEW.md` were not edited. Remaining resource,
power-loss, continuation, historical availability, full-history source truth,
empirical accuracy and profitability limits in the initial review remain.
