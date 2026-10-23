# B8 results — hourly per-token on-chain panel for perp-listed ERC-20 tokens

Exploratory study with a pre-declared plan (`PLAN.md`, amendment 1 before the pass); every
comparison is in `TABLES.md` (generated) and `research_artifacts/onchain-b8/forecast/results.json`.
Universe 146 tokens (mainnet ERC-20 contract, ≥ 2 years of hourly perp bars); pass 2020-06-01 →
2026-07-29 (2,249 days, one unavailable); panel 5,166,317 token-hours, 4.65M with complete
features; test years 2022–2026 with 596k–1,146k rows, 8,760 hours and 79–144 tokens each
(2026: 5,000 hours, 118 tokens). 18 pre-declared rows.

## Answer

The token's own hourly exchange-flow and transfer-activity features do not improve forecasts
of its next-6-hour or next-24-hour volatility beyond its price and volume history: linear
models get worse, trees change by 0.0–0.1 % of squared error. They do improve the forecast of
which tokens will be more volatile than the panel over the next 24 hours (XV24), in both
families and 3–4 of 5 years, by 0.5 % (ridge) to 1.1 % (trees) of squared error. The effect is
broad but thin: two thirds of tokens improve, three quarters of the gain comes from 15 tokens,
2024 is flat and 2026 reverses. It is explanatory, of the same kind as ETH's flow-intensity
result, and not a trading signal.

## Q1 — pooled per-token volatility (V6, V24)

| Comparison | V6 ridge / trees | V24 ridge / trees |
|---|---|---|
| P1 vs P0 (token-hour series added) | +0.0013 [+0.0005, +0.0023], 2/5 / +0.0002 [−0.0001, +0.0005], 3/5 | +0.0053 [+0.0031, +0.0079], 2/5 / +0.0004 [+0.0000, +0.0009], 3/5 |
| P2 vs P1 (cross-sectional z-scores added) | −0.0001 [−0.0011, +0.0009], 3/5 / **−0.0002 [−0.0005, −0.0000], 5/5** | −0.0004 [−0.0013, +0.0005], 4/5 / −0.0003 [−0.0006, +0.0001], 4/5 |
| P2 vs P0 | +0.0012 [−0.0003, +0.0029], 3/5 / −0.0001 [−0.0004, +0.0003], 3/5 | +0.0049 [+0.0025, +0.0076], 2/5 / +0.0002 [−0.0003, +0.0007], 3/5 |

Against squared errors of 0.24 (V6 trees) and 0.14 (V24 trees), the on-chain block changes
nothing: the only pass (V6 trees, P2 vs P1) is 0.1 % of error, carried evenly across years
and tokens (67 % of tokens better, −0.0002 median) and too small to read. Ridge is worse
with the block in 2022–23 (alpha 10,000–100,000 chosen), the same first-fold extrapolation
seen in B6 and B7. Price and volume history alone explain 43 % (V6) and 51 % (V24) of the
variance against the training mean.

## Q2 — cross-section (XV24 = V24 minus the hour's panel mean)

| Comparison | ridge | trees | per year, trees (2022 … 2026) |
|---|---|---|---|
| P1 vs P0 | **−0.00036 [−0.00048, −0.00024], 3/5** | **−0.00071 [−0.00102, −0.00044], 3/5** | −0.0020, −0.0010, +0.0001, −0.0007, +0.0007 |
| P2 vs P1 | +0.0000 [−0.0001, +0.0001], 4/5 | **−0.00010 [−0.00019, −0.00001], 4/5** | +0.0002, −0.0000, −0.0003, −0.0003, −0.0001 |
| P2 vs P0 | **−0.00036 [−0.00047, −0.00026], 4/5** | **−0.00081 [−0.00111, −0.00054], 4/5** | −0.0019, −0.0010, −0.0002, −0.0010, +0.0006 |

The block passes the criterion in both families (P1 vs P0 and P2 vs P0): 0.5 % of the ridge
error (0.0788) and 1.1 % of the tree error (0.0741), against a baseline that already holds
the token's price history and the cross-sectional z-scores of its 24-hour volatility and
volume. The cross-sectional z-scores of the on-chain series add a further 0.1 % for trees.
Per year the gain is largest in 2022 (79 tokens) and 2023, flat in 2024, back in 2025 and
reversed in the 2026 half-year.

Post hoc (labelled): per-token mean differences for trees P2 vs P0 are negative for 96 of
146 tokens (median −0.0009), more often and more strongly in the liquid tercile (median
−0.0013, 69 % better) than in the illiquid one (−0.0005, 56 %); 78 % of the row-weighted
total gain comes from the 15 best tokens (QNT, FTT, UNFI, SFP, MDT …) and 49 tokens are
worse (RIF, CAKE, 1000BONK, BNB, ARB the most). `research_artifacts/onchain-b8/forecast/per_token.csv`.

## Q3 — reading

The per-token result has the shape of the ETH result: activity intensity on the chain tells
a little about relative volatility, nothing about a token's own volatility level once its
price and volume history is known, and nothing about direction (not tested here by design).
The effect is an order of magnitude smaller than B4's ETH flow effect (6.6 % in the sealed
window) and fades in the latest year.

## Chance

18 rows, 6 passes (about 1 expected). Five sit in one coherent place (XV24, both families,
P1 and P2 against P0, plus the z-score increment) and are read as a finding; the sixth (V6
trees P2 vs P1, 0.1 %) is not.

## Disclosures

- 2020-11-01 is missing from the AWS tables (as in B4/B6); its 24 missing hours remove 47
  (24-hour sums) and 191 (168-hour sums) hours of every token's features.
- Token-hours without a bar have missing USD series; the sample keeps rows from 30 days after
  each token's first bar. The universe is a 2026 snapshot; wrapped or bridged tokens with little
  mainnet activity (BONK, SRM, ICP, WAVES, RDNT) carry near-constant on-chain series; two
  wrong-contract members were excluded before the pass (amendment 1).
- Early-stopped trees hit the 600-iteration cap in most 2024–2026 folds for all sets alike;
  ridge chose alpha 100,000 in the largest folds.
- V6 / V24 are missing where the future window has no price change (amendment 1).
- The forecast stage was OOM-killed four times before the memory fixes (`STATE.md`); the V6
  unit of the third launch is reused, the method is unchanged.

## Closure

B8 is closed: per-token exchange-flow and activity features add nothing to a token's own
volatility forecast and about 1 % of squared error to the forecast of its volatility relative
to the panel, fading by 2026. Together with B4–B7 this fixes the programme's reading of hourly
on-chain data: flow and activity intensity carries a small amount of volatility information,
priced where an option market exists, and no directional information.
