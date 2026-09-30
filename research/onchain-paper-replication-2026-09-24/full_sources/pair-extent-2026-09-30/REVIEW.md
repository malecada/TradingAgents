# Independent pair extent review

The corrected source is accepted in principle for metadata/file-extent verification and policy-derived reservation, subject to the exact final source/evidence snapshot below. It is not a numerical integrity checker, ResearchRun admission layer or empirical allocation permit. Only source, compact evidence and hash metadata were reviewed; no tests, numerical array bodies, profiles or empirical jobs were run/read. Only this review was written.

## E1 — owner metadata outside the declared root

Initial `extent.py:84–89` required the publication manifest to remain below `root`, then derived `owner_path = outer.parent.parent / 'owner.json'` without checking containment of that derived path. Supplying a complete publication directly as `root/manifest.json` allowed reading and accepting `root.parent/owner.json`. The intended journal wrapper constructed a safe root, but the public verifier accepted this malformed boundary.

The initial source SHA-256 `6855bc23cd89d0c854614ed07054d6d7d9e868ce170e31f340c68055d95123a7` is retained as `extent-before-root-layout-fix.py`. `red04.log` is a clean behavioral counterexample: a real complete manifest plus matching external owner was accepted when rejection was required. The correction enforces the exact `root/session/artifact-NNNNNN/manifest.json` layout and safe session name before inventory or metadata reads. The derived owner file is therefore inside root. `green04.log` records 13 passing tests in 0.221 seconds. This resolves the reported containment defect without loosening any existing checks.

## Reservation and complete-file inventory

`reservation_bytes` requires the exact pair policy field set, positive non-boolean integers, bounded chunks and enough per-session allowance for the owner plus one publication. It derives the publication reservation as `max_checkpoint_bytes + 65,536` bytes. `reserve_pair` records that exact value with the typed numerical identity before the caller creates/allocates its session. This is an envelope derived from the supplied policy; the caller must still bind that policy to registration and use the same validated policy for numerical creation. The actual PairSession performs its own graph/config/capacity checks.

`publish_pair` requires the current pending reference and identity, verifies its derived owner and fixed session parent, calls the extent checker, and only then publishes the journal event. An insufficient reservation or failed verification leaves the pending reservation and saved files intact. It does not refund charges, select another checkpoint, silently rerun a pair or perform orphan reconciliation.

The verifier inventories at most 11 entries with directory depth at most two beneath a publication. That bound covers the largest current format: eight files and three nested directories for a ranked checkpoint. It compares the exact allowed file and directory sets, including the no-state completed-score format. It rejects extras, missing files, symlinks, multiple hard links and cross-device files/directories. Compact metadata is limited to 64 KiB and read through no-follow descriptors with pre-read/during-read file-stat checks.

The outer manifest hash is tied to the caller's exact reference. Nested composite, annealing and hardening metadata hashes are joined through their parent manifests. Policy, typed numerical identity, backend and session parent are compared with canonical JSON representations so numeric type changes such as 2 to 2.0 do not disappear through Python equality. Integer schema/shape/extent fields receive explicit checks. Owner metadata must exactly match the supplied owner/identity/policy/parent and is accounted separately.

For progress, the checker enforces the current float64/int64 array extent formula `8*n*m + 128` for each declared array and the expected three-array annealing or four-array ranked inventory. It checks the conservative state/checkpoint envelope, sums every saved publication file's logical length and confirms both the saved state and whole publication fit their corresponding allowances. It does not open NPY files, verify their headers, recompute their hashes, validate numerical values or prove that the declared shape matches a real admitted graph. Those duties remain with the separately verified numerical loader and admitted caller. Completed-score metadata is likewise not independently rescored.

## Atomicity, accounting and evidence limits

The before/after inventory compares device, inode, mode, link count, size, modification/change timestamps and block counts, including directory and owner observations. This detects observed changes while checking; it is not a lock against concurrent mutation or a transactional snapshot. A sole admitted writer must retain ownership across reservation, save, verification and publication. The checker returns a report but does not itself durably journal that report. An eventual registered caller must retain the extent evidence and ensure the journal publication cannot be bypassed or mixed with another policy.

Reported physical allocation is the sum of file `st_blocks * 512`, separately for publication and owner. It excludes directory blocks, ancestors, other publications, concurrent scratch and workflow artifacts. This is correctly distinct from logical length and does not prove sufficient disk space or a process memory bound. Journal charges for owner, events, start/terminal and ancestor reservations remain separate; no ancestor byte total is reset by this helper.

The saved `green03.log` records 12 tests in 0.198 seconds, with real annealing, ranked and completed PairSession artifacts. The no-array-read fixtures intercept `Path.read_bytes`, `os.open` and, in the annealing case, NumPy loading. Tests cover inventory/extent damage, links, metadata hash and identity changes, exact policy types, actual reserve-and-publish integration and retained pending state on under-reservation. `red02.log` is a behavioral type-equality failure; `red03.log` is two missing-wrapper API errors, not two independent semantic failures. The earlier logs and source snapshots are preserved. These are tiny synthetic artifacts; no broad suite, capacity-scale storage profile or empirical release follows from them.

The initial J2 gap is addressed concretely for callers that use both wrappers with their actual pinned PairSession policy: policy-derived reservation precedes allocation and exact saved file lengths are checked before the journal event. This does not close the remaining registered owner/death/purpose/source compatibility, global guard, fatal cleanup, observer reconciliation, dictionary directional or MCM partial-row requirements. The maintained package and Graph10 scientific/resource scope are not changed by this isolated component.

## Final corrected-source acceptance

Accepted for the extent-only component scope described above. The final containment regression also replaces `os.open` with a failure sentinel during the malformed-root call, proving that rejection occurs before any metadata descriptor is opened. Saved `green05.log` records all 13 tests passing in 0.215 seconds. The corrected implementation is unchanged from the layout fix; only the regression was strengthened. No further blocking source finding remains within this scope.

Exact final reviewed SHA-256 values:

- `extent.py`: `c62c743c67490e37b9aca2e6722d143e02df009c5398bb2fd246e9051f1ac3ac`
- `test_extent.py`: `b5c1d9b00f803cd4ee7d15aa7428f99d257352afd5e0e4454d8e9adc9e5777ee`
- `red04.log`: `cca0bdcb21b734ca9ffbc307e456d5dcba31358da8a0bf626c3a90a9bdf56cca`
- `green04.log`: `43519b1fe1c206e122047ed1aa02cec2e442a3f311a01dead282b09c53faf177`
- `green05.log`: `f982d11ba94b6db145c7532b14817be16bb6c52146a2d3853a97492f51899490`

A future source-binding manifest or implementation document must preserve these exact bytes and the stated limitations; no not-yet-saved manifest is claimed verified here. This acceptance is not a registered execution or whole-pipeline release.

Final evidence addendum: the subsequently saved `bindings.json` contains 196 entries; every current file hash matched independently, including all 178 prior maintained-package verification entries unchanged. Manifest SHA-256 is `ba733a8ef4f1a3d7d6a75778eb0816ce0ffa9774093a720ac164202dbb23d200`. The saved `IMPLEMENTATION.md`, SHA-256 `3be714fe12a573d9275c406d31aaa003367964fe3f2f597b771d4e898470ce3a`, accurately distinguishes extent verification from array-content validation, file-block reporting from total allocation, and this unregistered wrapper from future admitted consumers. It retains the initial failed exception-type fixture and missing-wrapper failures without presenting them as successful behavioral evidence. Final evidence reconciliation supports the scoped acceptance above; it does not extend the earlier full-suite result to this new candidate.
