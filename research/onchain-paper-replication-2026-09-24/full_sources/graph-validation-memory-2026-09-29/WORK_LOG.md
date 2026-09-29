# Exact duplicate validation memory

Engineering continuation of G1. Replace full Python sets of node identities and
edge tuples with sorted adjacent comparisons. Edge sorting still has linear
NumPy index/workspace cost; the graph and its IDs remain resident. Compare sorted
edge endpoints in bounded blocks, retaining overlap across block boundaries.
Do not encode endpoint pairs by integer multiplication, which could overflow.
This is not an out-of-core validator or full-history capacity claim.

Synthetic tests compare the duplicate decision against an independent Python
pair-set oracle across signed/unsigned endpoint dtypes and input permutations,
exercise a duplicate at a large comparison boundary and Unicode node identity,
and refuse whole-graph Python set construction. No empirical inputs or frozen
configuration change. The preceding neural02 has a fixed59-module inventory;
this new module is separately verified and not included in that run.

Red01 retained1expected whole-set allocation failure and8 passing correctness
controls. Green01 passed81 focused graph, canonical-hash, ETH/BTC builder and
registered-producer tests in24.75s. Guard26.091s, peak sampled
110227456bytes, no memory events, child0/cleanup.

The separate measure01 guard completed the200,000-node/200,000-edge synthetic
duplicate-check diagnostic. Peak traced edge-check allocations were29,183,193
bytes for the old tuple set and3,701,120 for sorted block comparison; node checks
were12,583,176 and2,400,184 respectively. Inputs and all other validator/pipeline
allocations are excluded. Instrumented times are diagnostic only; no real-data
speedup or total RAM reduction is inferred. measure.py and measurement.json retain
the complete procedure/results; source-bindings.json binds implementation/tests.

Independent review is in progress. The preceding498-test neural result belongs
to the earlier contracts implementation; it is not reattributed to this change.

Independent REVIEW.md found no correctness defect and confirmed the focused
receipt. All source bindings remain unchanged. Both verification/measurement
guards are terminal and cleaned up. No empirical release follows.
