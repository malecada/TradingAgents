# Full-panel continuation operation

Identity: `eth-full-history-feature-panel-resume-20260922`, cumulative 15/15 once
claimed. Execution checkout:
`/home/malecada/Data/onchain-research/TradingAgents-onchain-fullpanel-resume`.
Interpreter: `/home/malecada/master_thesis/TradingAgents-audit-fixes/.venv/bin/python`.
Use the frozen source recorded in launch-observation.json and claim.json.
The source must be remotely verified and admission must pass before launch.

Launch exactly once in the fixed checkout, with PYTHONPATH set to that checkout:
`<pinned-python> -B research/onchain-graph-2026-09-16/fullpanel_resume/launch.py --source <frozen-source>`.
The outer launcher is a detached finite process. Record its PID/start ticks/boot ID
and full command. Its memory guard creates an exclusive resources/compute directory
and one transient user systemd service for the entire process tree. This changes
no persistent machine or VPS service. Read resources/compute/live.json, child.log,
child_exit.json and final.json; outer output alone is not worker progress.

Before declaring interruption, inspect matching PID/start/boot identity, the
recorded systemd unit and cgroup members, including separately sessioned descendants.
A live unit must never be duplicated. Resource limits are kernel 6 GiB max,
4 GiB high, 512 MiB swap, two CPUs, startup 9 GiB MemAvailable and running 3 GiB
host reserve. A stale monitor lease stops the whole child unit. Verify actual
readback and current progress after launch. Both volumes need 20 GiB free.
A terminal failure or guard receipt is spent evidence, never a retry invitation.

Completed-day metadata republication precedes new extraction; this can take time
without new source progress. Exactly 206 old daily outputs must be byte-identical.
The first new source date is 2022-07-26. Inspect research_runs/<identity>/outputs,
fullpanel/artifacts/checks and cleanup receipts. All old fullpanel execution
artifacts stay untouched. Only the explicit completed-date seed is restored.

Original hash root: `/home/malecada/master_thesis/onchain-fullpanel-hash-scratch-20260922`.
New writable root: `/home/malecada/master_thesis/onchain-fullpanel-resume-hash-scratch-20260922`.
Never copy either root into Git, remove old data or append to the original root.
The old run is failed and its resource receipt empty; never launch any original
fullpanel final review or replay that run.

After compute exits with its unique terminal and final guard receipt, check that
no review process, resources/review directory or independent-report.json exists.
Run the same frozen continuation launch.py command once with `--review`.
The independent check creates no claim and uses its own whole-job cgroup/receipt.
A failed or unknown resource record is evidence only. Independent review verifies
all 1,096 source days, 1,094 graph days, the two boundary exclusions, unchanged
numerical plan, strict phase hashes and exact global old/new identity union.
No historical publication or model accuracy is thereby admitted.

On success or failure, preserve all compact outputs, prefix/check/cleanup/append
receipts, resource logs, terminal and independent report with exact size/SHA256
manifests. Import only after capacity review, preserving previous archive bytes.
Keep global hashes until reviewed closure. Update study STATE and this STATUS,
commit/push and verify remote source. Source metadata backup is not off-device
raw backup. A further interruption requires evidence reconciliation and a new
reviewed continuation, using the user's standing resumption authorization.

The active 30-minute heartbeat stays quiet for healthy unchanged progress,
notifies meaningful progress/failure/completion or required action, advances to
frozen review at compute terminal and pauses after independently verified closure.
Completed source-download and seven-day-pilot monitors remain paused.
