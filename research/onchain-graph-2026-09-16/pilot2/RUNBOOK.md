# Seven-day numerical pilot operation and closure

The user selected step 1 and previously requested ongoing process monitoring.
The authorized task ends after January 2–8 numerical validation and independent
closure. The source download is complete and its separate monitor stays paused.

Execution checkout:
`/home/malecada/Data/onchain-research/TradingAgents-onchain-pilot2`.
Frozen source: `d6b556de45859a1cdd098ad69aad7e161caad96c`.
Pinned interpreter:
`/home/malecada/master_thesis/TradingAgents-audit-fixes/.venv/bin/python`.
Identity: `eth-seven-day-offline-pilot-20260922`; 13/13 cumulative allowance used.
Compute launcher PID 1660211 is bound by `launch-observation.json` to its boot
identity/start ticks. Session 65658 was the original tool session; process and
receipt evidence take precedence after a later wakeup. Both compute and review
use 8 GiB sampled process-tree RSS, two CPUs and no elapsed kill.

## Observe without duplication

Read Data checkout `pilot2/compute.log`, `pilot2/artifacts/results/`, the identity's
`research_runs/` directory and `pilot2/resource.json`. Check PID, boot ID, start
ticks and descendants before deciding a process stopped. Resource files are
created empty at launch and filled only when the guard exits; an empty file is
not a completed resource receipt. Do not run compute again, delete a claim,
replace partial artifacts or edit frozen source. No numerical restart or second
attempt is automatically admitted. If a process disappears without terminal
closure, preserve it and investigate before proposing a distinct continuation.
Source decoding is followed by cross-day uniqueness and seven motif counts;
a long count phase alone does not establish a hang.

## Independent check after compute exits

When the compute process has exited, a unique complete/failed terminal exists,
and resource.json contains valid JSON, run the frozen independent checker once.
Check no prior review process, report or independent-resource.json exists first.
Use the exact source in the execution checkout, with PYTHONPATH set to it:

```bash
PYTHONPATH=/home/malecada/Data/onchain-research/TradingAgents-onchain-pilot2 \
/home/malecada/master_thesis/TradingAgents-audit-fixes/.venv/bin/python -B \
research/onchain-graph-2026-09-16/pilot2/launch.py \
--source d6b556de45859a1cdd098ad69aad7e161caad96c --review
```

Retain its output log, PID/start/boot observation and independent-resource.json.
The report is `pilot2/independent-report.json`. Review never creates another
research claim. Failed-run review preserves evidence only; passed:true does not
by itself mean numerical_pilot_success:true. If independent checking fails,
preserve its log and guard receipt; do not replay or weaken the checker.

## Close and preserve

Reconcile all 17 cells/20 outputs, 8-day uniqueness, seven days' boundary links,
numerical checks, completion-day counts and actual resources. Import complete
new derived artifacts, lifecycle files, guard receipts, logs and independent
report immutably into the coordinator at the same relative paths, checking
source-to-mirror length and SHA-256. Existing files must match exactly; never
replace source or raw captures. Preflight capacity and maximum Git object size.
Retain import manifest and a compact result/independent closure review. Record
failures and unavailable cells without rerunning the experiment. Update study
STATE.md and pilot status. Commit/push reviewed results and verify remote HEAD.
The coordinator startup claim is already an exact mirror; do not count it as
another attempt. Raw remains local and is not a verified off-device backup.

Success requires all seven target days counted and numerical_pilot_success:true
with clean guard exits. Independent checks reconstruct source/dyads and bounded
Local40 subsets, not exhaustive full-day star/triangle recount or canonical-chain
and publication-time proof. No direction accuracy is measured here.

The numerical heartbeat should stay quiet during unchanged healthy computation,
advance to the authorized independent check at terminal completion, notify on a
meaningful completion/failure or required action, and pause after closure. No
full-panel feature extraction, acquisition, market-price join, model fit,
financial claim or trading follows automatically.

Monitor identity: `monitor-seven-day-ethereum-graph-pilot`, created as a 30-minute
thread heartbeat on September 22, 2026. The older source-download heartbeat is
still paused. If this foreground task closes the pilot before a heartbeat runs,
pause the numerical monitor immediately after closure.

## Superseding review status, September 22

Compute completed all17cells/20outputs. The original independent check stopped
on an activity dictionary schema mismatch and is terminal, with its log/resource
preserved. Do not rerun original --review. ACTIVITY_CHECK_CORRECTION.md records
the bounded separately committed correction; its contract/launcher use new
independent-report-v2.json and independent-resource-v2.json paths. The active
foreground task owns preparation/launch; never start a duplicate on a heartbeat.
