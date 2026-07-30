# Prediction Lab — STATE

Updated: 2026-07-30 (program kickoff)

- **Phase:** 1 (harness + Tier 0/1 classical battery)
- **Last completed:** T1/T2 daily battery — **NO-SKILL both cells**
  (lit-consistent; report p1_tier1_t1t2.md, commit `9b741c2`). Forensics v1
  on the T3 HARQ pass: K1-ETH FAIL exposed **levels-HAR baseline fragility**
  (HARQ "beat" it even on shuffled data → margin partly baseline-badness);
  K2 leak-probe was mis-designed (interaction channel). v1 verdicts recorded
  in forensics_t3.json.
- **In flight (background):** forensics v2 (A2 rq alignment audit; K3 pairwise
  DM HARQ vs log_har + EWMA on real data — the charter-A1 strongest-baseline
  test; K4 shuffled vs robust reference).
- **Next action:** collect forensics v2 → T3 verdict + report; launch t1_t4t6
  battery (`docs/superpowers/plans/2026-07-30-prediction-lab-phase1.md`)
- **Blockers:** none
- **Holdout status:** sealed (2025-04-01 → 2026-07-01); zero spends
- **Ledger:** `data/predlab/trial_ledger.jsonl` (create on first registration)
- **Standing rules:** charter §5 protocol; one backlog item per loop iteration; gates
  registered before any battery result; forensic kill-tests on every PASS; never write
  outside `data/predlab/`, `docs/predlab/`, `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, THESIS §54+, and `docs/superpowers/` predlab files.
- **Infra-failure counter:** 0 (3 consecutive → stop loop and surface)
