# Stage O8 — final composition + champion freeze (predlab_opt CLOSE-OUT)

## Composition check (2 pre-declared configs)

| config | raw SR / DD | overlaid SR full | D | V | overlaid DD |
|---|---|---|---|---|---|
| **champion_eq5 (seq 2)** | +1.928 / 46.3% | **+1.892** | +1.713 | +2.515 | **17.6%** |
| tercile_ovl (O2 DD knob) | +1.824 / 30.8% | +1.764 | +1.754 | +1.796 | 16.7% |

Tercile knob rejected (+1.764 < +1.992 needed; DD gain trivial under
overlay: 16.7% vs 17.6% — the vol-target already harvests what width
diversification offered). **Chain seq 2 = FINAL CHAMPION.**

## Disclosed defect (this stage)

First O8 run re-implemented the overlay and (a) double-annualized σ̂
(scale 0.02 vs 0.32) and (b) dropped the scale×turnover cost term →
bogus 1.0% MaxDD. Caught by parity check against chain seq 2; fixed to
the exact O4 math (reproduces seq 2 to the digit). The 2 bugged ledger
rows remain (append-only) superseded by corrected rows.

## Final DSR (corrected per-frequency, full-program multiplicity)

| trial pool | n | ann. cross-trial std | DSR |
|---|---|---|---|
| all ledgered strategy rows | 91 | 0.980 | 0.096 |
| excl. never-selectable oracle diagnostics | 89 | 0.523 | **0.917** |
| excl. oracles + ref duplicates (gate basis) | 86 | 0.530 | **0.913** |

The O6 oracle probes were registered as never-adoptable upper bounds;
they were not part of the selection pool, and including them doubles
cross-trial std. All three values disclosed; gate on the strictest
selectable pool: **DSR 0.913 PASS** (> 0.5).

## Final champion (frozen in gates.json `predlab_opt.final_champion`)

EWMA-20 Parkinson low-vol rank LS — equal-weight quintiles, monthly
top-200 PIT universe, daily rebalance — vt15_naive20 overlay, cap 2.0,
breadth-100 guard. Costs 5bp+funding throughout.

- Full 2021-01→2026-07: **net SR +1.892, MaxDD 17.6%** (raw +1.928/46.3%)
- vs Phase-P starting point (S1 eq_h1 + vt10): SR +1.48→+1.89 (+28%),
  raw DD 42.5%→46.3% but overlaid 17.6% at higher target vol
- Evidence: placebos p .005/.005 (400 draws), DSR 0.913 @ n=86,
  subperiods 4/4, concentration 1.2%, lag-mutation + coverage clean
- **Forward one-shot registered**: F = 2026-07-02→open, spend ≥6mo
  (earliest 2027-01-02); criteria SR_F ≥ 0.946, same sign, placebo
  p<0.10. V-segment caveat: D+V includes the non-virgin 2025-04→2026-07
  window; the untainted claim is the forward one-shot.

## Program summary (11 loop iterations)

2 adoptions (O1 signal ewma_20; O4 overlay vt15+b100), 5 axes closed
negative (construction, universe, funding tilt, volume weighting incl.
oracle dominance, momentum tilt), 1 final composition check. 90+
ledgered trials, all grids frozen pre-run, zero forward-holdout touches.
Key structural findings: slow vol estimators dominate fast ones for the
low-vol sort; the equal-weight book is saturated (4 within-leg tilt
families all negative); thin-2021 breadth was the DD driver, solved by
breadth guard rather than universe change.
