# Independent original-import03 timeout closure review

Decision: **ACCEPTED as a permanently FAILED, locally retained and closed attempt**, with the reporting correction below. This is not numerical acceptance, full MCM completion, capacity proof, external recovery or permission to retry. The exact first failed target and second unavailable target remain spent/retained; the unused dependent publication-failure03 identity must not be blindly started.

Original result `EXECUTION_PRIMARY01.json` is retained unchanged at SHA256 `1e75072838dc25d8f132c345d38b22af544954a0753c02c5cf4033c2224e6949`. Retention manifest is `f590948a38b5a25a7a56c089d2e3ca670db1b6298f668784aa1d998e13922a89`; complete archive is `4ef0b859c2529668f4a90965b0555005dc0e8099ea1249717cdcc7390e2544cd` (2,618,781 bytes). The actual identity is `original-import-native-success-20261003-03`, source `bb9e6ac95b2be13dbbfe5b77c55a5ce35a0926a9`, registration `a468d1b6ea8bba450b3a553fb42d08c18009b267db022e58e2795c105a9d5731`, claim `7e35261724e6bf2d58ca484a2ef39606d7a586313dca5fe7f0c06fe6b8ef88ef`, failed terminal `e0fb5527f662461300dfa153bed8a155661c32f0e98e43690b512c5019259351`.

## Material reporting correction: retained cell denominator

The registered `outputs/cell-ledger.json` and `outputs/resource-summary.json` are absent. The original result correctly reports those missing outputs and `cells=null`, but its newly constructed `separate_root_unavailable_cells` classifies both cells unavailable. That summary is less specific than the actual retained worker evidence and must not replace it.

Both genuine durable source dispositions exist under `research_artifacts/onchain-paper-replication-2026-09-24/sources/<identity>/`. The selected observer collected them, byte-equivalent as JSON, into `runs/<identity>/postmortem-cells.json`, SHA256 `8dc88aae95d2647f35d341503f5d700f2b25f4696733f9a06ed66e570bd14779`:

- `import-target-01`: **failed**, `SystemExit: owned execution interrupted; never relaunch this identity`.
- `import-target-02`: **unavailable**, with the same recorded interruption reason.

The observer receipt authenticates that exact postmortem ledger and every associated evidence hash. Its two IDs equal the registered cell denominator. Thus the original failed terminal's phrase “complete denominator retained” is supported by the durable postmortem/source records, not by a nonexistent worker output ledger. Preserve the original result and add an explicit correction/reference before treating its summary as machine-readable cell truth. No original receipt or unavailable/failed status should be rewritten.

The two actual registered output bodies are `resource-binding.json` and `resource-journal.json`, both genuine failed resource-terminal observations from the interrupted worker. Their exact hashes equal the failed terminal's complete output map. They are not a successful Binding completion or a fabricated outer replacement. `COLLECTOR_FAILURE03.json` honestly preserves the earlier collector's refusal at the missing ledger; additive collector04 then archived the actual partial tree. Neither collector reran the workload.

## Actual timeout and partial finalization

The native guard records1,802.523400692 seconds, sampled peak402,456,576 bytes and zero `high`, `max`, `oom`, `oom_kill` and other recorded memory events. The native systemd result is `timeout`, main status125; child receipt says125/`signal`. The original guard's `child_exit_code` remains null and is not silently replaced with the separate child receipt. Its ordinary reason is `registered wall-clock limit exceeded`. The selected positive raw validator consequently refuses `child terminal snapshot failed/missing`; that refusal is correct for a failed run and remains evidence.

Independent read-only `journalctl` output retained in `unit-journal01.txt` gives the concrete shutdown sequence: start at04:13:12 local time, runtime limit at04:43:12, main exit125, then `final-sigterm` expiry and SIGKILL at04:43:14. The killed workload was1758327; a Git process2364209 and surviving Python/jemalloc threads are also identified. The displayed04:xx times are Europe/Prague; the coordinator's02:xx times are UTC. This is a wall-limit failure, not evidence of insufficient RAM.

Selected source explains the partial receipts without requiring a replay:

- `tradingagents/research/onchain_replication/resources.py:466–469` uses `KillMode=control-group`, `TimeoutStopSec=2s` and `SendSIGKILL=yes`. Native-child handling at`:249–262` returns125 and publishes its snapshot when signaled; this does not wait for all workload finalization to succeed.
- `job.py:321–324` raises the recorded `SystemExit` in the worker on SIGTERM/SIGINT.
- `resource_fixture.py:301–328,350–359` first attempts independent source-cell dispositions and failed journal sealing, then summary assembly/storage observation, failed binding/journal outputs, the worker ledger and finally summary output. The retained tree proves execution reached the two failed output writes, while later two outputs are absent.
- Each `run.write_json` performs genuine `_check_source` admission before its immutable write (`tradingagents/research/lifecycle.py:170–177`), so shutdown work includes source/Git checks. A Git subprocess was actually killed during the two-second grace period. The exact internal instruction being executed when killed is not preserved; no traceback establishes that it was specifically the ledger's source check rather than another finalization check. Ordinary secondary errors are also retained only through the primary selection policy. The supported cause is **forced process death interrupting incomplete finalization**, not a proven absent output branch or numerical mismatch.
- After verified owned cgroup death, `job.observe` (`job.py:463–490`) authenticates existing source dispositions, writes the separate complete postmortem denominator and closes the genuine claim failed. It does not pretend the missing worker ledger or summary was published.

A future bounded shutdown path may need independently reviewed postmortem publication/accounting that does not depend on the dying worker finishing repeated expensive admission checks. This observation does not authorize relaxing native limits, extending the current job or synthesizing old outputs. The separate local canonicalization candidate is not reviewed by this closure.

## Proven work and limits

The genuine original dictionary import completion exists at SHA256 `170c4e77cb891494ca854c0ee0f45267d97030347045ad8e613d3411a7106cd7`. Its metadata retains32 ordered motifs and explicitly records no historical dictionary recomputation. The first MCM stage exists and is incomplete; no `stage-complete.json` exists for it. The source performs independent scalar reference comparison only after `produce_imported` returns (`resource_fixture.py:339–343`). No MCM stage completed, no target result was published and no scalar reference comparison was reached. Partial matching/event/tail bytes are retained but were only hashed, not interpreted as verified scores. No claim of zero matching work is made.

The native readbacks retain3GiB memory high/max, swap0, actual inherited two-CPU affinity, hard/soft4MiB file limit and30-minute RuntimeMaxUSec. CPU quota controller availability is false; enforced CPU evidence is affinity/thread readback, not a falsely claimed active quota controller. The owned-tree1GiB limits and10GiB free-space floor are sampled stop policies, not a filesystem kernel quota. The current result does not establish completion capacity for all160 comparative scalars, later paper resource cells or financial fits.

## Full preservation and final accounting

Independent `review_checks01.py` streamed every archive member without extraction and rehashed the original frozen tree. All939 members match:665 regular files,274 directories including the root,6,585,516 logical file bytes and9,453,568 allocated bytes including directory blocks. All names, modes, file sizes/hashes and actual original block counts match; there are no surviving symlinks, hardlinked regular files or unlisted members. The selected159 source files match both current bytes and original committed source; the registration matches Git and release. All32 registered input bodies were hashed without interpreting arrays or historical samples.

The final selected post-tail storage record observes664 files/274 directories,937 entries excluding root,6,584,555 logical bytes and9,449,472 allocated bytes. Its declared self-exclusion exactly accounts for the remaining961-byte/4,096-allocated-byte post-tail receipt and one entry. The complete final tree has938 entries excluding root,939 including root. The older guard storage sample is lower because later observer/outer publications had not yet occurred; it is not asserted to be the complete final inventory.

The local archive includes the two previous genuine failed claims and their outputs/history together with current failure03. Three engineering attempts are now spent under adopted ceiling4; the originally allocated dependent failure03 has no claim. This does not refund earlier attempts, create a successor, discharge the refusal suite or change the paper36-closed/highest64 accounting. External recoverability of this new failed tree remains a separate next check.

## Closed cleanup and scope

The original outer cleanup receipt is preserved with `pid_absence_verified=false` and `unresolved_pid_absence=true`, despite a reaped supervisor and absent native cgroup. This review does not rewrite it as successful proof. Independent later readback confirms the original cgroup absent and the unit failed/timeout125 with empty ControlGroup. All11 PIDs/thread IDs identified across the original six receipts, last CPU-thread readback and journal are absent:1756801,1756805,1756967,1757654,1758323,1758327,1759689,1760203,1760206,2363054,2364209. These actual later observations support ending the source freeze, separately from the original outer's unresolved field.

Only new review files/logs were written in this investigation directory. No source, capsule, claim, gate, budget, registration, numerical object, original result or process was modified or replayed. No numerical module was imported. No timing-share profile or model/paper agreement was measured. Closure acceptance permits preserving and reviewing the failed outcome; every fresh attempt still requires its own exact source, budget/admission and release.
