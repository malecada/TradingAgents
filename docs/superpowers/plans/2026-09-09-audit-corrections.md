# System audit corrections implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development to execute independent tasks, followed by spec and code review. The user has approved execution of the audit plan; routine choices do not require renewed approval.

**Goal:** Repair the confirmed system defects, make affected evidence resolvable, execute the registered bounded correction, and reconcile the thesis.

**Architecture:** One isolated branch combines predlab and xsect source, while original worktrees, raw stores and results remain intact. Small shared accounting/availability helpers enforce contracts at actual callers; append-only correction metadata carries historical limitations.

**Tech Stack:** Python3.13.13, numpy/pandas/scipy, pytest, Git, LaTeX/latexmk.

**Spec:** docs/superpowers/specs/2026-09-09-audit-corrections.md

## Global constraints

- No secret reads, live orders, VPS changes, new strategy search or unspent holdout use.
- Preserve every original artifact; new empirical output only under the committed correction key.
- Tests exercise actual behavior with hand-derived expectations. Record failing regression before implementation, then targeted green tests.
- Parallel owners do not edit one another's files. Commits are coordinated by the root after review; do not stage another owner's work.
- Use the existing sibling predlab Python executable from this checkout with PYTHONPATH pointed here. Logs stay in docs/audit/verification or root audit artifacts, not raw data directories.

## Tasks and ownership

### A. Executable accounting (accounting agent)

Files: tradingagents/predlab/{pp,opt}.py; tradingagents/xsect/{portfolio,trend,carry_xs,ls_common,liq_fade,combo}.py; tradingagents/backtesting/{engine,runner}.py; scripts/predlab_pp_dev.py; overlay helpers in scripts/predlab_opt_o4.py, predlab_correction_aug24.py, predlab_champion_backtest.py and predlab_bybit_r1.py. Add a focused shared accounting helper only if needed. Own corresponding regression tests.

- [x] Pin audit counterexamples: first loss[-.2,0,0] has drawdown.2; weekly units in prices100/110/121 and100/100/100 finish1.105; doubling/halving hourly returns compound0; caller S2/S3 receives expm1(logreturn); inactive days remain in Sharpe.
- [x] Implement initial-capital NAV, explicit held-unit/turnover semantics, missing-held-price failure, complete clock, single fees, signed funding and consistent aggregation per spec.
- [x] Verify existing causal lag tests, new counterexamples and impacted engines; preserve original result JSONs and record changed historical contracts.

### B. Forecast and causal data (data agent)

Files: tradingagents/predlab/{tier2,runner,losses}.py; scripts/predlab_nlst{2,3,4}_features.py; scripts/predlab_nlst_dex_p0.py; tradingagents/dataflows/{sentiment_store,onchain_store,coinmetrics}.py; scripts/backfill_alpaca_news.py and ingest_hf_bitcoin_news.py; fetch/RV robustness functions if independent. Own corresponding tests. Coordinate shared runner statistics policy with root.

- [x] Regression: missing selected ENet feature yields explicit unavailable value; ProbClip preserves it; runner assigns baseline on the identical timestamp and reports fallback without losing an observation.
- [x] Regression: mutating a later pool cannot change an earlier actionable score; unknown raw feature is not counted as known; changing end-of-day ETH close cannot alter an earlier intraday entry.
- [x] Implement prospective availability/version preservation and reject conflicting overwrite; strict known availability differs from an assumed lag. Never refetch or replace historical stores.
- [x] Verify model/runner, mutation, timestamp and versioning tests; document the need for historical qualification where genuine vintages are unavailable.

### C. Execution and paper parity (execution agent)

Files: tradingagents/predlab/{live_exec,binance_client}.py; scripts/predlab_s1_{live,paper}.py; execution runbook; corresponding tests. pp/opt are accounting-owned; import only stable signal/universe helpers and coordinate added interfaces.

- [x] Reproduce rejected batch, failed flatten, dry-to-live transition, partial marks, stale dates, unknown503 retry from the audit with fake exchange state.
- [x] Make completion depend on actual reconciliation; preserve incomplete state, stable order IDs/status lookup, and accurate residual closure. Prevent blind POST retry and validate signal/price age and account mode.
- [x] Share monthly universe/signal definitions using explicit trade date. Version the corrected journal and expose funded/net returns, fees, scale and measurement coverage under the agreed accounting contract.
- [x] Verify dry-run never places orders or consumes live state, unknown execution cannot duplicate exposure, and paper month-boundary fixtures agree with research.

### D. Evidence and inference controls (root)

Files: tradingagents/predlab/{registry,dm,rollup}.py; scripts/predlab_xfam_lib.py, predlab_xfam_prx.py, predlab_opt_o6.py, predlab_oflow_p0.py; docs/audit/corrections.json and resolver; data/predlab/gates.json new key only.

- [x] Commit charter and gate before results. Keep old gate criteria unchanged.
- [x] Test identity separation and append-only correction lookup; log code/gate/data provenance and enforce registration for empirical writers. Keep compatibility for archived rows through an explicit resolver.
- [x] Correct ordinary-ADF cointegration misuse, reversal gate sign, denominator handling and mislabelled oracle dominance. Version prospective HAC/selection policies without rewriting historic gates.
- [x] Mark unavailable/unrecomputed claims accurately, including bybit/champion, S2/S3, ENet, DEX, stale sealed flags and prior uncommitted registration exceptions.

### E. Bounded evidence correction (root after A/B/D)

Files: scripts/audit_correction_2026_09_09.py; new result directory and evidence tests.

- [x] Preflight exact gate, clean committed source, source data/forecast hashes and original 2021–2025Q1 interval; refuse pre-existing output.
- [x] Execute seven original S2/S3 cells once; report paired original/corrected metrics and original criteria. Reassess saved ENet only with the fixed fallback rule and explicit diagnostics, no fits.
- [x] Preserve every denominator and failed cell; append correction/ledger records and THESIS_FINDINGS addendum. Any historical recalculation outside this narrow charter remains explicitly unvalidated, with no new profit claim.

### F. Manuscript and final review (root, may delegate after implementation slots free)

Files: thesis-latex abstracts, introduction, post-audit, discussion, conclusion, included literature/results tables and figures, reproducibility appendix; root AGENTS/CLAUDE status and RESEARCH_LOOP_GUIDE.

- [x] Withdraw invalidated positives and qualify forecast/closure claims. Replace invalidated champion chart in the included thesis with transparent corrected evidence or remove the unsupported performance illustration; preserve source provenance in Git.
- [x] Map assignment requirements to engineering and corrected evaluation; no assertion of a validated strategy, exhaustive impossibility, or actual deployment health.
- [x] Compile/inspect PDF and reconcile cross-references. Review changes across code and thesis, run offline relevant suites, commit only task-owned changes, push reviewed correction branch and thesis backup.

## Interface and conflict review

| Pair | Shared boundary | Decision |
|---|---|---|
| A/C | pp/opt signal, universe and net-accounting definitions | A owns engines; C owns paper. Preserve build_signal/monthly_universe API; communicate any accounting helper before paper integration |
| B/D | runner loss metadata and statistics | B owns runner; root owns dm/rollup; invalid forecasts use existing baseline and expose raw/fallback fields |
| A/E | corrected S2/S3 functions | No empirical execution until A tested and committed; E imports verified functions without relogging old families |
| B/E | saved ENet reassessment | E does not refit; applies declared invalid-forecast policy on the original saved clock |
| D/F | result claims | F uses explicit correction resolver and preserved original evidence |
| A–F | acceptance vs implementation | Hand-derived independent examples determine correctness; historical profitability is not a software acceptance condition |

## Progress ledger

- Initial integration: b7dff69 combines both committed research branches; only CLAUDE and THESIS_FINDINGS conflicted, resolved using the canonical current findings and consolidated worktree instructions.
- Current state: A–D implemented with failing-before/fixed-after synthetic regressions and independent review. Final integrated offline verification passed779tests;2historical parity/marker tests were deselected and the3-test physical-data coverage file was excluded because raw stores remain in the preserved source worktree. The bounded correction subsequently completed once on committed source cc6801e: all seven S2/S3 cells and sixteen saved ENet diagnostics are retained, with unchanged inputs. S2 fails its original paired gate; S3 remains below SR1 and ineligible. Completion is appended in the ledger, corrections register and THESIS_FINDINGS §88. The final 92-page manuscript passed compilation and visual inspection and was pushed to its private backup. Independent artifact checks passed 108/108; all 55 original gate entries and the recorded original evidence hashes remain unchanged. Completed source, outcomes, correction records and reports are retained on the reviewed correction branch.
