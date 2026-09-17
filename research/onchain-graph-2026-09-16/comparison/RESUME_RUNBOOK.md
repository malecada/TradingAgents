# Source continuation and recurring monitor

The user explicitly authorized resumption, ongoing monitoring and resumption
when the process stops. The app heartbeat
`monitor-and-resume-on-chain-history-download` is active every30minutes, attached
to this task. It should stay quiet while unchanged, report meaningful restarts,
completion or actionable problems, and pause after verified source completion.
This is a local desktop task; checks require the host and app to be available.

## Current continuation

The continuation `eth-graph-source-resume-20260917` is active from fixed source
`e01968240a67632cadaf96f5e0a6341ff0ed2f6a`, launched22:01:25UTC September17.
Launcher607888/startticks3143994, worker608637. Do not duplicate the worker.
Execution checkout:
`/home/malecada/Data/onchain-research/TradingAgents-onchain-resume`.
Consult STATE.md and RESUME_STATUS.md for the latest exact committed source and
launch evidence. Old `eth-graph-source-recovery-20260917` is terminal14complete/
507unavailable; its last process30581 is gone. Never relaunch it.

Before first launch, commit and independently approve the final source/gate/
charter/amendment, push and verify remote hash. Create the new fixed checkout on
Data, use the pinned coordinator `.venv/bin/python -B`, and call
`resume_start.py --source FULL_HEAD` there. Custom policy admission and standard
lifecycle admission must pass. No existing claim or launch intent is reusable.

Inspect `comparison/resume-started.json`, PID/startticks/bootID/command, live
worker/resource receipt, `research_runs/eth-graph-source-resume-20260917/outputs/`
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
remain required. The current one-use9-to10certificate cannot grant another claim.
The standing user request authorizes this preparation and continuation; numerical
experiments, provider switches and trading remain outside its scope.

Investigate unknown causes. Do not automatically restart against source denial,
changed ETags, integrity failures,8GiBguard failure or disk/raw/metadata limits.
Report the concrete condition and next action when it needs user input. Retain
all failed requests and copies in storage accounting. Do not increase resource
ceilings to force a restart. There is no process-level auto-restart or automatic
reboot replay. Monitor checks run when the desktop host/app is available.
