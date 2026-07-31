# Phase-2 T7 report — cross-sectional IC battery (2026-07-31)

Registered `predlab_p2_t7` (frozen pre-result): monthly PIT top-200 universe
from the 799-symbol survivorship-safe store, 5 fixed signals, ridge/LGB
combos, floors |IC| ≥ 0.02 ∧ NW-t ≥ 3 ∧ 2/3 sub-period right-sign. Dev
2021-01-01 → 2025-03-31 (n = 1,551 days); holdout sealed.

## Raw-signal ICs vs next-day return rank (all five PASS floors)

| Signal | mean IC | NW-t | sub-periods right-sign |
|---|---:|---:|---|
| park_5 (trailing vol) | **−0.0888** | **−17.5** | 3/3 (2025Q1 −0.116) |
| mom_5 | −0.0548 | −12.6 | 3/3 |
| mom_21 | −0.0503 | −10.6 | 2/3 |
| rev_1 | +0.0362 | +8.5 | 2/3 |
| volchg_5 | −0.0229 | −6.9 | 3/3 |

Readings: (1) the **vol axis is the dominant cross-sectional return
predictor** — high-trailing-vol names underperform next day; (2)
**cross-sectional momentum is REVERSAL at daily horizon** in the top-200 —
mechanistically explaining §43's xs_mom trading failure (it was long
tomorrow's underperformers by construction); (3) classic short-term reversal
and a volume-spike fade both present. 7d horizon: same structure (park_5
−0.103/t −9.0; momentum negative; volchg dies). Vol-rank target: trivial
persistence (park_5 IC 0.565) — predictability-exists, mundane.

## Combos (registered): floors smashed, but no gain over best single signal

| Model | mean IC | NW-t | sub-periods |
|---|---:|---:|---|
| ridge_combo | +0.0822 | +19.2 | 0.088 / 0.077 / 0.078 |
| lgb_combo | +0.0772 | +24.1 | 0.085 / 0.070 / 0.072 |

Both pass every floor with the smoothest sub-period profiles in the battery —
but neither exceeds |park_5| = 0.089. Champion selection (single-signal vs
combo) is a Phase-5 MCS question; no post-hoc pick here.

## Microstructure forensic (declared slice, not a new signal)

park_5 holds in BOTH liquidity slices — top-50: IC −0.101 (t −15.7);
ranks 51–200: −0.083 (t −16.0). The effect is STRONGER among the deepest
names → not a bid-ask-bounce/illiquidity artifact. rev_1 shows the expected
mild size gradient (+0.029 top-50 vs +0.042 in the band) — partially
microstructural at the band, present in majors.

## Verdict

**T7 ret-rank 24h (and 7d): SKILL-CANDIDATE** — multiple floor-passing,
sub-period-stable, liquidity-robust signals plus passing combos, on a
pre-registered frozen grid. The TS-vs-XS asymmetry (time-series returns
unpredictable at every horizon; cross-sectional ranks richly predictable) is
the Phase-2 headline. Standing caveats: IC ≠ tradable (rev_1/park are
high-turnover; §43/§46 showed cost fragility at the portfolio level —
Phase-P question, explicitly out of scope); holdout untouched.
