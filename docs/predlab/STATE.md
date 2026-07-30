# Prediction Lab — STATE

Updated: 2026-07-30 (program kickoff)

- **Phase:** 1 (harness + Tier 0/1 classical battery)
- **Last completed:** Plan Task 10 — Tier-0 battery, 28/28 cells (**P1-04 ✓**),
  baseline reference table in reports/p1_tier0.md; eval_start protocol fix
  (origins now inside registered dev window, TDD-pinned); 61 tests green,
  commits `a01e518`+`65d54e7`; ledger 214 rows
- **Next action:** Plan Task 11 — Tier-1 daily T1/T2 (ARIMA/ETS/logit wrappers)
  (`docs/superpowers/plans/2026-07-30-prediction-lab-phase1.md`)
- **Blockers:** none
- **Holdout status:** sealed (2025-04-01 → 2026-07-01); zero spends
- **Ledger:** `data/predlab/trial_ledger.jsonl` (create on first registration)
- **Standing rules:** charter §5 protocol; one backlog item per loop iteration; gates
  registered before any battery result; forensic kill-tests on every PASS; never write
  outside `data/predlab/`, `docs/predlab/`, `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, THESIS §54+, and `docs/superpowers/` predlab files.
- **Infra-failure counter:** 0 (3 consecutive → stop loop and surface)
