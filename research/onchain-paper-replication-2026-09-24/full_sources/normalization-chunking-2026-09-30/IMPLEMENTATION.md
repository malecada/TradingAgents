# Isolated normalization safe points

The existing scalar annealing prototype normalizes the full dense matrix in one
atomic step. This independent module implements scale, full-width row blocks,
column blocks and exponentiation as separate operations with successful-return
safe points. It does not change the registered solver or scientific configuration.

The first synthetic diagnostic found 28 exact-value mismatches in 288 cases when
column blocks were normalized naively. The largest column-reduction difference
was approximately 2.66e-15. These random inputs included negative Q entries, so
the diagnostic rejects unconditional equivalence without itself establishing a
reachable annealing counterexample. Its `bitwise` field names mean array_equal,
which does not distinguish signed zero. Original probe bytes remain unchanged.

Pinned SciPy separates maxima and uses log1p in its reduction. A singleton
column block can change the reduction axis from strided to contiguous. The second
probe duplicates singleton columns for C-order references with multiple columns,
then discards the duplicate result. It retains a true singleton when the original
matrix has only one column. Across 1,152 synthetic cases, all 576 C-order cases
matched by exact value; 45 of 576 F-order column/output cases differed, and 16
F-order row cases differed. These observations motivate a strict C-order contract;
they are not a universal equivalence proof.

The implemented state machine accepts finite nonnegative C-order float64 Q and
positive finite temperature, rejecting scaled overflow. Q must remain frozen by
the caller. It produces one new dense output, costing 8*n*m retained bytes in
addition to Q and other caller state. A numeric call-size allowance bounds native
reduction input elements, including the duplicated singleton, but SciPy creates
several additional temporaries. It is not a peak-RSS or wall-duration bound.
Creation includes full validation and dense allocation. No measured full-size
memory or speed improvement is claimed.

Four synthetic tests pass, including 60 nonnegative random/zero/tie cases whose
final dtype-compatible output bytes equal the original full-matrix SciPy formula.
They advance one block at a time, cover all four phases, reject inadequate
capacity and F-order layout before output allocation, preserve Q, and inject an
exception after a scaling write. An escaping exception poisons scratch state;
advancement refuses it. Saved red evidence is a missing-module import failure,
not four behavioral counterexamples.

This module has no durable save/load, source identity, production owner, admission
or cache integration. Only states produced by create are supported; caller edits
or input mutation are outside its contract. It must be integrated after all edge
updates, which still read the old M. Existing checkpoint evidence, the scalar and
Torch implementations, capacity limits and every empirical outcome remain
unchanged. Further integration must retain exact operation order, freeze inputs,
validate durable checkpoint identities and measure resources under a guard.
