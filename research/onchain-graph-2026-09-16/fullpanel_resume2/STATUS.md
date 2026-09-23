# Second continuation running — September 22, 2026

**September 23, 21:00 UTC — independent final verification running.**
The frozen review launcher started at 20:59:51 UTC (22:59 Prague), after host
available RAM reached 9.4 GiB. Compute is not being replayed. Launcher PID9238,
start ticks12504, boot `df1f8c6b-0492-497f-8d23-bb55c45d37f6`; review unit
`onchain-resume-0f30e5a99d374456ae665f2ea48ee752.service`.
Live checker membership and actual 6 GiB memory high/max, 512 MiB swap and CPUs
0,1 were verified. At 21:00:33 UTC cgroup memory was 1.33 GiB with no OOM events.
See the [review startup observation](review-startup-20260923/observation.json).
No final review verdict exists yet. Never duplicate this review attempt; use
its launch observation, resources/review receipts and independent-report.json.
Full compact evidence import/backup still needs additional main-partition space
above the 20 GiB reserve. Continue the authorized comparison preparation after
reviewed graph closure and preservation; no model has been fitted.

**September 23, 18:57 UTC — compute complete; final review awaiting capacity.**
Compute terminated successfully at 18:35:02 UTC, with 2,193 cells/1,099 outputs
and only the two registered graph-boundary exclusions. All terminal output
hashes were checked. Global uniqueness admitted 1,221,389,903 distinct
transactions with zero duplicates; the 6 GiB guard completed with no OOM events
and verified cleanup. Elapsed compute time was 23h32m40s.

Independent review has not been launched: no review owner, review resource
directory or report exists. Host MemAvailable is approximately 8.6 GiB, below
the frozen 9 GiB startup threshold. Wait until it meets that threshold before
using the same frozen launch.py --review exactly once. Do not lower limits or
replay compute. The main partition has about 20.49 GiB free; the full compact
evidence payload is approximately 0.91 GiB before Git overhead, so full import
would breach the 20 GiB floor. Additional main-partition space is needed before
full import. A small immutable terminal/summary/panel/hash-audit/resource snapshot
is preserved under [compute completion](compute-completion-20260923/observation.json).
All original raw and hash roots remain preserved. Review, full evidence backup
and final closure remain pending; the monitor stays active.

**September 23, 18:24 UTC — all daily extraction finished.** All1,096 source
days and1,094 graph days are published, with only the two registered boundary
exclusions (2022-01-01 and2024-12-31). Retained daily checks cover1,221,389,903
source rows. Every daily output/audit/cleanup hash link was checked. The worker
remains active in the final global identity audit; no compute terminal or final
guard receipt exists yet, and independent final review has not been launched.
No OOM events are recorded; memory-cap reclaim events occurred. Main-partition
free space is about20.5 GiB, so evidence-import capacity must be checked before
copying results. Preserve all hash roots. See the
[daily completion observation](daily-completion-20260923/observation.json).

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
