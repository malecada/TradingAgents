# Independent live review — storage05

September 30, 2026, 08:43:09 UTC observation. Decision: the active attempt is consistent with the reviewed conditional release. This is not a preservation or eviction closure. Only compact receipts, binding hashes, Git bytes, file stats and process/cgroup metadata were inspected. No source/recovery body, credential contents or network response was read, and no duplicate transfer, job or guard action was launched.

HEAD is frozen at `f07509f6303f5449912673b0f433335b610f8eb6`. All 30 original plus 37 contextual entries match, comprising 62 unique paths. The 61 nonconnection entries also match their bytes in that commit. The sole exception is the exact local/untracked connection metadata hash, checked without printing or reading its contents. The fresh preflight reports pushed HEAD equality; this review independently checked local committed bytes, not the remote branch.

Preflight at 08:41:43.020579 UTC binds the accepted release review and actual accepted storage04 and graph08 verifier closures. It records unused identity, no active unit, 10,006,376,448 available RAM bytes and 18,384,154,624 free disk bytes. That exceeds the full 14,514,860,032-byte recovery scratch requirement and is 3,719,004,510 bytes below the December requirement. Adding the potential 3,760,664,576-byte reclaim would leave only 41,660,066 bytes above that planning threshold before any other disk changes. This is arithmetic, not a capacity reservation or a promise that December will fit. Actual successful closure and a fresh disk check remain mandatory; the deferred roughly 192 MB synthetic checkpoints are not accommodated by this nominal margin.

The exact live monitor is PID 1054259 with independently read start ticks `8598554`; its command is this preparation's `offload.py` launcher. The guard worker command is the same script with `--worker`. The one active replication unit observed is `onchain-replication-8b4f55068c054baf90610a90d5242a49.service`, matching the saved live receipt. No second replication unit or duplicate transfer was observed.

Direct kernel readback confirms memory.max 268,435,456 bytes, memory.high 201,326,592 bytes and memory.swap.max 0. The guard retains 3 GiB host reserve, 3.5 GiB startup, 10 GiB disk floor, two-CPU affinity and 14,400 seconds. At 73.6633 seconds elapsed, sampled peak memory was 201,818,112 bytes with 5,423 high-throttle events and zero max/OOM/OOM-kill events. These are mutable observations, not final resource outcomes. The frozen transport's operation deadline remains 5,400 seconds and payload allowance 8 GiB.

The intent pins the exact manifest and remote prefix for only the closed graph07 ledger. Its original path remains present at 3,760,664,576 bytes with the unchanged recorded stat identity. The recovered manifest exists, but no recovered body, verified/evicted receipt, restoration sidecar, complete or failed receipt existed at this observation. Thus no full recovery, body verification, local removal or remote preservation completion is inferred. The reviewed full recovery/hash and metadata-roundtrip ordering must finish before source deletion can count.

| Durable evidence | SHA-256 |
| --- | --- |
| Manifest | `9b1f35a22c620e95a6db696e167f9aae8b02cb8fe2d7db604c4f6b1c7282a5c7` |
| Preflight | `1c0dee53d6712245a7326c4adcd4eeb78f9ba7cb370541ceee7c6d8fd82a417c` |
| Intent | `5d18d347576602df2ac32376c5ab95219e70e68d69787e351ee6fe8285240587` |
| Accepted release review | `9b801c7d15d8a581cece1ad724df1f0ebc876570b5682e0a5f0dbd6ca788dc52` |

Keep HEAD and all 62 bound paths unchanged while this owner runs. Retain every partial/failure and do not relaunch the identity. Require actual terminal, recovery/restore/completion proofs, original sidecar/source reconciliation and exact owner/cgroup cleanup for independent closure acceptance. Graph09 gate generation remains contingent on that accepted closure; no empirical claim or financial result follows from this live review.
