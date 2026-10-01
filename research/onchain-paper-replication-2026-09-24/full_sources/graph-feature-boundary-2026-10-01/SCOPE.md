# Native graph feature to tensor boundary

This isolated engineering component converts already admitted native float32 MCM
and int64 edge arrays into independent CPU tensors matching the maintained graph
encoder interface. It preserves C-order feature identity, node/motif order and
edge order. No matching, neighborhood reconstruction, fitting, optimizer or raw
financial input is involved. It is not itself a provenance admission route.

An expected feature hash and caller-supplied combined lease are mandatory. Array
types/shapes, finite similarities in [0,1], endpoint ranges, exact hash and numeric
allowance are checked before tensor allocation. Leases surround conversion;
source layout/content and output content are rechecked before return. Outputs
are independent but mutable model inputs, not immutable admission receipts.

Numeric reservation is twice the combined source payload plus nine bytes per
validation/copy chunk entry: resident inputs, both output tensors and one int64
or float32 buffered chunk with a boolean comparison temporary. Iteration is in
bounded C-order contiguous blocks, including Fortran/negative-stride inputs.
Iterator/block references are released before the next array. The bound excludes
retained parent graph data, dictionary receipts, Python/allocator overhead and
model state/activations; it is not an RSS or aggregate workflow limit.

Existing feature_hash raises TypeError on shape (2,0) edge arrays when casting a
multidimensional zero-size memoryview. The derived boundary hashes the same
canonical metadata with an empty byte payload. Nonempty hashes agree with the
maintained utility; empty-edge support still needs an explicit downstream hashing
correction/integration. Frozen historical sources were not changed. Duplicate
edge and graph identity admission remain the responsibility of the graph route;
this converter validates endpoint ranges without sorting, deduplication or graph
semantics substitution.

red01: CLOSED five missing-component assertion failures, 0.002s, session20153,
exit1. check01: CLOSED five methods with two errors, 0.098s, session10211, exit1;
both errors arose in the fixture's existing feature_hash call on an empty array.
Original source/tests and log are preserved. The corrected fixture uses an
independent canonical-metadata/C-order-byte reference hash, retains maintained
nonempty hash comparisons and tests empty edges explicitly. The source also
releases block/iterator references before subsequent buffer allocations.

check02 terminal evidence and independent review are recorded alongside this
scope. Tests cover exact tensor values/types and independent storage, actual
GraphEncoder forward equivalence without training, layouts and empty edges,
preallocation budget/schema/value/hash refusals, lease/copy drift and owner-lease
failure. The GraphEncoder fixture uses two motif columns with otherwise frozen
model configuration; this is a synthetic interface check, not paper-scale proof.

Still required: actual registered owner/MCM ticket/graph/policy integration,
durable graph_complete publication and strict tensor/native storage admission,
exact graph/date/fold denominator and top-level representation reuse, empty-edge
hashing integration, aggregate/physical resource measurement and empirical
registration/amendments. No financial trial or resource admission follows here.
