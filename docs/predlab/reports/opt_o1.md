# Stage O1 — signal construction (predlab_opt)

Grid frozen pre-run (gates `predlab_opt.stages.O1`, 11 configs): park mean
windows {3,10,20}, close-to-close vol {5,10,20}, vol-of-vol {10,20}, EWMA
park {5,10,20}. Portfolio params = incumbent eq_h1 defaults. Full window
2021-01-01 → 2026-07-01; D = 2021-01→2025-03, V = 2025-04→2026-07
(NON-VIRGIN, consistency check only). Reference: incumbent park_5
full-window SR +1.657 (D +1.483 / V +2.198), MaxDD 42.5%.

## Results (net SR, 5bp+funding)

| config | full | D | V | MaxDD | turn | 2×costs | conc |
|---|---|---|---|---|---|---|---|
| park_3 | +1.598 | +1.480 | +1.971 | 38.5% | 0.95 | — | 1.6% |
| park_10 | +1.735 | +1.508 | +2.449 | 47.5% | 0.39 | — | 1.3% |
| **park_20** | +1.786 | +1.511 | +2.666 | 44.3% | 0.24 | +1.706 | 1.5% |
| cc_5 | +1.185 | +0.803 | +2.312 | 56.2% | 1.06 | — | 1.3% |
| cc_10 | +1.556 | +1.452 | +1.872 | 35.1% | 0.58 | — | 1.3% |
| cc_20 | +1.746 | +1.487 | +2.539 | 39.5% | 0.34 | — | 1.8% |
| **vov_10** | +1.830 | +1.749 | +2.080 | 40.5% | 0.52 | +1.647 | 1.3% |
| **vov_20** | +1.872 | +1.621 | +2.650 | 34.1% | 0.30 | +1.763 | 2.3% |
| ewma_5 | +1.645 | +1.530 | +2.019 | 39.4% | 0.68 | — | 1.2% |
| **ewma_10** | +1.841 | +1.617 | +2.562 | 42.0% | 0.41 | +1.708 | 1.1% |
| **ewma_20** | +1.928 | +1.671 | +2.757 | 46.3% | 0.25 | +1.849 | 1.2% |

Bold = clears ΔSR ≥ +0.10 + V-consistency + concentration. All five also
pass sub-periods 4/4 and MaxDD ≤ 1.25× incumbent (cap 53.1%).

## Reading

- Slower vol estimators dominate: every 20-window variant beats its
  5-window sibling. Lower turnover (0.24-0.30 vs 0.64) both cuts costs
  and appears to track the persistent component of the low-vol anomaly.
- Parkinson-family > close-to-close at matched windows (range info
  helps); cc_5 is the worst config (turnover 1.06 + noisiest estimator).
- Vol-of-vol is competitive as a standalone (vov_20 +1.872, best MaxDD
  34.1%) — vol *stability*, not just level, prices the cross-section.
  vov_10 has the best D-window SR (+1.749) of all configs.
- No single-name concentration anywhere (max 2.3% abs share).

## Top candidate → verification (O-02b)

`ewma_20` (full +1.928, Δ +0.271 vs incumbent; 2×costs +1.849; subs 4/4).
Pending: dual placebos, DSR at n_trials = 27 (16 prior + 11 O1),
lag-direction canary, cost-off sanity, coverage audit
(`scripts/predlab_opt_o1_verify.py` → `opt_o1_verify.json`). Adoption
only on full pass; chain row to `opt_champion_chain.jsonl`.

## O-02b verification verdict (2026-07-31)

| check | result |
|---|---|
| placebo p_shift / p_xshuffle (200+200) | .005 / .005 PASS |
| DSR (registered gate, corrected per-frequency, n=27) | **0.842 PASS** |
| DSR original units-bug value / daily-only sensitivity | 0.169 (retained) / 0.991 |
| alignment sensitivity (lag mutation) | +1.93 → −1.91 unshifted — PASS (no smearing leak) |
| cost-off sanity / coverage | PASS / 2008/2008 days, median 200 names |

Disclosures: first DSR run repeated the PP-02 hourly-conversion units bug
(fixed per house precedent, both retained); `peek>real` canary expectation
was mis-specified for risk sorts (informative form = alignment
sensitivity; mechanical no-lookahead pinned in test_opt.py).

**ADOPTED: ewma_20 replaces park_5 as champion signal (chain seq 1).**
New incumbent: full net SR +1.928 (D +1.671 / V +2.757), MaxDD 46.3%,
turnover 0.25, 2×costs +1.849.
