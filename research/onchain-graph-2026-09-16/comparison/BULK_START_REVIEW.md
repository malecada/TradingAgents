# Independent finite-capture startup observation

Observation time: September 16, 2026, 18:25:28.784907 UTC. This bounded review
inspected process and checkpoint metadata only. The job was not modified,
restarted or rechecked against all raw response bodies.

**Operational startup verified; acquisition remains active.** The source
checkout HEAD, launch receipt, claim source and design source all match
`771dfeb54a90ca0724e345ddd183754e5ca80e2b`. The claim's embedded experiment matches
the retained gate, whose SHA256 is
`3c0544be6b5c83e1192255c947ded86102e06a4deff24f2057f26c8d2b3f2c34`.

Launcher PID 640039 is present with Linux process start ticks 975775, matching
the immutable launch receipt and its exact command. Its child worker PID
640678 has parent 640039, start ticks 976000, the expected fixed-source runner
command and CPU affinity `{0, 1}`. These identifiers distinguish the observed
processes from PID reuse. This is a point-in-time observation, not a guarantee
of future liveness or completion.

All three imported evidence objects—launch intent, started receipt and active
claim—matched their source and destination sizes and SHA256 values in the
import manifest. No source or evidence file was changed by this review.

The January 8, 2022 checkpoint is complete and records the runner's independent
raw check as verified: 145,788,190 received bytes, 106,445,109 stored raw bytes
and 93 files. Its manifest hash independently matches
`6a1969ea60cce88032dc618acdc91f4a986e288f9822c3369e6f7c012c3c28ae`;
the manifest result fields match the lifecycle output, all listed member sizes
are present and the member count matches the check receipt. This observation
verified those metadata bindings; it did not rerun the full raw-byte checker.

Two dated lifecycle outputs were present at observation, through January 9,
2022, whose latest checkpoint status was also complete. No `complete.json` or
`failed.json` terminal receipt existed. The reserved resource receipt was still
empty, as expected while its supervising launcher remains active; that alone
does not establish a memory-limit failure. The earlier imported first-progress
snapshot showed one completed day and is superseded for live progress by this
timestamped observation.

The active claim consumes the fixed single remaining-cohort allowance at 8/8.
No new allowance, automatic restart or replay follows from startup. Whole-run
completion, later source availability, numerical graph integrity, historical
publication timing, forecast value and profitability remain untested. Bulk raw
output remains on Data without a verified off-device backup; launch-receipt
imports and a committed source identity do not establish bulk-data recovery.
