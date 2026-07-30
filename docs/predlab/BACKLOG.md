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

- [ ] P1-01 `tradingagents/predlab/` package skeleton + eval core, TDD: loss functions
      (MSE, MAE, QLIKE, MASE), rolling-origin splitter with purge/embargo, DM test with
      HLN correction (HAC lag ≥ h−1), Clark–West, Giacomini–White, Pesaran–Timmermann,
      Newey–West mean test, stationary block bootstrap on loss differentials. Add
      `arch` dependency (also provides SPA/StepM/MCS for later). Unit tests include
      worked examples validated against reference implementations
      (statsmodels/arch/dieboldmariano) and known-answer fixtures.
- [ ] P1-02 Data: 5m klines for BTCUSDT+ETHUSDT (Binance Vision monthly zips, 2020-01
      → 2026-07; adapt `scripts/fetch_xsect_klines_1h.py` template, `INTERVAL="5m"`,
      keep taker columns) → parquet under `data/predlab/klines_5m/` (idempotent,
      tail-append, no date-embedded cache names) → RV/BV/RQ builder from 5-min returns
      (hourly + daily aggregates) + volume series + Parkinson range. Sanity: RV vs
      close-to-close vol ratio plausible; coverage report with honest denominators.
- [ ] P1-03 Registration: write `data/predlab/gates.json` Phase-1 battery (cells,
      baselines, losses, effect floors from charter §5, dev/holdout windows, refit
      cadence, seeds, stop rules) + init empty ledger. Plumbing probes: timestamp
      reconciliation on the new stores; leaky-canary harness check (train-on-future
      model must win big — proves harness can detect leakage).
- [ ] P1-04 Tier 0 baselines run, all Phase-1 cells (RW/zero, mean, persistence,
      seasonal-naive, EWMA, climatology) → baseline loss table per cell → ledger rows +
      report card. (Baselines are the null — no gates evaluated yet.)
- [ ] P1-05 Tier 1 battery, daily horizon (24h): AR/ARIMA/ETS on T1; logit-on-lags for
      T2; GARCH(1,1)/EGARCH/GJR + HAR-RV(+HARQ if RQ ok) on T3; seasonal-AR on T4;
      AR(1)+ on T6. DM/CW/PT vs baselines, per charter §5 → ledger + cards.
- [ ] P1-06 Tier 1 battery, 1h horizon (same model set, hourly bars; overlapping-h
      HAC handling verified) → ledger + cards.
- [ ] P1-07 Tier 1 battery, 7d horizon (direct + iterated forecasts compared) →
      ledger + cards.
- [ ] P1-08 Phase-1 report: predictability map v1 (classical), BH-FDR across Phase-1
      cells, sub-period stability tables → `docs/predlab/reports/phase1_map.md` +
      THESIS §54 draft section. Memory milestone update.

## Phase 2 — Tier 2 ML battery (registered small feature sets)

- [ ] P2-01 Feature builders (PIT-safe, tested): price lags, RV lags/terms,
      taker-imbalance (`taker_buy_quote_volume` in 1h/5m stores), OI deltas (build
      sub-daily OI store from Vision metrics zips, free from 2021-01 per
      reference_data_source_audit_jul30), funding, calendar; per-cell-family
      registered feature lists (≤ 25 each) appended to gates.
- [ ] P2-02 LGB + elastic-net + kernel-ridge on T3 (vol) and T4 (volume) daily+1h —
      the literature-favored cells first. vs HAR/seasonal baselines.
- [ ] P2-03 Same Tier 2 set on T1/T2 (returns/direction) daily+1h; reconcile any T1
      LGB result against §40 retirement verdict explicitly.
- [ ] P2-04 T7 XS battery: wide-universe (PIT 150–300 syms) next-24h/7d return-rank +
      RV-rank ICs, ridge/LGB rank models vs zero-IC null; NW-t on IC series.
- [ ] P2-05 Phase-2 report: map v2, FDR update, memory milestone.

## Phase 3 — Tier 3 DL (GATE: compute decision + Tier≤2 evidence)

- [ ] P3-00 DECISION POINT: surface GPU/cloud question to user with Tier≤2 evidence
      summary (which cells qualify per charter §4 Tier-3 entry rule). Do not proceed
      without answer.
- [ ] P3-01+ (defined after P3-00)

## Phase 4 — Tier 4 foundation models (zero-shot first)

- [ ] P4-01 Leakage-safe evaluation windows per model (from RESEARCH.md release/cutoff
      table) registered in gates; CPU-feasible models first (per RESEARCH.md).
- [ ] P4-02 Zero-shot battery on Phase-1 cells within safe windows; compare vs Tier 0/1
      on identical spans (matched-window re-runs of baselines).
- [ ] P4-03 Report + map v3.

## Phase 5 — combination + final MCS

- [ ] P5-01 Forecast combinations on cells with ≥1 skilled/near-skilled model; MCS
      across final per-cell model sets; champion freeze per surviving cell.
- [ ] P5-02 HOLDOUT one-shots for champions (U4), per charter. Final map + report +
      THESIS §; memory milestone.

## Phase P — profitability mapping (OUT OF SCOPE until a U1–U5 survivor exists)

- [ ] PP-00 New spec + registration (separate design doc; not started by the loop).
