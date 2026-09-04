# oflow — Order-flow linear P0 (registered 2026-09-04)

Status: **REGISTERED pre-result.** Gates key `predlab_oflow` in
`data/predlab/gates.json` is written in the same commit as this file, before
any imbalance series is computed. Source: `master_thesis/LEADS_SCOPE_2026-09-02.md`
Lead 7 ("literature's best-replicated T1 family, never tested directly here";
internal GBDT features were negative). Protocol: the xfam P0 protocol (§72,
charter 2026-08-25) verbatim. Decisions under the user's afk autonomy grant:
(a) the 8 cells as listed; (b) hourly survivors are priced at taker (primary)
and, if any survive, also through the exec_pf passive overlay (§77) as a
reported sensitivity — §77 showed passive fills do not rescue a
mean-reversion entry, so the taker price is the honest one.

## Goal (falsifiable)

Lagged signed taker flow predicts the next bar's return (time series, BTC and
ETH, 1 h and 24 h; plus a 5-minute-resolution variant), and cross-sectional
flow rank predicts next-day / next-7-day return rank on the top-200 PIT
universe — tested as direct predictive regressions. Null: no cell survives
BH-FDR q < 0.10 with the registered effect floors.

## Data (on disk, no new fetch)

- 1 h store `TradingAgents/data/xsect/klines_1h/` (393 symbols; `quote_volume`,
  `taker_buy_quote_volume`, 100 % non-null); breadth 78 names at 2021-01,
  157 at 2023-01, 243 at 2024-01 — the cross-sectional cells are evaluated
  only on days with ≥ 25 in-universe names with flow data (first such date
  reported).
- 5-minute store `data/predlab/klines_5m/{BTCUSDT,ETHUSDT}.parquet`
  (`taker_buy_quote_volume`).
- Daily 799-symbol store for closes and the monthly top-200 PIT universe
  (`opt.monthly_universe`, prior-month median quote volume).

## Signal (frozen)

`imb_t = (2·taker_buy_qv_t − qv_t) / qv_t` on the bar's own quote volumes;
`z_t` = rolling z-score of `imb` over a 30-day window (720 bars at 1 h, 30 rows
daily, 8,640 bars at 5 min; min_periods = half the window), computed from bars
≤ t only. Daily imbalance = Σ taker_buy over the UTC day ÷ Σ qv, minus its
complement, from the 1 h store. The 5-minute variant uses the imbalance of the
LAST 5-minute bar of hour t ([t+55 min, t+60 min)). XS variant = within-universe
rank of the daily z.

## Cells (8, pre-named; BH-FDR q < 0.10 across all 8; simple returns everywhere)

| cell | test | floor |
|---|---|---|
| TS-1h BTC, TS-1h ETH | OLS r_{t+1} ~ z_t, HAC lag 24 | two-sided p < 0.01 AND same slope sign in 3/4 years 2021–2024 |
| TS-24h BTC, TS-24h ETH | OLS r_{d+1} ~ z_d, HAC lag 5 | same |
| TS-5m→1h BTC, TS-5m→1h ETH | OLS r_{t+1} ~ z5_t, HAC lag 24 | same |
| XS-24h IC, XS-7d IC | daily Spearman IC of z-rank vs next-day (next-7-day) return rank, NW-t lag 5 (10) | |IC| ≥ 0.02 AND NW-t ≥ 3 AND right sign in 2/3 sub-periods (2021–22 / 2023–24 / 2025Q1) |

A cell "survives" iff it clears its floor AND its p is rejected by BH-FDR. The
sign is not pre-fixed (continuation vs reversal both admissible); the dev sign
is a declared one-bit fit carried into P1 and counted in its multiplicity.

## Cost pre-statement (arithmetic, before any run)

An hourly sign(z) book flips roughly every other bar (≈ 12 flips/day) ⇒
≈ 60 bp/day at 5 bp taker ⇒ needs ≥ 5 bp mean |effect| per traded hour. A
TS-1h survivor whose P0 slope × E|z| implies < 5 bp per bar is recorded as
"real but arithmetic-dead" without a P1 run (llg precedent, §72).

## P1 (one frozen config per surviving cell; house gates)

TS: position = sign(z_t)·1, hold one bar, 5 bp taker per side on |Δpos|;
24 h cells add realized funding. XS: quintile long-short daily via
`opt.run_ls` (q 0.2, equal weight, 5 bp + funding). Gates: dev net SR ≥ 1.0,
circular-shift placebo (500 draws, min shift 30 bars) p < 0.10, 2× cost-stress
keeps sign, max single-name |PnL| share ≤ 50 %, convention swap no flip.
Hourly survivors additionally reported through the exec_pf LTM overlay.

## Multiplicity

8 P0 cells (BH-FDR); P1 n_trials = number of survivors × 2 (sign bit);
cumulative ledger denominator reported.

## Holdout

H2 contamination-disclosed 2025-04-01 → 2026-07-01 (price panel observed by
prior programs; flow signal virgin); one-shot only after stop-and-decide.
F window untouched.

## Stop rule

0/8 ⇒ family CLOSED ("order flow carries no linear next-bar information at
the tested horizons on this data"); no lag/window/threshold changes. Any
survivor ⇒ P1 as registered, then stop-and-decide.

## Mechanics

Predlab worktree; `scripts/predlab_register_oflow.py`,
`scripts/predlab_oflow_p0.py` (own 1 h cache `data/predlab/oflow/cache_1h/`
including the taker panel; xfam_lib `nw_tstat`, `bh_fdr`,
`year_sign_consistency`, `circular_shift_placebo`; `xsec.daily_ic`;
`opt.monthly_universe`); results `data/predlab/oflow/p0_result.json`; ledger
`predlab_oflow`; THESIS §80. Effort 1 day; cost $0.
