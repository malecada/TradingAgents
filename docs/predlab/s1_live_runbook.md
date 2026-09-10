# S1 execution and paper measurement — version 2

The September 9 correction remains local source work. A September 10 read-only VPS audit verified legacy paper/execution code, absent v2 journals and an absent funding store; no deployment occurred. The current integration and manual rollout are documented in `docs/operations/OPERATIONAL_INTEGRATION_2026-09-10.md` and `docs/operations/MANUAL_ROLLOUT.md`. Historical instructions and journal definitions remain available in Git; the current execution contract is documented in `docs/audit/execution-repair.md`.

## Journal boundary

The paper trader writes `predlab/s1_paper/journal_v2.jsonl` and `journal_champion_v2.jsonl`. The executor reads the latter and writes `predlab/s1_live/journal_live_v2.jsonl`, `fills_v2.jsonl`, `order_state_v2.jsonl`, `closure_v2.jsonl` and `journal_dry_v2.jsonl`. The account's `halt.flag` and day-equity baseline remain shared safety state. Testnet execution uses `predlab/s1_testnet/` for its own execution state. Existing journals are never rewritten or copied into the new files.

Paper net returns require complete held closing prices and observed daily funding. Both loaders read the existing local `xsect/funding/` store; an absent or stale store produces explicit incomplete measurement. The event-coverage check records its inferred cadence because historical exchange schedules are unavailable. No funding fetch is triggered by the paper trader. Gross close/mark diagnostics are not funded returns. The base/overlay accounts include actual drift turnover, fees and signed funding; a missing measurement or clock gap cannot be silently converted to zero. The volatility scale requires 20 contiguous corrected base-net observations.

## Execution interpretation

A current paper row must name yesterday's as-of date and today's trade day, with version 2 and complete desired marks no older than 10 minutes. Sizing additionally fetches bid/ask quotes with exchange timestamps, requiring coverage of every desired and held symbol within 90 seconds. Missing prices cause WAIT. The live scale remains capped at 1.1, with the uncapped requested scale preserved separately. Whole-book risk includes positions that could remain if a departure order fails and frozen targets not yet filled. The per-name cap remains 5% of gross for every book size.

`run --dry-run` writes only its separate hypothetical journal. It places no orders, changes no leverage and consumes no live completion or day-equity key. An ordinary `run` first validates one-way position mode and handles outstanding order intents. `done` means actual positions were reconciled to the stored target quantities. `incomplete` means residual positions, rejected orders, working orders or unknown execution remain. A journal date alone is not proof of completion.

Order intents are durably recorded before POST and assigned stable client IDs. GET requests may retry; an order POST does not. Unknown execution is resolved through order-status lookup. A lookup that does not find an uncertain order does not authorize a second submission. Do not delete or hand-edit intent records to force a retry. Definitively rejected orders can be retried on a later wake against actual residual positions. The executor assumes a dedicated account, with no other host placing concurrent orders.

`status` reports incomplete reconciliation, stale rows, halt flags and positions. `compare` reports gross fill-versus-paper-mark differences; it marks incomplete fee coverage and does not turn missing commissions into a zero total.

## Emergency closure

`predlab_s1_live.py close-all` writes `halt.flag` before account reads and orders, checks one-way mode, resolves outstanding order states, then attempts reduce-only closure. The response reports success only after positions are actually zero and no unknown or working order remains. `closure_v2.jsonl` records residual positions when closure is incomplete.

Ordinary wakes remain halted while the flag exists. Repeat `close-all` to retry a definite rejected close; the flag remains set. Unknown submissions, unavailable position snapshots, hedge mode, untradeable instruments or residual quantity below lot precision require account evidence and operator action. Inspect and resolve the cause before explicitly resuming. Never interpret a halt flag as evidence that the account is flat.

Any production deployment and system service edits require separate operator execution. The implementation performed no VPS mutations or live/testnet account operations and makes no deployment-health or strategy-validation claim.
