# Registered graph-production integration

Status: implemented and verified; independent correction findings closed. No empirical release.

The source-job interface now supports an explicitly registered `graphs` operation
with `{"plan_input":"registered_input_name"}`. A build plan binds one asset,
graph configuration input, complete Monday-to-Monday coverage, exact week list,
source-manifest input names and the ETH schema or BTC precision policy. A reuse
plan binds graph inputs, original source membership and their coverage proofs.
Every source and graph cell is retained, including unavailable outcomes.

Both assets use one validation ledger across the whole supplied stream. An
exclusive retained SQLite workspace commits consumed source members and their
counts atomically at verified decoder boundaries. Immutable receipts follow
commits; failure rolls back the uncommitted suffix and preserves the database.
Generator abandonment is failed, and the same workspace cannot be reopened.
A receipt does not authorize restarting a terminal claim or adopting its prefix.
A reviewed successor-copy/admission protocol remains required for that operation.

Before decoding, ETH member-interval unions and BTC daily partition unions must
cover every required week. Observing one transaction in a week does not establish
coverage. Each completed graph carries separate coverage evidence bound to its
manifest, plan and claim. This retains zero-row source files that naturally do
not appear in transaction-derived graph source hashes. Reuse verifies that
coverage proof and exact week/availability boundaries as well as array hashes;
it performs no decoder call or new cross-graph transaction validation.

BTC publication/reuse retains the outer exact-rational manifest, edge/incident
sidecars, integer fees and observed-chain-order qualification. Source-only work
does not import the neural runtime. Sealed graph outputs become explicit inputs
to a later population claim; no automatic fit follows graph publication.

Independent review found incomplete source-coverage admission and an omitted
reuse-end-boundary check in the initial increment. REVIEW.md preserves those
findings. Both have failing-before-fix regressions and passing focused corrections;
WORK_LOG.md and the guard directories retain all verification attempts, including
the deliberately stopped pre-fix offline01 run. Final source identities are in
source-bindings.json. No original scientific configuration was modified.

Still pending: partial SQLite-prefix continuation, full-history/canonical source
admission and cross-cohort reconciliation, bounded graph/feature/sampler residency,
GAT/device integration, large-neighborhood feasibility, measured working disk and
resource admission. Financial claim accounting remains24/51, with all1,420fits
pending. This increment does not establish full paper coverage or numerical
agreement. Raw stores, closed runs, failed artifacts and completed backup remain
unchanged.

## Final verification

The named offline02 target completed: 2,747 standard tests and97 subtests,
473 neural tests and one CUDA skip; 3,220 tests passed in total. Standard test
time1111.60s; neural362.40s. Guard elapsed1477.888s, peak sampled
2633498624bytes, child0, no memory-limit events,
cleanup verified. All seven source bindings still match. The separately
prepared activation-checkpointing module was added after neural collection and
is excluded from these57 neural modules; its own verification is separate.

REVIEW_CORRECTIONS.md independently closes P1/P2 with no new critical defect in
the correction delta. The final suite executes all26 current graph-production
and aggregation cases. No empirical release follows.
