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
- **Last completed:** P2-01 COMPLETE (a/b/c, @`03a7567`): feature builders
  (mutation-pinned), OI 5m stores (BTC 525k rows 0-missing; ETH 430k, Vision
  data begins 2021-12-01 — 334 confirmed 404s), Tier-2 wrappers (enet+lgb,
  leak-pinned), **predlab_p2_ml registration FROZEN** (16 cells, per-symbol
  eval_start remedy decided pre-freeze after the coverage gate REFUSED first
  pass at ETH 77.6%; windowed coverage 98.9-100%).
- **Next action:** P2-02 — Tier-2 battery tier in predlab_run_battery.py
  (series+features loader honoring per-symbol eval_start) → run T3/T4 cells
  first (literature-favored), secondary DM vs Phase-1 champions.
- **Blockers:** none
- **Holdout status:** sealed (2025-04-01 → 2026-07-01); zero spends
- **Ledger:** `data/predlab/trial_ledger.jsonl` (create on first registration)
- **Standing rules:** charter §5 protocol; one backlog item per loop iteration; gates
  registered before any battery result; forensic kill-tests on every PASS; never write
  outside `data/predlab/`, `docs/predlab/`, `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, THESIS §54+, and `docs/superpowers/` predlab files.
- **Infra-failure counter:** 0 (3 consecutive → stop loop and surface)
