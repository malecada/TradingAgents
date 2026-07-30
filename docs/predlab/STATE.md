# Prediction Lab — STATE

Updated: 2026-07-30 (program kickoff)

- **Phase:** 1 (harness + Tier 0/1 classical battery)
- **Last completed:** Plan Task 7 — RV stores built (**P1-02 ✓**): 5m fetch done
  (692k rows/sym 2020-01→2026-07-30, 0 dup, monotonic), rv_1h 57,660 + rv_1d
  2,402 periods/sym, sanity PASS (BTC 2021 ann. vol 0.718 / ETH 0.904; RV/CC
  in-band 86.5%/88.7% vs 80% floor), 53 tests green
- **Next action:** Plan Task 9 — baselines + cell runner + plumbing/canary probes
  (completes P1-03) (`docs/superpowers/plans/2026-07-30-prediction-lab-phase1.md`)
- **Blockers:** none
- **Holdout status:** sealed (2025-04-01 → 2026-07-01); zero spends
- **Ledger:** `data/predlab/trial_ledger.jsonl` (create on first registration)
- **Standing rules:** charter §5 protocol; one backlog item per loop iteration; gates
  registered before any battery result; forensic kill-tests on every PASS; never write
  outside `data/predlab/`, `docs/predlab/`, `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, THESIS §54+, and `docs/superpowers/` predlab files.
- **Infra-failure counter:** 0 (3 consecutive → stop loop and surface)
