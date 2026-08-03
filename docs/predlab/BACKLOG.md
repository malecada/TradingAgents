# Prediction Lab — BACKLOG

Ordered work items. One item per loop iteration (split an item rather than overrun).
Checkbox flips only after: tests green + forensic checks done + ledger/report updated +
committed. Governed by `docs/superpowers/specs/2026-07-30-prediction-lab-charter-design.md`.

## Phase 1 — harness + Tier 0/1 classical battery (BTC/ETH)

> Execution detail for Phase 1 lives in
> `docs/superpowers/plans/2026-07-30-prediction-lab-phase1.md` (Tasks 1–15).
> Work plan-task-by-plan-task; tick a P1 checkbox here once its covering plan tasks
> are done (P1-01 ↔ Tasks 1–5; P1-02 ↔ Tasks 6–7; P1-03 ↔ Task 8; P1-04 ↔ Tasks 9–10;
> P1-05 ↔ Tasks 11–13; P1-06/07 ↔ Task 14; P1-08 ↔ Task 15).

- [x] P1-01 `tradingagents/predlab/` package skeleton + eval core, TDD: loss functions
      (MSE, MAE, QLIKE, MASE), rolling-origin splitter with purge/embargo, DM test with
      HLN correction (HAC lag ≥ h−1), Clark–West, Giacomini–White, Pesaran–Timmermann,
      Newey–West mean test, stationary block bootstrap on loss differentials. Add
      `arch` dependency (also provides SPA/StepM/MCS for later). Unit tests include
      worked examples validated against reference implementations
      (statsmodels/arch/dieboldmariano) and known-answer fixtures.
- [x] P1-02 Data: 5m klines for BTCUSDT+ETHUSDT (Binance Vision monthly zips, 2020-01
      → 2026-07; adapt `scripts/fetch_xsect_klines_1h.py` template, `INTERVAL="5m"`,
      keep taker columns) → parquet under `data/predlab/klines_5m/` (idempotent,
      tail-append, no date-embedded cache names) → RV/BV/RQ builder from 5-min returns
      (hourly + daily aggregates) + volume series + Parkinson range. Sanity: RV vs
      close-to-close vol ratio plausible; coverage report with honest denominators.
- [x] P1-03 Registration: write `data/predlab/gates.json` Phase-1 battery (cells,
      baselines, losses, effect floors from charter §5, dev/holdout windows, refit
      cadence, seeds, stop rules) + init empty ledger. Plumbing probes: timestamp
      reconciliation on the new stores; leaky-canary harness check (train-on-future
      model must win big — proves harness can detect leakage).
- [x] P1-04 Tier 0 baselines run, all Phase-1 cells (RW/zero, mean, persistence,
      seasonal-naive, EWMA, climatology) → baseline loss table per cell → ledger rows +
      report card. (Baselines are the null — no gates evaluated yet.)
- [x] P1-05 Tier 1 battery, daily horizon (24h): AR/ARIMA/ETS on T1; logit-on-lags for
      T2; GARCH(1,1)/EGARCH/GJR + HAR-RV(+HARQ if RQ ok) on T3; seasonal-AR on T4;
      AR(1)+ on T6. DM/CW/PT vs baselines, per charter §5 → ledger + cards.
- [x] P1-06 Tier 1 battery, 1h horizon (same model set, hourly bars; overlapping-h
      HAC handling verified) → ledger + cards.
- [x] P1-07 Tier 1 battery, 7d horizon (direct + iterated forecasts compared) →
      ledger + cards.
- [x] P1-08 Phase-1 report: predictability map v1 (classical), BH-FDR across Phase-1
      cells, sub-period stability tables → `docs/predlab/reports/phase1_map.md` +
      THESIS §54 draft section. Memory milestone update.

> Perf notes (2026-07-30, measured): (1) SARIMAX `.apply()` ~98ms/origin →
> extend-cache shipped (`ef3b02c`), ~20x. (2) The remaining 1h-battery cost is
> the MLE refits themselves: high-vol windows (2021-2022) run 3-10x slower
> than calm ones (24 → ~7 orig/s cumulative). Before any future ARIMA battery
> (Phase-5 confirmations): warm-start each refit with
> `start_params=prev_res.params` (params drift slowly at refit_every=24;
> expect 2-5x on fits) + consider `maxiter` cap. TDD: same-quality pin
> (loglike within tolerance of cold-start fit).

## Phase 2 — Tier 2 ML battery (registered small feature sets)

- [x] P2-01a Feature builders from EXISTING stores (PIT-safe, tested):
      price/RV lags + ratios, taker-imbalance (`taker_buy_quote_volume` in
      rv stores), funding features, calendar (hour/dow sin-cos). All features
      lagged into the origin's information set; mutation-pinned.
- [x] P2-01b Sub-daily OI store: fetcher for Binance Vision futures METRICS
      monthly zips (5m OI from 2021-01 per reference_data_source_audit_jul30)
      → data/predlab/oi_5m/ + hourly/daily aggregates + OI-delta features.
- [x] P2-01c Registration: per-cell-family feature lists (≤ 25 each) appended
      to gates as `predlab_p2_ml` entry (windows, grids, floors inherit charter)
      BEFORE any Tier-2 result.
- [x] P2-02 LGB + elastic-net + kernel-ridge on T3 (vol) and T4 (volume) daily+1h —
      the literature-favored cells first. vs HAR/seasonal baselines.
- [x] P2-03 Same Tier 2 set on T1/T2 (returns/direction) daily+1h; reconcile any T1
      LGB result against §40 retirement verdict explicitly.
- [x] P2-04 T7 XS battery: wide-universe (PIT 150–300 syms) next-24h/7d return-rank +
      RV-rank ICs, ridge/LGB rank models vs zero-IC null; NW-t on IC series.
- [x] P2-05 Phase-2 report: map v2, FDR update, memory milestone.

## Phase 3 — Tier 3 DL (GATE: compute decision + Tier≤2 evidence)

- [x] P3-00 DECISION (user, 2026-07-31): **SKIP Tier-3 DL, proceed to Phase 4**
      (foundation models, CPU). Tier-3 revisited only if Phase 4 shows DL-class
      gains. Rationale: LGB added skill only on volume; vol/direction champions
      resisted all challengers; lit says DL gains marginal.
- [-] P3-01+ (not defined — Tier 3 skipped by user decision)

## Phase 4 — Tier 4 foundation models (zero-shot first)

- [x] P4-01 Leakage-safe evaluation windows per model (from RESEARCH.md release/cutoff
      table) registered in gates; CPU-feasible models first (per RESEARCH.md).
- [x] P4-02 Zero-shot battery on Phase-1 cells within safe windows; compare vs Tier 0/1
      on identical spans (matched-window re-runs of baselines).
- [x] P4-03 Report + map v3 (p4_fm.md; map delta folded into Phase-5 planning).

## Phase 5 — combination + final MCS

- [x] P5-01 Forecast combinations on cells with ≥1 skilled/near-skilled model; MCS
      across final per-cell model sets; champion freeze per surviving cell.
      (@9050a8c: 10 champions frozen; lgb_cal MCS-excluded; ttm_ens dev-upgrade)
- [x] P5-02 HOLDOUT one-shots for champions (U4), per charter. Final map + report +
      THESIS §57; memory milestone. (**SPENT 2026-07-31: 7/10 PASS** — BTC HARQ
      rv ×2, LGB volume ×4, T7 park_5; FAIL: ETH egarch floor, 2× logit Brier
      gate with sign edges intact. Forensics: all nulls collapse incl. corrected
      same-collapse T4 pairing; subs 5-6/6. reports/p5_holdout.md + phase5_map.md)

**PROGRAM COMPLETE.** U1–U4 usable models exist (volume ×4, BTC rv ×2, XS rank).

## Phase P — profitability mapping (registered predlab_pp, 2026-07-31)

- [x] PP-00 Spec + registration (specs/2026-07-31-phase-p-profitability-design.md;
      gates keys predlab_pp + predlab_p6 frozen @127d5d6, user-approved 2026-07-31).

- [x] PP-01 Engine + 13 pinned tests (@b70a993).
- [x] PP-02 Dev gates (@c3fc773): S1 PASS all 4 (net SR 1.48, placebos, DSR 0.70
      corrected, subs 3/3; config eq_h1 frozen); S2 FAIL do-no-harm guard
      (TE claim strong, SR worse); S3 dead (costs kill 1h edge).
- [x] PP-03 Strategy holdout SPENT 2026-07-31: **S1 PASS — net SR +2.20 (gross
      +3.31), placebos .025/.005, MaxDD 32%, 4/5 quarters positive.** Report
      pp_profitability.md + THESIS §58. First validated strategy post-rebuild.

## Phase 6 — deferred model upgrades (registered predlab_p6; BLOCKED on data)

- [ ] P6-xx NEW sealed holdout 2026-07-02→open; spend earliest 2027-07.
      Candidates frozen: ETH ttm_ens, T2 recalibration, T4 alt generalization.

## PP2 — S1 risk overlay + forward track (registered predlab_pp2, 2026-07-31)

- [x] PP2-01 Registration + dev: vt10/15/20 all PASS gates (MaxDD -77/-66/-55%,
      SR 1.40 vs raw 1.48); **vt10 frozen** for forward confirmation.
- [x] PP2-02 S1 daily paper-trader (scripts/predlab_s1_paper.py): live Binance
      book journal, idempotent, fill-check vs prior close, vt10 scale after 21d.
      First forward row 2026-07-30. OPERATOR: schedule daily run (cron, any UTC
      hour after 00:05): `cd TradingAgents-predlab && uv run python
      scripts/predlab_s1_paper.py`
- [ ] PP2-03 Forward confirmation one-shot: when >=6 months journal accrued
      (earliest ~2027-02), evaluate vt10 vs concurrent raw book per frozen
      criteria (MaxDD <= 0.75x raw AND SR >= 0.9x raw).

## Phase O — system optimization cycle (registered predlab_opt, 2026-07-31)

> Spec: `docs/superpowers/specs/2026-07-31-system-optimization-design.md`.
> Windows: design D 2021-01→2025-03, validation V 2025-04→2026-07 (NON-VIRGIN,
> consistency check only), forward holdout F 2026-07-02→open (spend ≥6mo, one-shot,
> final champion only). Champion chain: `data/predlab/opt_champion_chain.jsonl`.
> Each stage: freeze grid in gates.json BEFORE first run, ≤12 configs, ledger row
> per config, kill-tests before any adoption.

- [x] O-00 Spec + registration (gates key `predlab_opt`; user-directed scope
      expansion 2026-07-31).
- [x] O-01 Engine: refactor `pp.py` S1 path into parameterized
      `tradingagents/predlab/opt.py` (signal fn, universe size/floor, quantile
      width, weighting, buffer bands, cadence, tilts, overlay). TDD; pin test must
      reproduce eq_h1 dev numbers EXACTLY (sr_net 1.4829604657, maxdd 0.4246460613,
      turnover 0.6669561499) + D/V split metrics helper + placebo/DSR/forensic
      harness reuse.
- [x] O-02 Stage O1 signal construction: grid 11 cfg frozen + run (@O-02a/b).
      5 adoption candidates; top ewma_20 full +1.928 (Δ+0.271), all subs 4/4.
- [x] O-02b ewma_20 ADOPTED (chain seq 1): placebos .005/.005, DSR corrected
      0.842 (units-bug 0.169 disclosed+retained; daily-only 0.991), alignment
      sensitivity PASS, coverage clean. New incumbent full SR +1.928.
- [x] O-03 Stage O2 portfolio construction: 12 cfg, NO ADOPTION (best rank
      +1.924 < needed +2.028); incumbent construction stands; tercile noted as
      DD-dial for O8. Card opt_o2.md.
- [x] O-04 Stage O3 universe: 9 cfg, NO ADOPTION (best adv5m +1.974 <
      +2.028); identical-MaxDD anomaly probed+resolved (thin 2021 breadth =
      common DD episode); breadth floor noted as DD lever. Card opt_o3.md.
- [x] O-05 Stage O4 overlay: 12/12 PASS gates; vt15_naive20_b100 ADOPTED
      (chain seq 2): SR +1.892, MaxDD 46.3→17.6%; breadth guard ADDS SR
      (thin-2021 net-negative). HAR = deep-DD knob (6.9% at vt10). Card opt_o4.md.
- [x] O-06 Stage O5 funding tilt: 8 cfg, NO ADOPTION (best +1.960, Δ+0.032 <
      floor). Mechanism VALIDATED (carry −0.99→+0.71 monotone; reverse hurts);
      premium real but thin vs turnover cost — §46 reconciled. Card opt_o5.md.
- [ ] O-07 Stage O6 volume-forecast weighting: freeze grid → run → card.
- [ ] O-08 Stage O7 momentum tilt inside book: freeze grid → run → card.
- [ ] O-09 Stage O8 final composition + champion freeze + report + THESIS §59 +
      memory milestone; register final champion for F one-shot.
