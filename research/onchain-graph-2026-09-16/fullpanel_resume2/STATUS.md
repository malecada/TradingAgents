# Second continuation running — September 22, 2026

The successor started at **19:02:19 UTC (21:02 Prague)** from remotely verified
source `87b6ac39d12a4f9a2ac1832f34f68647c52c53c8` in
`/home/malecada/Data/onchain-research/TradingAgents-onchain-fullpanel-resume2`.
Identity `eth-full-history-feature-panel-resume2-20260922` has claimed its single
cumulative 16/16 allowance. At **19:42:00 UTC (21:42 Prague)**, all 206 saved
daily outputs were verified byte-identical and **12 new source/graph days** had
completed through **2022-08-06**: 218/1,096 source days and 217 graph days.
The July 26 counting failure point has been passed; its independent daily check,
hash append and cleanup receipts agree. Full-panel admission remains pending.

The same PID/start/boot and fixed source were verified. Kernel limits remain
6 GiB high/max and 512 MiB swap; sampled live members have CPU affinity0,1.
Sampled cgroup peak is4.848 GiB, with zero high/max/OOM/OOM-kill events.
Data/root free space is37.02/52.24 GiB, above both20 GiB floors. The excluded
previous hash root is still empty. The [recovery observation](recovery-milestone-20260922/observation.json)
preserves output hashes and first-new-day evidence. This is an operational and
receipt check, not a new raw recount or final global hash-union verification.

Outer PID1037781, start ticks846345, boot
`6690623b-3299-42d4-8d7b-0847268fbe0c`; unit
`onchain-resume-1c93e59484014df7ba31aaa38a09de49.service`.
Actual kernel readback confirms memory.max = memory.high = 6 GiB, swap512 MiB
and CPUs0,1. The host startup/running reserves remain9/3 GiB and monitor lease
15 seconds. No machine-wide oomd changes or exemptions were made. Read the
execution checkout's resources/compute/live.json and child.log for live state.
The new telemetry observes unit/ancestor PSI, anonymous memory, file cache and swap.
No final compute resource verdict or full-panel numerical admission exists yet.

The preceding run was killed by systemd-oomd at18:05:58 UTC for sustained user
ancestor memory pressure. Its4 GiB lower throttle likely contributed; other
processes' contribution is not separated. It published no new source day.
All206 source days/205 graph days, partialJuly26 evidence and the empty preceding
hash root are preserved. Its failure-only terminal and frozen independent
failure-evidence review are complete. The earlier reboot cause remains unknown.

Independent successor release review passed. The named pinned offline target
passed **2,682 tests and97 subtests in18m12s**. All2,922 input and68 source bindings
were verified before claim; committed Data admission passed. See CHARTER.md,
RUNBOOK.md, launch-observation.json, admission-observation.json and startup-import.json.
The30-minute monitor follows this exact source/identity. Never duplicate this
worker or replay any claimed identity. New hash appends belong only to the
resume2 root; the original populated root stays immutable and the resume1 root
must stay empty.

After terminal compute, use only this same frozen fullpanel_resume2/launch.py
with --review under the runbook. Preserve compact evidence and both hash roots
until reviewed closure, then verify remote backup. Raw data remains local,
without verified off-device full backup. Acquisition, prices, models, trading,
paid services and production changes remain outside scope.
