# B2-CP3 forensics — why the screen is negative

Run 2026-10-14 on the development window only (2017-10 → 2024, walk-forward test
years 2019–2024). No sealed 2025–26 price, volume or target was read.

## Registered result

0 of 40 comparisons pass the gate (`SCREEN.md`); `selection.json` is empty, so the
sealed holdout stays unused. Many linear comparisons are significantly worse out of
sample (for example T5 log volume, S3 vs S1: +0.669 MSE, interval +0.467 to +0.917).
The closest cases are tree models that are better in 6 of 6 years with an interval
that still crosses zero: T3 weekly return S3 vs S1 (−0.00157, upper +0.00043) and T1
daily direction S4 vs S2 (−0.00748, upper +0.00492).

## Checks

1. **The harness finds signal where it exists.** Price/volume history alone (S0,
   linear) against a training-mean constant, same folds: T4 next-week log realised
   volatility R² 0.216; T5 next-week log volume R² 0.961. Direction and return are not
   predictable from price history (T1 log-loss gain −0.002, T2 −0.006, T3 R² −0.10),
   as expected for a liquid market.
2. **Feature counts against samples.** S0 7, S1 35, S2 55, S3 227, S4 379 columns
   against 378 weekly development rows (65 training rows in the 2019 fold). The ridge
   and logistic models often selected the largest alpha on the registered grid (1000),
   so the motif sets were under-regularised; this explains why S3/S4 are worse, not
   just equal.
3. **Tree probabilities overfit.** HistGradientBoosting log loss on next-week direction
   from S0 is 0.806 against 0.694 for the constant; on ~250 training rows the fixed 300
   iterations are too many for probability estimates.
4. **Exploratory compression (post hoc, not registered, not confirmatory).** Each block
   reduced to 10 principal components fitted on the training fold, alpha grid widened to
   0.1 … 1e5, same folds and bootstrap
   (`research_artifacts/onchain-b2/explore/pca_probe.txt`). No block improves any target:
   T1/T2/T3 differences are within ±0.003 with intervals across zero; for T4 and T5 every
   block makes the forecast worse (e.g. T4 + activity +0.011, T5 + exchange flows +0.013,
   intervals above zero).

## Reading

Within this design, weekly ETH transaction-graph features — activity, exchange and
whale flows, motif histograms and role-split motif scores — add no out-of-sample
information to price and volume history for next-day or next-week direction, next-week
return, realised volatility or volume over 2019–2024. The null survives a harness that
does detect volatility and volume persistence, and a lower-variance (compressed,
more regularised) variant. It is a negative result for these features at these
horizons, not proof that no on-chain information exists at other horizons, assets or
with other constructions.

The sealed 2025–01-06 → 2026-10-05 window has not been read and remains available for a
future, separately registered hypothesis.
