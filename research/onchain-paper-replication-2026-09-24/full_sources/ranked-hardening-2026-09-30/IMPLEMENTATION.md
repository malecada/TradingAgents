# Isolated stable-ranking hardening prototype

The accepted full synthetic profile attributed 238.23 seconds to remaining
hardening scans, compared with 17.82 seconds to annealing. Its actual overlap with
storage06 prevents interpreting those as isolated performance. This prototype
changes only the implementation of fixed-matrix greedy hardening: cast real
values to float64 exactly as the reference, negate in place, use stable ascending
sort, then select entries whose row and column have not been used.

Proof of equivalence on the supported domain: the first admissible entry in the
fixed descending-value, ascending-row-major-index order is precisely the global
maximum remaining after masking used rows and columns. Induction over selected
pairs gives the reference sequence, including equal-value and signed-zero ties.
Finite inputs are required; integer comparisons occur after the float64 cast.
No alternative assignment optimizer, scientific pair limit or model is introduced.

Domain is explicitly narrower: existing two-dimensional NumPy arrays with real
bool/integer/float dtypes no larger than eight bytes. Complex, object and wider
real dtypes are refused. Nonfinite values are refused after casting. This matches
the intended float64 soft matrices; broader reference inputs are not claimed.

The numeric explicit allocation allowance is
(9 + sizeof(intp))*n*m + n + m + 16*min(n,m): float64 key, stable index order,
conservatively co-counted finite boolean scratch, used-axis masks and int64 pairs.
The input, Python interpreter/iteration objects, allocator overhead and native
NumPy stable-sort workspace are excluded. This is not a process memory bound.
At the original four-million pair cap, shape2000-square uses68,036,000 explicitly
accounted bytes on the pinned64-bit runtime. No capacity-size run has occurred.

Four small synthetic tests pass (green01.log), covering96 deterministic/random
fixture matrices, exact assignment parity, pair/tie sequence, unchanged input,
pre-sort capacity rejection, unsupported/nonfinite inputs and exact allowance
boundary. red01.log retains the prior missing-module failure. The existing full
offline suite is not rerun for this isolated artifact; production is unchanged.

This function is atomic and has no checkpoint/resume interface. Stable sort is
also atomic. Interrupted results must be discarded; it cannot replace the
reviewed resumable production candidate. Next requirements are independent code
review, bounded capacity-scale synthetic measurement under a new identity and
explicit process guard, and separately reviewed checkpoint integration before
any production use. Existing profiles and empirical jobs must not be rerun.
