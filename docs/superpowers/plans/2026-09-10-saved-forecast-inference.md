# Saved Forecast Inference Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development to implement and independently review this plan. The user has authorized execution in the current task.

**Goal:** Complete the fixed sixteen-case forecast reliability diagnostic without changing forecasts or research verdicts.

**Architecture:** A pure analysis module consumes saved corrected forecast/baseline frames and the registered policy. A separate guarded runner pins inputs, creates an immutable output and writes sixteen forensic records. Original model and accounting modules remain unchanged.

**Tech Stack:** Existing Python3.13.13, NumPy2.3.0, pandas2.3.3, SciPy and PyArrow runtime at `../TradingAgents-predlab/.venv/bin/python`.

**Spec:** `docs/diagnostics-2026-09-10/forecast-charter.md`

## Global Constraints

- Sixteen fixed cells; development ends2025-03-31 at00:00UTC; no refit, new forecast, market acquisition or holdout read.
- BootstrapB2000, mean block21calendar days, seed20260910; retain physical-clock masks and baseline-fallback observations.
- Holm family16; unresolved nested primary tests unavailable; no model selection or strategy promotion.
- Only new module, runner, tests and output paths; central748-row financial ledger remains byte-identical.
- Registration/input hashes and reviewed executable source must be committed before empirical execution. Root coordinates all commits and empirical runs.

## Task 1: Pure masked-clock inference

Files: create `tradingagents/predlab/saved_forecast_inference.py` and `tests/predlab/test_saved_forecast_inference.py`.

Inputs: corrected and baseline frames, exact full UTC clock, target/loss definition and registered policy. Outputs: full-clock paired losses/masks, observed and bootstrap diagnostics, stability/effect descriptors, explicit eligibility and failures. Paired resamples must share their indices, preserve denominator masks, and avoid an n_boot×full_clock allocation when a streaming accumulator suffices.

- [ ] Write synthetic tests before implementation: a missing middle hour must remain an unscoreable clock row; fallback prediction equal to baseline must produce exactly zero differential while remaining counted; reversing two forecast errors must reverse the mean differential; multiplying all volume absolute errors by a positive constant must preserve relative improvement and diagnostic p-value.
- [ ] Cover deterministic paired resampling, zero eligible resamples, degenerate equal forecasts, target mismatches, nested-test exclusion and unavailable slots in the sixteen-test adjustment. Deliberately demonstrate failures before implementing missing behavior.
- [ ] Implement the charter equations and fixed stability partitions, reusing loss helpers where their semantics match. Do not call generic DM on incomplete clocks.
- [ ] Run `PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -B -m pytest -p no:cacheprovider -q tests/predlab/test_saved_forecast_inference.py` and retain evidence.

## Task 2: Guarded offline runner

File: create `scripts/audit_saved_forecast_inference_2026_09_10.py`.

Input: committed `audit_saved_forecast_inference_2026_09_10` gate and pinned source artifacts. Output: exclusively created `data/diagnostics/2026-09-10/forecast/` containing start provenance, paired per-origin records, result.json, sixteen-row forensic ledger and artifact hashes.

- [ ] Test refusal without explicit execution, changed input/gate, duplicate output, inconsistent expected cell denominator and out-of-window materialization.
- [ ] Implement preflight before financial parsing, exact hash verification, date-filtered baseline loading, immutable namespace creation, complete unavailable-cell records and final input rechecks.
- [ ] Verify saved non-volume loss means and volume relative-loss ratio against the immutable previous result. Preserve prior MASE means as reference fields.
- [ ] Run new tests together with `tests/predlab/test_audit_nested_inference.py` and existing forecast availability/registry regressions identified by inspection.

## Task 3: Independent review, one run and interpretation

- [ ] Review source for dependence, masking, loss signs, nesting and multiplicity before committing executable code.
- [ ] Root commits reviewed code and runs the CLI once with `--execute`; no other agent launches empirical work.
- [ ] Independently reconcile all16records, origin masks and aggregate metrics, and reproduce selected arithmetic from saved output without rerunning the registered bootstrap.
- [ ] Report all cells and limitations in `docs/diagnostics-2026-09-10/RESULTS.md`; append completion notes only after result verification.
- [ ] Run the shared preservation verifier against the registration commit, commit complete evidence and push the research branch.
