# Independent preservation02 live review

Snapshot: 2026-09-30T04:43:35.672207+00:00. No blocking launch or ownership discrepancy found. Preservation02 is active; no completed backup or eviction is claimed.

Current HEAD and saved preflight source are `0a8a0b664c6291a7b87a2263f15c2785d3e88909`. All 22 original and 12 contextual hashes match. Exactly 33 bound paths match committed HEAD; the sole untracked exception is the exact manifest connection_path with its unchanged expected hash. Only its path/status/hash were checked, not its contents. The saved correction-review hash matches preflight02. This independently confirms the corrected rule; the earlier failed preflight remains preserved.

Preflight02 records accepted and absent graph06 producer/verifier prerequisites, no active unit or reserved preservation identity before launch, 10,023,653,376 bytes available RAM and 17,111,171,072 free disk bytes. Recovery scratch required 14,125,166,592 bytes. The graph07 requirement is 22,396,522,013 bytes, leaving an actual recorded shortfall of 5,285,350,941 bytes. These values justify the current conditional operation; they do not imply an earlier graph06 shortage or guarantee future graph07 space.

The exact live monitor is 809178, with /proc start ticks 7162253. Unit is onchain-replication-01bf2c415ebb4ce1b7929d21e7474575.service. The read-only replication-unit listing shows exactly this one active unit. Guard command targets this directory's reviewed offload.py --worker with the pinned interpreter. This engineering guard has no ResearchRun owner_identity object; monitor start ticks, command and exact cgroup provide the reviewed live identity.

Direct kernel readback confirms 268,435,456-byte memory.max, 201,326,592-byte memory.high and zero swap. Guard records two-CPU affinity, 3 GiB host reserve, 3.5 GiB startup, 10 GiB disk floor and 14,400 seconds. At the sampled live receipt, elapsed time was 61.749244411999825 seconds, peak 201,805,824 bytes and memory.high events 6,660; max/OOM events were zero and no limit reason was set. Throttling is explicit and does not establish completed transfer, adequate throughput or absence of later failure.

Intent binds the unchanged manifest and exact 3,370,971,136-byte graph04 ledger scope, with no automatic retry. The recovered compact manifest equals the local manifest; this proves only that compact roundtrip, not body recovery. At review, the original ledger path still exists, no per-file verified/evicted receipt exists, and neither final guard nor aggregate complete is present. No source body was opened or rehashed by this reviewer.

Freeze HEAD and all 34 bound paths through this exact owner. Do not duplicate or restart it. Later acceptance requires actual full body/restoration/completion receipts, independent compact reconciliation and cleanup. Preservation03 remains separately conditional, sequential after accepted preservation02 closure and fresh capacity; proposed reclaimed bytes cannot count as actual. No financial claim or fit is created by this operation.

| Evidence | SHA-256 |
| --- | --- |
| preflight02.json | e172cac714a5d53e72df25a8885cb6477e829838dc35d4f264c9031108aa7ebd |
| intent.json | 10a18f4d24260f6a0c67f3e9624738bb58de2e0afa36f484aa4e03b26079d6ab |
| bindings.json | 03e46485430c60f931668e00bcab8fd8972db7e28e603aeef04f88659a1a19c9 |
| continuation-bindings01.json | 0e7dd9b3b8f557771124a65c110b8890978626654bd37e040876d4d5b51c14a1 |

Only this review was written. No remote query, body read, launch, test, cgroup action or frozen source/HEAD modification occurred.
