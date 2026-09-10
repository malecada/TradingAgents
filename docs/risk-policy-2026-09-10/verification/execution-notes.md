# Execution record

Registration commit: `67eb720` (charter, exact gate and original engine/archive). All39 prior gate objects and the748-row ledger prefix were verified unchanged before implementation. All264 registered file hashes matched. The ignored `data/` warning from `git add` did not omit the tracked gate; `git show HEAD:data/predlab/gates.json` confirmed the committed key before implementation authorization.

Independent checker synthetic tests, before empirical execution:

```text
PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -B -m pytest -p no:cacheprovider -q docs/risk-policy-2026-09-10/verification/test_check_results.py
3 passed in 2.27s
```

The fixture uses a fabricated sinusoidal1241-date price path, no repository market observations. It verifies causal sigma, detects changed control flags/weights and deliberately corrupted funding, and checks the daily-size/new-episode policy's saved arithmetic independently of the evaluator. No empirical comparison has been run at this stage.

Pre-execution verification subsequently passed84 engine/controller tests (42new and42 existing),72 evaluator/runner tests (35new and37 existing),16 new preservation/admission tests and42 independent-checker tests. Existing regressions overlap between suites; the executed counts must not be summed as distinct tests. Independent engine, evaluator, ledger, checker and report reviews are retained. The135 new tests across the four new test groups passed before empirical execution.

Source/document whitespace checks passed after excluding captured `.txt` tool logs. Raw failing-test output retains pytest's trailing whitespace intentionally; its bytes and prior recorded hashes are preserved. This exception affects captured evidence only, not executable source or prose. Available disk space before execution was25GB.

The complete reviewed source was committed and pushed as `2dfb047d5c2f2ff821706736eb9f5508a14e7304` before the run. Registry preflight passed on the clean checkout with gate SHA-256 `0d0aff566b8eb3fa25f4d5be582782e788e4a6568c2cf58769c3041c6e746ff6` and correction-policy SHA-256 `3dcca1e8e4c9edfd1c55c819cb2c930ef785489b1ce10a7c2c8c46fbc1952ea2`.

One empirical execution began at2026-09-10T15:08:34.567525Z. Runtime: Python3.13.13, NumPy2.3.0, pandas2.3.3, PyArrow23.0.1. The exact command was:

```bash
set -o pipefail
PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -u -B scripts/audit_factor_risk_policy_2026_09_10.py --execute 2>&1 | tee docs/risk-policy-2026-09-10/verification/empirical-run.txt
```

The start receipt reserves the immutable output namespace and all72 pending identities. Input admission and the original-control gate precede alternative interpretation. Executable files, gates and correction policy remain frozen during execution; the narrative log may be appended separately.

The complete empirical control gate passed before alternative execution: all144 original sleeve traces and72 original return frames across the four cost assumptions reproduced their pinned references. The immutable `control-parity.json` receipt records every trace check. This is compatibility on the registered saved history, not verification of the original price/funding assumptions or strategy validity.

The single run exited0 and completed at2026-09-10T15:20:32.939946Z, approximately11m58s after its start. All72 identities,288 index evaluations,576 sleeve books and72 frozen-log shadows are complete. The runner appended72 unique financial rows once, yielding820 rows with the original748-row prefix unchanged. Final ledger SHA-256: `4459ddc70d41d9a99db06ab53d9ad4c8f42b6f4d282abd93b4857b4474041927`. Result SHA-256: `245ad6a30022a4ab7f115b1acb52d33dc5537ce43d8c0b6850e5ec25391d1006`.

The precommitted independent checker completed successfully with13,780,216 assertions,576 traces,288 return frames,144 original trace comparisons,72 original return comparisons and72 convention shadows; no unavailable cases or financial replay. Its immutable receipt is `result-review.json`. The precommitted formatter then produced five complete reports with72 primary rows,54 direct contrasts,288 sensitivity rows,144 primary sleeve rows,216 period rows and72 convention rows. Reviewed interpretation is separately authored in `INTERPRETATION.md` and the two independent interpretation notes.

Initial final preservation passed for2,093 empirical output files totaling209,140,604 bytes, including every output hash, the result and prepared-ledger suffix. Findings and cycle closure were appended afterward, and the workspace state was updated with a new snapshot. The original registration criteria and all old gate objects remain unchanged. Git retention and the document-complete preservation check are recorded separately at final staging.
