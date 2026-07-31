# Prediction Lab — STATE

Updated: 2026-07-30 (program kickoff)

- **Phase:** 1 (harness + Tier 0/1 classical battery)
- **Last completed:** **Tier-1 daily verdicts finalized** (P1-05 ✓, commit
  `50ac86f`, report p1_tier1_t3t4t6.md): T3 BTC HARQ = SKILL-CANDIDATE;
  T3 ETH = predictable-vs-weak-only (baseline-fragility exposed); T4 both =
  SKILL-CANDIDATE (ΔMASE 16.5%/21.4%, vs best-t0 too); T6 AR(1) baseline
  wins; T1/T2 nulls. Forensic method lessons recorded (same-collapse
  shuffled-null rule; multi-seed for heavy tails). Window-cap param shipped.
- **PHASE 1 COMPLETE** (@`11b440f`): 9/28 dev SKILL-CANDIDATES (map:
  reports/phase1_map.md; THESIS §54; memory milestone saved). Holdout sealed,
  0 spends, 180 ledgered configs.
- **Last completed:** P2-01a — PIT-safe Tier-2 feature builders (mutation-
  pinned strict lag; taker-imbalance, RV/ret/flow/calendar, funding), 98
  tests green, commit `2887415`.
- **Next action:** P2-01b — sub-daily OI store (Vision futures metrics
  monthly zips, 5m from 2021-01) → data/predlab/oi_5m/ + aggregates; then
  P2-01c registration (`predlab_p2_ml` gates entry) BEFORE any Tier-2 result.
- **Blockers:** none
- **Holdout status:** sealed (2025-04-01 → 2026-07-01); zero spends
- **Ledger:** `data/predlab/trial_ledger.jsonl` (create on first registration)
- **Standing rules:** charter §5 protocol; one backlog item per loop iteration; gates
  registered before any battery result; forensic kill-tests on every PASS; never write
  outside `data/predlab/`, `docs/predlab/`, `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, THESIS §54+, and `docs/superpowers/` predlab files.
- **Infra-failure counter:** 0 (3 consecutive → stop loop and surface)
