# Finite Data-partition capture

This is a finite job started under the user's download instruction, not a
recurring automation. Source checkout:
`/home/malecada/Data/onchain-research/TradingAgents-onchain-bulk`.

Before launch, require committed source/gates/review, successful metadata-only
admission, a verified matching remote commit and a current Data free-space check.
Use the pinned research Python 3.13.13 environment. The launcher supervises a
child under the unchanged 8 GiB process-tree RSS guard and two-CPU affinity.
No duration kill or automatic restart is configured.

The launch receipt records exact source, command, PID and Linux process start
ticks. It is written once. `bulk-progress.log` receives bounded per-date JSON
progress. `bulk-resource.json` is reserved at startup and filled at termination;
an empty resource file alone is not evidence of a memory-limit failure.
`research_runs/eth-remaining-graph-capture-20260916/claim.json` consumes the one
attempt. Dated outputs are published immediately and remain immutable.

For status, read the launch receipt and compare PID plus `/proc/PID/stat` start
ticks before identifying a process as this job. Inspect the latest bounded log
entries and the count of `outputs/graph-*.json`; each record retains complete or
unavailable status. Read `complete.json`/`failed.json` and the resource receipt
when present. No terminal receipt means active or interrupted, not completed.
Do not restart from this runbook merely because the process is absent.

After completion or interruption, preserve every existing source file, receipt,
checkpoint and failure. Independent lifecycle closure and byte reconciliation
precede any numerical continuation. The per-day checker already validates raw
object/range/schema/manifest bindings, but graph canonicality, duplicate checking,
cross-day boundaries and all predictive measurements remain unadmitted.
Progress and terminal receipts may be imported separately into the coordinator;
do not copy the full bulk raw corpus into Git or claim it has an external backup.
The initial tranche has its own verified remote backup. Raw bulk output remains
on the Data partition, with off-device recovery still unresolved.
