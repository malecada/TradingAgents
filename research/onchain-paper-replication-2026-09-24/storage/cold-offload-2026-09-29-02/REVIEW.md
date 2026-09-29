# Independent prospective cold-offload continuation review

September 29, 2026. Reviewed the exact delta from the previously reviewed `cold-offload-2026-09-29-01` script, the new manifest/bindings, saved synthetic test result and predecessor closure metadata. Only source, compact receipts and local stat/tracking metadata were read. No archive bodies, connection/credential contents, remote queries, transfers or tests were executed by the reviewer.

**Accepted for one bounded execution of this exact new cold-move identity under the user's existing storage-offload authority and explicit prospective 10 GiB disk policy.** This is pre-execution acceptance, not evidence of transfer success or reclaimed space. All runtime admission and preservation checks must pass before any source unlink.

## Exact scope and lineage

The new manifest's nine file rows are exactly equal to the first attempt's rows: **3,584,497,664 bytes**, with the same original paths, hashes, stat identities and owner receipts. Independent current metadata checks confirm every source still has that exact stat identity, is regular, single-link and untracked. All original owner cgroups are absent with failed/cleanup-verified receipts. No raw transaction, graph, SQLite, configuration or historical receipt is selected.

The first offload remains failed at its original hash `8630c4c1ad9dc6c70dd1f0e0916a79ec860ac8690d506cfe6ec768ac4fec8525`, with verified cleanup, absent cgroup and zero per-file verified/evicted receipts. The new worker checks that exact terminal and rejects any predecessor per-file result requiring reconciliation. It uses a distinct exclusively created remote prefix ending in `cold-offload-2026-09-29-02`, leaving old partial remote objects untouched. At review, the new local `guard01` directory is absent. This is a separately retained successor, not reopening or resuming the terminal first attempt.

## Reviewed delta and preservation

The script changes only the finite wall allowance from **3,600 to 7,200 seconds**, the prospective free-disk floor from **20 to 10 GiB**, and the explicit predecessor/policy hash and closure checks. Existing 256 MiB memory maximum, 192 MiB high threshold, zero worker swap, 3 GiB runtime host reserve and 3.5 GiB startup reserve remain unchanged. The longer wall allowance accommodates slower transfer but does not guarantee success at an inferred throughput; each transfer still has its own existing timeout and the finite outer guard remains authoritative. The disk change is not a RAM-reserve amendment and cannot prevent another unrelated host-memory stop.

All reviewed per-file preservation ordering is unchanged: source identity/no-follow handle and advisory lock; body upload/full size-and-hash readback; restoration metadata upload/full readback; fsynced verified receipt and original-path sidecar; final original path/descriptor identity checks; then unlink and directory fsync. Failed body/metadata/durability steps retain the original. Failed scratch and remote objects remain for reconciliation. Completion-candidate roundtrip still precedes local terminal completion. Source availability changes only for files that satisfy every check; restoration requires fresh capacity, a new temporary download, exact byte/hash verification and an absent original path.

One-file recovery scratch remains at most 512 MiB plus bounded compact metadata/diagnostics, network payload remains 8 GiB, and the rate ceiling remains 32 MiB/s. Fresh local free space must exceed the new 10 GiB floor plus 512 MiB body scratch and 16 MiB metadata margin; fresh remote capacity must cover the full target bytes plus 1 GiB. Reported available capacity is not substituted for these worker checks. Readback supports recoverability at the time of execution, not indefinite remote durability or another independent replica.

## Source and test evidence

All **ten non-connection entries** in the eleven-file binding manifest were independently rehashed and match. The remaining connection metadata pin matches the original manifest and is enforced by the worker; the reviewer did not open that file or any key/known-host contents. Tests are byte-identical to the reviewed corrected first-attempt tests. Saved `green01.log` reports **8 tests passed in 0.022 seconds**, covering per-file preservation, failed publication and aggregate completion ordering. These unchanged tests validate the preservation helpers; the new predecessor/policy routing was assessed statically, not exercised against the remote service.

- `manifest.json`: `4abf11a0860b54923cf83e007f614fd299b19a9397931d2bd8584b49d7f8621d`
- `offload.py`: `abcaef5d0eca38f8efcc02f138b8024c96a60b1654399589cbc04d6c3e198c50`
- `test_offload.py`: `73b8b4762100c0fd96ae372a6bce573122b27f7ccd0e53b12f627bd0193cb576`
- `bindings.json`: `45efb56cc70f4a552c09454f26b0b8328ab9c92fbaa3adde20db5997305a9e06`
- `green01.log`: `389e01ee0077dce7ff8ae1df1438b65e14d6292ee9b9d485b644cb488f507f64`

No substantive new finding blocks this successor. Preserve its own terminal identity, partial transfers and per-file outcomes on any failure; do not silently retry either attempt. Final closure must establish which exact files completed remote restoration verification before local eviction. Historical source jobs and the first offload remain failed, and no empirical claim, financial fit or broader storage eviction is included in this acceptance.
