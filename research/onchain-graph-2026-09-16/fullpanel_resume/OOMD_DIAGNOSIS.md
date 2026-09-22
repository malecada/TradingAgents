# Continuation memory-pressure failure — 2026-09-22

The continuation was killed by **systemd-oomd at 18:05:58 UTC**, not by a
recorded kernel OOM event. This explains this continuation's termination only;
the cause of the earlier reported reboot remains undetermined. No empirical
payload was rerun during this diagnosis, and no frozen source or resource
configuration was changed.

## Retained evidence

The read-only command `journalctl -b -u systemd-oomd --utc --no-pager -n 3`
identified unit
`onchain-resume-6c8905d1544d46efbf56c676221a8722.service` as the victim of
memory pressure in `/user.slice/user-1000.slice/user@1000.service`:
52.41% exceeded 50.00% for more than 20 seconds with reclaim activity.

The final resource receipt remains in the separate execution checkout:

`/home/malecada/Data/onchain-research/TradingAgents-onchain-fullpanel-resume/research/onchain-graph-2026-09-16/fullpanel_resume/resources/compute/final.json`

SHA-256:
`2f45e1104330f3eff2d2d9c70c4c9b4db4326eceb6cf9f3e6e39860bcecc8b06`.

| Recorded field | Value |
| --- | --- |
| Source | `c739b6f0958e23b90ff5038dd46c9356581369c3` |
| Elapsed execution | 875.970121 seconds |
| Kernel memory.max / memory.high | 6 GiB / 4 GiB |
| Kernel memory.swap.max | 512 MiB |
| Last sampled high events | 16,136 |
| Last sampled max / oom / oom_kill / oom_group_kill events | 0 / 0 / 0 / 0 |
| Peak sampled memory.current | 4,447,776,768 bytes |
| Last sampled host MemAvailable | 7,857,930,240 bytes |
| Unit result / main status | signal / 9 |
| Child terminal receipt | Absent; no child exit code was inferred |
| Guard cleanup | Verified, empty ControlGroup, unit failed |

The log ends after restoring the 206 retained dates and starting the July 26
extract phase. It does not locate the exact instruction or allocation at the
time of death. Source/count stage artifacts require the separate forensic
inspection; the word `extract` alone includes more than decoding.

Read-only `systemctl show user@1000.service` confirms
`ManagedOOMMemoryPressure=kill` with a 50% limit and no ancestor MemoryHigh or
MemoryMax limit. `oomctl dump` confirms the monitored user cgroup and the
20-second pressure duration. At inspection, swap was approximately 1.9 GiB
used of 1.9 GiB. That is a later observation, not the swap state at failure.

## Interpretation

The installed systemd 249 primary manuals were inspected locally:
`/usr/share/man/man5/systemd.resource-control.5.gz` and
`/usr/share/man/man8/systemd-oomd.service.8.gz`. They specify that MemoryHigh
aggressively reclaims memory and throttles processes, whereas MemoryMax is
the hard containment bound. systemd-oomd uses pressure stall information and
can kill a descendant cgroup before kernel OOM. Consequently, zero kernel
OOM counters do not exclude an oomd kill.

The peak just above 4 GiB, 16,136 high events and explicit reclaim-pressure
kill strongly support the 4 GiB local throttle as a contributor. The 6 GiB
hard bound was not reached in retained samples. The host reserve monitor did
not trigger because global MemAvailable remained above its 3 GiB floor in
the final sample. Available host RAM does not prevent cgroup-local reclaim
from stalling a throttled workload.

The ancestor pressure measurement also includes other processes. These
receipts cannot establish that the research unit was the sole source of
ancestor pressure or that its unrestricted working set would fit 6 GiB.
There is no retained memory.stat/PSI time series to divide anonymous data,
file cache, swap and other-process pressure. The isolation did retain its
failure receipt and successfully remove the research cgroup.

## Least-change candidate for a separately reviewed continuation

Keep the hard **MemoryMax=6 GiB**, swap maximum 512 MiB, two-CPU affinity,
3 GiB host reserve, 9 GiB startup reserve, heartbeat and whole-unit cleanup.
Change only the successor unit's **MemoryHigh to 6 GiB**, equal to MemoryMax,
so it does not deliberately throttle at 4 GiB while another 2 GiB remains
inside the existing hard bound. This retains the user's 8 GiB outer maximum
and does not alter the host's oomd policy or grant more than the current
6 GiB physical-memory ceiling.

This is a resource-contract change, not an already admitted retry. The
frozen guard rejects `memory_high_bytes == memory_max_bytes`, and its
worker/final checks encode the old values. A successor must update its own
guard, admission, worker assertion and independent resource check together;
the failed version and its receipts must remain immutable. Raising high to
an arbitrary intermediate value merely moves the unmeasured throttle point.
No claim is made that equal high/max makes all 1,096 dates fit or prevents
oomd action caused by other user processes.

Before any separately admitted execution, synthetic verification should
confirm equal-high/max readback under a tiny cap and retain the existing
cleanup, lease and direct-run-bypass checks. Add bounded telemetry for the
unit and monitored user's memory.pressure, memory.events, memory.stat and
memory.swap.current. A successor may add an explicitly frozen early pressure
abort below the observed oomd threshold, with synthetic tests for sustained
pressure and recovery; no empirical threshold optimization is warranted.
The startup gate should also wait for low ancestor pressure, because a
MemAvailable-only gate cannot detect an already-stalled user cgroup.

Do not disable systemd-oomd, change ancestor limits, exempt the workload,
increase swap or blindly repeat the failed configuration. A later hard-cap
failure would establish a different limitation requiring its own evidence.

## Source workaround assessment

Read-only inspection of the unchanged `fullpanel/day.py` and
`pilot/numeric.py` shows overlapping memory representations: a sparse
temporary Parquet file, an Arrow row group plus Python column lists,
integrity/hash sets and accumulated events; the source phase later converts
event tuples into lists, and graph counting retains further structures.
These are plausible memory consumers, not proof of the failing allocation.

A streaming or smaller-batch decoder could eventually reduce Arrow/Python
overlap, but would change the numerical implementation and need independent
equivalence tests for ordering, duplicates, exact transaction hashes,
integrity and boundary behavior. It would not automatically reduce the
counting stage. Given the demonstrated high-limit throttling, such a source
rewrite is not the least-change first response. No decoder or counting
workaround was implemented or evaluated here.

## Verification scope

Checks comprised local status, resource receipt and log inspection, receipt
SHA-256, systemd properties, journal, oomctl, installed primary manuals and
bounded source reads. No tests were needed for this documentation-only
diagnosis; no broad suite, allocation probe, raw decode, empirical replay or
service mutation was performed.
