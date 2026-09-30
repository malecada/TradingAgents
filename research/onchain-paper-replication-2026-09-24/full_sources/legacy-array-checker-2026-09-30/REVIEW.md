# Independent isolated legacy array-checker review

Initial acceptance withheld for AC1 below. No additional material numerical blocker was identified in the inspected candidate. This review covers source and invented-fixture evidence only; it does not read empirical arrays or admit a metadata adapter, guarded execution or saved-graph reuse. Only this review was written; no tests/jobs, empirical arrays/raw bodies, frozen source or commits were changed or executed.

## AC1 — unexpected np.load container is not explicitly closed

At `arrays.py:132`, np.load is assigned directly into arrays. The subsequent isinstance(np.memmap) check at134 correctly refuses other objects, but cleanup at185–188 only closes their `_mmap`. A valid ZIP/NPZ container saved at an allowed `.npy` filename and rehashed into the supplied manifest makes np.load return an NpzFile. That object has a close() method and owned archive/file descriptors, but no `_mmap`, so rejection leaves its handle explicitly unclosed. It can remain retained through the exception traceback or a diagnostic reference; eventual garbage collection is not the claimed deterministic cleanup.

The installed NumPy source confirms the path: ZIP magic causes np.load to transfer its open file from ExitStack into NpzFile, whose close() is responsible for releasing it. Filename extension and allow_pickle=False do not prevent this container result. Reject unexpected magic/header before loading, or explicitly close every unexpected closeable result before refusal as well as every previously opened mapping. Keep malformed-file refusal and cleanup failures visible.

Add a rehashed disguised-NPZ fixture that updates the declared bytes, file hash and expected manifest hash, records the returned handle and requires it closed after refusal. This tests the real container boundary rather than a hash mismatch that prevents np.load. Also retain the existing successful and numerical-failure map-close checks. No runtime counterexample was executed by this review.

## Independently inspected behavior

The five-array algorithm preserves the accepted Graph10 verifier's independent canonical identity and numerical checks without importing production graph helpers. It verifies exact membership, declared file hashes and byte totals before mapping. The stronger same-device/single-link regular-file checks reject leaf symlinks and hardlinks, manifest size and total-array budgets are checked, and final directory membership/file signatures are rechecked. np.load uses read-only mappings and disables pickle; map payload extent must end at the declared file size, rejecting trailing bytes when reached. Duplicate JSON keys are refused.

The numerical checks cover sorted unique nonempty nodes, int64 directed-edge endpoints/order, float64 feature shapes, finite positive edge aggregates and integer counts, admitted/raw/exclusion conservation, log1p edge transforms and four independently reconstructed node features at1e-12 relative/absolute tolerance. Graph identity uses independently emitted canonical JSON. Empty edge populations remain governed by the caller's metadata admission; this source does not infer the historical graph's domain metadata validity from numerical conservation alone.

The finally block attempts all opened memmap closes on both success and error and surfaces cleanup failure. AC1 is the missing non-memmap resource case. As documented, serialization can materialize one entire edge-index row; total declared NPY bytes bound the input extent, not total Python/NumPy peak RAM. The future finite guard must still bound actual working memory. Stat checks detect ordinary file changes; exclusive stable ownership and fixed path/metadata admission remain necessary and are not supplied by this pure checker.

## Test evidence and limits

Closed green01.log records11passes in0.062seconds following11 missing-component failures in red01. Tests use invented two-node arrays and cover independent identity/count/features, unchanged files, declared-hash/extra-file refusal, rehashed feature corruption, count conservation, node ordering/endpoints, feature dtype/fractional counts, leaf links, pre-load budget refusal and mapping cleanup on both success and numerical failure. No suite was rerun during review.

The retained tests do not yet exercise disguised containers, failure midway through the load sequence, explicit cleanup-close failure, malformed NPY extent/header, late input mutation, duplicate JSON or chunk-boundary ordering. Those are verification gaps rather than additional demonstrated defects; AC1 is the concrete required correction. Tiny-fixture parity does not establish empirical array correctness, complete metadata/claim/source/coverage joins, peak resource feasibility or raw transaction/exclusion semantics.

| Initially inspected artifact | SHA-256 |
|---|---|
| arrays.py | `efd94aa49d46e336cdfb7f7db2179caea3bcc7bc94e90b2d33e596ef6901ea8c` |
| test_arrays.py | `5bc67d40a5899c69ae09d95d1e7ded690a3c14e14a705afdf172c28db7ef4b14` |
| green01.log | `72a92019676faed00dceab0be665ddc587431cc173b4bff7191a25538600102f` |
| red01.log | `5dc7d16dc6b6f894c61a30211a90377147243c9bf821cd9289098acbf0842d07` |

The active correction offline01 retains source0c100035b96b6e50cf9231d8b018eb67d0bcb2c1 and its existing freeze. This isolated review neither alters that closure nor authorizes a concurrent empirical verifier, source staging or a repeated identity.
