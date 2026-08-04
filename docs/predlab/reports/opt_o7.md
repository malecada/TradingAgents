# Stage O7 — momentum/trend tilt inside the book (predlab_opt)

Grid frozen pre-run (8 configs: 6 within-leg momentum tilts — skip-5
momentum z, λ=±0.5, windows 30/90/180d — + 2 SMA trend gates). Disclosed
priors: standalone XS momentum NEGATIVE (§43), wide trend NEGATIVE (§45).
Base: ewma_20 raw book SR +1.928, MaxDD 46.3%.

## Results

| config | full | D | V | MaxDD | turn |
|---|---|---|---|---|---|
| mom30_win | +1.832 | +1.569 | +2.627 | 49.4% | 0.40 |
| mom90_win | +1.842 | +1.606 | +2.584 | 47.3% | 0.32 |
| mom180_win | +1.808 | +1.546 | +2.673 | 49.3% | 0.30 |
| mom30_lose | +1.798 | +1.575 | +2.538 | 48.6% | 0.43 |
| mom90_lose | +1.830 | +1.566 | +2.701 | 46.4% | 0.36 |
| mom180_lose | +1.908 | +1.666 | +2.679 | 44.2% | 0.32 |
| gate_sma100 | +1.176 | +1.059 | +1.595 | 79.3% | 0.60 |
| gate_sma200 | +1.423 | +1.284 | +1.887 | 71.1% | 0.45 |

## Verdict: NO ADOPTION — axis closed this cycle

- Tilt family: flat-to-negative in BOTH directions and at every window
  (−0.02…−0.13 vs incumbent; best mom180_lose +1.908 < floor +2.028).
  Momentum carries no incremental information within the low-vol book —
  consistent with §43 (standalone) now also conditionally.
- Trend gates actively destructive (−0.51/−0.75, DD 71-79%): zeroing
  leg names breaks the long/short balance episodically (turnover up,
  breadth down, residual net exposure) — same failure shape as O3 thin
  books.
- Fourth consecutive within-leg modification negative (ivol, carry,
  volume, momentum). The equal-weight low-vol book is saturated: no
  tested secondary characteristic adds SR at 5bp costs.

Ledger: 8 rows (cumulative predlab_opt trials: 68; program n_trials: 84).
