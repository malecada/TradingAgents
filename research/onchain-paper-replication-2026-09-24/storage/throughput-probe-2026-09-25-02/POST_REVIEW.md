# Independent completion and interpretation review

September 25, 2026. **No remaining material finding.** Probe02's bounded
diagnostic completion and reported descriptive gains are supported by the
inspected source-bound receipts. Probe01 remains a separate failed attempt.
No preservation-concurrency change, ISP-capacity claim or financial conclusion
is admitted by this result.

## Independent reconstruction

All 13 source/parent hashes in the contract, all six result receipt hashes and
all five release bindings independently matched their current files. The
completion contract identity matched the reviewed contract, and its three stage
objects exactly matched the separately retained stage receipts. Verification
used only small JSON/source reads, SHA-256 and standard-library arithmetic;
no test suite, transfer, model, decoder or empirical rerun was invoked.

The pooled single rates were reconstructed using total bytes divided by total
single-stage seconds, rather than averaging reciprocal timings:

| Quantity | Independently reconstructed value |
| --- | ---: |
| Pooled single upload | 0.9788309662147804 MiB/s |
| Parallel aggregate upload | 1.112778527144982 MiB/s |
| Upload gain | 13.684442519037553% |
| Pooled single download | 2.3563780255515967 MiB/s |
| Parallel aggregate download | 3.0314771127768165 MiB/s |
| Download gain | 28.649863472869043% |
| Pooled single useful-payload roundtrip | 0.6915595949795011 MiB/s |
| Parallel useful-payload roundtrip | 0.8139851712171798 MiB/s |
| Useful-payload roundtrip gain | 17.70282375177046% |

For the last three rows, the numerator is 64 MiB of unique payload and the
denominator includes both upload and download seconds. It is intentionally not
128 MiB of transferred network payload. The result clearly labels this convention
and excludes packing/local verification from transfer timings.

All four download-verification entries are present. The same source0 SHA-256
appears in single-before, parallel0 and single-after; parallel1 has its own
SHA-256. The reviewed worker checks these against generated-source hashes before
publishing a stage. The generated files have since been removed, so this review
verifies source logic and retained integrity receipts, not a new byte-for-byte
readback of deleted random payloads.

## Terminal and cleanup evidence

The guard records COMPLETE, child exit 0, cleanup verified, 176.33803952699964
seconds, 166,707,200-byte sampled peak, zero memory events and an inactive/dead
unit with empty ControlGroup. The child receipt independently records exit 0
and workload PID 320818. A fresh local read-only check found that PID and the
recorded control-group directory absent. No local `.bin` or `.download` probe02
files remain and no worker `failed.json` exists.

The cleanup receipt contains exactly the four generated remote paths from the
stage receipts, all reported removed following successful `rm` exit. The reviewed
worker can only select these probe02 paths for cleanup. This is command-success
evidence; no additional remote listing was performed by this reviewer. The
parent01 partial objects are outside these paths and its failure/closure hashes
remain bound and unchanged.

The result's initial assertion that the 64 MiB/s cap was nonbinding was narrowed
after review: averages were far below the cap, while burst-level effects were
not measured. The final wording avoids claiming more than the timing evidence.

## Scope of the conclusion

The report correctly discloses one bracketed comparison with competing backup
traffic, connection setup, slower individual parallel connections, before/after
drift, no confidence interval and no isolated link-capacity estimate. The 17.7%
transport gain does not establish a corresponding reduction in full-backup
completion time. A CPU/GPU remedy is unsupported by this narrow diagnostic; the
diagnostic does not prove that either resource is irrelevant to other workloads.

The review did not isolate shared-link utilization, independently measure burst
rates, re-audit the full historical transfer budget, test financial behavior,
verify the replication architecture at runtime, or independently reconstruct
the parent's latest whole-backup progress count. Those claims are separate.
No additional research claim or automatic follow-up run was authorized here.

## Final reviewed identities

| Object | SHA-256 |
| --- | --- |
| RESULT.json | b842cd52c937f85324dfc6fca9af54e0f74abf0931936b007609c2af96704050 |
| RESULT.md | f67f2887af88c535340ba1166b4a2863ed4f9ff265e33b975babbfd913fc9e52 |
| contract.json | 65640889af02ca795882073f97617c126132a97e3eb9596d0acf65a34a01724d |
| probe.py | 332382290567fd104bcd618cf0d98bb3aeeadc43e21fb0ea88d6538020ba5581 |
| RELEASE.json | dc70a94035021e50acb0d54b5aae3590de2e1febf4be4a50e44b0efbf49aa490 |
| run/complete.json | 7d07acca89da63e920d27f722ba26fcd047caab81c1da8fe93707c55dc784c1b |
| run/cleanup.json | cc63b0238a33785e630cdecbc9a4d4c0e5d7493ec07c7d25d639efb3d94254e7 |
| run/guard/final.json | 465c0e78edc5d72dfa5e8aadf079dc5141b40c8d80c8c1ff50fa9257dbf4194b |

Only this new review file was written by this reviewer during the closure task.

## Subsequent backup termination — status correction

The original backup03 controller subsequently became terminal FAILED, independently
of the completed probe02 disposition. Its bulk03 guard recorded a disk-floor
breach: 21,473,370,112 bytes free against a 21,474,836,480-byte floor, a shortfall
of 1,466,368 bytes. The guard elapsed time was 1050.4547542149994 seconds, with
cleanup verified and zero kernel OOM counters. The guard's null child-exit field
is qualified by the separate child receipt, which records exit -15. The controller
retains bulk01/bulk02 as complete and bulk03 through bulk13 as pending or failed.

A fresh read-only check found the recorded cgroup absent and recorded process
IDs 305961, 305966, 326654 and controller 14574 absent. All four embedded receipt
hashes and JSON contents in `backup-terminal-after-probe.json` matched the actual
controller/phase/guard/child records. The snapshot hash is
`6ab10d02e71b2abbf5c6c043f1431f0cacfa6188b64d7e164dce94225ba039e2`.
Its later free-space observation is distinct from the breach-time value above.

The final RESULT.md now supersedes the earlier running-status statement. Its
previous reviewed hash was
`5d4bd95b53f137713811579a31d35a51ec62d093fce53c4e4b88a355fdd2dfc4`;
the corrected hash appears in the table. The probe measurements and RESULT.json
remain unchanged. The background snapshots establish backup activity during
the probe, not current activity after terminal failure.

No causal attribution of disk growth to the probe is supported by these receipts.
The partial archive sizes and cumulative verified-file count were recorded by
the parent task; their bytes/full inventory were not independently reconstructed
in this narrow follow-up. No terminal identity was restarted. Restoring working
space and independently reviewing a new continuation are required before any
backup restart; the successful throughput diagnostic does not bypass those gates.
