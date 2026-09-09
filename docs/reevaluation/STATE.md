# Lead reevaluation state — September9

Branch research/audit-reevaluation-2026-09-09 in TradingAgents-audit-fixes. Repaired base b1290ae is preserved on fix/system-audit-2026-09-09. User explicitly authorized this reevaluation.

Registration e3c0d63; pre-result settlement clarification e4e60d7; original RNG/P2 clarification4fe113b. Gate audit_reevaluation_2026_09_09 has26 primary cases: momentum12, carry6, liq_fade6, PRX1, NLST4cohort1. Original/cumulative accountingDSR n=74/87/100 and150. No forecast retraining; PRX original rolling formation fits are intrinsic and disclosed.

Current stage: all four wrappers implemented;171 integrated offline tests passed in19.03s. Independent accounting/PRX/DEX reviews have no unresolved blocker. This commit freezes source before execution. NO historical reevaluation outcome has been computed. All source must be reviewed and committed before any --execute run. Original raw stores remain read-only. Common wrappers enforce output exclusion, preflight, date-filtered market reads, complete cell IDs and input checksums. All roots/intervals/criteria are frozen in the gate; NLST4 allows only original development-created IDs' existing settlement data through April15,2025. Never admit April-created pools or new holdout samples.

Owner boundaries: root common I/O/tests, registration, integration/reporting; accounting owner24 cells; statistics ownerPRX50monthly P0; dataownerNLST4 original3981rows. Do not call legacy script mains. No RPC/API, orders, VPS edits, credential reads or empirical source amendments after outcomes.

Next: finish code, independent reviews, targeted integration tests, commit source; then execute each family once and preserve all successes, failures and blocked cells. Append outcomes/corrections/findings before report and push. Current correction policy stays untouched during empirical runs so run provenance remains fixed.
