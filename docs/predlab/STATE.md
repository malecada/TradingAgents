# Prediction Lab — STATE

Updated: 2026-07-30 (program kickoff)

- **Phase:** 1 (harness + Tier 0/1 classical battery)
- **Last completed:** Plan Task 6 — 5m fetcher shipped (38 tests green, commit
  `33691de`); **fetch running in background** (BTC+ETH 2020-01→now, Vision bulk)
- **Next action:** Plan Task 8 — registry + Phase-1 registration (data-independent;
  Task 7 RV builder waits for the fetch to finish)
  (`docs/superpowers/plans/2026-07-30-prediction-lab-phase1.md`)
- **Blockers:** none
- **Holdout status:** sealed (2025-04-01 → 2026-07-01); zero spends
- **Ledger:** `data/predlab/trial_ledger.jsonl` (create on first registration)
- **Standing rules:** charter §5 protocol; one backlog item per loop iteration; gates
  registered before any battery result; forensic kill-tests on every PASS; never write
  outside `data/predlab/`, `docs/predlab/`, `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, THESIS §54+, and `docs/superpowers/` predlab files.
- **Infra-failure counter:** 0 (3 consecutive → stop loop and surface)
