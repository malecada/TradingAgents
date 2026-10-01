# Independent allocated-storage breach closure

Accepted as the expected failed guard outcome for the single `breach01` synthetic attempt. The guard stopped its owned workload after observing an allocated-byte breach; this is evidence of sampled enforcement, not prevention of the overshoot.

The raw final/live receipts are byte-identical. Intent command and every explicit policy field match the final receipt, and all three intent source hashes match current bytes, including the corrected `probe_v2.py`. The actual synthetic payload is exactly 262,144 `x` bytes, SHA-256 `d509bff642a353f88582e8a846ecae041c333b79c57a7a24ff310fbdb7e914e9`. Independent file-plus-directory `st_blocks * 512` accounting is 266,240 bytes, agreeing with the retained breach and exceeding the 65,536-byte allowance.

Final phase is failed with `StorageLimit: storage allocated limit exceeded`, elapsed 0.39052018499933183 seconds, and verified cleanup. Persisted kernel readback is 256 MiB maximum, 192 MiB high and zero swap; CPU IDs are 0 and 1. Recorded memory-event counters, including the later child terminal snapshot, are zero. Guard sampled memory peak is 8,630,272 bytes; the child terminal snapshot is later and reports 8,986,624 bytes, so the former is not a complete memory peak.

The final guard's child-exit field is null because the limit branch precedes normal completion collection. The separately retained child receipt records workload exit -15, consistent with the stop; final cleanup reports unit failed/dead, exit-code status 1 and stop return 0. Monitor 2854815, wrapper 2854818 and payload 2854823 are absent. The exact `onchain-replication-7e20735134614a3c88865e926467735b.service` cgroup is absent, the boot ID remains current, and the active/activating onchain-unit listing is empty. The stale pre-stop `unit_properties` field is not substituted for the later cleanup evidence.

The last successful storage observation and successful-sample peaks still show only the empty directory (4,096 allocated bytes). The separate `storage_breach` contains the actual failed observation. These fields must remain distinct in later reporting.

Evidence SHA-256: intent `4d9506e14443ec540e55403b9f7c8c62a737128883f97214221f1e659975acfe`; final `e7bf8b495dd85ded67be9d879a97392c932fcf83ac4ced4889b0e2578efe3715`; child exit `a90313a23484ae5d1ce49a56f42403450bbd96399b3e987c856580b3b77111d8`; driver result `b4c96c90e5c39437c1dfe92bfe20bc30b2b200b03d84e6f06ffd39127a378ff7`.

No workload, test or verifier was rerun. Live kernel inspection was missed because the attempt had already closed; persisted readback is the kernel evidence. This result establishes neither a hard filesystem quota nor whole-workflow storage coverage, process-memory capacity, registered research ownership or empirical admission. The positive attempt and its separate post-terminal driver error remain unchanged.
