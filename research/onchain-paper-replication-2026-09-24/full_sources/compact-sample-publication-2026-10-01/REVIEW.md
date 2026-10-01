# Independent corrected compact sample publication review

Accepted for bounded durable numeric publication from the actual current-owner Draws result. CSP1 and CSP2 in the preserved `REVIEW_INITIAL.md` are closed. This accepts numeric publication and exact resident-to-saved byte equality, not scientific sample-provenance admission, dictionary consumption, cold reuse, native selection or empirical release.

The review independently inspected the implementation, correction diff, tests, retained failure/success logs, component writer, strict reader and Draws verification contracts. No tests, historical jobs or empirical numerical files were run/read by the reviewer. Only this review note was written.

## Corrected boundaries

**CSP1:** After its last external lease, `Published.check()` now calls callback-free `Draws._verify()` and then `_evidence()`. The former verifies the retained draw chain, completion/start references, resident records, RNG terminal state and original numeric fingerprint; the latter verifies the new publication. This closes the late callback paths that previously allowed a changed original resident sample or corrupted draw file to escape despite valid saved numeric files. The new tests arm the mutation only after numeric comparison and separately exercise those two paths.

**CSP2:** Immediately after the final pre-writer external lease, `publish()` now verifies the pinned Draws evidence/resident fingerprint and exact saved start bytes before `save_component`. The fingerprint covers the same numeric shapes/dtypes/bytes and sample metadata used in sizing. Therefore unchanged fingerprint plus frozen policy/context preserves the admitted size contract; another independent size calculation at this point is unnecessary. The growth regression replaces a resident feature matrix after sizing and forbids writer entry. It now refuses before creating the artifact while preserving the failed attempt.

These checks are callback-free boundaries, not atomic protection against continuously mutating external processes. Existing ownership/frozen-input assumptions still apply.

## Source and resource assessment

The actual Draws type/current Owner, selected plan/job input, policy hash, training/Binding/draw references and separately admitted strict-reader source are joined. Exclusive deterministic namespace creation, nonblocking Owner transition lock, root inode/device checks, exact file inventory and retained failure/poisoning behavior are consistent with the bounded first-attempt contract.

For the supported contiguous native float64/int64 payloads, the estimator mirrors the existing writer's tree, array names, NPY header sizes and canonical manifest bytes. Fixed-length placeholder hashes preserve encoded lengths. Its running structural/scalar/descriptor lower bound prevents unrestricted tree growth before the final manifest-cap check. It does not bound Python allocator overhead. The positive fixture checks the actual total serialized bytes against the receipt.

The logical allowance covers artifact cap plus three 8192-byte receipts, permitting start, complete and failed records together. Original and loaded payloads are reserved as `2 * numeric`; the returned receipt retains the original samples and does not construct another AttributedGraph copy. The strict reader inspects every declared header, extent, member hash and inventory before numeric allocation. Byte-view equality avoids a full-array boolean comparison buffer. These are payload/logical bounds, excluding metadata objects, I/O buffers, parent graphs, filesystem allocation and process RSS. Full-size throughput and whole-workflow physical feasibility remain unmeasured.

## Evidence inspected

- red01: 1 missing-module failure, 8 deselected, 23.47 seconds.
- check01: 1 failed, 8 passed, 244.19 seconds. The failed allocation trap intercepted shared NumPy allocation during PCG64 metadata processing, before reader admission. Other then-current publication/refusal/preservation cases passed.
- red02: 3 failed, 9 deselected, 87.92 seconds. Both final resident/draw mutations were accepted, and post-sizing growth reached the forbidden writer.
- Corrected check02: 5 passed, 7 deselected, 152.72 seconds. It covers positive actual saved numeric publication, the reader-local preallocation trap, both final callback mutations and post-sizing growth.

The revised NumPy proxy traps only allocations in the strict reader and leaves unrelated RNG metadata operations intact. Earlier passing cases and the final targeted five remain separate evidence; no combined final-source twelve-case run is claimed. Raw check02 is terminal and supersedes the earlier Active entry in RESULT observed during review.

The fixture uses actual temporary ResearchRun/Binding/Owner/Training/Draws joins with mocked guard surfaces and the inherited two-train/two-test supplied population. No full calendar/exclusion denominator, price/label reconstruction, independent weighted-probability recomputation or full-fold resource claim follows. The receipt correctly sets `numeric_artifact_published=True` and `sample_provenance_admitted=False`. Actual induced-neighborhood/draw-proof admission remains the next required scientific join.

## Exact reviewed bytes

- `compact_samples.py`: `f14a11212edd281901aab69fbe9b1164251988472baa65da6b319d50ff436d7b`.
- `test_compact_samples.py`: `9f5b105479811e2049af33c1be8b4afb78e30a7070ee0d2f601e8857847d9d5b`.
- Preserved `samples-check01.py`: `aa2cfa8368f6e74ec95cbb54a7ae65e1199d2e7c96c69107b12c1d77a79184f1`.
- Preserved `test-check01.py`: `c348e2b43f783d4e557b0c972255807afe9104882d6314942cabaa73862ca497`.
- `check01.log`: `53cb0aa61eab325714e13d2a84818d2eb1cebe96b4f3487132ed70c4b9e514a6`.
- `red02.log`: `29c9da14e09db247b124e820db39999fd62d9e2b03ccfd0e8d633440a6cd67d4`.
- `check02.log`: `72c0d191aad0ce11e638ffcb5bda1e5e7f6bfdb59f98c3b14a567516997297d6`.
