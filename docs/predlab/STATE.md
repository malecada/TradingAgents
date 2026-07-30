# Prediction Lab — STATE

Updated: 2026-07-30 (program kickoff)

- **Phase:** 1 (harness + Tier 0/1 classical battery)
- **Last completed:** Task 13 code (SeasonalAR/Ar1/Dar1, commit `9497d0d`).
  **T3 daily battery LANDED — first candidate PASS:** HARQ beats HAR-levels
  both symbols (BTC ΔQLIKE 11.6% dm_p 1.0e-3; ETH 15.4% dm_p 4.8e-12);
  GARCH ≤ HAR; HAR>EWMA on BTC (lit-consistent); ETH levels-HAR outlier-weak.
- **In flight (background):** t1_t1t2_24h battery; forensics_t3 kill-tests
  (K1 shuffled-target, K2 rq-leak mutation).
- **Next action:** collect forensics + T1/T2 battery → write p1_tier1 reports;
  then T4/T6 battery runs
  (`docs/superpowers/plans/2026-07-30-prediction-lab-phase1.md`)
- **Blockers:** none
- **Holdout status:** sealed (2025-04-01 → 2026-07-01); zero spends
- **Ledger:** `data/predlab/trial_ledger.jsonl` (create on first registration)
- **Standing rules:** charter §5 protocol; one backlog item per loop iteration; gates
  registered before any battery result; forensic kill-tests on every PASS; never write
  outside `data/predlab/`, `docs/predlab/`, `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, THESIS §54+, and `docs/superpowers/` predlab files.
- **Infra-failure counter:** 0 (3 consecutive → stop loop and surface)
