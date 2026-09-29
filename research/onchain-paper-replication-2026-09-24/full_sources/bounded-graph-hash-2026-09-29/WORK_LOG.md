# Bounded graph identity serialization

Synthetic engineering continuation addressing the serialization portion of G1
in GRAPH_MEMORY_REVIEW. Preserve byte-for-byte canonical JSON identities while
bounding temporary lists for long edge rows and node-ID sequences. The original
GraphSnapshot copies, validation sets and eager population loading remain separate
unresolved allocations; this change alone cannot establish full-history capacity.

No empirical inputs, claims, configurations, dictionary outputs or held-out data
are changed. Tests independently compare the complete legacy canonical JSON hash
on ETH/BTC, empty arrays, long edge rows, long identity lists, wide feature rows,
Unicode/escaping and finite floating-point values. A serializer boundary probe
rejects lists exceeding1024 elements, exposing the current unbounded conversion.
Existing duplicate-edge validation must remain in force.

The new module was added after the activation neural01 command fixed its58-module
inventory. That run does not include these new tests. Production hashing is not
changed while that run is active.

Red01 retained three expected serializer-bound failures and11 passing identity/
validation controls. The corrected serializer streams flat arrays/tuples in
1024-element chunks and preserves separators, Unicode encoding and scalar JSON
formatting. All14 tests passed in the neighboring activation increment's
review-green01 (combined30passed/1CUDA skip). Full neural02 and independent
review are in progress. source-bindings.json records the exact source/tests.

## Final verification

Combined neural02 completed all59 onchain modules:498passed/2CUDA skips in
326.39test seconds; guard328.903s, peak sampled
821239808bytes, child0, no memory-limit events,
cleanup verified. All five corrected source/test bindings match. The newly
prepared graph-validation-memory test module is excluded from this fixed
59-module command and has its own evidence.

Independent review found no unresolved critical issue in the final increment.
No frozen scientific configuration, empirical claim or financial result changed.
Full-size capacity, GPU parity and full paper coverage remain unestablished.
