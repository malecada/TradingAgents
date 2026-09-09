# NLST4 implementation verification

The registered wrapper is `scripts/audit_reevaluate_nlst4_2026_09_09.py`; regression coverage is `tests/predlab/test_audit_reevaluate_nlst4.py`. Implementation follows gate/charter commit `e3c0d63` and the pre-result settlement/creation clarification `e4e60d7`. No empirical correction has been executed by this implementation task. A tested-source commit remains required before `--execute`; the shared `RunContext` enforces committed-source preflight and exclusive output creation.

## Frozen behavior

- The original feature table supplies only pair identity, quarter and new-set membership. The event table supplies only the original entry reference clock. Both complete input files are hashed. The wrapper requires all 3,981 unique pairs and exactly 2,776 new pairs, verifies screening/snapshot membership and exact creation-block agreement, and never enumerates new pool files.
- Each pool JSON is parsed independently; raw logs are not accumulated. Only per-pool features, buyer histories and deployer histories remain in memory. Progress is printed every 250 pools. Existing raw caches and original output tables are never written.
- Entry/horizon selection retains the original interpolated creation and Sync rules. Exact cached entry headers govern decisions. Wallet/deployer return availability is the later of nominal seven-day completion and the exact selected exit header. Missing outcomes never become completed wallet records. A reference-clock mismatch clears decision, availability and completion timestamps, preventing that row from donating to later normalization.
- Every frozen creation remains in the history metadata, even when its pool/header/raw2/window is unavailable. Independently known deployer identity preserves created-pool counts. Unknown identity makes affected later deployer counts unavailable; unknown buyer/outcome history makes affected wallet/deployer-return features unavailable once it could have entered the original strict creation-time history. Decisions before known earliest completion are not tainted by unavailable future outcomes. Known zero counts are never manufactured by dropping unknown priors.
- A raw window at or after the entry block makes its dependent features unavailable. Legacy ownership records remain NaN unless successful retrieval, exact window and Boolean value are proven. Missing pool/raw/header/FX/schema information retains an explicit unavailable row. Missing values remain absent from raw and standardized feature counts.
- Frozen ten signs, six-feature minimum and strictly prior same-quarter normalization are reused. Same-time rows cannot normalize each other. Exact completed five-minute ETH quotes feed unchanged constant-product cashflows at $1,000/$5,000 with the registered LP/gas assumptions.
- The original 1,000-draw quarter bootstrap (seed 7), full-new-cohort q80, NW lag 5 and original T1/T2 thresholds remain fixed. Every bootstrap value is retained, including unavailable draws; any unavailable draw makes primary T1 unavailable. A finite-only quantile is separately labelled diagnostic. Requested, event-available, scoreable, per-quarter and feature denominators are reported. Unavailable required statistics receive `diagnostic_verdict=UNAVAILABLE`, rather than a negative signal conclusion. Missing $5k selected-cohort observations cannot silently disappear from the stress mean.
- `promotion_eligible=False` and `causal_entry_rule_tested=False` are unconditional. Even a synthetic case passing both historical thresholds remains a retrospective ranking/cohort diagnostic. No P1 or holdout evaluation is present.
- Imported RPC/fetch aliases, RPC-pool methods and HTTP transport are hard-fenced during pool reconstruction. Cache-only header lookup raises an actionable error on missing headers. `RunContext` records every consumed source hash, rechecks sources at completion, archives the full cohort, and records the one registered cell.

## Regression evidence

Initial RED command:

```text
PYTHONPATH=. /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python -m pytest tests/predlab/test_audit_reevaluate_nlst4.py -q
```

`nlst4-red.txt` records eight expected assertion failures because the wrapper did not exist. The first implementation passed those eight tests. A second regression phase (`nlst4-metadata-red.txt`) records two expected failures: missing pool metadata aborted the cohort, and unavailable diagnostics lacked an explicit verdict. Both were corrected. The same phase added caller-level archival/hash preservation, dead-pool nominal-completion and command execution-fence checks.

Root review identified two additional denominator failures, demonstrated in `nlst4-denominators-red.txt`: a missing global source omitted the registered cell, and a partially unavailable bootstrap distribution could still pass T1. The wrapper now finishes a blocked cell with the frozen 3,981/1,205/2,776 planned counts when global input recovery fails, without inventing rows. It retains all 1,000 bootstrap values and disallows inferential T1 promotion from a smaller finite subset. Source-integrity failures in the final common provenance check still propagate; no wrapper is allowed to falsely assert that a changed source remained unchanged.

Independent final review identified omitted-prior histories and insufficient creation-block validation. Four RED regressions in `nlst4-history-red.txt` demonstrate invalid prior b24 undercounting, missing raw2 identity/history, missing entry-header history, and an accepted one-block cache mutation. The corrected histories retain independently known creation/deployer facts and explicitly qualify unknown dependencies. `nlst4-history-green.txt` records 18 passing wrapper tests at that stage. A final RED regression (`nlst4-clock-red.txt`) demonstrates the reference-clock normalization-donor leak; its fix and an earliest-completion guard raise wrapper coverage to 20 tests.

Final focused suite:

```text
PYTHONPATH=. /home/malecada/master_thesis/TradingAgents-predlab/.venv/bin/python -m pytest tests/predlab/test_audit_reevaluate_nlst4.py tests/predlab/test_audit_reeval_common.py tests/predlab/test_audit_causal_dex.py tests/predlab/test_nlst2.py tests/predlab/test_nlst3.py tests/predlab/test_nlst_lib.py -q
```

**63 passed in 6.12 seconds**; exact output is `nlst4-offline-suite.txt`. The earlier wrapper plus common-run subset passed 23 tests (`nlst4-green.txt`). `git diff --check` passed. Tests use temporary synthetic files and explicit hand-calculated constant-product/gas cashflows; no original financial outcome was calculated.

## Limits retained

Creation times remain interpolated, the original new set has already been examined, and the global q80 selector remains retrospective. Legacy ownership is unavailable for every inventoried pool. Causal normalization and history requirements can further reduce the scoreable count; unknown deployers in earlier pools can also make later history features unavailable. The resulting coverage has not been computed. Frozen gas/LP assumptions exclude MEV and are not observed live fills. A missing global cohort/anchor/header/market source records the registered cell as blocked/unavailable; a damaged individual pool remains in the cohort with a reason. Synthetic success does not establish empirical data integrity or a positive research result.

The source inventory and exact settlement bounds are recorded in `docs/reevaluation/triage-data-forecast.md`. No additional fetch, April-created cohort, forecast refit, ENet repeat or holdout access is authorized by this wrapper.
