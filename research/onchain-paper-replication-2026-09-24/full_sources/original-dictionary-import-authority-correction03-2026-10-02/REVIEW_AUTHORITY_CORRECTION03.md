# Independent authority correction03 review

Disposition: **WITHHELD for complete imported authority/stage execution**. OIS1 is corrected. The new descriptor-owned metadata helper addresses the former inner read/write cleanup gap. Immediate owner inventory/token cleanup and the new resource journal's lifetime anchoring still require narrow corrections. This is not rejection of the corrected helper or authorization to change historical bytes.

Manifest03 SHA256 `ac57a45ce7acab0557cec192e842579b782ab23dbe2ad4c970162880cacf2f75` was independently verified: all23 listed files,160,745 bytes total, match their recorded sizes and hashes; all9 Python files parse without imports. Snapshot and patch source, implementation report, both RED records, ten final test methods and retained GREEN logs were read. Old OIP/OIS review findings and the import-stage contract remain applicable. Only this review file was written; no tests, source imports, numerical arrays, jobs, guard, claims, network, registrations or commits were executed.

## Remaining material findings

### OIA1 — Immediate imported-owner cleanup still replaces the first fatal

Locations: `compact_owner.py:48–63` (`_held`), `compact_owner.py:96–106` (`entries`), called by `original_import_stage.py:57` and its `complete_import` held scope, and by Owner.boundary/verify_current.

These two functions are AST-identical to withheld02. They are exercised by import construction/integrity and completion itself; they are not merely future MCM array or stream code.

`entries` enters the scandir iterator as a context manager and closes its directory through inherited `io._release`. A traversal MemoryError/SystemExit followed by iterator-close or directory-close failure can therefore be replaced by that later exception or a new CleanupFailure. The new import_metadata reader is not on this inventory path and cannot recover the original fatal after replacement.

`_held` always creates a new CleanupFailure when lock.release raises, regardless of an active body fatal or whether the release error is itself the first actual fatal. The original body/release error becomes at most a cause/note rather than the selected exact fatal. An import-body MemoryError followed by an ordinary release failure is a direct source-level counterexample to the claimed first-fatal contract. An ordinary body error followed by release MemoryError also selects the wrong object.

Correct these exact immediate boundaries, retaining the legacy route's behavior unless an independently reviewed shared correction is intentional. Own the iterator and directory separately; attempt independent closes once, retain the first actual fatal and earlier ordinary causes, and revoke/poison the held token on unresolved release. Include exact-source sentinels for traversal/iterator-close/fd-close and held body/release mixed ordinary/fatal order, plus the successful/refusal controls. No rerun of a historical authority or model identity is needed.

### OIA2 — Resource FeatureJournal failure sealing does not retain original namespace authority

Locations: `feature_journal.py:61–76,89–97`; compare `import_metadata.birth:72–80`.

The new resource constructor discards birth's original directory inode. `_publish` checks only that its supplied path.parent equals mutable self.directory, then the metadata helper anchors whichever directory currently occupies that path. It does not pin/rejoin the original resource role, journal path/inode or original owner/start bytes. `seal('failed')` does not call the genuine Binding or otherwise authenticate those originals.

Consequently replacing the consumed original journal directory with another regular directory before failure sealing passes the local path relation and within-operation root checks: failed.json can be published into the replacement namespace. Mutating journal.directory has the same problem; changing `_metadata_role` to None selects the inherited writer instead of preserving the original private opt-in. These source-level counterexamples concern the newly introduced resource metadata journal itself. They do not require numerical component publication.

Capture the resource journal's original path, birth inode, role and canonical owner/start/required-set identity before returning it. Require the original pins and metadata on each resource publication/seal, with final rejoin after callbacks/IO; preserve the consumed original namespace on refusal. A role's private naming is not a runtime lifetime pin. Add tiny resource-journal sentinels for root replacement, path/role/config mutation and failure sealing after a publication error, checking original bytes remain retained. Legacy journal defaults need not be redesigned.

## Corrections accepted at narrow source scope

`resource_binding.assert_selected` requires literal resource_only=True, exact registered job-input name and the Binding-recorded SHA. Calls now cover original.admit, its selection/lease, prepare and selection refresh, stage construction/integrity and attachment. This closes OIS1's same-descriptor A/B job mismatch. Actual typed Binding/source/runtime/guard authentication remains the genuine factory path; helper tests use an invented metadata object and do not execute that factory.

`import_metadata.write/read` avoids fdopen ownership transfer. Successfully acquired parent/child descriptors enter one final close boundary; exclusive/no-follow file access, regular/single-link/same-device checks, finite64KiB bodies, file and parent fsync for writes, descriptor/path signatures and within-operation parent rejoin are explicit. Failed child open closes the already acquired parent. The reused `_close_owned` is AST-identical to accepted original candidate03 and chooses actual fatal objects before ordinary uncertainty wrappers. This addresses the old delegated score_batches inner read/write problem. It does not make callers that retain other unsafe cleanup helpers fatal-safe.

Imported Owner metadata birth/read/closure and ImportStage intent/completion now select that helper. Matching-owner resource metadata snapshots and initial FeatureJournal owner/start/claim writes use it; resource fatal construction/bind errors are reraised rather than converted to ordinary JournalConstructionError. Genuine lifecycle/source/input/native-guard checks remain inherited and are not claimed exhaustively fault-injected here.

The original evidence pins, numeric-byte equality, explicit Dictionary.identity and original graph/array-object checks are AST-identical to corrected02. Original scientific dictionary/matching/order are kept distinct from current execution backend/source/runtime. Prebirth required-stage selection, typed imported-stage receipts, zero credited historical pairs and normal poison/terminal refusal remain source properties; no actual successful stage/capability was constructed in this review or these logs.

The private resource FeatureJournal opt-in intentionally rejects `__call__` numerical component publication. That explicit refusal is appropriate for this partial candidate; it does not complete scientific output publication. OIA2 requires the opt-in identity to remain the one originally selected.

## Evidence limits and next boundary

Final green-journal01 reports ten passing distinct methods. The tests compile selected AST with stdlib substitutions and tiny temporary files; source module imports are excluded, journal require_hash is stubbed, and Binding metadata uses SimpleNamespace. Initial RED records fail because the new selector/helper/journal seam was absent, not because the real old factory/complete imported stage was exercised. They establish helper behavior and the selected fake-context class path, not genuine admitted authority. The inventory and held-token failure combinations above are not among the ten methods. Repeated seven-check GREEN logs do not increase the final distinct denominator.

The exact correction should receive new immutable files/evidence and another source review. This review does not integrate withheld02, authority03 or typed-MCM03. Later compact MCM stage/score-stream/array/publication IO remains independently unproved, as stated in IMPLEMENTATION03. Genuine dispatcher/schema, complete installed-source/runtime closure, original26 Git-blob and full input/intent/sample/graph ancestry, checked targets/new dated kernel, resource terminal and a guarded genuine two-target fixture are still required. The fixture must prove revocation, retained first output on second-target failure, numeric identities/denominators and cumulative accounting using real authority.

No financial leakage, return/cashflow convention, fees/funding, exposure reuse, model result, full-size RAM or storage capacity was tested. All23 resource cells, nine MCM graph outputs, original32 motifs,1,420 financial fits and full score-tail retention remain in scope. The unresolved dispatcher/storage route cannot be replaced by a successful metadata helper or an unavailable-cell omission. No spent-sample, closed-identity or budget status changes follow.
