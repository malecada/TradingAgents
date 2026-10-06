# Packed archive read-control candidate — not installed or admitted

The concrete patch in `CANDIDATE02.patch` retains legacy default behavior and adds only explicit `read_controls = {schema_version:1, format:packed-archive-read-controls-v1, shard_bytes:4194304}` selection. It changes repeated cold-read receipt storage; writer event bytes, numerical payload bytes, remote names,16 verification allowances, checkpoint/replay/RNG/scientific ordering, transport command/payload allowances, native limits and physical budgets are unchanged. No data-body, numerical import, network, credential, connection-body or empirical access occurred.

## Source changes

- New `archive_read_controls.py` uses existing `archive_control_history.Journal`. Each original intent/verified/complete name and exact raw JSON bytes is appended and durably read back. No prior control is removed or rewritten. A bounded source-mapping-derived inverse validates every record name, raw bytes, order, chain, shard extent, membership and inode. Current acknowledged shard signatures are rejoined after callbacks before existing temporary-payload disposal; cold byte audits run at existing final read/scientific boundary checks.
- New pure `archive_read_control_capacity.py` exposes the same scalar policy and capacity to runtime and the accepted metadata calculator. Maximum canonical success-role sizes are748/204/134 bytes, derived using128 ASCII remote-name bytes,64-byte hex fields and existing8MiB payload extent; tested at exact boundary. These are schema-derived encoded bounds, not arbitrary lower quotas. Error/cleanup evidence retains8192-byte limits and explicit extra frames/files.
- `archive_pair_reader` selects the packed route and shared inverse; `archived_stage` uses that same final check. `archive_pair_writer` accepts and anchors the explicit read selector but retains its original physical writer/copy/read layout. `archive_owner_policy` and `archive_dispatch` admit the selector and use its read reservation. All other operation/lease/owner joins remain existing source.
- Accepted `controls01` gains matching byte/file/directory arithmetic; accepted handoff `prepare_builder03_input02` forwards the selector. Source pins include originals. Candidate files are complete reviewable replacements; the patch targets runtime plus the accepted metadata sources only.

No fresh generic journal/launcher/review framework is introduced. On transfer failure, original intent/failed raw records, root failed evidence and the partial payload remain. An incomplete or mutated history cannot become a successful cold read. Filesystem/cache concurrency and failed fsync retain existing refusal semantics; no retry or success coercion is added.

## Seven-count result

Archive workflow metadata reservation falls from10,655,301,632 to1,871,270,400 bytes, saving8,784,031,232. Archive file slots fall from1,300,724 to168,052; directory slots425,617 to48,145. The mandatory structural logical/entry incompatibility demonstrated by the earlier draft is removed by representation/accounting, without cutting stages/events/verifications.

Known total new reservations, excluding the two unresolved residual domains and current baseline, are10,882,072,416 logical bytes,13,418,092,135 modeled allocated bytes and558,745 entries. An explicitly conditional illustration retaining the earlier unproven lifecycle/cache proposals and adding authentic3,496,602,912 graph-array bytes reaches14,680,665,216 logical /17,236,982,595 modeled allocated /563,181 entries before other baseline entries/bytes. This fits the frozen16/20GiB/1M numerical thresholds only conditionally. Array-byte metadata is not a fresh complete writable baseline. No capacity/admission claim is made.

## Focused verification

13 stdlib-only offline tests passed in the checkout-local pinned runtime. Actual candidate ArchivePairLog/reader paths perform16 complete independent synthetic cold reads. Tests verify packed-vs-legacy payload-byte/replay equality, exact inverse, maximum encoded schemas, legacy default directories, failure receipt/partial-payload preservation, callback mutation refusal before disposal, post-completion mutation, missing/partial/foreign records, invalid policies and mutated writer binding. An invented6,000-record receipt sequence exercises multiple existing Journal shards and cold inverse/mutation detection. All candidate sources compile.

The source loader removes exactly the unused `import numpy as np` line from original scalar/descriptor IO; no numerical function executes. An audit hook refuses numerical imports, network and subprocess. Temporary files remain exclusively inside this new directory and tests remove only their own invented fixtures. No broad matrix or empirical replay was run. Full Owner/ResearchRun/native integration was not executed and remains independent-review work.

## Exact integration requirements

Root must independently review source pins/patch and apply candidate runtime files after the active freeze permits, add both new helper sources to the exact source closure, update the accepted metadata successor dependency hashes for candidate controls/handoff, and resolve its added pure capacity import to `archive_read_control_capacity.capacity` in the existing stdlib loader. No new preparer framework is needed. Rebind archive policy/descriptor/input hashes using ARITHMETIC02's `new_archive_policy`. Builder03's scientific/transport formulas do not change.

Fresh whole-writer baseline after approved recovery/retirement, source-proven/enforced full lifecycle/native-cache bounds, selected final caller/OwnerBinding/private Transport and exact registered resource gates are still required. The old prospective residual declarations are not silently promoted to maxima. Five-second actual scan adequacy remains unknown; fewer entries do not prove timing. Root owns independent review and actual release.
