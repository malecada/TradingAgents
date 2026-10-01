# Independent component review

Accepted for the stated native-array to independent CPU-tensor conversion boundary. No material blocker was identified in the reviewed source and saved synthetic evidence. This component is not an owner/provenance admission route, publication step or empirical release.

## Source and evidence

All 89 declared bindings match current bytes. Manifest SHA-256: `e121fb7ec19f6b8ed40df9d30fa47792faf88d8d26d9b92dd1d7fde4a9e2929a`. The inventory binds the declared sources and evidence; it is not a complete empirical execution closure.

- `boundary.py`: `792deafa7270a686c923dcd2f6b26bf16de14d1a86608bda620c608d1e4c20c5`.
- `test_boundary.py`: `cc82bec5d46158ea06ae9b2d6abcf9e5ae36b450899077d131eef795f61153aa`.
- `check02.log`: `97b5b95c93375e26e2e771d9ebae166f7fd6af775793df4d6ff3cadfcc1f5dae`.

The saved corrected log reports five methods passing in 0.025 seconds. The missing-component red evidence, original two-error run and its exact source/test snapshots remain preserved. No tests were rerun for this review.

## Assessed contract

The converter requires exact native float32 nonempty MCM and int64 two-row edge arrays, an explicit expected hash, an explicit positive numeric bound and a callable lease. It checks score finiteness/range, endpoint range and input hash before tensor allocation. CPU tensors have independent storage, fixed float32/int64 types and no gradient requirement. The conversion preserves source node/motif order and directed edge-column order.

Hash inspection confirms the same sorted dictionary keys, canonical shape/dtype metadata and C-order payload sequence used by maintained `feature_hash` for nonempty arrays. Buffered iteration requests contiguous bounded chunks, allowing Fortran and negative-stride inputs without a whole contiguous input copy. The output hash is checked separately after source layout/content checks and the post-copy lease.

The numeric formula counts both source payloads and both tensor payloads plus one maximum-width int64 chunk and one boolean comparison chunk: `2 * (mcm.nbytes + edge_index.nbytes) + 9 * chunk_entries`. It is checked before allocation. Block and iterator references are explicitly released before subsequent array iteration. Remaining tensor/NumPy aliases refer to already counted output storage. This reasoning supports the stated numeric subset; it is not a measured allocator or process-memory bound.

The tests exercise the exact one-byte budget boundary, schema/dtype/value/hash refusals before mocked tensor allocation, explicit lease failure, source drift during copying and the post-copy lease, independent storage, output hash identity and noncontiguous layouts. Actual GraphEncoder forward outputs equal the independently constructed tensor reference without training. That fixture uses two MCM columns and otherwise the recorded model configuration; it does not establish paper-scale capacity or training behavior. Scratch peak and allocator/RSS behavior are not directly measured by these tests.

## Explicit unresolved integration

Maintained `evaluation.py:149` cannot cast the multidimensional empty-edge memoryview. The original fixture errors confirm that limitation. The corrected test uses an independent canonical-metadata/C-order-byte reference for empty payloads and retains maintained hash comparisons for nonempty arrays. The derived boundary's empty-edge identity is therefore explicit, while compatibility with the existing downstream hash utility remains unresolved. This acceptance must not be reported as having repaired that maintained utility.

Returned tensors are intentionally mutable model inputs, not immutable admitted receipts. The caller must supply the actual combined owner/source lease and independently admitted graph/MCM identity. Duplicate edges, graph semantics, exact date/fold denominators, durable graph completion, top-level reuse and historical continuation are not verified here. Parent graph/dictionary residency, Python and allocator overhead, model state/activations, aggregate workflow limits and physical resource admission remain excluded. Repeated checks do not create an atomic snapshot against continuous mutation.

Review activity was limited to source, compact logs and declared compact-file hashes. No test, historical job, financial experiment or empirical numerical-array/raw-body read was performed. No scientific configuration, empirical budget or historical result was changed.
