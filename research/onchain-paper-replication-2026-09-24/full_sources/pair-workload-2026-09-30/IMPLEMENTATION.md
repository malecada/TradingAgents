# Exact directional matching workloads — isolated candidate

This candidate derives dictionary and MCM matching purposes from their actual
algorithmic loop membership. It does not accept caller-selected pair purposes.
The dictionary retains scalar bidirectional averaging, original-index tie order,
PCG64 partition advancement, hierarchical membership expansion and medoids.
Each purpose binds the workflow, explicit scalar backend, configuration, sample
identity plus typed graph contents, ordered sample indices and current block
(indices, expanded owners, level/partition, RNG state and hierarchy prefix).
Complete distance matrices for an already encountered ordered subset are shared,
matching the existing scalar dictionary implementation's matrix cache.

MCM purposes bind graph and node ordering, dictionary identity and ordered
representatives, center index/ID and motif index. Scores remain float64 through
dictionary distance averaging; MCM assigns each completed scalar once to its
float32 output cell. Missing results are never encoded as a numeric zero. The
callback's exact completed-pair map supplies the intended validity mask; the
matrix is returned only after every cell has a completed result. Replay derives
the same requests from the original seed and inputs, allowing the callback to
reuse an exact completion rather than enter a solver again.

The callback must return an explicit purpose hash and finite scalar similarity in [0,1]. This verifies
a join, not the truth of the score or durable publication. No reference is loaded
by this driver. The admitted pair/journal adapter must establish source/runtime,
current owner/lease, failed ancestry/death, exact reference/extent/body integrity,
orphan reconciliation and workflow quotas before computation or reuse. The
candidate is intentionally outside the running offline suite's frozen closure.
It has no empirical consumer, no registration admission and no resource-fit claim.
The simple in-memory NeighborhoodIndex is retained here for tiny tests; production
routing must integrate the already reviewed bounded array index policy before
large-graph use. The matrix ceiling counts cumulative retained dictionary entries
or full MCM entries; it does not bound total process RAM or graph/index allocations.

The output dictionary intentionally has a distinct identity: its configuration
contains pair_execution with the full explicit backend, and matching_config_hash
binds configuration plus backend. Existing accelerated consumers refuse this new
matching hash. No existing artifacts are reinterpreted or historical defaults
changed. Registered cache/descriptor routing still needs composition.

Eleven tiny tests pass in green01.log (0.335s), following eleven missing-module
failures in red01.log. Tests compare every full distance matrix, hierarchy,
membership and representative with the existing scalar oracle; compare restarted
request/computation order after the first direction; verify MCM values, reversed
motif order, valid-zero partial-row replay, incompatible source-independent
workflow/config/backend purposes, invalid callback joins and pre-pair capacity
refusal. The score store is explicitly a test-only in-memory cache backed by
match_reference, not PairSession, FeatureJournal, registered ResearchRun or a
crash-durable recovery test. It does not prove ranked-backend numerical parity,
actual interrupted checkpoint continuation or complete-feature reuse.

No frozen source, current named test membership, HEAD, historical result or
empirical budget changed. Maintained owner offline01 has separately reported
failures and remains running; its final diagnostics and closure take precedence
before maintained implementation proceeds.

Independent review identified W1: accepting any finite double allowed overflow
when assigned to float32 MCM (and overflow in bidirectional addition). red02
records dictionary-side failures; red03 independently exercises both consumers
and records eight counterexample failures, including the MCM overflow warning.
The callback boundary now refuses scores outside [0,1] before averaging or
float32 conversion. This range is implied by the normalized nonnegative scalar
similarity, not an accuracy filter or test-result tuning. Pre-fix code/tests/docs
and the original bindings remain preserved. green02 records12 passing tests
in0.391s. No
maintained source or frozen binding changed.
