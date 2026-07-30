# Prediction Lab — STATE

Updated: 2026-07-30 (program kickoff)

- **Phase:** 1 (harness + Tier 0/1 classical battery)
- **Last completed:** Plan Task 12 code — HAR family + GARCH via arch fix()
  + wants_x_hist runner channel, 72 tests green, commit `bfee2f0`
- **In flight (background):** t1_t1t2_24h battery (T1/T2 daily) + t1_t3_24h
  battery (T3 daily GARCH/HAR ladder)
- **Next action:** collect BOTH batteries → forensics (charter §5: any PASS →
  kill-tests; HAR must beat EWMA else probe harness) → reports; then Task 13
  (T4 volume + T6 funding models)
  (`docs/superpowers/plans/2026-07-30-prediction-lab-phase1.md`)
- **Blockers:** none
- **Holdout status:** sealed (2025-04-01 → 2026-07-01); zero spends
- **Ledger:** `data/predlab/trial_ledger.jsonl` (create on first registration)
- **Standing rules:** charter §5 protocol; one backlog item per loop iteration; gates
  registered before any battery result; forensic kill-tests on every PASS; never write
  outside `data/predlab/`, `docs/predlab/`, `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, THESIS §54+, and `docs/superpowers/` predlab files.
- **Infra-failure counter:** 0 (3 consecutive → stop loop and surface)
