# Prediction Lab — STATE

Updated: 2026-07-30 (program kickoff)

- **Phase:** 1 (harness + Tier 0/1 classical battery)
- **Last completed:** **Tier-1 daily verdicts finalized** (P1-05 ✓, commit
  `50ac86f`, report p1_tier1_t3t4t6.md): T3 BTC HARQ = SKILL-CANDIDATE;
  T3 ETH = predictable-vs-weak-only (baseline-fragility exposed); T4 both =
  SKILL-CANDIDATE (ΔMASE 16.5%/21.4%, vs best-t0 too); T6 AR(1) baseline
  wins; T1/T2 nulls. Forensic method lessons recorded (same-collapse
  shuffled-null rule; multi-seed for heavy tails). Window-cap param shipped.
- **Last completed:** t1_7d battery — **all 8 cells null** (P1-07 ✓, commit
  `36a66cd`): skill is horizon-local (daily HARQ edge gone at 7d; plain HAR
  wins T3), overlapping-sum trap makes fitted T1/T2 models actively worse.
- **In flight:** t1_1h battery (final battery; 8 cells, capped ARIMA/GARCH per
  amendment).
- **Next action:** collect 1h + forensics on any PASS → P1-08 map roll-up
  (rollup.py ready) + THESIS §54 + memory milestone
  (`docs/superpowers/plans/2026-07-30-prediction-lab-phase1.md`)
- **Blockers:** none
- **Holdout status:** sealed (2025-04-01 → 2026-07-01); zero spends
- **Ledger:** `data/predlab/trial_ledger.jsonl` (create on first registration)
- **Standing rules:** charter §5 protocol; one backlog item per loop iteration; gates
  registered before any battery result; forensic kill-tests on every PASS; never write
  outside `data/predlab/`, `docs/predlab/`, `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, THESIS §54+, and `docs/superpowers/` predlab files.
- **Infra-failure counter:** 0 (3 consecutive → stop loop and surface)
