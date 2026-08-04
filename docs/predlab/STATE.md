# Prediction Lab — STATE

Updated: 2026-07-31 (Phase O kickoff)

- **Phase:** O (system optimization cycle, `predlab_opt`) — user-directed
  open-ended optimization of models + strategy + universe, best honest
  backtest. Incumbent: **ewma_20 eq quintiles + vt15_naive20_b100 overlay (chain seq 2:
  SR +1.892, MaxDD 17.6%)**.
  Original S1 eq_h1 (holdout +2.20) superseded at seq 1.
- **Last completed:** O-08 stage O7 momentum tilt NO ADOPTION (8 cfg; 4th
  within-leg tilt negative — book saturated). Prior: O-07 volume CLOSED BY
  DOMINANCE; O-05 overlay adopted (seq 2).
  Prior: O-04 universe no-adopt (DD anomaly resolved); O-03 no-adopt; O-02b
  ewma_20 champion (seq 1). Prior: O-01 engine @791ccf1 (18 tests, eq_h1 exact parity pin; suite 147 green). Prior: O-00 registration (spec
  `2026-07-31-system-optimization-design.md`, gates key `predlab_opt`,
  BACKLOG Phase O). **Next action: O-09 stage O8 final composition + champion freeze + THESIS §59 +
  forward-holdout registration.**
- **Phase-O window discipline:** design D 2021-01→2025-03; validation V
  2025-04→2026-07 NON-VIRGIN (consistency check only, never a fresh-holdout
  claim); forward holdout F 2026-07-02→open SEALED (one-shot, final champion,
  ≥6mo accrual). Old holdout re-runs stay blocked.
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
- **P2-02 COMPLETE** (@`871c30d`, report p2_tier2_t3t4.md): **LGB beats the
  volume champions in ALL FOUR T4 cells** (Δ5.4-12.1% ≥ 5% floor, pairwise DM
  p ≤ 6.7e-5, cross-symbol × cross-grid, permute-y null p≈1.0, leak guard
  bite-tested) — first genuine ML increment over best classical. T3 vol: ML
  never beats HAR/GARCH champions (4/4) — OI/positioning features add nothing
  on vol. enet catastrophic on trending volume.
- **P2-03 COMPLETE** (@`bddbc51`, report p2_tier2_t1t2.md): T1 nulls hold —
  LGB actively harmful on return levels 4-19% (4/4), **§40 retirement
  reconciled on independent forecast-space ground**. T2 1h logit champions
  hold; LGB carries the program's strongest sign association (PT p 2.3e-44)
  but loses Brier to miscalibration → LGB+calibration declared as Phase-5
  combination candidate.
- **PHASES 1+2+4 COMPLETE** (Phase 3 skipped by user decision @`36a0adc`;
  Phase 4 @`197a8bd`): THESIS §54-§56, maps v1/v2, p4_fm report. Returns
  null across FOUR model classes; TTM routed into ETH-vol Phase-5 MCS;
  TabPFN declared-drop (revivable via TABPFN_TOKEN). Holdout sealed, 0
  spends.
- **P5-01 COMPLETE** (@`9050a8c`): predlab_p5 registered pre-MCS; per-cell
  MCS run on stored dev forecasts; 10 champions frozen (p5_champions.json).
- **P5-02 COMPLETE — HOLDOUT SPENT 2026-07-31 (@`b124b89` + finalize): 7/10
  PASS.** USABLE (U1–U4): LGB volume ×4 (+26.6…+44.8% MASE, ≥ dev), BTC
  HARQ rv ×2 (+15.1%/+22.6% QLIKE, > dev), T7 park_5 (IC −0.083, NW-t
  −11.5). FAIL: ETH egarch (+7.4% real but < 0.5×dev floor), 2× logit
  (sign edges +2.51/+1.69pp held; Brier gate missed). Forensics: T3 nulls
  ≤|0.31%|; T4 corrected same-collapse nulls all negative (naive pairing
  +30% artifact disclosed — collapse-class lesson); T7 shuffle |IC|≤0.008;
  subs 5-6/6 quarters. reports/p5_holdout.md, phase5_map.md, THESIS §57.
- **PROGRAM COMPLETE.** Phase P (profitability) is out of scope until
  separately spec'd + registered (PP-00). ETH-vol TTM ensemble remains a
  dev-level upgrade candidate (never holdout-spent, champion-only contract).
- **Blockers:** none
- **Holdout status:** SPENT (one-shot per champion, 2026-07-31); re-runs
  blocked by verdicts file + spend rule
- **Ledger:** `data/predlab/trial_ledger.jsonl` (create on first registration)
- **Standing rules:** charter §5 protocol; one backlog item per loop iteration; gates
  registered before any battery result; forensic kill-tests on every PASS; never write
  outside `data/predlab/`, `docs/predlab/`, `tradingagents/predlab/`, `tests/predlab/`,
  `scripts/predlab_*.py`, THESIS §54+, and `docs/superpowers/` predlab files.
- **Infra-failure counter:** 0 (3 consecutive → stop loop and surface)
