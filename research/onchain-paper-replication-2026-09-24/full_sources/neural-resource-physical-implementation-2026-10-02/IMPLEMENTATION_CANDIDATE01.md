# Explicit neural physical route — frozen candidate01

Independent review is required. No empirical execution, OS user-unit launch, old-identity replay, registration adoption, source commit or namespace reservation occurred. The new optional `resources.physical_policy` applies only to `kind=neural_resource`; omission preserves the old route. Existing `workflow_storage.py` is unchanged. All old evidence and earlier failures remain retained.

The seven exact source/test files and raw attempts are pinned by `candidate01.json`. Actual snapshots are under `snapshots/candidate01/`. The previous moving candidate was preserved in `snapshots/pre-authority01/` before correcting NPH1–4. Intermediate source snapshots were not captured for every early attempt; retained patch scripts are not represented as complete reconstructions.

## Original authority and ownership

The original launcher creates the exclusive control root, creates an original lock and anchor, and remains alive through `monitor.wait()` and observer reconciliation. The anchor includes root/experiment/source/policy, original launcher, control and lock identities, and the abstract local socket's parent PID/start ticks/UID/address. The anchor digest is carried through monitor and worker arguments and the guard child's explicit public context. There is no integrity key in arguments, environment or disk.

The launcher retains dynamic original identities in memory. A bounded abstract Unix socket verifies server SO_PEERCRED PID/UID and `/proc` start ticks. The parent exclusively creates each lifecycle/producer root and captures its inode at birth. The parent itself publishes the bounded claim and captures its hash at that transition. Clients cannot submit replacement original inode/hash values. Original birth receipts are disk evidence joined to the parent's hashes; mutable `physical-state.json` is no longer authority. Coherent disk receipt/root replacement, deleted claims, dangling planned roots and original control replacement refuse.

The threat boundary is trusted admitted local processes and accidental/callback namespace rebasing, not hostile process-memory, kernel or arbitrary same-user-code control. No general authentication service is introduced. Parent loss or authority-thread/transport failure prevents further selected mutations. External reconciliation without the original live context refuses rather than inferring authority from current disk. Existing bytes remain available for separately reviewed recovery; there is no automatic resumption, refund or fresh claim.

RPC never reacquires the physical flock held by its client. Accept is bounded by a 0.2-second polling timeout; socket I/O is capped at two seconds and each received message has an absolute two-second deadline and `max_json_bytes` frame ceiling. Parent shutdown joins for three seconds. Handler fatal objects are retained and rethrown at the launcher boundary; socket cleanup is once-only and preserves fatal primary identity/notes or promotes uncertain ordinary cleanup to a fatal error. This process lifetime dependency is intentional.

## Three roots, writes and reads

The exact roots for E are:

- control: `research_artifacts/onchain-paper-replication-2026-09-24/runs/E`;
- lifecycle: `research_runs/E`;
- producer: `research_artifacts/onchain-paper-replication-2026-09-24/sources/E`.

The three parent scaffolds must already be canonical existing directories on the workspace device. The selected authority never creates arbitrary ancestors. The existing lifecycle ledger lock remains the existing shared ledger serialization mechanism; it is not a fresh experiment root or a separately budgeted scientific output. The optional lifecycle hook changes only selected root creation and metadata publication. Default lifecycle bytes/behavior remain unchanged.

Every observed root is joined to the original parent authority. Traversal holds root/child directory descriptors, uses nofollow relative operations, rejects symlinks/special files/cross-device entries/unexpected hardlinks, and rejoins original path/inode after traversal. Entry/depth/time limits apply. Metadata readers use nonblocking, nofollow descriptors, regular-file and size admission before allocation/JSON parsing, and final inode/extent/time joins. This is a sampled boundary, not an atomic filesystem snapshot.

Selected JSON encoding is bounded before publication, including depth and encoded bytes. Immutable metadata publication and temporary hardlink coexistence occur under the same interprocess lock used by scans. Failed partial writes and uncertain cleanup remain retained. Active writes reserve space for failure/terminal metadata; terminal writes and the final observer/lifecycle tail use the reserved budget. Sixteen entries are withheld from ordinary activity; a metadata publication also reserves two coexisting entries. Terminal tail still refuses actual aggregate/entry breaches; preservation is best effort, never a claim that failed storage can always publish another file.

The guard's selected systemd command uses `LimitFSIZE` and requires exact soft/hard RLIMIT_FSIZE readback before release. `child.log` reaches a finite per-file boundary; observed saturation is a terminal guard failure. The source still requires the original memory/cgroup/CPU controls. Selected scratch variables TMPDIR/TMP/TEMP, XDG_CACHE_HOME and TORCH_HOME refer to accounted directories under control/scratch. Child and worker verify the inherited mapping and reset/check `tempfile`'s cached choice before relevant library imports. This contains configured library scratch; it is not a kernel-wide filesystem sandbox or an assurance about hostile arbitrary writes.

Final physical accounting follows guard finalization and observer/lifecycle terminal writes. `physical-final.json` states its before-self snapshot and bounded own-write reservation; its publisher checks actual totals after publication. External failed recovery without authority cannot append a replacement final receipt.

## Proposed finite refusal ceilings

`proposed-policy.candidate01.json` is unadopted. It proposes 8 MiB per file, 256 KiB encoded JSON, 160 MiB allocated aggregate, 128 MiB logical aggregate, 128 entries and 32 MiB reserved terminal tail. This leaves active logical96 MiB and active allocated128 MiB. Tail32 MiB exceeds two8 MiB file extents plus sixteen256 KiB metadata extents (20 MiB); this is a finite conservative refusal reserve, not a guarantee of every filesystem's allocated peak. A single metadata write reserves `max_json_bytes+8192` plus two entries for temporary coexistence. Frame overhead can make the effective claim payload ceiling slightly smaller than the nominal JSON ceiling; refusal occurs before parent publication.

The proposed real neural producer allowance64 MiB is separate from these whole-route limits. The tiny worker fixture retains its existing synthetic producer allowance128 MiB; it was not substituted for a final real registration. Its measured actual bytes are much smaller. Real graph/model peaks, filesystem allocation behavior, actual user-unit control/log volume, and successful physical feasibility remain unknown. The source caps provide refusal boundaries and sampled accounting, not a proof that all nine real requirements finish or an invented physical upper bound.

## Retained verification and failures

`check13.log`: 141 passed, one added-fixture API typo (`run.complete` instead of the actual `run.finish`). This included the existing lifecycle/default-route, neural runner and resource tests under the normal reviewed conftest. The lifecycle tests use their self-contained synthetic Git repositories and declared `engine.py`; there is no source-owner scan of the changing shared checkout. The model worker uses invented graphs and mocked source admission/guard while exercising actual model, optimizer, serialization, load and lifecycle output behavior.

`check14.log`: the corrected selected lifecycle plus selected tiny-model worker passed, 2 passed/37 deselected, 8.95 seconds. Production bytes did not change between check13 and check14. The final source contains39 physical tests; all corresponding cases have passing evidence across the two runs. The earlier red logs and all unsuccessful checks remain unchanged. Red06 reproduced six reader/authority failures. Red07/red08 captured missing original-anchor/live-parent interfaces. Red09 reproduced fatal-parent loss at shutdown. Red10 reproduced missing terminal entry reserve. Red11 captured missing selected scratch interface. Red12 reproduced three socket cleanup/constructor gaps, then check12 passed all three.

The final nine-cell synthetic worker measured:

| Role | Allocated bytes | Logical bytes | Entries |
|---|---:|---:|---:|
| control | 53,248 | 2,311 | 14 |
| lifecycle | 40,960 | 18,576 | 7 |
| producer | 4,550,656 | 4,455,795 | 30 |
| total | 4,644,864 | 4,476,682 | 51 |

There were33 regular files. The control fixture includes original authority metadata, scratch directories and final observer receipt; it does not contain an actual launched systemd guard's complete output. Separate mock-guard tests verify launch properties, readback-before-release and tail ordering. One tiny actual subprocess verifies a4096-byte RLIMIT_FSIZE boundary and retained partial bytes; this is not a user-unit/cgroup smoke test. A real bounded guard smoke, if required, remains a future separately identified synthetic action after review.

Before empirical admission, the complete dynamic package source closure must be frozen in the admitted checkout or isolated source snapshot. Concurrent archive integration prevents a shared-checkout empirical freeze now. Exact final source/runtime/registration/budget/physical availability and the proposed caps still require coordinator reconciliation and independent review. This candidate does not relax the6 GiB worker ceiling,3 GiB reserve,9 GiB startup requirement,10 GiB disk floor, two-CPU binding, full nine-cell population or scientific model behavior.
