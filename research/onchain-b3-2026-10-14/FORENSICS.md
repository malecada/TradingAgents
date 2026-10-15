# B3-CP4 forensics — why the screen is negative

Run 2026-10-15 on the development window only (2017-10 → 2024, walk-forward test
years 2019–2024). No sealed 2025–26 price, volume or target was read; the holdout
command refused on the empty committed selection and wrote no lock.

## Registered result

0 of 42 comparisons pass the gate (`SCREEN.md`). Whole-graph structure (F4), motifs on
the top-20,000 graph (F5) and all on-chain sets together add no out-of-sample
information to price/volume history and B2's activity features for next-day or
next-week direction, next-week return, volatility or volume, or 4-week return or
volatility. As in B2, the linear on-chain sets are significantly worse on volatility
and volume (for example T5, S7 vs S0: +0.931 MSE, interval +0.652 to +1.229).

Closest cases, both tree models adding F4 to activity: T6 4-week return S5 vs S1
(−0.00729, interval upper +0.00008, better in 4 of 6 years) and T3 weekly return S5 vs
S1 (−0.00130, upper +0.00011, 4 of 6).

## Checks

1. **The harness finds signal where it exists.** Price/volume history (S0, linear)
   against a training-mean constant on the same folds: T4 next-week log realised
   volatility R² 0.213, T7 4-week log realised volatility R² 0.089, T5 next-week log
   volume R² 0.955. Direction and return are not predictable from price history
   (T1 log-loss gain −0.0003, T2 −0.0004, T3 R² −0.021, T6 R² −0.052).
2. **The near misses are less-bad overfitting, not information.** Tree models on
   returns lose to the constant forecast with every feature set (post hoc,
   `research_artifacts/onchain-b3/explore/nearmiss_probe.txt`):

   | Target | Trees S0 | Trees S1 | Trees S5 |
   |---|---|---|---|
   | T3 weekly return, R² vs constant | −0.222 | −0.215 | −0.119 |
   | T6 4-week return, R² vs constant | −0.486 | −0.282 | −0.162 |

   Adding F4 columns moves the trees toward the constant rather than past it;
   S5 trees still lose
   12–16 % of MSE to a constant. Per F4 group, the largest S1 + group differences on T6
   (clustering −0.0052, PageRank −0.0029) are of the same kind and are post hoc.
3. **Feature counts against samples.** S0 7, S1 35, S5 95, S6 287, S7 307 columns
   against 378 weekly development rows (65 training rows in the 2019 fold, 326 in
   2024). Ridge chose alphas up to the 1e5 end of the grid in several folds.
4. **Partial correlations after F0 (post hoc).** Each of 60 transformed F4 columns
   against each weekly target, after OLS on the seven F0 columns over the 378
   development weeks; the null is the count of |r| > 2/√n under circular shifts of
   the target residual (500 shifts, which keep both autocorrelations):

   | Target | Count above 0.103 | Shift-null mean / 95 % | p | Largest |
   |---|---|---|---|---|
   | T2 | 4 / 60 | 2.5 / 9 | 0.22 | core3 share change +0.142 |
   | T3 | 7 / 60 | 2.7 / 10 | 0.08 | core3 share change +0.170 |
   | T4 | 2 / 60 | 2.5 / 7 | 0.58 | transitivity change +0.153 |
   | T5 | 5 / 60 | 2.9 / 9 | 0.17 | core3 share z +0.188 |
   | T6 | 8 / 60 | 3.1 / 9 | 0.10 | core3 share change +0.205 |
   | T7 | 6 / 60 | 3.3 / 9 | 0.22 | transitivity change +0.147 |

   No target exceeds its shift null at 5 %. The dense-core shares (2-core, 3-core) and
   the leaf share carry the largest return correlations with a consistent sign
   (denser week, higher following return), but T2, T3 and T6 share the same returns
   and overlap in time, so the three rows are not independent evidence.

Full output: `research_artifacts/onchain-b3/explore/forensics.txt`.

## Reading

Within this design, the structure of the whole weekly ETH transaction graph —
degree inequality, connectivity, reciprocity, dense cores, PageRank concentration,
clustering and address turnover — and motif features on a 4× larger top graph add no
out-of-sample information to price and volume history at 1-day, 1-week or 4-week
horizons over 2019–2024. Together with B2 (0 of 40) and the M2 paper-scale
replication (direction accuracy 0.490), this closes the weekly on-chain graph line
for ETH in this programme. The dense-core return correlation is the only consistent
pattern and stays below its null; it is recorded as an untested observation, not a
lead.

The sealed 2025-01-06 → 2026-10-05 window has not been read and remains available for
a future, separately registered hypothesis.
