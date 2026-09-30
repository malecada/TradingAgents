# Independent corrected named offline closure

Accepted as a successfully completed named offline verification with cleanup and source preservation verified. The source freeze may release for subsequent engineering. This is limited to the reviewed named profile; it is not the whole legacy test tree, empirical admission, numerical-backend agreement or financial validation. Only this review was written; no tests/jobs, empirical arrays/raw bodies, source edits, staging or commits were performed.

## Completed results

The saved child.log contains both terminal summaries, with no FAILED entries:

| Batch | Passed | Skipped | Passed subtests | Seconds |
|---|---:|---:|---:|---:|
| Standard | 2776 | none reported | 97 | 1037.09 |
| Neural | 876 | 2 | 12 | 770.49 |

Together these are3652passed tests,2skips and109passed subtests. The log explicitly reports75 encountered files withheld for the standard batch and26 for the neural batch; these counts are not added as unique tested files or treated as passing coverage. The two skipped cases remain skipped. `closure01.json` records the exact batch counts and times, source/inventory counts and six receipt hashes, all independently reconciled.

The previous owner-integration offline01 remains failed with all53 original failures retained. Its child.log still has SHA-256 `1637cfb0215dc2a791536ce1a4163edeca9aeb9b9cb71e60d8b3b954c3d96518`, and its closure still retains53failed node IDs. The corrected result is a separate execution under corrected test fixtures, not a rewrite or retry of that identity. Historical and production disk thresholds were not lowered by synthetic fixture capacity.

## Source and ownership closure

At2026-09-30 19:17:02UTC, actual HEAD was `0c100035b96b6e50cf9231d8b018eb67d0bcb2c1`, unchanged at the end of source verification. All1798 current hashes independently matched the manifest and the same committed file bytes. The raw manifest and accepted release review also matched committed bytes. Independently reconstructed1680 tracked-Python,86 required-package and265 named-test inventories matched exactly. These are observations at the freeze-release boundary; later deliberate engineering changes do not alter this historical statement.

Final and live receipts are byte-identical terminal snapshots. The owner identity joins kind `synthetic-disk-fixture-correction-offline01`, the actual source above and manifest SHA-256 `68b146f63204502c55bf04effcadca906f5e0a30cf54cb3fe34f8c881484af64`. The command remains repository `.venv/bin/python -B scripts/verify_offline.py`. Final phase is complete, child_exit_code0 and cleanup_verified true. child_exit.json reports verifier/workload PID1116982, exit0, reason `workload exited` and no snapshot error; its terminal memory snapshot exactly equals the final snapshot. cpu_ready identifies wrapper1116978 and CPUs0–1; release records verified kernel controls, consistent with the earlier independent live observation.

Monitor1115110/start tick1152453 is dead: its /proc directory is absent. Known wrapper1116978, verifier1116982, standard child1116983 and retained neural child1502945 are also absent. The host boot ID matches the receipts. The exact cgroup for `onchain-replication-9220914c0ad0439cb1320854e0e6931d.service` is absent, and an independent systemd query returns no active or activating replication units.

The cleanup stop command returned5, which is preserved rather than represented as0. Both terminal and cleanup unit readbacks show inactive/dead, empty ControlGroup, ExecMainStatus0 and Result success. Together with independently absent cgroup/processes, this supports completed cleanup of an already terminated unit; the nonzero stop return does not establish a surviving worker. The terminal memory snapshot is a pre-cleanup observation, not current memory retained by an active cgroup.

## Resource outcomes and exact evidence

Guard elapsed time is1810.801784358seconds, below the3,600second limit. Peak sampled cgroup memory is2,509,381,632bytes. High/max/OOM/OOM-kill/group-kill counters are all zero, elapsed_time_kill is false and limit_reason is null. Retained kernel controls are3GiBmax/2.75GiBhigh/zero worker swap with two-CPU affinity. Final available host RAM9,877,512,192bytes and disk19,802,480,640bytes exceed the active3GiB/10GiB floors. This observed envelope does not establish production sampling feasibility below its separate20GiB requirement or resource bounds for new empirical workloads.

| Artifact | SHA-256 |
|---|---|
| closure01.json | `482491fe4ab6e9a425ca546b697a5f561b822e0af28e22d7c8b449044fe1fe23` |
| offline01/child.log | `9b51ca08dc6c537b147d47a835154f5cf059284588fee6af69339d56508b5314` |
| offline01/final.json and live.json | `086933401acc95ffb07cce9a16a9e3f1ea32fbf8a7bb9a8114ec5c77b7e2808e` |
| offline01/child_exit.json | `06d8f5509032e8bf71b9529d2c2571a5005d83fdc2017b2cce9eca2df4514006` |
| offline01/cpu_ready.json | `6d465e5b09fb56fdb6c0e65151ec34f7e7f10436adb74a47d08de773774dd582` |
| offline01/release.json | `82560e2694628ad002f9cc4b76fe2cd7b1b545cc825269f01057f04c6fe268b5` |

Preserve this completed identity and every original failure/receipt unchanged; never relaunch either offline01 identity. Independently prepared isolated candidates outside the named test inventory are not promoted to admitted consumers by this result. No empirical trial allocation, graph/body rerun, raw-semantic verification, numerical continuation or financial fit was admitted by the named engineering verification. Zero strategies are validated.
