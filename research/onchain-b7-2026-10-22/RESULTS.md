# B7 results — feature and target engineering on the hourly on-chain tables

Exploratory study with a pre-declared plan (`PLAN.md`, amendment 1 before the run); every
comparison is in `TABLES.md` (generated) and `research_artifacts/onchain-b7/forecast/results.json`.
Tracks: A′ = 2019-04 → 2024-12 against price, intraday and 1-minute range features (test years
2020–2024); B = 2021-04 → 2026-10-12 against the same plus DVOL and hourly near-expiry implied
volatility (groups 2022–24 and 2025–26, both opened in B4–B6). Samples ≈ 41,000 tested hours per
track and target (per-year rows and J positives in `TABLES.md`). 198 rows; 12 units, 16 minutes.

## Answer

Re-engineering the same hourly series (weekly deseasonalisation, five time scales, bursts,
event-time, interactions) does not beat B4's two transforms, the 39 B6 series add nothing
under the new engineering either, and early-stopped larger trees are worse than B4's small
fixed trees for every volatility-type target. The only coherent signal is the one already
known: B4's flow block improves next-6-hour forecasts of volatility (V6) and of the largest
5-minute move (M6) in the option-era window, in both families, by 1.4–3 % of error. Tail
events (J6, J24) are not forecast by anything beyond the base rate and price history.

## Q1 — engineering (reading guide: Y1 vs X1, Y1 vs X1a, Y2 vs Y1, trees_es vs trees_fixed)

| Comparison | A′ V6 ridge / trees | A′ V24 ridge / trees | B 2022–24 V6 ridge / trees | B 2025–26 V6 ridge / trees |
|---|---|---|---|---|
| Y1 vs X1 (new engineering vs B4's 22 columns) | +0.005 [−0.001, +0.010] / −0.001 [−0.005, +0.004] | +0.010 [+0.003, +0.016] / +0.003 [−0.005, +0.012] | +0.007 [+0.003, +0.012] / +0.006 [+0.000, +0.013] | +0.003 / −0.003 [−0.005, −0.000] |
| Y1 vs X1a (vs B4's transforms of all 15 series) | +0.002 / +0.003 | +0.005 / +0.003 | +0.005 [+0.001, +0.009] / +0.008 [+0.001, +0.015] | +0.003 / −0.002 |
| Y2 vs Y1 (B6 series added) | +0.481 / +0.017 [+0.011, +0.024] | +0.721 / +0.011 | +0.037 / +0.024 [+0.015, +0.033] | +0.011 / +0.001 |
| trees_es vs trees_fixed on Y2 | +0.016 [+0.011, +0.021], 1/5 | +0.009 [+0.003, +0.014] | +0.013 [+0.008, +0.018] | −0.001 [−0.003, −0.000] |

No engineering row meets a pre-declared criterion for V6, V24, M6 or M24 in either track
(Y1 vs X1a passes once, A′ J6 trees, −0.0018 [−0.0035, −0.0003], the single pass among 24
Y1-vs-X1a rows). The new engineering is worse than B4's columns in 2022–24 (both families,
all four volatility-type targets) and marginally better only for trees in 2025–26 (V6
−0.003, M6 −0.003, sign rows). The B6 series hurt everywhere: linear models blow up as in B6
(alpha 10,000 chosen; first folds extrapolate dormant entity features; A′ V24 +0.72 of
squared error), trees lose 1–2 % of error. Early stopping on the time-ordered tail chose
24–317 iterations with 15 leaves and was worse than 100 iterations with 7 leaves in 4 of 5
years of A′ and in 2022–24 of B for V6, V24, M6 and M24; it beat the fixed trees only for
J24 in B (−0.014 [−0.026, −0.003], 2022–24), where the fixed trees overfit the rare class.

## Q2 — targets (reading guide: X1 vs X0 and Y2 vs X0 on J and M, V as reference)

| X1 vs X0 (B4 flows vs baseline) | A′ 2020–24 ridge / trees | B 2022–24 ridge / trees | B 2025–26 ridge / trees |
|---|---|---|---|
| V6 | +0.002 / +0.007 [+0.001, +0.014] | **−0.008 [−0.011, −0.005], 3/3 / −0.009 [−0.013, −0.005], 3/3** | **−0.006 / −0.009** |
| V24 | +0.003 / +0.020 | −0.000 / −0.012 [−0.024, −0.001], 1/3 | −0.002 / −0.002 |
| M6 | −0.001 / −0.010 [−0.017, −0.004], 4/5 | **−0.008 [−0.011, −0.005], 3/3 / −0.009 [−0.013, −0.006], 3/3** | **−0.007 / −0.013** |
| M24 | +0.010 / +0.010 | +0.012 / +0.005 | −0.003 / −0.001 |
| J6 (log loss) | −0.001 / −0.007 [−0.012, −0.003], 4/5 | +0.000 / −0.002 [−0.005, +0.000] | +0.000 / +0.002 |
| J24 (log loss) | −0.001 / −0.004 | +0.002 / −0.001 | +0.000 / −0.006 |

Track B, V6 and M6: the flow block passes in both families and both groups (2022: −0.003 /
−0.004, 2023: −0.015 / −0.018, 2024: −0.006 / −0.006 for V6 ridge / trees; M6 alike), a
1.4–1.7 % (V6) and 1.6–3.3 % (M6) reduction of squared error against a baseline that already
holds price history, 1-minute ranges, DVOL and hourly implied volatility. This is the B4/B6
finding at a stronger baseline (B6: 2–4 %). The V24 trees pass is carried by 2023 (−0.045;
2022 and 2024 ≈ 0) and is not read as a finding. Track A′ (no option market, 2020–24): the flow
block adds nothing to V6 or V24 once 1-minute range features are in the baseline (trees
worse in 2020, 2021 and 2023), consistent with B4's reading that pre-2025 flows were largely
an intraday-activity proxy; M6 trees pass (−0.010, 4/5) with ridge null. Tail targets: the
A′ J6 trees pass (−0.007, 4/5) is the baseline's own overfit — the X0 trees used 417 and 335
iterations in 2020–21 against a log loss worse than the base rate (0.0996 vs 0.0943) while
X1 used 49 and 34 — and the logistic rows (ridge) are null; J24 is null everywhere; in track
B no J row passes an interval criterion. Y2 vs X0 passes only where X1 vs X0 does, by less.

## Chance

198 rows, 33 `passed` flags, of which 23 are sign-only 2025–26 rows (expected ≈ 50 % by
chance) and 10 interval passes among 132 interval rows (≈ 7 expected). The interval passes
cluster in one place — X1 vs X0 for V6 and M6 in track B, both families — and that cluster
replicates B4 and B6; the rest (A′ J6 trees ×3, A′ M6 trees, B V24 trees, J24 trees_es vs
fixed) are single-family or single-year and are read as chance.

## Disclosures

- Sample attrition: track A′ keeps 47,119 of 50,448 window hours, track B 47,456 of 48,480,
  mostly from 168-hour price windows after missing Binance bars (2020: 7,304 of 8,784
  rows); the unavailable days 2020-11-01 (B6 tables) and 2025-09-24 (B4 tables) remove 191
  rows each; `rg_range24` voids 24 rows per outage hour (518 rows in A′). The row set is
  the same for every set and family within a track and target.
- J positives per test year are 64–205 (base rate 1.7–1.9 %); the first folds use fallback
  alpha 100 and, after amendment 1, the minimum iteration count when the validation tail has
  fewer than 10 positives (A′ 2020: 10 of 586).
- `ev_since_10m` is zero in 44 % of hours since 2019 (a ≥ $10M stablecoin deposit occurs in
  most hours); the event-time features are therefore near-constant after 2022.
- Track B's option-market columns are B6's (identical computation).

## Closure

B7 is closed: feature engineering beyond B4's two transforms, the B6 series, tuned tree
models and tail or largest-move targets add nothing new. The hourly ETH on-chain content
remains exchange-flow intensity → next-6-hour volatility level and largest move, worth
1–3 % of squared error beyond price, range and option-market information in 2022–26 and
nothing in 2020–24 once intraday ranges are known.
