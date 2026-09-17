# Source continuation checkpoint

The user authorized resumption and recurring monitoring/resumption on September17.
The old recovery is terminal:14complete/507unavailable; see RECOVERY_CLOSURE.md.
Exactly507remaining dates are prepared for bounded transport continuation under
`eth-graph-source-resume-20260917`. The frozen saved prefix is19responses from
August8,2023. All577completed bulk/recovery dates are excluded from new requests.

The new launcher is not yet started. Source implementation and independent
review are in progress; commit, remote verification and admission precede launch.
Planned fixed checkout is
`/home/malecada/Data/onchain-research/TradingAgents-onchain-resume`.

The requested app heartbeat `monitor-and-resume-on-chain-history-download` is
ACTIVE every30minutes in this task. See RESUME_RUNBOOK.md for safe progress
checks and subsequent continuation under standing user authorization. Do not
start a duplicate worker while preparation or an existing worker is active.

Bounds:4attempts per logical request with5/15/45second backoff,8GiB sampled
process-tree RSS,twoCPUs,20GiBfree-disk floor,120GiBraw and2GiBmetadata ceilings.
Successful physical/selected body hardlinks consume one charged stored body;
all failures and historical prefix copies count. No numerical/prediction result.
Raw stores remain local-only; metadata backup is verified separately at commit.
