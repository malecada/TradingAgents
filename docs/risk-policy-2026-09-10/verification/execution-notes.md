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
