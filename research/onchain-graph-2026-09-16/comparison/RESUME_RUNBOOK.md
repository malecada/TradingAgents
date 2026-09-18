# Source continuation and recurring monitor

The user explicitly authorized resumption, ongoing monitoring and resumption
when the process stops. The app heartbeat
`monitor-and-resume-on-chain-history-download` is active every30minutes, attached
to this task. It should stay quiet while unchanged, report meaningful restarts,
completion or actionable problems, and pause after verified source completion.
This is a local desktop task; checks require the host and app to be available.

## Current continuation

The continuation `eth-graph-source-resume3-20260918` started at
01:12:02.592767 UTC on September 18 from fixed source
`c27a93d7f736cd05e41277d966572bd931e659b8`, pushed and remotely verified before
launch. Launcher PID 1479563/start ticks 4287728, worker PID 1480459.
Boot ID: `18ed8946-0984-4865-8cf5-c701a0f7ed65`.
Execution checkout:
`/home/malecada/Data/onchain-research/TradingAgents-onchain-resume3`.
Consult STATE.md and RESUME3_STATUS.md for current observations. Check the process
identity afresh; never duplicate a live worker or replay a claimed identity.

Inspect `comparison/resume3-started.json`, PID/start ticks/boot ID/command,
worker/resource receipt, `research_runs/eth-graph-source-resume3-20260918/outputs/`
and terminal receipts. An empty resource receipt is normal while the guard is
active. Distinguish complete date cells from a lifecycle receipt named complete.
Source evidence is in `comparison/bulk-artifacts/DATE` and sibling
`DATE-attempts` directories. Selected successful bodies are hardlinked to physical
attempt evidence and counted once; failed responses remain retained separately.

Resume2 is terminal with zero new complete dates and 446 unavailable dates;
its launcher 1059665 and worker 1060485 are gone. Its closure and all earlier
closures are preserved. The resume3 cohort retains exactly those 446 dates and
excludes 638 previously completed bulk/recovery dates. Twelve separate reference
days remain outside that bulk denominator.

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
remain required. The current one-use 11-to12 certificate cannot grant another claim.
The standing user request authorizes this preparation and continuation; numerical
experiments, provider switches and trading remain outside its scope.

Investigate unknown causes. Do not automatically restart against source denial,
changed ETags, integrity failures,8GiBguard failure or disk/raw/metadata limits.
Report the concrete condition and next action when it needs user input. Retain
all failed requests and copies in storage accounting. Do not increase resource
ceilings to force a restart. There is no process-level auto-restart or automatic
reboot replay. Monitor checks run when the desktop host/app is available.

## Inherited control reservation and compact closure

The resume3 contract reuses audited unused space from the 128 MiB control pool
already charged by resume2. It adds no new reservation and carries the prior
metadata counter forward undiminished. Runtime controls have a 64 MiB allowance;
compact closure copies have a separate 44 MiB allowance. Source/static checkout
replicas remain outside the logical family metadata counter, but consume actual
disk space and remain subject to the 20 GiB free-space floor.

Before copying closure evidence, compute actual allocated bytes and ensure all
startup copies, review/import records and closure copies together fit the 44 MiB
allowance. Mirror claim, dated lifecycle outputs, index, summary and terminal/
resource receipts plus a compact per-date hash index. Do not mirror full per-day
raw manifests or the progress log. Preserve them on Data and reference their
hashes. Audit actual allocated bytes again after copying; diagnose any excess.

Any further pool reuse must retain resume2 as the original reservation and add
actual spending by resume2, resume3 and every later consumer. Never reset the
pool audit to the immediate parent or silently add another 128 MiB charge.
See RESUME3_CHARTER.md and resume3-reserve.json for frozen bounds and scope.
