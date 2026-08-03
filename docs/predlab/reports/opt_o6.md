# Stage O6 — volume/liquidity weighting (predlab_opt)

Grid frozen pre-run (8 configs: 6 deployable PIT liquidity weightings + 2
ORACLE future-volume diagnostics, dominance design — LGB volume champions
are BTC/ETH-only, so the question "could per-alt volume forecasts weight
the book?" is answered via the perfect-foresight upper bound instead of
building 200 alt models). Base: ewma_20 raw book SR +1.928.

## Results

| config | full | D | V | MaxDD | conc |
|---|---|---|---|---|---|
| qv_w7 | +1.332 | +1.064 | +1.990 | 88.9% | 7.1% |
| qv_w30 | +1.499 | +1.332 | +1.965 | 67.1% | 4.5% |
| qv_sqrt_w7 | +1.786 | +1.400 | +2.824 | 61.0% | 4.3% |
| qv_sqrt_w30 | +1.858 | +1.578 | +2.711 | 52.9% | 3.3% |
| qv_inv_w7 | +1.287 | +1.433 | +0.783 | 51.3% | 1.4% |
| qv_inv_w30 | +1.536 | +1.494 | +1.676 | 53.8% | 1.4% |
| DIAG oracle_next1 | −4.456 | — | — | 100% | 4.8% |
| DIAG oracle_next7 | −3.627 | — | — | 100% | 4.2% |

## Verdict: NO ADOPTION — axis CLOSED BY DOMINANCE

- Every deployable weighting loses SR vs equal weight (best qv_sqrt_w30
  −0.07) and concentrates risk (MaxDD 53-89% vs 46%).
- Both tilt directions fail: toward liquidity (mega-cap concentration)
  AND away from it (small-name books, V-window collapse +0.78).
- **Oracle future-volume weighting is catastrophic** (−3.6/−4.5, 100%
  DD): tomorrow's volume spikes mark blowup/pump names; weighting toward
  predicted volume anti-selects into event risk. Any volume FORECAST
  weighting is bounded by this — the forecast-weighting question closes
  without building per-alt LGB models (predlab_p6 alt-generalization
  forecast-skill claim untouched).
- Consistent with O2 (ivol) and O5: within-leg re-weighting of an
  equal-weight quintile book only ever hurts here. Equal weight is the
  robust construction on this anomaly.
- LGB volume champions keep their P5 role (execution support), not
  portfolio weights.

Ledger: 8 rows (cumulative predlab_opt trials: 60; program n_trials: 76).
