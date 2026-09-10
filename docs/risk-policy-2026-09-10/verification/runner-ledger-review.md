# Independent runner and ledger review

Verdict: **PASS; no material blocker found in the bounded failure/ledger review.** Reviewed `scripts/audit_factor_risk_policy_2026_09_10.py` SHA-256: `5a541de99ec8a22e343d838a24d74f8550cf20894c0a34ca3ec757ab37c60bcd`. Binding registration: `67eb720305ccddff266df396e61d03dc2fa1985e`.

The runner performs committed-source preflight and exact fixed-grid validation, refuses an existing output namespace, and records all72 pending identities before input admission. All264 pins, the exact original financial-ledger prefix, original configuration receipt and preceding result output hashes are checked before target values enter. Arrow date filters precede pandas materialization. Every A00 variant and both sleeve traces/returns must match the original controls before alternatives run.

Per-sleeve calculation/diagnostic failures retain their identity and reason; a successful companion sleeve is retained, while the two-sleeve index remains unavailable. A global admission, provenance or A00 parity failure records all72 identities as unavailable and preserves the prepared failure receipt. At normal completion, hashes, the original ledger prefix and full registry provenance are rechecked. All72 rows and the final payload are serialized before central append. The append holds an exclusive file lock, verifies the original prefix again, flushes and fsyncs, then confirms exact resulting bytes. The output namespace and unchanged-prefix requirement prevent an ordinary rerun from appending again.

Independent metadata-only probes used the actual `prepare_rows`, `metrics_status`, `unavailable_cell`, `execute` failure flow and preservation schema checker. No engine simulation was permitted:

| Synthetic probe | Verified result |
|---|---|
| All72 complete | 72 unique trial IDs;288 indices;576 sleeves;72 shadows accepted by final preservation schema |
| All72 unavailable | Same exact denominators accepted, with explicit reasons |
| One unavailable alternative sleeve | 71 complete cells/1 unavailable;287 complete indices/1 unavailable;575 complete sleeves/1 unavailable;71 complete shadows/1 unavailable |
| Global input failure, intact synthetic prefix/provenance | Start and failure receipts retain72 identities; exactly72 unavailable rows appended once; no accepted result |
| Same failure with changed source/gate provenance |72 prepared unavailable rows; central synthetic ledger unchanged; recovery required |
| Same failure with conflicting ledger prefix |72 prepared unavailable rows; conflicting synthetic ledger unchanged; recovery required |

All probes passed. Synthetic executions used temporary directories, mocked registration/admission, and a hard-failing simulation function. Existing financial data, outcomes and the real ledger were not read or modified by these probes. Passed worker financial-path tests were inspected rather than redundantly executed.

The final preservation validator accepts the actual runner's configuration wrapper and nested status/reason schema. It validates only identities, byte preservation and availability denominators; numerical evidence remains the separate result checker's responsibility. An interruption or write failure after a prepared receipt/central append can leave recovery-required artifacts without an accepted `result.json`; the runner preserves those artifacts and refuses an automatic replacement/retry. This is an explicit manual recovery boundary, not a successful comparison.
