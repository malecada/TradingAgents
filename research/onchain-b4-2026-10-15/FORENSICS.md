# B4-CP4 forensics — what the confirmed volatility result is, and what it is not

Registered result (`SCREEN.md`, `HOLDOUT.md`): 3 of 42 development comparisons passed
the gate; in the sealed 2025-01-01 → 2026-10-12 window, two of them passed Holm at
α = 0.05 and one failed:

| Selected | Sealed loss difference | p (Holm) | Result |
|---|---|---|---|
| V6 next-6-hour log realised volatility, linear, price + stablecoin flows (HS) vs price (H0) | −0.0222 (15,529 h) | < 0.0001 | pass |
| V6, trees, price + ETH flows (HE) vs H0 | −0.0108 (15,529 h) | < 0.0001 | pass |
| R7 7-day log return, trees, price + all Coin Metrics metrics (DA) vs D0 | +0.0003 (643 d) | 0.867 | fail |

Everything below is exploratory: the development checks were run after the screen and
the sealed checks after the window was opened. Outputs:
`research_artifacts/onchain-b4/explore/` (`forensics.txt`, `mechanism_a.txt`,
`mechanism_bcd.txt`).

## 1. Size and stability in the sealed window

| Comparison | Loss, flows vs price | R² against a constant | Relative error change |
|---|---|---|---|
| V6 linear HS vs H0 | 0.3165 vs 0.3387 | 0.336 vs 0.290 | −6.6 % |
| V6 trees HE vs H0 | 0.3093 vs 0.3201 | 0.351 vs 0.329 | −3.4 % |

Both differences are negative in every quarter from 2025Q1 to 2026Q4 (stablecoin
flows −0.020 to −0.028; ETH flows −0.007 to −0.015). The development gain of the
stablecoin comparison came from 2023 (−0.017) and 2024 (−0.016) and was absent in
2019–2020; it grows with stablecoin activity.

## 2. Richer intraday price baseline (P0)

H0 has 1-, 4-, 24- and 168-hour returns, 24- and 168-hour realised volatility and
24-hour volume, but no last-hour size of move or last-hour volume. P0 adds |r₁|, 4- and
6-hour realised volatility, and last-hour and 4-hour volume.

| Comparison | Development (walk-forward 2019–2024) | Sealed 2025–26 (refit on development) |
|---|---|---|
| P0 vs H0, V6 linear | −0.0099 [−0.0118, −0.0081], 6/6 years | — |
| P0 + stablecoin flows vs P0, V6 linear | −0.0004 [−0.0016, +0.0007], 2/6 | −0.0072, p < 0.0001 |
| P0 + stablecoin flows vs P0, V6 trees | +0.0027 [−0.0009, +0.0066], 3/6 | −0.0116, p < 0.0001 |
| P0 + ETH flows vs P0, V6 linear | +0.0029 [+0.0010, +0.0048], 1/6 | −0.0020, p 0.012 |
| P0 + ETH flows vs P0, V6 trees | −0.0022 [−0.0036, −0.0008], 4/6 | −0.0049, p < 0.0001 |
| P0 + stablecoin flows vs P0, V24 linear / trees | +0.0032 / +0.0212 (worse) | −0.0013 / −0.0039, p < 0.0001 |

Reading: over 2019–2024, most of the registered gain is last-hour market activity that
the registered price baseline omits; exchange data carries it equally well. In
2025–26, stablecoin flows still add to the richer baseline (about 2–4 % of loss) — a
post hoc result on a single window that has already been used once.

## 3. Timing canary (development, V6)

| Stablecoin/ETH features | Linear HS vs H0 | Trees HE vs H0 |
|---|---|---|
| Moved one hour into the future (oracle) | −0.0071 | −0.0089 |
| Registered timing | −0.0044 | −0.0035 |
| Lagged one hour | −0.0042 | −0.0030 |

The harness rewards future information (oracle row), and the registered gain survives a
one-hour lag almost unchanged: it does not depend on same-hour alignment between chain
and exchange clocks.

## 4. Which stablecoin features carry it (development, V6 linear, one group at a time)

Current-hour z-scores (−0.0054, 5/6 years), transfer counts (−0.0040, 4/6) and
large inflows ≥ $1M (−0.0033, 5/6) carry the gain; 24-hour sums make it worse
(+0.0016) and the 24-hour net flow does nothing (+0.0002). The information is the
intensity of stablecoin movement to and from exchanges in the current hour, not the
direction of net flow.

## 5. Other checks

- **Harness against a constant.** Price history explains next-6-hour log volatility
  (R² 0.40 linear, 0.47 trees), 24-hour (0.45 / 0.55) and 7-day (0.20 / 0.17); returns
  and direction are no better than a constant at any horizon (R² ≤ 0.001, log-loss gain ≤ 0).
- **Deposit inference.** Labels-only stablecoin flows perform as well as
  deposit-expanded flows for V6 (linear +0.0001, interval across 0; trees +0.0054, the
  expanded flows worse); for ETH flows
  the expansion helps only V24 linear (−0.0019, interval below 0).
- **Motivating return claims.** After H0, neither ETH nor stablecoin net inflow predicts
  1-, 6- or 24-hour returns (largest |t| 2.1, labels-only ETH at 24 h); the arXiv
  return claims are not reproduced here. ETH net inflow relates positively to
  next-6-hour volatility (t 2.4).
- **Feature counts.** H0 8, HE/HS 19, HA 40 columns against 59,138 hourly development
  rows (4,414 excluded by missing Binance bars); D0 7, DF 17, DA 27 against 2,648
  daily rows.
- **R7 (failed).** Both trees arms lose to a constant forecast (R² −0.27 vs −0.34) —
  the B3 pattern of less-bad overfitting; the sealed window rejected it.

## Reading

The registered, one-shot test confirms that hourly exchange-flow activity — stablecoin
transfers and ETH transfers to and from exchange entities — improves next-6-hour ETH
volatility forecasts over the registered price/volume baseline out of sample (−6.6 %
and −3.4 % squared error, every quarter of 2025–26). It is a volatility result, not a
return or direction result: no flow feature predicts returns. Most of the
development-period gain is reproduced by last-hour exchange activity that the registered
baseline lacked; the part that survives a richer intraday baseline appears only in the
2025–26 window and is post hoc. A future study that wants to claim on-chain information
beyond exchange activity needs that richer baseline registered from the start and a
new sealed period (from 2026-10-13).
