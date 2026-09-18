# Source continuation and recurring monitor

The user explicitly authorized resumption, ongoing monitoring and resumption
when the process stops. The app heartbeat
`monitor-and-resume-on-chain-history-download` is active every30minutes, attached
to this task. It should stay quiet while unchanged, report meaningful restarts,
completion or actionable problems, and pause after verified source completion.
This is a local desktop task; checks require the host and app to be available.

## Current continuation

The continuation `eth-graph-source-resume2-20260918` is active from fixed source
`ee2a1b806b28b9815eb2347fba7984ec67e208f3`, launched00:21:17UTC September18.
Launcher1059665/startticks3983261, worker1060485. Do not duplicate the worker.
Execution checkout:
`/home/malecada/Data/onchain-research/TradingAgents-onchain-resume2`.
Consult STATE.md and RESUME2_STATUS.md for the latest exact committed source and
launch evidence. Old `eth-graph-source-resume-20260917` is terminal61complete/
446unavailable; its last process607888 is gone. Never relaunch it.

Before first launch, commit and independently approve the final source/gate/
charter/amendment, push and verify remote hash. Create the new fixed checkout on
Data, use the pinned coordinator `.venv/bin/python -B`, and call
`resume2_start.py --source FULL_HEAD` there. Custom policy admission and standard
lifecycle admission must pass. No existing claim or launch intent is reusable.

Inspect `comparison/resume2-started.json`, PID/startticks/bootID/command, live
worker/resource receipt, `research_runs/eth-graph-source-resume2-20260918/outputs/`
and terminal receipts. An empty resource receipt is normal while the guard is
active. Distinguish complete date cells from a lifecycle receipt named complete.
Source evidence is in `comparison/bulk-artifacts/DATE` and sibling
`DATE-attempts` directories. Selected successful bodies are hardlinked to physical
attempt evidence and counted once; failed responses remain retained separately.

## Subsequent stops

If live, never create another worker. For transient transport exhaustion or a
reboot, resume under the user's standing instruction after reconciling partial
and complete evidence and determining no previous worker remains. Do not ask
for routine reconfirmation. Completed/failed identities and raw stores are
immutable. Interrupted nonterminal claims require documented failure-only closure
with retained output hashes, not claim deletion or an implicit replay.

A subsequent continuation must use a fresh registered identity, exact remaining
cohort and valid saved-prefix reuse, with a concrete source-only amendment that
preserves the cumulative lineage and byte budgets. Independent engineering review,
synthetic failure checks, frozen source, committed gate and remote verification
remain required. The current one-use10-to11certificate cannot grant another claim.
The standing user request authorizes this preparation and continuation; numerical
experiments, provider switches and trading remain outside its scope.

Investigate unknown causes. Do not automatically restart against source denial,
changed ETags, integrity failures,8GiBguard failure or disk/raw/metadata limits.
Report the concrete condition and next action when it needs user input. Retain
all failed requests and copies in storage accounting. Do not increase resource
ceilings to force a restart. There is no process-level auto-restart or automatic
reboot replay. Monitor checks run when the desktop host/app is available.
