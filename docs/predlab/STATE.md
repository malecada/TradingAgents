# Prediction Lab — STATE

Updated: 2026-07-30 (program kickoff)

- **Phase:** 1 (harness + Tier 0/1 classical battery)
- **Last completed:** **Tier-1 daily verdicts finalized** (P1-05 ✓, commit
  `50ac86f`, report p1_tier1_t3t4t6.md): T3 BTC HARQ = SKILL-CANDIDATE;
  T3 ETH = predictable-vs-weak-only (baseline-fragility exposed); T4 both =
  SKILL-CANDIDATE (ΔMASE 16.5%/21.4%, vs best-t0 too); T6 AR(1) baseline
  wins; T1/T2 nulls. Forensic method lessons recorded (same-collapse
  shuffled-null rule; multi-seed for heavy tails). Window-cap param shipped.
- **Next action:** t1_7d battery running in background (launch `bgu8ccaf9`);
  when it lands: collect + launch t1_1h (heavy — run overnight-style in
  background), then forensics on any PASS, reports, P1-08 roll-up
  (`docs/superpowers/plans/2026-07-30-prediction-lab-phase1.md`)
- **Blockers:** none
- **Holdout status:** sealed (2025-04-01 → 2026-07-01); zero spends
- **Ledger:** `data/predlab/trial_ledger.jsonl` (create on first registration)
- **Standing rules:** charter §5 protocol; one backlog item per loop iteration; gates
  registered before any battery result; forensic kill-tests on every PASS; never write
  outside `data/predlab/`, `docs/predlab/`, `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, THESIS §54+, and `docs/superpowers/` predlab files.
- **Infra-failure counter:** 0 (3 consecutive → stop loop and surface)
