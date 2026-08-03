# Stage O3 — universe (predlab_opt)

Grid frozen pre-run (gates `predlab_opt.stages.O3`, 9 configs; signal
ewma_20, portfolio eq-quintile-daily). Reference: top-200 no floor, full
net SR +1.928, MaxDD 46.3%.

## Results (net SR, full 2021-01→2026-07)

| config | full | D | V | MaxDD | 2×costs |
|---|---|---|---|---|---|
| topn100 | +1.772 | +1.782 | +1.766 | 46.3% | +1.706 |
| topn150 | +1.889 | +1.644 | +2.639 | 46.3% | +1.814 |
| topn300 | +1.845 | +1.655 | +2.563 | 46.3% | +1.761 |
| adv1m | +1.931 | +1.675 | +2.757 | 46.3% | +1.852 |
| **adv5m** | +1.974 | +1.726 | +2.770 | 43.9% | +1.894 |
| adv20m | +1.771 | +1.613 | +2.228 | 60.4% | +1.700 |
| topn150_adv5m | +1.933 | +1.702 | +2.639 | 43.9% | +1.858 |
| topn300_adv5m | +1.921 | +1.734 | +2.570 | 43.9% | +1.836 |
| topn300_adv20m | +1.769 | +1.612 | +2.228 | 60.4% | +1.698 |

## Verdict: NO ADOPTION — axis closed this cycle

Best = adv5m +1.974 (Δ+0.046 < +0.10 floor). Universe surface flat
around top-200; ADV 5M floor is a mild consistent positive (better full,
D, MaxDD, 2×costs) but under the adoption floor. adv20m harmful (cuts
breadth in the thin early period; DD 60.4%).

## Forensic probe (identical-MaxDD anomaly) — resolved, not a bug

topn100/150/300/ref all showed BIT-IDENTICAL MaxDD 0.4634814671 despite
different net series (1918/2008 days differ; max daily diff 12.3%).
Probe: DD trough = 2021-03-28 for every config. In Q1-2021 the listed
USDT-perp cross-section (min 78 names/day, coverage audit) is smaller
than every top-N cutoff → all universes degenerate to "all listed names"
during exactly the DD-defining episode; books diverge only later.
Consequence recorded: the strategy's worst drawdown lives in the
thin-breadth early regime — a breadth floor (min-names guard), not a
tighter universe, is the relevant DD lever; noted for O4/O8.

Ledger: 9 rows + 1 ref (cumulative predlab_opt trials: 32; program
n_trials for next DSR: 48).
