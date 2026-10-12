# Observer resource-ledger correction

Status: tested source candidate, uninstalled. All original36 claim, terminal, observer, postmortem and durable output bodies remain unchanged. Failed36 remains terminal and spent. This correction changes future observer reconstruction, not the historical terminal or financial interpretation.

The actual36 `outputs/cell-ledger.json` contains its one registered resource-only cell with status `failed`, the original compact-MCM predicate failure reason, `financial_fit_complete:false` and `paper_financial_fits:0`. Its bytes are bound by the exact original `failed.json` output hash and claim hash. The original `postmortem-cells.json` instead marks that cell `unavailable`. `READONLY36_JOIN01.json` retains both dispositions and before/after hashes of all five original claim/terminal/ledger/postmortem/observer bodies. No original file was rewritten.

The omission is in `job.py` observer reconstruction: it gathers batch, source and treatment records but does not consult the registered resource-pilot output ledger. The candidate adds one narrowly scoped helper and merge call before the existing unavailable fallback. It:

- reads the exact claim-registered execution job and selected real-pilot policy, checking their input hashes and bounded extents;
- requires the compact-resource route and one selected real-pilot ledger whose output name and cell ID belong to the original claim;
- checks the actual claim bytes and exactly one existing failed/complete terminal, then reuses `_terminal` to authenticate the claim/terminal/output-hash join;
- reads the exact retained ledger and checks its terminal hash, singleton denominator, original cell ID, failed/complete status, failure reason and strict resource-only/nonfinancial fields;
- rejoins claim, terminal, output and selected input bytes before returning the original row;
- rejects a conflicting existing durable disposition; no absent/corrupt ledger is replaced with an invented failed cell.

No terminal or no terminal-recorded ledger yields no additional row, preserving the existing unavailable fallback. A terminal-recorded missing/corrupt ledger fails closed. A complete resource ledger remains explicitly nonfinancial. The original complete-terminal observer path remains unchanged because it already uses authenticated terminal cells; the helper's complete-terminal case is independently covered. Existing observer records remain subject to their original immutable readback path, so this does not silently revise earlier observer results.

`job.py`, `ORIGINAL_job.py`, `PATCH01.diff`, `INVERSE01.diff` and `SOURCE01.json` retain the source candidate, original and exact inverse. No live source, Git, gate, STATE, registration, claim or network action was performed.

## Focused evidence

`TEST01.log` retains14 passing metadata-only controls. After adding a direct check of the actual observer merge statements, `TEST02.log` records15 passing controls. The final run used the pinned interpreter with a60s timeout and standard-library unittest/AST extraction; no project job module or numerical module was imported, and no arrays or labels were accessed. Synthetic terminal fixtures are test bytes only, not empirical authority.

Coverage includes exact actual36 read-only discrepancy/recovery, failed and complete resource rows, missing/corrupt output, absent ledger/terminal, contradictory terminals, wrong claim hash, modified claim object, changed selected input, wrong denominator/cell/status, widened financial fields, empty failure reason, nonresource route preservation, terminal mutation during recovery, and actual merge conflict refusal. Actual whole-observer execution, cgroup actions and publication were not exercised. Future integration/review and external evidence preservation remain Root responsibilities.
