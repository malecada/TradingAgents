# Independent closed checkpoint-comparison review

Disposition: **accepted as a completely retained failed outer attempt with separately completed tiny numerical/profile components**. The original parent is FAILED, exit 1, and remains permanently closed. No retrospective reconstruction upgrades its original terminal or authorizes a rerun. The evidence supports the specified finite checkpoint comparison; it does not demonstrate full-graph capacity or admit a financial fit.

## Frozen evidence

| Object | SHA-256 |
|---|---|
| execution-result01.json | 85d8bef932d6079a81d0ade096f98f93f034d9df5b40d3fdff704b400862059d |
| retained-execution01.json | 845bc057ceae7b9c1f82fd67e0ce313b3c27e9709ee4ac29dfeb5d2bf3b5bb7f |
| retained-execution01.tar.gz | 124ae811761a9bc87e6388420dd5c391f78180db8f7478162f29ab73eb7e5f45 |
| collect_execution01.py | ea490c685413ef8d497cfb6db21a9f824585499d91472c1207995838313967b5 |
| collector01.log | c5e8bb119dcf7fe4cbdf8d7426d946b8369e978d3561defa89647d36770e7aa8 |
| outer-exit01.json | ac30f809df2b66f777bbe9f4f3815da0d27ecb4ed9ca7928d00c43f2755353e9 |
| original launch01.log traceback | 996c7f7cdb59ce78c0313b9d436649bcdc900a48d49102d35e9437cd2b4dc969 |
| original failed launcher-terminal.json | bc63899808a178d41f5a8e68279f5ee0f98593e84229e22dd515b8267c94a385 |

The single identity is `neural-checkpoint-comparison-20261002-01`, actual source commit `09f2a2066a445d7399dac3165014e0ffd0019269`, release02 `52fe0fb4202bf847cf62b801e1ef52cc6205ec1855c0b8490e5cfb71f6f1e499`, outer session 85714. The reservation, source/manifest/identity receipts and original failed terminal join these values. Independent read-only Git/current hashing verified all 142 selected source bodies against the actual execution commit. No model, checkpoint or numerical array was loaded by the review; all reconstruction used stdlib metadata, bytes and source.

## Actual failure and review gap

The native guard completed with child exit 0 after 17.208608139997523 seconds. Coordinator and all three numerical arms wrote passed terminals. The outer launcher then failed at `native_launcher03.py:196`, directly indexing `ready['file_size_limit']`. The original `guard/cpu_ready.json` genuinely contains only `cpus` and `pid`.

The producer schema explains this exactly: `resources.py:167–171` adds `file_size_limit` only when the physical context is selected. This invocation used the ordinary guard plus the separately reviewed native file-limit wrapper, without a physical policy. The prospective native review and synthetic corpus missed this composition mismatch: the corpus supplied the optional field in its fabricated ready record. The corpus therefore did not establish compatibility with the actual ordinary-guard ready schema. The original prelaunch source readback could not detect a runtime receipt-shape mismatch either.

The KeyError is a real failed parent result, not a native limit failure or a numerical disagreement. Independent evidence of the intended file limit exists: original systemd readback gives both LimitFSIZE values as 4,194,304; coordinator and each arm's original native intent record a successful `resource.getrlimit(RLIMIT_FSIZE)` check before numerical import. No field has been inserted into cpu_ready, and neither the original validator nor the numerical computation was rerun. Future callers must bind the actual selected guard schema or use the independently authenticated native/worker receipt route; they must not retry this identity or relabel it successful.

The metadata-only collector imports the frozen stdlib launcher and invokes its metadata checks, not its launch path. It preserves the failed parent explicitly and authenticates the separate original native/unit/arm evidence. The review independently reconstructed the material joins rather than relying solely on that collector's conclusion. `numeric_replay_or_import: false` in the collector result describes retrospective verification, not a claim that the original engineering attempt contained no numerical computation.

## Completed numerical denominator

All three fresh arm processes completed sequentially with distinct PIDs. Their start/end receipts, terminal identity and manifest/source hashes match. Each phase time lies strictly inside its corresponding arm interval; arm intervals do not overlap.

| Arm | Cases | Exact phase files | Scalar samples | Numerical comparison records |
|---|---:|---:|---:|---:|
| correctness | 10 | 147 | 488 | 3,823 |
| profile_false | 2 | 22 | 241 | None; profile only |
| profile_true | 2 | 22 | 248 | None; profile only |

Independent reconstruction checked every expected phase name/index/mode, monotonic ordering, sample-count sum, ordered case/checkpoint flag, derived configuration hash and all 14 original checkpoint-manifest paths. The misleadingly named `checkpoint_directory` field contains the returned manifest.json path; the paths were checked as retained manifests without deserializing state.pt. Archive verification covers every checkpoint body.

All 3,823 retained correctness comparison records report bitwise equality and max_abs 0. The fixed source oracle compares initial parameters/RNG, outputs/losses, named gradients and input-gradient policy, Adam/state/RNG, checkpoint reload/refusal without mutation, same-arm continuation and inference results. Five cases each exercise checkpoint false and true: shared weekly graphs, input gradients, the declared dropout diagnostic, 28 distinct graphs and regression. Original numerical settings/tolerances and the selected streamed backend remain pinned. Graph encode pre-entry counts are exactly two or 28 on forward; backward counts are zero without checkpointing and two or 28 with it. This is actual finite synthetic numerical evidence, not a financial experiment or general equivalence theorem.

Correctness instrumentation deliberately retains backing allocations. Its observed saved-backing sizes are not process memory requirements. Fresh profile processes carry no such tensor observer, but share the same cgroup and the second case within each profile inherits allocator/cache history. Observed 10-ms sampled current maxima are 416,833,536 bytes without checkpointing and 418,226,176 bytes with checkpointing. Both profile marker sets reach the same cumulative unit peak, 419,291,136 bytes, which includes prior arms and must not be subtracted. These observations do not establish a process-memory reduction. The guard's 250-ms sampled maximum is separately 419,049,472 bytes; the difference illustrates sampling/measurement scope, not inconsistent arithmetic.

## Native controls, cleanup and full retention

Original kernel readback enforces memory.max=memory.high=1,073,741,824 bytes and zero swap. Initial and terminal high/max/oom/oom_kill/oom_group_kill/low counters are all zero. The unit has a two-minute native deadline and 4 MiB hard/soft file limits. The guard retained its 3 GiB ongoing host reserve, 4 GiB startup requirement, 120-second watchdog, sampled complete-owned storage and 10 GiB disk floor. Final recorded free disk is 19,910,078,464 bytes. The CPU quota property says 2s, but `cpu_quota_controller_available` is false; supported enforcement is the actual inherited two-CPU affinity and thread readbacks.

Cleanup stop returned 5 with successful inactive/dead/empty unit-property records, verified guard cleanup and no original cgroup. The reviewer independently observed all eight recorded PIDs absent: 1393712, 1393878, 1393883, 1393885, 1393994, 1394080, 1394084 and 1394136. The original unit path was also absent. No model process was launched or stopped by the review.

Every retained current member was independently matched to the manifest and archive by exact name, kind, mode, size and SHA-256 for regular files. The archive is 5,993,832 bytes and contains exactly 245 regular files and 37 directories, 282 members total, with no links, duplicate names, traversal or unexpected member type. All original files, including the empty native child log, failed launcher terminal, checkpoint bodies, phase records, arm logs and control/closure receipts, remain present. The complete final tree totals 7,539,340 logical file bytes and 8,581,120 allocated bytes including directories.

That complete final tree exceeds the last guard sample by 9,025 logical bytes, 12,288 allocated bytes and three entries. This is retained finalization output, not a reason to substitute the smaller sampled denominator. The outer traceback/exit receipt and collector/result/inventory/archive are separate from the original owned tree and are pinned separately above. The recovery archive proves local retention only; committed external recoverability still needs its separate backup/retrieval evidence.

No actual paper-family claim, empirical successor or financial fit was created. Existing history remains 36 closed paper attempts, 27 complete and nine failed, highest adopted ceiling 64. There is no refund, budget 65 or permission to reuse this closed engineering identity. The initial full-size graph/model capacity, broader paper coverage, original motif/MCM resource route and 1,420 financial fits remain independently outstanding.
