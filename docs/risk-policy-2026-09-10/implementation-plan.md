# Implementation and verification plan

1. Commit this charter, gate/input hashes, original engine/gate archives and history/design reviews before new code or outcomes.
2. Add a separate causal target controller and a minimal optional engine hook. Preserve the default API, all accounting and original stop anchor behavior. Prove transitions and hand-derived accounting with synthetic tests.
3. Add a dedicated runner/evaluator for the frozen72 identities and four cost cases, strict saved-input admission, A00-first parity, full-clock metrics and independent state per sleeve/variant. Retain failures, contrasts, shadows and an append-once ledger receipt. Synthetic fixtures must exercise failure handling and complete denominator retention.
4. Independently review both source changes and reporting. Verify preservation of baseline source/artifacts, prior gate objects,270 opaque external inputs and financial ledger prefix. Commit reviewed source before the one empirical run.
5. Run only the committed new runner. Retain start/failure metadata and all outputs. Independently reconstruct results from saved traces, verify hashes/denominators/accounting and append the fixed72 ledger records once.
6. Render all primary configurations and contrasts plus the complete cost and sleeve evidence. State remaining data/fill/validation limits and preserve negatives. Append findings and cycle closure, update workspace state, commit and push the dedicated branch.

Ownership: engine/controller and its tests — repair_accounting; runner/evaluation and its tests — repair_execution; preservation/admission and independent review — repair_data; registration, integration, empirical execution, final reporting and commits — root. No agent executes new empirical outcomes before root's committed-source authorization.
