# Independent refusal04 source review

Disposition: narrow parser correction accepted at source level; genuine oracle and execution readiness WITHHELD.

Reviewed immutable manifest `3458e6ea025ae5c0e510eb96a0d6ca9371ca6f933d54147167edc7f2cf2fac09` (31 files, four dependencies), inventory `3c1472b172bf72bb67f1e502be3f591db8043e2ec6d80e618fed01f139cc74bd` (163 source entries), and helper `fb563b56b8f9d51c06d6f585349d5ab3bbdd7cf7f711be7a3cc21b0d582aa456`. All manifest bodies/dependencies and all 163 inventory origins were independently size/hash checked. All 13 formula pins match their inventory selections. Prior03 and every frozen body remain unchanged.

## Blocking finding: oracle and primary constructor limits are inconsistent

`guarded_formula_oracle04.py` selects `ArrayNeighborhoodIndex(graph, max_buffer_bytes=1048576, edge_chunk=65536)`. The pinned actual constructor computes:

    16*(e+n+1) + 16*e + 40*(n+1) + 4*n
      + edge_chunk*(64 + 2*node_width + 2*edge_width)

With the admitted float64 widths 4 and 2, the two-node/two-edge graph requires 10,486,000 bytes, exceeding the selected 1,048,576 bytes. The full edge_chunk is charged, with no min(edge count, edge_chunk). The constructor therefore refuses before graph hashing, array-index allocation or any of the proposed 64 comparisons. The oracle cannot currently be presented as a runnable genuine proof seam.

At the coordinator's explicit request, the same read-only source path was checked in frozen `original-import-native-successor-preparation03-2026-10-03/capsule02`. Its actual imported_kernel.py passes the numeric policy fields directly. Both success and second_target_publication_failure policies select the same 1 MiB/65536 combination; the two/three-node graphs require 10,486,000/10,486,092 bytes. This is also a known deterministic refusal in the primary source path. No primary source, policy or CAP03 was modified. A fresh recorded preclaim source/policy amendment and review are necessary before launch. No buffer increase or numerical-policy change is authorized by this review.

`review_buffer_counterexample01.py` extracts and evaluates the actual constructor's scalar AST, importing no arrays or package. `review-buffer01.log` records both values. This arithmetic is source evidence, not an executed numerical failure, spent claim, OS measurement or capacity result.

## Parser assessment

The previous arbitrary purpose/pair vulnerability is corrected. The actual parser independently derives row-major center-by-original-motif identities from registered tiny target bytes, original dictionary evidence, matching configuration, authenticated owner context, backend and pinned numerical component bodies. Both begin and completion records must equal the expected ordinal's identities; coherent rehashing of the event chain alone no longer suffices.

The safe NPY reader is restricted to exact two-node Unicode IDs, little-endian float64 features/int64 endpoints, C ordering, finite values, bounded dimensions and 65536-byte bodies. Member extent/hash and registration joins precede reconstruction of the complete weekly graph record. Its metadata remains covered by the original graph hash and registration; it is not newly inferred scientific metadata.

Read-only comparison with the selected ArrayNeighborhoodIndex confirms undirected hop expansion, ascending selected global nodes, refusal rather than capacity truncation, retained induced directed edges, and final original edge-column ordering via keep.sort. Feature values, center and parent identities remain unchanged. The local typed identity matches the original framing, ASCII JSON, dtype/shape/byte extents and little-endian C bytes. Purpose uses cache_key UTF-8 canonical JSON without a newline; annealing and outer pair identities use their separate ASCII-escaped newline-terminated serialization. Context, backend and all five numerical-component hashes remain included. No simplified matching algorithm is introduced.

The raw parser remains supplementary to the mandatory real source/runtime/native verifier. Its successful recognition of fabricated retained-format fixtures grants no genuine Binding, Owner, ResearchRun, numerical or scientific completion authority.

## Independent checks and limits

- Re-executed unchanged resealing corpus against actual03: six expected failures reproduced (purpose, pair, both, swapped roles, different motif and different center). `review-predecessor01.log` retains exit 1 and exact failures.
- Re-executed actual04 suite: all 15 methods pass, recorded in `review-current01.log`. The suite explicitly checks absence of numerical/package imports.
- Independently checked all 163 source bodies and 13 formula pins, and 96 finite metadata neighborhood cases spanning all directed two-node edge subsets, self-loops, reversed column order, both centers and three hop depths. `review-independent01.log` records the result. These are scalar/list synthetic records, not NumPy arrays or empirical outcomes.
- Actual-source constructor arithmetic reproduces the deterministic buffer conflict described above.

No numerical imports, array-library execution, genuine guards/jobs/claims, registration edits, live edits, network, commits or STATE changes were performed. The missing genuine oracle proof, all 27 variants across 16 classes, four preclaim cases, at most 23 claims, 17 Owners and 19 journal groups remain pending. This narrow parser acceptance does not admit those attempts, alter frozen CAP03, establish native cleanup, financial-fit readiness, paper agreement or memory savings.
