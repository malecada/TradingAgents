# Independent review

Accepted for bounded current-owner compact graph artifact publication and saved tensor loading. The late-owner-revocation defect is corrected and the revised growth/value tests reach their intended boundaries. No remaining material blocker was identified in the reviewed scope. Source, test, raw log and hash inspection were performed independently; no tests, numerical jobs or empirical artifact replays were run by the reviewer.

## Publication and loading contract

The adapter consumes actual `compact_features.Features`, its current dictionary/MCM/required-graph ancestry, and the same registered graph-output input selected by both plan and job. It holds the owner transition lock. Per-required-graph logical output reservation includes the artifact allowance and three bounded metadata records; source array, original tensor and one readback payload must fit the separate `3*N` allowance. Exact native float32/int64 NPY headers, scalar/tree metadata and manifest size are preflighted before writing. The writer receives NumPy views and therefore emits the array-node subset supported by the explicitly source-admitted strict reader.

Publication's post-write manifest hash is not sufficient evidence on its own: before returning Published, the strict reader checks exact inventory, hashes, headers, aggregate extents and payload sizes, then actual loaded bytes are compared with the original admitted feature arrays. The valid changed-score regression writes a fully regenerated component with a finite in-range wrong value and reaches the exact numeric-byte mismatch. It therefore proves this value join rather than only malformed-file refusal.

Later loads retain the admitted artifact hash/lineage, repeat strict admission, and construct CPU tensors sharing only the newly read arrays, independently of the original feature tensors. Loaded checks enforce dtype, device, contiguity, no-grad and the shape/value feature identity. Published/Loaded full checks rejoin original ancestry and saved component content after the last callback; checking an existing Loaded receipt does not create another full graph payload. Tensor contents remain mutable and their checks must be respected by future consumers.

Exclusive namespaces, original inode joins and exact directory membership prevent silent retry or adoption of partial publication. Failures retain partial/complete evidence and poison the owner. Explicit new-adapter descriptor cleanup uses the fatal storage helper and guarantees transition-lock release. This does not claim exhaustive fault injection of every inherited generic I/O close path.

## Late-owner defect and correction

The initial adapter could return after a final Loaded lease invoked the original successfully and then poisoned its owner. Numerical/component evidence alone did not repeat owner admission. `red02.log` reproduces the accepted revoked owner.

`compact_owner.verify_current` now provides the required callback-free final check, and artifact `_original` invokes it after live callbacks. It checks actual Owner/Binding/run identity, poisoned/closed/closing state, configuration and reservation pins, active claim and run terminal markers including dangling symlinks, exact first-owner parent inventory, bound metadata, compact root inode/path/device/owner bytes/exact inventory, stage intents and cumulative reservation. Bound metadata path/hash inventory is included in the construction-time Binding pin, so clearing `_snapshots` cannot weaken this final verification. No Owner/Binding lease or guard callback is invoked by the helper. The preceding live guard remains necessary; the filesystem contract is sampled rather than atomic.

## Evidence inspected

| Log | Observed terminal result | Qualification |
| --- | --- | --- |
| `red01.log` | 1 failed, 5 deselected, 81.27 s | Missing implementation only. |
| `check01.log` | 5 passed, 1 failed, 568.26 s | Initial positive, route/budget, partial writer and saved-inventory checks. Growth injection failed at nonresizable tensor storage and did not prove changed-size refusal. |
| `red02.log` | 1 failed, 7 deselected, 97.43 s | Actual final Loaded callback poisoned the owner but publication returned. |
| `owner-check01.log` | 12 passed, 139.19 s | Actual registered owner helper, forbidden external leases and terminal/foreign/configuration/reservation/snapshot/dangling-run/other-owner refusals. |
| `check02.log` | 5 passed, 4 deselected, 402.73 s | Final positive/readback, actual post-sizing growth, valid rehashed wrong value, final owner revocation and pure empty-edge encoding/readback. |

The corrected growth test uses `Tensor.set_` and asserts actual `(100,100)` shape while proving the component writer was not called. The saved-inventory injection only proves orphan-entry refusal, not original tensor mutation. The empty-edge case is a pure serializer/strict-reader check, not a complete registered zero-edge production run. There was no combined final nine-case artifact suite. Earlier retained cases and final targeted cases are reported separately.

## Limits

These are tiny synthetic registered fixtures with mocked guard surfaces. The adapter performs no learned encoder training/detachment. It does not establish complete calendar or price-label validity, representation publication/sealing, native dispatch, cold/historical reuse, full-size resource feasibility or empirical admission.

The `3*N` allowance is per admitted publication/load, not a total live-storage tracker. Repeated retained Loaded receipts, parent attributes beyond counted MCM/edges, dictionary/sample residency, provenance readbacks, I/O and validation scratch, Python objects, model state and RSS remain excluded. Logical output allowance is not a physical filesystem quota or inter-write growth guarantee. Arbitrary caller-expanded tensor storage/aliases require separate lifetime accounting.

## Final direct SHA-256 bindings

- `compact_graph_artifacts.py`: `fd1395b0c274b1b51dc26365fd0c2954f904492cf77ddb3d553ce40c6dc6bf8a`
- `compact_owner.py`: `f9b84224a97acb7f1c78665799376b37cd324077024b0ac7fe5c6933da08c13b`
- `test_compact_graph_artifacts.py`: `66c1ac382a7d9b19de3aab1b7c505f26ab09c19ce6c527c10da865aa327736a0`
- `test_compact_owner_final.py`: `5873a34b54f95828382505d8eab84e4ab2227ca04695ca3c124161bdee578a22`
- `check02.log`: `81ee7c47bbc1a5f62c84d4bdecc92ab84f685fe6094417f200c9eea09d7c72f5`
- `owner-check01.log`: `9ea05404661327781113151c2e059ece0cf61ae0dc16e5334d3bb7830329c438`

These direct reviewed-file hashes are not a complete transitive execution-source manifest.
