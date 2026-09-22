# Independent continuation startup review

The continuation is running under its admitted guard. At
2026-09-22 17:56:00 UTC (19:56 Prague), it was restoring the preserved
checkpoint: **70 of 206 daily outputs had been republished byte-for-byte**.
This is metadata restoration, not 70 newly extracted source dates. No new
source-day output, daily scratch or new hash-append receipt existed in this
snapshot. The first new extraction remains 2022-07-26 after seed restoration.

[startup-review.json](startup-review.json) records the bounded read-only checks.
The execution HEAD, claim and gate bind source
`c739b6f0958e23b90ff5038dd46c9356581369c3`. The 68 source files, six lifecycle
runtime files and 2,919 registered inputs match their hashes. The single
continuation claim consumes allowance 15/15 and retains all 2,193 cells and
1,099 registered outputs. No additional claim was made by this review.

Launcher PID 407768 has the recorded start ticks 420327 and boot identity
`6690623b-3299-42d4-8d7b-0847268fbe0c`. Worker PID 408890 is inside the active
`onchain-resume-6c8905d1544d46efbf56c676221a8722.service`, with the exact
registered command, execution directory and CPU affinity [0, 1]. The monitor
lease is fresh. The process inventory finds the expected launcher and worker,
with no additional full-panel executor.

Actual kernel readback confirms memory.max 6 GiB, memory.high 4 GiB and
memory.swap.max 512 MiB. Current cgroup memory was 502,792,192 bytes, approximately
0.47 GiB. OOM and OOM-kill counters were zero; both filesystems remained above
their 20 GiB free-space floors. These are startup observations, not a promise
about future unrelated host load or a final resource-success receipt.

All 1,417 restored seed artifacts already present match the plan's exact sizes
and SHA256 values. The 70 published seed outputs likewise match their archived
bytes and form the expected chronological prefix. There is no completed or
failed lifecycle terminal and no final compute-guard receipt. The finite job
must retain exclusive ownership and continue under the existing monitor.

No raw capture was decoded or recounted, and no global hash body was scanned.
Remaining-date results, exact global uniqueness, final memory/cleanup evidence,
full-panel admission, historical availability and any financial claim remain
untested. The earlier reboot's cause remains undetermined.
