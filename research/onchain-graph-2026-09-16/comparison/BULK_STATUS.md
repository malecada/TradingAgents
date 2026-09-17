# Remaining graph capture — historical active checkpoint

**Superseded September 17:** the original job is terminal with 563 complete and 521 unavailable source dates. See [closure](BULK_CLOSURE.md) and [recovery runbook](RECOVERY_RUNBOOK.md). The observations below are historical, not current liveness.

The finite capture started at 18:22:04 UTC on September 16, 2026 from reviewed
source `771dfeb54a90ca0724e345ddd183754e5ca80e2b`. That exact source was pushed and
matched the remote branch before launch. Metadata-only admission passed in both
the coordinator and preserved Data checkout. Fifteen focused synthetic tests
passed; independent preflight verified all 36 source hashes, 21 inputs,
1,085 cells and 1,086 registered outputs.

Execution directory:
`/home/malecada/Data/onchain-research/TradingAgents-onchain-bulk`.
The launcher was PID 640039 with Linux start ticks 975775. Its guarded child was
PID 640678, observed with CPU affinity 0–1 and 157,152 KiB RSS during the first
day. That instantaneous RSS is not the final peak. The resource receipt remains
pending until termination; the fixed limit is 8 GiB with no duration kill.

At 18:24:21 UTC, January 8, 2022 was complete and independently checked:
145,788,190 received bytes, 106,445,109 compressed source bytes and 93 files.
January 9 was active; no terminal receipt existed. An independent [startup review](BULK_START_REVIEW.md) at 18:25:28 UTC then
confirmed two complete dates through January 9 and the same active worker.
The final scheduled denominator
is 1,084 new source dates, with 12 existing raw days referenced separately and
the existing January 9, 2024 blocks reused. The download can stop early for
storage or provider denial; unavailable dates remain explicit.

Exact launch receipts, the active claim and first checked day's metadata were
mirrored to the coordinator. Their immutable copy manifests are in
`bulk-launch-evidence/`. They are partial progress evidence, not completed-run
closure or a copy of the bulk raw store. The canonical live artifacts and later
dated outputs remain in the Data checkout. The local claim inventory is now 45;
the remaining-cohort source allowance is consumed at 8/8, with all original
family limits and failed outcomes preserved.

Follow [BULK_RUNBOOK.md](BULK_RUNBOOK.md) for a fresh status check. Do not rerun
the starter or claimed identity. There is no automatic restart, recurring
monitor or future scheduled assistant task. Progress past this timestamp must
be established from the process identity and retained dated/terminal receipts.

Raw output has a 120 GiB ceiling including prior bodies, metadata a 2 GiB ceiling
including its lifecycle reservation, and acquisition checks a 20 GiB free-space
floor plus working reserve. These limits do not guarantee all dates fit. The
bulk corpus has no verified off-device backup; Data and the workspace share a
physical NVMe. The first bounded tranche has its own verified remote backup.

After capture, independently reconcile closure and failed/unavailable dates,
then assemble and admit the numerical graph panel with preserved overlap context,
canonicality, exact duplicate checks and motif validation. Actual prediction
evaluation remains pending under the prepared matched M0/M1/M2 protocol. No
price interpretation, label, prediction-accuracy result or economic conclusion
has been produced by this raw acquisition.
