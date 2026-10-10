# Pilot29 terminal outcome and denominator review

Disposition: **ACCEPT_ACTUAL_FAILED_TERMINAL_AND_BOUNDED_PARTIAL_PROGRESS**. The original29 attempt failed at the registered eight-hour wall limit. Its partial matching records remain engineering evidence. No complete MCM, joint update or financial fit is established.

The exact failed body `100e51b2408119975cac58abec88b09b17203736f3a8254011507da147f977e0` joins original claim `5b81c3cb892f75a0b1505bb08049c5cc985b4dd43f01e38899c8f7abf54c2504`, unchanged source21f6ca992f98d817f3eddcc3c3867674d0b3c942 and gate f6be8198d971451eea91647bf853de036b82405ffcb70e18db61ef204e76c898. All three retained output hashes match the failure record. The complete registered denominator contains one resource joint-update cell, durably `unavailable`, with reason “owned worker ended before durable cell disposition; no retry”. It is not a completed or missing-denominator cell.

Actual terminal and cleanup:

- Original Root handle96601 returned1 in chunk86d0cd. Guard final/live are identical, phasefailed, elapsed28,802.760730498 seconds, limit “RuntimeError: registered wall-clock limit exceeded”, original limit28,800 seconds.
- Monitor final/live `child_exit_code` remains null. Separate guard/child_exit.json records125, reason`signal`, workload_pid10200 and a terminal memory snapshot. In `resources.py:235,295–306`,125 is the guard wrapper's initialized result when it receives a signal before observing process.returncode. It must not be reported as an actual worker exit status. Root1, guard-wrapper125 and unknown worker exit remain distinct.
- Native cleanup reports stop return0, verifiedcleanup, unitResult`timeout`, ExecMainStatus125 and emptyControlGroup. The elapsed_time_kill field remains false; it was not rewritten to true to match the wall-clock classification.
- Actual observer evidence hashes join launch, final/live, observer-death, postmortem cells and unsealed journals. Parent stdout equals observer.json and stderr is empty. Earlier original PID metadata for8425/9258/9741/10197/10200 is retained. The reviewer independently observed all five current/proc paths and the original cgroup absent. This proves current absence and joins recorded cleanup; it does not invent per-PID wait statuses or complete histories.

Partial matching and exposure:

- Exactly52 numeric summaries cover `[0,212992)` with208,448 computed and4,544 reused occurrences. Counts are independently summed from original summary metadata, not new numerical runs or new unique-sample claims.
- Three externally recovered/reviewed groups cover196,608 cells. Their immutable review/manifests were hash-joined without redownloading or replaying prior matrices.
- Four local completed batches48–51 cover another16,384 cells. Their pending/payload/completion hashes, extents and original closure-token entries match. These remaining local bodies require the separately planned incremental preservation; this review supplies no new external-recovery claim for them.
- No pending-only batch52 or later matching file exists. Token, origin and score extents match212,992 cells. The terminal fourth group is not falsely treated as externally closed. Completion of the previous callback is source-proven through208,896 cells because batch51 began; last-batch post_batch return and the final delivered counter are not durably proved merely by spool/token extents (`compact_mcm_batched.py:405–415`, `batched_driver.py:166–183`).
- The attempted first graph still requires56,584,576 cells. All seven original graphs require415,968,128 cells (accepted header arithmetic:12,999,004 nodes×32). Journaled progress is0.051203923% of that whole denominator;415,755,136 cells have no completed-journal evidence. “No evidence” is not a claim that no interrupted suboperation or work occurred.

The representation has a failed seal, no completed graph events, and the first MCM has a SystemExit failure. Remaining six graph stages are absent. `unsealed_journals:0` means no representation needed the observer's separate unsealed-journal reconciliation because this representation already had a failed seal (`job.py:557–575`); it does not mean all pair work completed. The selected caller only enters training after all required MCM productions complete (`real_pilot_import_caller.py:554–570`). Training result remains null/unavailable, joint updates and financial fits receive zero completion credit. Training duration/loss/checkpoint quality are unknown, not fabricated zeros.

Measured timings and resources:

| Observed quantity | Value and scope |
|---|---|
| Journal cells / guard elapsed |7.394846695 cells/s over this failed attempt; no full-population forecast |
| Sum of52 inclusive numeric timings |10,896.994408290s;19.545940102 cells/s on that narrower timer |
| Last sampled memory.current |4,280,623,104B |
| Peak sampled memory.current |5,368,373,248B |
| Last unit kernel memory.peak readback |5,370,806,272B; includes charged cache, not guaranteed final lifetime maximum |
| Last child snapshot memory.current |4,281,503,744B, distinct observation |
| Memory events |high1036;max/oom/oom_kill/oom_group_kill0 |
| Peak sampled writable logical/allocated |5,591,281,244B /5,169,836,032B |
| Minimum sampled whole-volume free bytes |31,773,495,296B; includes unrelated activity |

The two timing denominators differ and are not a disjoint solver/overhead profile. Storage and memory observations do not prove continuous bounds or capacity for whole MCM/training. Ancestor memory is not workload-only and is not added to the unit. Final monitor counters/nulls are retained verbatim.

Accounting is an incremental reconciliation: accepted prior68 closed=33complete+35failed, plus this exact newly failed claim, gives69closed=33complete+36failed and no remaining active29 claim. Effective budget100 remains unchanged. This review did not replay all historical claim bodies. No attempt refund, same-identity restart, reopened exposure or fresh-sample credit follows from the failure. The preceding state prefix is retained as the stated historical basis.

Verification:345 focused checks passed on the first attempt;2,564,118 counted verifier input bytes, below16MiB, plus an8,192-byte retained preceding-state prefix. Pinned stdlib interpreter, CPU3/nice10,30CPU seconds,384MiB address-space and4MiB per-file output bounds. The actual input snapshots, script, raw stdout/stderr and artifact hashes are preserved. No scientific/native import, numerical rerun, network, process action, credentials, deletion, Main/Git/STATE/registration or financial-ledger mutation occurred.

No claim is made of numerical method correctness, full-purpose reconstruction, cache-key equivalence, immutable complete spool, whole-MCM completion, neural update, economic benefit, current availability of other remote objects or externally backed-up review files. No additional effort is needed to classify this terminal failure; incremental preservation remains Root's separate next action.
