# Exact pair-workspace implications

The completed cardinality census establishes a largest complete weak one-hop
neighborhood of 701,309 nodes in the selected retained week. Under the current
4,000,000 pair-entry ceiling, matching that neighborhood is admitted only when
the opposite motif has at most five nodes. No actual motif-size distribution or
test outcome is inferred here. The 35 oversized neighborhoods remain required.

| Opposite nodes | Pair entries | One float64 matrix (bytes) | Current pair cap |
|---:|---:|---:|:---|
| 1 | 701,309 | 5,610,472 | within |
| 5 | 3,506,545 | 28,052,360 | within |
| 6 | 4,207,854 | 33,662,832 | exceeds |
| 32 | 22,441,888 | 179,535,104 | exceeds |
| 100 | 70,130,900 | 561,047,200 | exceeds |
| 1,000 | 701,309,000 | 5,610,472,000 | exceeds |
| 10,000 | 7,013,090,000 | 56,104,720,000 | exceeds |
| 701,309 | 491,834,313,481 | 3,934,674,507,848 | exceeds |

The final row is a conditional maximum-by-maximum pair, not evidence that such
a pair occurs in the admitted dictionary or MCM. Each row counts just one dense
float64 matrix; the iterative solvers retain several matrices and additional
normalization/edge-product/input/output buffers. These values are neither peak
RSS nor hardware purchase recommendations. The accepted sparse hardening and
score-only output work does not remove dense iterative V/M/Q/log-state.

The next resource claim measures exact induced edges for all 35 oversized centers,
which determines another missing dimension of pair workload. Production changes
must preserve full membership and the literal matching arithmetic, including
tie/reduction order where claimed. Tiling, recomputation or external arrays need
bounded workspace and durable intra-solver state with synthetic continuation
equivalence. GPU use alone does not prove these memory shapes are admissible.

The existing neighborhood and pair ceilings remain frozen. Because they are part
of current configuration/cache identities, a future execution-capacity change
needs an explicit prospective lineage and independent compatibility review. No
silent cap increase, neighborhood truncation, motif downsampling, reuse under a
different identity or test-driven tuning is authorized by this arithmetic note.
All original resource, asset/history and comparison requirements remain pending
unless separately closed by retained evidence.
