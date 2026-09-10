# Factor Risk Diagnostics Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development to implement and independently review this plan. The user has authorized execution in the current task.

**Goal:** Explain observed risk, turnover and stop/halting behavior across the fixed factor grid using saved traces.

**Architecture:** A pure sleeve-analysis module reconstructs diagnostic volatility and accounting identities from saved targets and primary traces. A guarded offline runner records every one of36sleeves, dated exposures, stop events and reconciliations. No backtest or alternative policy is executed.

**Tech Stack:** Existing Python3.13.13, NumPy2.3.0, pandas2.3.3 and PyArrow runtime at `../TradingAgents-predlab/.venv/bin/python`.

**Spec:** `docs/diagnostics-2026-09-10/factor-risk-charter.md`

## Global Constraints

- Eighteen original configurations ×BTC/ETH;36primary traces and36target files only, each1240/1241dates.
- No signal regeneration, engine invocation, raw-market loading, alternate Sharpe, risk-rule change or holdout read.
- Nominal risk proxies and component identities are descriptive; do not infer causal cost savings or pooled-account dollar results.
- Thirty-six forensic records; preserve original748-row financial ledger, source, results, gates and cash tails.
- Commit registration/input hashes and reviewed source before empirical execution. Root coordinates commits and empirical runs.

## Task 1: Risk and accounting primitives

Files: create `tradingagents/strategies/factor_risk_diagnostics.py` and `tests/test_factor_risk_diagnostics.py`.

Inputs: one exact target frame, one primary trace, fixed original constants. Outputs: daily exposure/risk/turnover annotations, stop-event table, sleeve summaries and explicit reconciliation failures.

- [ ] Write tests before implementation for causal lag alignment and future-price perturbation invariance, rising volatility under a constant target, entry leverage clipping and preserved warmup.
- [ ] Test the signed turnover identity with N=100,H=60,w=0.5,w_ref=0.5: target-change0, maintenance−10 and actual opening turnover10. Test opposing components and retain netting instead of adding their absolute values.
- [ ] Test separate incoming/applied/closing exposure, charge identities and observed row classes on long and short synthetic traces.
- [ ] Implement pure calculations; never call the backtest, signal or position-builder functions.
- [ ] Run `PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -B -m pytest -p no:cacheprovider -q tests/test_factor_risk_diagnostics.py` and retain evidence of expected failures and passes.

## Task 2: Stop transitions and guarded runner

File: create `scripts/audit_factor_risk_2026_09_10.py`.

Input: committed `audit_factor_risk_2026_09_10` gate and saved factor artifacts. Output: exclusively created `data/diagnostics/2026-09-10/risk/` with provenance, per-sleeve annotations/events, result.json and36-row forensic ledger.

- [ ] Test same-target re-entry, reversal, flat successor, permanent halt, final-row censoring and repeated stops with uniquely counted next-entry charges.
- [ ] Test staged peaks and halt crossings both before and after exit charges, including a false portfolio_stop_hit flag followed by a true permanent halt.
- [ ] Test immutable output creation, changed hashes, missing/duplicate dates and unsupported target transitions; unavailable sleeves remain in the denominator.
- [ ] Implement the guarded runner with explicit `--execute`, registry preflight, hashes checked before parsing and after output, and no writes outside the new output namespace.
- [ ] Run the new tests plus existing factor trace, correction and sizing golden tests.

## Task 3: Independent review, one run and interpretation

- [ ] Independently review alignment, signed accounting, trace stage ordering, masked summaries and all prohibited engine calls before executable source is committed.
- [ ] Root commits reviewed code and runs once with `--execute`; no agent launches an empirical runner independently.
- [ ] Reconcile all36sleeve identities and original totals/halt dates against saved evidence. Review stop classifications and risk-proxy limitations using representative saved events.
- [ ] Add complete results and warranted next questions to `docs/diagnostics-2026-09-10/RESULTS.md`, preserving all original verdicts.
- [ ] Run shared preservation checks, commit complete evidence and push the research branch.
