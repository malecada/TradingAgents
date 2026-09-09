# Independent review of evidence and bounded correction controls

Review date: 2026-09-09. The implementation was reviewed in the isolated audit checkout, based on commit `9aee7a95a35e9c037455f4bd829f77279b1c68da` plus the pending repair changes. This report does not certify a later code revision or any empirical result.

**Disposition: the five actionable defects identified during this review have been repaired and checked. No remaining blocker was identified for the fixed, committed development-only correction. The clean-source preflight must pass after the final implementation commit. No strategy is validated by this review.**

## Scope and method

The review covered `tradingagents/predlab/{registry,dm,rollup,evidence,runner}.py`, the bounded correction entry point, its forecast reconstruction dependencies, the actual HARQ battery callers, and the related statistics/ledger changes in xfam, PRX, O6, order-flow, RVIR, smart-wallet, and P1 rollup code. Bybit cache provenance changes were also inspected. Requirements were checked against the committed correction registration, the approved specification and plan, and the preserved audit reports.

Only source, registration metadata, audit documents, and synthetic fixtures were used. No original market/forecast/result store was opened for outcomes, no historical model was fitted, no empirical strategy was run, and no holdout was evaluated. The synthetic missing-source probe reads only the local registration metadata to retain the fixed 16-cell denominator. Its temporary Git repository and temporary Parquet outputs are independent of the research stores.

## Findings and repair verification

| Severity | Original defect | Repaired location and verification |
| --- | --- | --- |
| P1 | ENet reconstruction retained 23 extra hourly timestamps on the final development day. The original battery clipped at the inclusive midnight `2025-03-31`, so the reconstructed expected clock would disagree with all saved hourly cells. | `scripts/audit_correction_2026_09_09.py:156–158` now clips RV input at the original midnight endpoint before building features and comparing the complete forecast clock at lines 183–185. The original `_clip` implementation and reconstruction logic were compared directly. |
| P1 | A truncated S2/S3 input could silently become a shortened successful correction because the strategy engine intersects/clips supplied endpoints. A synthetic 40-day/40-hour source was accepted. | `require_strategy_clock` at lines 88–91, invoked for returns and each forecast at lines 103–108 and 133–135, requires the complete original 1,551-day or 37,201-hour clock and finite observations. The same truncated fixture now stops with `incomplete original strategy clock or unavailable observations`; the endpoint regression test passes. |
| P2 | The executable correction policy could be edited without tripping the clean-source guard. Deleting a blocking policy in a temporary Git checkout allowed preflight under the old key. | `tradingagents/predlab/registry.py:77,89,93–97` resolves the policy against `PROJECT_ROOT`, includes it in the dirty-input rejection, and records its SHA-256. The same probe now rejects `uncommitted executable/configuration inputs: docs/audit/corrections.jsonl`. |
| P2 | A missing RV/OI/funding source raised before ENet cell records were created, losing the registered denominator instead of reporting dependent unavailable cells. | `scripts/audit_correction_2026_09_09.py:153–171,208–211` retains source-group exceptions and emits per-cell stopped statuses. The missing-source probe now returns all 16 registered cell records. |
| P1 | Nested-test selection existed in rollup but actual battery/runner/card records did not declare nesting, so the branch was unreachable and nested comparisons could still use ordinary DM inference. | `tradingagents/predlab/runner.py:129–137,165–169,267–269,302–303,329–332` propagates explicit model-to-baseline nesting and the gate's registered test. Actual HARQ battery callers declare the relation. `tradingagents/predlab/rollup.py:67–79,91–93` respects test eligibility and suppresses selection significance/promotion when inference is unavailable. Synthetic actual-caller, row, card, ledger, and rollup regressions pass. |

The nested-inference repair is appropriately conservative. Clark–West is eligible only for an explicitly nested squared-error comparison with that test registered in the verified gate. Known nested QLIKE comparisons remain `inference_eligible=False` with `primary_test=unavailable_nested_loss_test`; adjusted champion significance is unavailable and promotion is blocked. DM, GW, and CW statistics may remain labelled diagnostics. A valid QLIKE inference design would require separate registration; the repair does not create one retrospectively.

## Controls confirmed for the bounded run

- The fixed grid contains the original three S2 cells and four S3 cells, with 20% target volatility, leverage cap 3, thresholds .50/.52, smoothing 1/24, and 5 bp fees. Actual drifted-notional maintenance costs are covered by the committed allowed-change amendment.
- S2 reports the original specific rule against both HAR and naive20: tracking-error reduction at least 15%, bootstrap p below .05, and Sharpe/drawdown no worse. S3 retains its original exploratory non-graduation restriction. No corrected winner is selected.
- Saved ENet reassessment reconstructs original selected-feature availability, minimum 60 complete training examples, refit cadence, baseline pairing, targets, and full saved origin clock. It does not refit coefficients. Zero/boundary forecasts are preserved unless the original unavailable-model/feature condition is independently established; a mismatched historical sentinel stops that cell.
- Parquet development filtering occurs before DataFrame materialization, and clocks are checked. SHA-256 covers whole input files as provenance; this byte-level hashing is distinct from analytical access to holdout observations.
- Preflight checks the committed gate, registered development bounds, correction policy, and clean executable/configuration inputs. Original artifact hashes are checked before execution, used input hashes are recorded and rechecked after execution, and the exact source commit is retained.
- Existing correction output directories prevent reuse. Return archives strip only the in-memory `BookInputs` metadata, retaining serializable accounting status/version. Result writing uses exclusive creation, and stopped/qualified statuses are retained for unavailable or inconsistent inputs encountered in the registered correction path.
- Legacy invalidated evidence remains qualified by the correction resolver; original gates and numerical artifacts are not rewritten. General forecast inference and selection controls do not retroactively make those historical results valid.

## Verification record

Before repair, the independent synthetic probes reproduced acceptance of truncated clocks and dirty policy, loss of all ENet cell statuses on a missing source, and absent nested metadata. Their original output is retained at `verification/independent-evidence-probes.json`.

After repair:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python docs/audit/verification/independent-evidence-probes.py
exit 0
truncated clock: rejected
dirty correction policy: rejected
missing ENet source: 16 explicit cell statuses
registered nested SE comparison: metadata exported; clark_west eligible
```

The updated probe supplies the new explicit `nested_models` mapping and registered-test metadata. An intermediate invocation mistakenly supplied a list and failed in the probe setup; it was corrected without a product-code change. The original failing observations remain unchanged in the before artifact.

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -m pytest -p no:cacheprovider tests/predlab/test_dm.py tests/predlab/test_rollup.py tests/predlab/test_registry.py tests/predlab/test_audit_evidence.py tests/predlab/test_bounded_audit_correction.py tests/predlab/test_audit_nested_inference.py -q
46 passed in 2.82s
```

Exact after outputs: `verification/independent-evidence-probes-after.json` and `verification/independent-evidence-tests-after.log`. The earlier focused suite passed 33 tests in 1.72s and remains in `verification/independent-evidence-tests.log`.

## Limits of this disposition

This is a source-and-synthetic review, not a claim that the preserved empirical inputs have complete provenance or that all 16 ENet cells will be scoreable. The bounded script must stop or qualify an input failure under its existing policy. The broader legacy strategy gate, including multiplicity calculations using invalidated S1 evidence, is not rerun or reconstructed from the seven-cell correction; the output explicitly disclaims candidate promotion. Historical holdout spending, execution approximations, and the closed research-program verdict remain unchanged.
