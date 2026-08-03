# Stage O2 — portfolio construction (predlab_opt)

Grid frozen pre-run (gates `predlab_opt.stages.O2`, 12 configs; signal =
chain-seq-1 champion ewma_20). Incumbent reference: eq quintiles, daily,
no buffer — full net SR +1.928 (D +1.671 / V +2.757), MaxDD 46.3%.

## Results (net SR, 5bp+funding; full 2021-01→2026-07)

| config | full | D | V | MaxDD | turn | 2×costs |
|---|---|---|---|---|---|---|
| decile | +1.875 | +1.443 | +3.207 | 66.8% | 0.30 | +1.809 |
| tercile | +1.824 | **+1.747** | +2.076 | **30.8%** | 0.20 | +1.737 |
| rank | +1.924 | +1.563 | +3.063 | 56.4% | 0.28 | +1.854 |
| ivol | +1.696 | +1.534 | +2.198 | 45.0% | 0.33 | +1.603 |
| buf25 | +1.920 | +1.741 | +2.501 | 42.3% | 0.19 | +1.854 |
| buf50 | +1.888 | +1.697 | +2.510 | 39.7% | 0.16 | +1.830 |
| buf100 | +1.778 | +1.617 | +2.304 | 35.7% | 0.12 | +1.731 |
| cad2 | +1.828 | +1.523 | +2.812 | 44.3% | 0.21 | +1.762 |
| cad3 | +1.918 | +1.608 | +2.901 | 43.6% | 0.18 | +1.859 |
| cad5 | +1.576 | +1.341 | +2.326 | 53.2% | 0.15 | +1.525 |
| decile_ivol | +1.780 | +1.322 | +3.237 | 66.2% | 0.37 | +1.697 |
| buf50_cad2 | +1.730 | +1.506 | +2.462 | 41.5% | 0.14 | +1.680 |

## Verdict: NO ADOPTION — axis closed this cycle

Nothing clears the +0.10 floor (needed ≥ +2.028; best = rank +1.924).
The incumbent construction (equal-weight quintiles, daily, no buffer) is
already at the flat top of this response surface. Stop rule: stage closed.

## Observations recorded for later stages (not acted on here)

- **Width is a risk dial, not an SR dial**: decile concentrates (V +3.21
  but MaxDD 67%), tercile diversifies (MaxDD 30.8%, best D-window SR
  +1.747, at −0.10 full SR). If the final composition needs DD headroom
  under the vol-target overlay (O4), tercile is the pre-declared knob.
- Buffers 25-50% deliver 25-35% turnover reduction at ≈flat SR —
  relevant only if later tilts (O5-O7) raise turnover costs.
- Deciles/rank load on the V regime (2025-26) — regime-dependent
  concentration premium, exactly what the consistency gate is for.
- ivol weighting hurts (−0.23): equal-weight legs already carry the
  low-vol tilt; double-tilting dilutes breadth.
- cad5 worst (−0.35): weekly rebalance too stale for a 20d-EWMA signal.

Ledger: 12 rows + 1 ref (cumulative predlab_opt trials: 23; program
n_trials for next DSR: 16 + 23 = 39).
