# Throughput diagnostic result

The smaller, separately reviewed probe02 completed in176.338guard seconds with
child0,verifiedcleanup,no memory-limit events and166,707,200-byte sampled peak.
All downloaded random payloads matched their SHA256 identities. Four generated
remote objects and all generated local probe02 payload/download files were removed.
The empty remote directory and compact receipts remain.

| Stage | Connections | Upload aggregate MiB/s | Download aggregate MiB/s |
|---|---:|---:|---:|
| single_before | 1 | 0.980 | 2.444 |
| parallel | 2 | 1.113 | 3.031 |
| single_after | 1 | 0.977 | 2.275 |

Against pooled single-connection timing, parallel aggregate throughput increased
13.7% for upload and28.6% for download. Combined serial upload-plus-download transport throughput increased
17.7% (from0.692 to0.814MiB/s of useful payload). This excludes local verification/packing costs and
does not establish a matching improvement in whole-backup completion time.

The active backup was a competing workload. Each stage recorded its process
types, but total shared-link utilization was not independently isolated. Both
single uploads were close (0.980 and0.977MiB/s); downloads were2.444 and2.275MiB/s.
There is one parallel observation, no confidence interval and no general link
capacity estimate. Observed averages were far below the64MiB/s per-connection probe cap;
burst-level cap effects were not measured. Additional CPU/GPU is not supported as a throughput remedy.

Probe01's128MiB variant remains terminalFAILED after402.892s: one verified single
roundtrip and a parallel-upload timeout at180seconds. Its partial objects and
receipts remain. A full-length remote partial is not counted as verified. The
32MiB successor changed only size/identity/budget, retains this failure and
consumed a separate declared allowance. No financial claims were added.

Decision: leave backup03 source and limits unchanged. The observed parallel gain is
modest and cannot be assumed to translate into a safe full-backup speedup. No
extra compute, paid resource, skipped recovery verification or production
concurrency change was performed. The recorded result is the completed bounded
test, not a claim that network tuning or the research replication is complete.

A final status check found backup03 terminal FAILED after crossing its local
20 GiB free-space floor; guard cleanup was verified. This supersedes the earlier
running-status observation. Verified preservation remains 5,832 files /
18,052,844,567 raw bytes including the reused pilot. Failed batch0034 partials
remain retained. No backup restart occurred. See `backup-terminal-after-probe.json`.
Restoring local working space and reviewing a fresh continuation identity are
required before transfer resumes; the cause of disk growth was not established.
