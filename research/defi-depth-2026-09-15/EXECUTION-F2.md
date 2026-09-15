# F2 isolated execution route

The only permitted F2 run root is
/home/malecada/master_thesis/TradingAgents-defi-f2.
It is a separate detached Git worktree; no F2 claim is created in the coordination
checkout. The original R1 execution worktree stays terminal and unchanged.

Before the first claim, move the clean new root to the committed final reviewed
source, verify every registered source/input/runtime hash there, verify the full
ordinary admission against that full currentHEAD and confirm no F2claim exists.
The source must contain all predecessor terminal evidence, including failedQ3.
Keep the pinned original Python3.13.13 interpreter; set PYTHONPATH to the isolated
root and verify the imported tradingagents package resolves there. At most two
computation threads; no elapsed/CPU watchdog or reused timed financial launcher.

The sole runner is research/defi-depth-2026-09-15/f2_source.py with --source equal
to the complete detachedHEAD. Gates-f2.json fixes1532cells and2611outputs. Exact
source/root/admission/session are recorded in the coordination STATE after launch.
From the instant a claim exists until terminal closure, **no commit, checkout or
merge may occur in this execution root**. All further preparation commits occur
in TradingAgents-audit-fixes. Never weaken the lifecycle's HEAD invariant.

Use the runner's existing foreground tool session to read progress/terminal output;
read-only claim/receipt checks may reconcile its actual status. Do not launch a
second worker or restart a partial/failed attempt. Preserve the complete source,
claim and outputs. Import byte-identical terminal evidence before later admissions.
An unavailable source/financial case is not economic failure. No orders, account
or wallet action, paid resource, VPN change, production work, options inspection
or implicit recurring/background automation follows from this route.
