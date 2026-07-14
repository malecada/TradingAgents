# Pre-Registration: Stress Index Early-Warning System (2026-07-14)

Frozen before any experiments run.

---

## Gate Definition

```json
{
  "registered": "2026-07-14",
  "dev_window": ["2021-11-01", "2025-03-31"],
  "holdout_window_start": "2025-04-01",
  "episode_rule": "crash day t: 10-day forward log-return of EW BTC+ETH close <= log(0.85); episode = maximal run of crash days, episodes separated by <10 non-crash days are merged; episode_start = first crash day",
  "warn_rule": "composite = mean(component z-scores, all lagged 1 day, z over trailing 365d window with min 180d); WARN active while composite >= k, released below k-0.25; components and k from grid",
  "grid": {
    "component_sets": [["z_fund", "z_oi"], ["z_fund", "z_oi", "z_liq"], ["z_fund", "z_oi", "z_liq", "z_fg"]],
    "k": [1.0, 1.5, 2.0]
  },
  "detection_window_days": 20,
  "dev_select": {
    "hit_rate_min": 0.5,
    "false_alarms_per_year_max": 6,
    "placebo_p_max": 0.05,
    "overlay_delta_maxdd_max": 0.0,
    "overlay_delta_sr_min": -0.10,
    "tiebreak": "lowest placebo_p, then most negative overlay_delta_maxdd"
  },
  "holdout_deploy": {
    "hit_rate_min": 0.5,
    "false_alarms_per_year_max": 6,
    "placebo_p_max": 0.05,
    "overlay_delta_maxdd_max": 0.0,
    "overlay_delta_sr_min": -0.10,
    "one_shot": true
  }
}
```

---

## Component Definitions (Frozen)

| component | formula (daily, per coin, then EW-averaged across BTC+ETH) |
|---|---|
| `z_fund` | z365(funding_rate_ma7) |
| `z_oi`   | z365(oi_close / oi_close.shift(30) − 1) |
| `z_liq`  | z365(liq_total_usd / oi_close) |
| `z_fg`   | z365(abs(fng_value − 50)) — portfolio-level, not per coin |

where z365(x) = (x − rolling_mean(x, 365)) / rolling_std(x, 365), min_periods=180. Every input series is `.shift(1)` FIRST (value dated D is computed from data ≤ D−1).

---

## Grid Closure

Grid is closed at 9 configs; any config evaluated outside this grid voids the experiment.

---

## Evidence Basis

- BIS WP 1087: Carry-liquidation asymmetry under crypto market stress (carry portfolios collapse during fund liquidation cascades; sell pressure on funding-based strategies asymmetric with respect to buy-and-hold)
- No published external system reports detection metrics for a positioning-based crypto early-warning index; this experiment produces the first pre-registered detection-metric evaluation. Evidence basis is mechanism-level only: BIS WP 1087 documents that a rise in standardized carry predicts increased sell liquidations (verified 3-0 in the Jul-12 research pass); design rationale in SENTIMENT_EARLY_WARNING_RESEARCH_2026-07-14.md (D2).

---

Document locked: 2026-07-14 (before Task 1 experiments)
