# F1 terminal closure and F3 admission handoff

This is an execution checkpoint, not a new experiment or a recovery command.
The same-claim adapter is already attached once. Never invoke it again, delete
the shared attachment marker, or change either execution checkout while active.

## Current owners

- Scientific root: `/home/malecada/master_thesis/TradingAgents-defi-f1`, fixed
  source `b2a1659e2645c6fa6cba03bba6b73d0c74b30bb8`.
- Additional recovery root: `/home/malecada/master_thesis/TradingAgents-defi-f1-recovery`,
  fixed source `e91889c4f7a94d02c7032d1bf164f30f9d398ed8`.
- Original claim SHA256:
  `2ad4dc79f812cafa80486b64a28cea1a45170c99380bb3eff9aaac187a1c6730`.
- Recovery tool session51245; PID78373 at the September16 continuation check.
  PID/session identity is temporary; verify the live command after any restart.
- All preparation, reports and commits belong in `TradingAgents-audit-fixes`.
  Original source/input/output bytes have no second writer.

## Terminal work, in order

1. Establish actual process termination and inspect both original run and entire
   external recovery directory, including hidden members. A scientific
   complete.json alone does not establish successful recovery completion.
   Preserve any failed/pending/contradictory record and its reason. A later PC
   interruption requires a new actual-state investigation; the spent one-shot
   empty-output adapter cannot be used again.
2. For an unambiguous completed recovery, run the existing unchanged structural
   verifier and `protocol_closure_audit.py` against the original scientific
   root. Write a new `f1-closure-audit.json` in the coordination phase directory.
   Do not execute an original runner or calculate a replacement financial book.
3. Independently review actual raw request/receipt pairs, permitted retry causes
   and pacing, canonical clocks, shared-field exclusions, response qualification,
   all registered cells, complete cash accounting and partial unavailable books.
   Retain both execution commits. Structural hash/count checks alone are not
   substantive economic or source review.
4. Import the complete scientific run byte for byte. Verify the exact source and
   destination inventories and every hash; retain all unsuccessful cases. Copy
   the entire external recovery event directory to
   `research_recoveries/defi-depth-f1-restart-20260916/` in coordination. Copy the
   original root's hidden shared marker
   `research_runs/.defi-depth-f1-20260915-recovery-attachment.json` as the separate
   `attachment.json` there. Never manufacture replacement start/complete records.
5. Create `f1-recovery-import.json` in the phase directory from that actual
   inventory. `recovery_chain.verify` requires these fields:
   `source_directory`, `source_members_sha256`, `attachment_source`,
   `attachment_sha256`, `destination_directory`, `destination_members_sha256`.
   Retain capture time, original/recovery source identities and per-member type
   and length as supplementary audit facts. For an unambiguous completed event,
   the original external members are started.json and complete.json; imported
   members add attachment.json. Additional original records cannot be hidden by
   selecting a successful subset. The closure review must attest completeness
   of the actual origin inspection and byte-exact mapping.
6. Verify the full chain using the registered original claim/terminal, config,
   adapter, decision, investigation, recovery receipts and import manifest.
   `recovery_chain.py` also binds source/config bytes to the recovery Git commit
   and checks the imported directory exactly. Retain the actual closure review
   as `reviews/f1-closure-review.md`; the prospective chain review is not its
   replacement.
7. Reconcile actual physical requests, uncertain requests, raw bytes and spent
   selection history. Write F1-RESULT.md separating absolute P, every D, risk,
   source availability, opportunity bounds and implementation/confirmation.
   The original F2 failure remains closed and is never filled or recalculated.
8. Only then run terminal-only `prepare_f3.py` in coordination. Check its exact
   ownership exclusions, inputs, manifests, remaining budgets and committed
   source bindings; obtain independent exact pre-execution review and commit
   the F3 gate. Create a separate detached F3 checkout at that final full commit,
   verify admission/input hashes there and launch once. Do not run F3 merely
   because preparatory synthetic checks passed.

## Interpretation and remaining scope

`MECHANISM-INTERPRETATION.md` explains the frozen hurdles with invented examples;
its independent review does not provide empirical outcomes. F1 and F3 retain
their separate economic questions and fixed primary metrics. F4 remains
data-unavailable under Q4's inspected packet, not economically disproved.
Continue justified remaining work without another go-ahead, within the finite
phase grant. No new orders, paid sources, account/wallet actions, VPN changes,
production edits, confirmation allowance or background automation is granted.
