# exec_fcst — Forecasts as execution inputs (registered 2026-09-04)

Status: **REGISTERED pre-result** (report-grade registration: numbers
pre-committed, dev-only H3, no strategy claim). Gates key `predlab_exec_fcst`.
Source: `master_thesis/LEADS_SCOPE_2026-09-02.md` Lead 10. Decision under the
afk autonomy grant: neutral EW book (the lead-1 book failed, §76).

## Goal (measurement)

(a) A causal intraday volume profile improves a participation schedule versus
uniform slicing under the §61 square-root impact model; (b) the Phase-1
realized-variance champions (HARQ BTC, EGARCH ETH) improve the impact model's
out-of-sample cost prediction versus a naive-20 volatility.

## Design (frozen)

- **Book:** equal-weight monthly top-200 PIT universe (`opt.monthly_universe`,
  prior-month median quote volume), weights 1/n set on the first trading day
  of each month and held (no daily rebalancing); AUM grid {1e7, 3e7, 1e8} USD,
  headline 3e7. Per name-day trade T = AUM·|ΔW|; dev 2021-01-01 → 2025-03-31;
  name-days with T > 0 and ≥ 20 hourly bars of data.
- **Impact per hour:** k·σ_h·x_h·√(x_h / V_h), k = 1, σ_h = trailing-20-day
  std of the symbol's hourly simple returns (lagged one bar), V_h = realized
  hourly quote volume; fees are identical across schedules and dropped.
- **Schedules:** S_uni x_h = T/24; **S_prof** x_h = T·ŝ_h with ŝ_h = the
  symbol's trailing-28-day mean share of daily quote volume by hour-of-day,
  computed from days strictly before the trade day (causal, no model fitting);
  **S_oracle** x_h ∝ realized V_h (cost lower bound, reported). The stored
  BTC/ETH one-step-ahead volume forecasts are NOT a day-start input and are
  out of scope (declared).
- **Cell (a) gate:** mean daily cost reduction 1 − Σcost_prof/Σcost_uni ≥ 5 %
  at AUM 3e7 AND stationary-bootstrap p_pos ≥ 0.90 (Politis–Romano, mean block
  21 d, 2,000 draws) on the paired daily differences cost_uni − cost_prof.
  Reported at the other AUM levels and against the oracle.
- **Cell (b):** predicted impact ∝ σ̂ and realized impact ∝ σ_real with the
  same trade and ADV, so the QLIKE of predicted vs realized impact reduces
  exactly to the QLIKE of the σ forecast (trade-invariant — stated now). Per
  day, σ̂ = √(pred RV) from the stored 24 h forecasts (BTC `harq`, ETH
  `egarch11`, `predlab_p1_classical`), σ_naive = √(trailing-20-day mean of
  realized RV), σ_real = √(y_true). Gate: mean QLIKE improvement ≥ 5 % AND
  Diebold–Mariano (HAC lag 5) p < 0.05, both coins.

## Stop rule / mechanics

Report-grade: every number is recorded regardless of outcome; no schedule,
window or k changes. Script `scripts/predlab_exec_fcst.py` (register / run);
result `data/predlab/exec_fcst_result.json`; ledger `predlab_exec_fcst`;
THESIS §85. Effort < 1 day; cost $0.
