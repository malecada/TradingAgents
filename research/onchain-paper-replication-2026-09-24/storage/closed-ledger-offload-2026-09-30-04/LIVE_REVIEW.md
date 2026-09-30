# Independent storage04 live review

September 30, 2026, snapshot at 07:06:25 UTC. **The single observed live preservation owner, release prerequisites and controls reconcile. Completion and recovery are not yet established.** Review used only compact receipts, file stats, hashes and process/kernel readback. No body, test, network operation, job, commit or frozen-source mutation was performed; only this review was written.

HEAD remains `34babb067f65794fbc8c67ed007a836c17cdfb5a`. All 30 original plus 37 contextual entries match, with four matching overlaps and **63 unique paths**. All 62 non-connection paths independently match committed bytes. The sole exact connection_path remains untracked with its bound hash; its contents were not inspected or printed. The saved fresh preflight records matching pushed HEAD, accepted storage03 and graph07 prerequisites, absent execution identity and no active replication unit before dispatch. This review did not repeat a remote HEAD query.

At preflight, available RAM was 9,919,787,008 bytes and free disk 19,179,577,344 bytes. August's 20,814,869,047-byte requirement was short by **1,635,291,703 bytes**, so the conditional need was present. Full recovery scratch admission of **13,962,608,640 bytes** was satisfied. These are launch-time observations, not guarantees of subsequent capacity.

The exact monitor is PID **947069**, and direct /proc start ticks are **8015938**, matching the supplied launch identity. Exactly one active replication unit was listed: `onchain-replication-ec563a3ff94d4c4b85fc2a58d8c7ac6f.service`. Its command invokes the reviewed storage04 worker under the pinned interpreter and cgroup guard. The generic storage guard has no ResearchRun owner_identity object; ownership is established here by this monitor/start-tick/unit/command join. Cgroup subprocesses are part of that single owned transfer, not separate transfer claims.

Direct kernel readback confirms **268,435,456 bytes maximum, 201,326,592 bytes high and zero swap**. The live receipt retains two-CPU affinity, 3 GiB runtime reserve, 3.5 GiB startup availability, 10 GiB disk floor and 14,400 seconds. At 95.820 seconds it reports a sampled peak of **201,576,448 bytes**, **6,410 high events**, zero max/OOM/OOM-kill events and no limit reason. Throttling is present; no zero-event or future-runtime claim is made.

Intent binds the reviewed manifest and exact remote prefix to the sole closed graph06 ledger, **3,208,413,184 bytes**. The recovered compact manifest equals the original byte-for-byte. The original source remains present with unchanged device/inode/size/timestamps and no remote sidecar. There is no body-recovery completion receipt, verified/evicted receipt, local completion, failure marker or guard final yet. Thus only started preservation and compact-manifest roundtrip are established; no full body recovery, eviction or reclaimed capacity is inferred.

The unchanged reviewed worker requires full source and recovered-body hash/size verification, restoration metadata roundtrip, durable verified record/sidecar and source revalidation before unlink. Aggregate completion must roundtrip before final local success. Preserve all partial evidence on failure and never relaunch this identity. No raw source, graph array or graph07 ledger is in scope. Freeze HEAD and all 63 bound paths until terminal reconciliation; graph08 remains unlaunched and its gate must await actual independently accepted preservation closure.

Reviewed receipt identities:

- preflight01.json: `cef61e5c8b860daf3c8a93f4502af773c33d50783c2f618f0946fd7f8446f547`
- intent.json: `72bc67e24ea45c79af757dd074a2611d2d8aef55d1ec50e59b2702b3a3249df1`
- manifest.json: `3b97e8e627a72a25bd640156fc22d8e5110ae2faf8079b0c9625c3c4ee2519fb`

This live review is not terminal acceptance, independent remote re-download or an external-backup completion claim.
