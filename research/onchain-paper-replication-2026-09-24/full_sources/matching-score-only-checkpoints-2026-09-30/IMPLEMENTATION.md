# Isolated score-only composite finalization

result_only.py composes the accepted composite checkpoint state and accepted
sparse scalar objective. A completed state produces the existing small MatchScore
container, with Python float64-reference score, iteration count and convergence
label. It does not call the composite dense result path, allocate an n-by-m hard
assignment or return/copy M. Production dispatch and all scientific capacities
remain unchanged. Reusing MatchScore does not imply the accelerated Torch
reduction or its float32 score conversion has been adopted.

The new numeric allowance is 80 times the number of selected pairs plus 32 times
the smaller of the right-edge count and chunk_edges. It reserves 16 bytes per
pair for the adapter's new int64 pair matrix and the sparse scorer's established
64-per-pair plus 32-per-edge-chunk scratch allowance. The chunk size is positive
and at most 65,536. This is a component allowance, not total process RAM: retained
V/M/Q, graph inputs, composite validation scans, Python objects and native/runtime
allocations are excluded. No empirical resource measurement is claimed.

The accepted sparse score drops zero-weight node and edge terms while preserving
nonzero scalar agreement and math.fsum reductions. Its conservative representable-
agreement envelope remains required and may reject finite inputs accepted by
other paths. It is not silently substituted for the accelerated matcher. Input
validation, identity hashing, sparse traversal/final summation and finalization
remain atomic; this change does not add scoring checkpoints or a wall-time bound.
State is read-only to this adapter. Finalization failure leaves a valid completed
checkpoint available; it does not advance or poison the matching state.

Three synthetic tests pass in 0.026 seconds in green01.log, following three
expected missing-interface assertion failures in red01.log. Three tiny graph
pairs exercise directed reciprocal/self-loop inputs, tied zero-edge graphs and
a single column. Scores, iteration counts and convergence match the literal
reference exactly. Dense result/score/allocation paths are blocked during the
adapter call; no assignment attributes are returned and M bytes/readonly state
remain unchanged. An incomplete state and insufficient allowance are rejected;
the latter before pair-array allocation. Original capacity checks remain active.
A stubbed sparse-component refusal checks error propagation only; it is not a
new domain-boundary proof. Existing accepted sparse-domain tests remain evidence
for the unchanged component. No empirical body was read and no fit occurred.

Independent review is pending. Full production integration, execution-policy and
cache identity, checkpoint ownership, capacities and bounded empirical pilots
remain required. The preceding full offline suite is not rerun: all its 163
production/source bindings are unchanged, and the new isolated adapter is covered
only by the focused synthetic checks stated above.
