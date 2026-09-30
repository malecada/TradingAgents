# Exact induced-edge sizing component

The isolated engine measures every directed edge induced by the complete weak
one-hop neighborhood of each explicitly selected center. It includes the center,
reciprocal columns, duplicate columns and self-loops, and verifies the neighborhood
cardinality against the retained expected value. No scientific node ceiling is
changed, and no empirical graph was read during engineering.

Two source-edge scans per center produce membership and count induced edges.
Only a single N-byte boolean membership array is retained, plus bounded chunk
comparison/gather temporaries. The conservative numeric reservation is
N + 32*min(edge_chunk,E) + 16*number_of_centers + 65,536 bytes. It excludes input
residency, Python/runtime allocations and callback state. It is not a measured
RSS, runtime or complete graph-validation bound. Center count is explicitly
limited to 64 and edge chunks to 65,536. A guarded registered wrapper is required
for actual measurements, aggregate resource limits and durable failure ownership.

The callback receives a copy after each completed center. Exceptions propagate;
this component does not claim filesystem durability or same-identity recovery.
A wrapper must publish each checkpoint durably, retain all selected cells and
refuse any existing launch identity. The planned whole-job guard is 540 seconds.

Five synthetic tests passed in 0.019 seconds. An independent neighbor-set oracle
covers directed/reciprocal/duplicate/loop/isolate cases, fixed random graphs,
zero edges and a 10,002-node full hub without truncation. Additional cases check
numeric allowance refusal before allocation, invalid endpoints/centers/cardinality,
and callback failure after two retained progress callbacks. Red01 is a missing
module import failure. Independent source/evidence review accepted this isolated component for integration. No package integration or
empirical release is implied by this prototype.
