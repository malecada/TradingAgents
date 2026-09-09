# Audit lead reevaluation implementation plan

> For agentic workers: use independent agents with synthetic regression tests and independent review. The user's request authorizes this bounded empirical correction; routine implementation choices need no renewed approval.

**Goal:** Determine which fixed lead rejections survive the audited measurement contracts, reporting every cell and qualification.
**Architecture:** Isolated research branch on repaired source; three family wrappers share immutable-run/provenance helpers. Raw stores remain in their preserved original worktrees.
**Tech Stack:** Existing Python3.13.13 environment, numpy/pandas/scipy/statsmodels/pyarrow, pytest, Git.
**Spec:** docs/superpowers/specs/2026-09-09-lead-reevaluation.md and committed audit_reevaluation_2026_09_09 gate.

## Global constraints

No secret reads, RPC/API fetches, live orders, VPS mutation, model fits, new signals or holdout evaluation. Keep every original gate and result immutable. All26 registered cells count even if invalid or blocked. Do not call a legacy script main or legacy momentum fast engine. Source must be clean and committed before results. Reuse prior779-test verification, then run meaningful new wrapper tests and impacted suites.

## Tasks

- [x] Read ledgers, gates, prior audits and source; classify affected versus unaffected leads; freeze full grids and candidate exclusions.
- [x] Commit charter and one new gate before results.
- [ ] Root: implement scripts/audit_reeval_common.py and tests/predlab/test_audit_reeval_common.py. Tests must reject an uncommitted gate/source, existing output, duplicate cell, changed input hash and post-March2025 market rows; completed summaries must include every declared cell and source/output hashes. Expose RunContext(family), read_market(path,start=None), track(path), finish(payload,cells), with cells as list of {id,config,metrics}; full documented interface sent to owners.
- [ ] Accounting owner: scripts/audit_reevaluate_accounting_2026_09_09.py and tests/predlab/test_audit_reevaluate_accounting.py. Use corrected portfolio.fast_weekly_portfolio, carry.run_ls_portfolio and liq_fade.pnl_from_weights. Synthetic weekly100/110/121 versus flat companion must equal actual held units; missing held price fails; complete calendar and daily compounding preserved. Verify exact12/6/6 grids, original/current DSR counts and gate short-circuit status; preserve all cells and forensic cost/convention replays.
- [ ] Statistics owner: scripts/audit_reevaluate_prx_2026_09_09.py and tests/predlab/test_audit_reevaluate_prx.py. Test corrected EG selection differs from ordinary residualADF on controlled fixtures, zero-selection month is retained, total50month grid is fixed, no P1 call exists, stationary-bootstrap seed deterministic. Capture full monthly counts and original/dependence diagnostics.
- [ ] Data owner: scripts/audit_reevaluate_nlst4_2026_09_09.py and tests/predlab/test_audit_reevaluate_nlst4.py. Test absent ownership does not become zero; raw2 entry-block fence; completed-history known time is actual exit; future pool mutation cannot change prior causal score; missing header/FX produces explicit unavailable record. Preserve original3981/2776 membership and global-q80 retrospective qualification.
- [ ] Independently review wrappers and provenance, run targeted offline tests, commit all source before outcomes. Prevent concurrent source edits during runs.
- [ ] Execute registered families once, verify saved artifacts and unchanged input hashes, append every outcome/blocked cell to ledger and correction records.
- [ ] Write full reevaluation report, findings addendum and current workspace status; report gate reversals separately from validated strategies; commit and push research branch. Update thesis only if materially necessary and then push private backup.
