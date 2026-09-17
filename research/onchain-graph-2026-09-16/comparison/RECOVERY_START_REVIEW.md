# Independent recovery startup observation

September 17, 2026. Bounded metadata review; no job mutation, restart, full raw
scan, numerical experiment or change to frozen review/approval artifacts.

**Operational startup verified.** At 13:44:16.433180 UTC, the launch receipt,
Data checkout HEAD and independently verified claim/design source matched
`bd162e1f26450386dab17cb8df3364b1f60b88c2`. The claim's registration SHA256 was
`74ccdb8bbc4acaedde2a4a5ba2a29f26b43d07f67a30fcf778dec811f0cd0e41`.
The retained amendment, approval and cohort input hashes matched that final gate.
The independent structural claim verifier passed against committed provenance.

Launcher PID 30581 had Linux start ticks 151133 and the exact registered launch
command. Boot ID `18ed8946-0984-4865-8cf5-c701a0f7ed65` matched the launch receipt.
Child worker PID 31243 had parent 30581, start ticks 151376, the fixed-source
recovery runner command and CPU affinity `{0, 1}`. The launcher itself is not
CPU-affinity restricted; the executing worker is. These are point-in-time
liveness observations, not guarantees of future progress.

Three dated outputs existed at that observation, all reported complete through
June 29, 2022. The latest output recorded 24 reused responses plus 15 new HTTP
requests and an independent raw-check status of verified. Neither `complete.json`
nor `failed.json` existed. The resource receipt was still empty while its
supervisor remained active; no final peak RSS or completion is claimed.

The first two completed checkpoints were independently reconciled from metadata:

| Recovered date | Reused responses | New HTTP requests | New received bytes | Logical responses |
|---|---:|---:|---:|---:|
| April 19, 2022 | 38 | 1 | 1,225 | 39 |
| June 6, 2022 | 23 | 16 | 18,618,976 | 39 |

Both outputs report complete source status and verified independent raw checks.
Actual manifest hashes match the lifecycle outputs:
`6448da824a19b2a8c086cea5b5893f8a49e40cdda4583c50d3bfc03187ca18b7`
and `427b116c55f8f7503b94d9d8594f3da3086e1ccbdf2a95f817c8d5dd3cf72561`,
respectively. Manifest fields match the outputs; all listed member sizes and
the full file denominator match actual files. Every intent and receipt hash
and request binding was checked. Cached receipt bytes and clocks match the
original source receipts; newly requested receipts have timestamps after launch.
Frozen prefix entries match the new manifest entries and reuse-provenance record.
Reused, new and logical request/received-byte counts reconcile independently.
Raw bodies were not rehashed again during this startup observation.

All seven metadata imports in `recovery-launch-evidence/import.json` matched
source and destination sizes and SHA256 values. Those copies preserve launch,
claim and first-two-checkpoint metadata only. They do not establish a recoverable
off-device copy of either raw corpus.

The active claim consumes the explicit ninth cumulative source allowance.
Original 563 complete dates and original failure evidence remain separate.
Whole-run completion, later source availability, full numerical graph integrity,
historical publication timing, forecast value and profitability remain untested.
The raw stores remain local on Data without a verified external backup. No
automatic restart or additional recovery allowance follows from this observation.
