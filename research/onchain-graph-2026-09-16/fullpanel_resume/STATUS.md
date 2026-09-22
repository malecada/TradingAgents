> September22 18:28UTC monitor correction: the continuation stopped at18:05:58UTC.
> systemd-oomd killed its unit for sustained ancestor memory pressure. All206
> source-day outputs remain preserved; no new source day completed. The4GiB
> memory.high throttle likely contributed; kernelOOM counters remained zero.
> Recovery preparation is under fullpanel_resume2; no worker currently runs.
> The original reboot cause remains undetermined.

# Continuation running — September 22, 2026

The feature worker restarted at **17:51:19 UTC (19:51 Prague)** from remotely
verified source `c739b6f0958e23b90ff5038dd46c9356581369c3` in
`/home/malecada/Data/onchain-research/TradingAgents-onchain-fullpanel-resume`.
Identity: `eth-full-history-feature-panel-resume-20260922`; cumulative 15/15
allowance is now consumed. The dedicated claim exists. Never launch a duplicate
or replay this identity.

Startup is restoring and republishing the 206 previously verified source-day
outputs before new extraction. At 17:56 UTC, the independent startup review verified 70 outputs
republished through 2022-03-11, with no new source day yet. All 1,417 retained
seed artifacts had also been restored with matching hashes. This is
metadata restoration, not lost work or new source progress. All 206 completed
source days and 205 graph days through 2022-07-25 remain preserved; the first new
date is 2022-07-26, with 890 source dates remaining. Publication includes the
normal source/lifecycle checks and can take several minutes.

Outer guard PID 407768, start ticks 420327, boot ID
`6690623b-3299-42d4-8d7b-0847268fbe0c`.
Unit `onchain-resume-6c8905d1544d46efbf56c676221a8722.service` was observed running
with actual kernel memory.max 6 GiB, memory.high 4 GiB, swap maximum 512 MiB
and CPU affinity 0,1. The independent startup review observed cgroup memory around 0.47 GiB,
a fresh monitor lease, zero OOM counters and both filesystem floors satisfied. These are
live observations, not a terminal resource-success verdict.

Read the execution checkout's `resources/compute/live.json` and `child.log`
for current progress. The [launch observation](launch-observation.json),
[admission observation](admission-observation.json), [startup import](startup-import.json)
[independent startup review](STARTUP_REVIEW.md) and [runbook](RUNBOOK.md) bind the execution identity and next actions.
The 30-minute monitor `monitor-full-history-ethereum-feature-extraction` is
active with this exact source and continuation paths. Completed source-download
and seven-day-pilot monitors remain paused.

The original run has a failure-only terminal. Its partial July 26 scratch and
three orphan prefixes remain archived and excluded from execution. The original
hash root is immutable; the separate continuation root receives only new dates.
The user reported OOM with other processes running; its cause remains unknown.
The original resource receipt stays empty. No original fullpanel final-review
launcher should be run.

Independent release review passed. The pinned named offline target passed
**2,584 tests and 97 subtests in 18m31s**. All 2,919 gate inputs and 68 source
bindings were checked before launch; committed admission passed in the completed
Data checkout. Source and checkpoint metadata are backed up remotely; raw bodies
remain local without verified off-device full backup.

After this compute run reaches a terminal state, use only the same frozen
fullpanel_resume/launch.py with --review as documented in RUNBOOK.md. Full-panel
numerical admission and global hash union remain pending. Historical availability,
matched price/model evaluation and financial claims remain unadmitted.
