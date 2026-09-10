# Risk-policy evaluator and runner implementation

Registration `67eb720` preceded implementation. The evaluator and runner implement the committed 72-identity grid with four cost variants, two independent sleeves per evaluation, 72 frozen-log shadows, 54 direct contrasts and 54 descriptive factorial contrasts. No actual financial inputs were evaluated by the implementation worker. No empirical runner execution or commit was performed.

The evaluator retains complete clocks and initial NAV, null Sharpe for valid zero-variance books, explicit risk/exposure/cost denominators, original-target sizing references, accounting/turnover/stop reconciliation, fixed periods and descriptive contrasts. A null metric does not invalidate an otherwise complete cash book. Original raw-target sizing age is explicitly distinguished from a daily resize. Invalid-log signs/order changes remain labeled diagnostics.

The runner admits the exact gate and pinned inputs, checks prior result/source receipts, clips Parquet dates before materialization and requires all original control traces and return clocks. All A00 cost controls precede alternatives. Every sleeve/arm/cost call creates a fresh controller; no signal is rebuilt. A sleeve failure preserves its successful sibling and leaves the index unavailable. An index-only failure preserves both sleeve measurements.

The output namespace is exclusive and its start marker retains all pending identities before admission. Global input/control failures preserve all unavailable identities and prepared failure rows. They append only while the original financial prefix and source/gate/policy remain intact. Corrupted provenance leaves the central ledger untouched and requires recovery review. Normal completion serializes all rows and the result before one locked central append, checks final bytes and publishes the result. Blind reruns are refused. Filesystem failure or process termination can interrupt finalization; preserved starts/receipts require explicit recovery review rather than a second financial execution.

## Synthetic verification

Test-first evidence is retained in `evaluation-red.txt` and `runner-red.txt`. `diagnostic-red.txt` records two missing-output regressions before adding the raw-sizing-reference label and frozen-log sign/order descriptors. `index-red.txt` records the missing index-failure isolation helper before its implementation. Synthetic mutation tests reject altered NAV, charges, targets, volatility and block metadata.

Final command, from `/home/malecada/master_thesis/TradingAgents-audit-fixes`:

```bash
PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -B -m pytest -p no:cacheprovider -q tests/test_audit_factor_risk_policy.py tests/test_factor_risk_policy_evaluation.py tests/test_factor_risk_diagnostics.py tests/test_factor_v2_trace.py tests/predlab/test_registry.py
```

**72 passed in 15.96 seconds**: 35 new evaluator/runner cases and 37 existing risk-diagnostic, V2 trace and registry regressions. Log: `evaluation-final-tests.txt`. Temporary fixtures construct only synthetic targets and control books; the registered-gate test reads metadata without any original forecast, price or financial-value payload. Cases cover A00-first execution, all four arms/costs, exact control parity, sibling/index isolation, missing inputs, prior execution-identity conflict, bad financial prefix, postflight provenance change, all failure identities, safe append and retry refusal. No network or account access occurs. The owned source diff passes `git diff --check`.

## Frozen source identities

| File | SHA-256 |
|---|---|
| `scripts/audit_factor_risk_policy_2026_09_10.py` | `5a541de99ec8a22e343d838a24d74f8550cf20894c0a34ca3ec757ab37c60bcd` |
| `tradingagents/strategies/factor_risk_policy_evaluation.py` | `9aa66c099a6f1b5c616c3e6dd020ddeb28e8f8d0db446dc16e8ca5eecf379a18` |
| `tests/test_audit_factor_risk_policy.py` | `22e7241d847322668bbadc24d9cdf8000625f0083ad865f545f3c0bab19936e1` |
| `tests/test_factor_risk_policy_evaluation.py` | `fc1dc8e9837660d68ec41566151fb03e7e5f8a9487717f0c44c7b121b8eac439` |

The runner's final two-line change after the initial root review explicitly matches the prior result's `git_commit` to the registered original execution commit. Removing those two lines reproduces reviewed SHA `d4f453864c4b0f304ba880de8bc4085d0d6f1cfb7241a22d63ac7d88224ccdfd`. This narrow change and its synthetic admission fixture were sent for final review. No further executable edits are planned before source freeze.
