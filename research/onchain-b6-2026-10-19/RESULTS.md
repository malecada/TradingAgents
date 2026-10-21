# B6 results — hourly graph structure, entity detail and minute-level events

Exploratory study with a pre-declared plan (`PLAN.md`); every comparison and event table
is in `TABLES.md` (generated) and `research_artifacts/onchain-b6/{forecast,events}/results.json`.
Tracks: A = 2017-10 → 2024-12 against the intraday price baseline (test years 2019–2024);
B = 2021-04 → 2026-10-12 against the intraday price baseline plus DVOL and hourly
near-expiry implied volatility (groups 2022–24 and 2025–26, the latter already opened in
B4 and B5). Samples: track A 49,161 hours (V6), track B 26,125 + 15,524.

## Answer

Hourly graph structure and entity detail add nothing to short-horizon volatility
forecasts. The only block that passes a pre-declared criterion is B4's flow-intensity
block against the option-market baseline for next-6-hour volatility. Very large
exchange deposits and withdrawals produce no price or volatility reaction within an hour
of their block, and the market does not move before them.

## Q1 — structure (X2 vs X1: structure on top of flows)

| Track, target | linear | trees |
|---|---|---|
| A, V6 | +0.0008 [-0.0017, +0.0031], 3/6 | -0.0004 [-0.0016, +0.0006], 1/6 |
| A, V24 | +0.0034 [+0.0007, +0.0061], 1/6 | -0.0051 [-0.0087, -0.0015], 2/6 |
| B, V6, 2022–24 | +0.0018 [-0.0003, +0.0040], 0/3 | +0.0041 [+0.0017, +0.0069], 1/3 |
| B, V24, 2022–24 | +0.0047 [+0.0011, +0.0086], 0/3 | -0.0003 [-0.0028, +0.0024], 1/3 |

No cell meets its criterion. The one interval below zero (track A, V24, trees, −0.005) is
better in 2 of 6 years and is carried by 2019 (−0.046), the first test year with 15 months
of training; every later year is zero or worse. In track B structure makes the forecasts
worse.

## Q2 — entity detail (X3 vs X1; X4 = structure + entity vs X1)

| Track, target | X3 linear | X3 trees | X4 trees |
|---|---|---|---|
| A, V6 | +0.7474 [+0.5054, +1.0052], 1/6 | -0.0017 [-0.0035, +0.0001], 3/6 | -0.0028 [-0.0049, -0.0008], 3/6 |
| A, V24 | +1.1861 [+0.7965, +1.6082], 2/6 | -0.0069 [-0.0137, +0.0001], 3/6 | -0.0065 [-0.0126, -0.0006], 2/6 |
| B, V6, 2022–24 | +0.0063 [+0.0029, +0.0097], 0/3 | +0.0096 [+0.0050, +0.0147], 1/3 | +0.0110 [+0.0058, +0.0172], 1/3 |
| B, V24, 2022–24 | +0.0024 [-0.0019, +0.0066], 0/3 | -0.0011 [-0.0058, +0.0041], 2/3 | +0.0000 [-0.0045, +0.0053], 2/3 |

- No cell meets its criterion. Track A trees come closest (X4, V6: upper −0.0008; V24:
  upper −0.0006) but win 3 of 6 and 2 of 6 years; the 2019 fold carries the mean
  (−0.014 and −0.062), and 2020–2022 are worse.
- The linear track A rows (+0.75, +1.19) are a first-fold artefact, not information
  (`research_artifacts/onchain-b6/forecast/diagnostics.txt`): in the 2019 fold the
  entity series were nearly dormant during training (DEX, MEV, bridge and issuance
  activity starts in 2019), so the ridge model extrapolated to predictions up to 19 on
  the log-volatility scale (fold error 4.98 against 0.36); every later fold is within
  +0.04 of X1. Trees are unaffected.
- In track B entity detail makes forecasts worse in 2022–24 (+0.006 to +0.011).

## Flows against the option-market baseline (X1 vs X0)

| Cell | Mean difference [95 % interval] | Baseline loss | Relative |
|---|---|---|---|
| V6, linear, 2022-24 | -0.0078 [-0.0105, -0.0051] | 0.286 | -2.7 % |
| V6, linear, 2025-26 | -0.0054 [-0.0088, -0.0018] | 0.271 | -2.0 % |
| V6, trees, 2022-24 | -0.0123 [-0.0156, -0.0087] | 0.301 | -4.1 % |
| V6, trees, 2025-26 | -0.0085 [-0.0114, -0.0057] | 0.270 | -3.1 % |

These four rows are the study's only passes under the pre-declared criteria (track B,
V6, both families; 2025–26 same sign). The V24 X1 vs X0 rows pass in 2025–26 only on the
sign and fail the 2022–24 interval, so they do not pass. In track A, flows against the
intraday price baseline alone are not better (+0.0028 [+0.0008, +0.0049], 2/6 linear;
+0.0029 [-0.0006, +0.0066], 3/6 trees), as in B4's forensics. The pass in track B does not
contradict B5: B5's option-market baseline used the implied volatility of the exact
target expiry at two decision times per day, whereas track B uses the nearest live expiry
per hour with up to three hours of forward fill, a coarser proxy that the flow features
partly complete. The 2–4 % gains here are of the size B4 reported.

## Q3 — minute-level events (ETH primary; BTC the same)

100,078 events over 2019–2026 (tier 1: 26,493 deposits and 21,913 withdrawals in 2019–24,
15,262 and 14,064 in 2025–26; tier 2 about a quarter of those). Against matched placebo
minutes, same year and hour of day, at least 60 minutes from any event:

| Response | Events | Placebo |
|---|---|---|
| Signed return 1, 5, 15, 30, 60 min after | 0.000 at every horizon, intervals within ±0.0005 | same |
| Return 15 min before the block | 0.000 | same |
| Log variance ratio, next 5 min vs previous hour | −0.36 (deposits), −0.37 (withdrawals) | −0.42, −0.39 |
| Same, next 60 min | −0.03 | +0.01 to +0.07 |

Both groups show the negative short-window ratio (the log of a 5-minute mean is biased
down against a 60-minute mean), so only the difference matters: the 5 minutes after an
event carry about 5 % more variance than placebo minutes, and the following hour slightly
less. No return response, no anticipation, no difference between deposits and
withdrawals or between tiers. Very large transfers coincide with active periods; they do
not move the market.

## Q4 — Tron

Not run. The keyless SQD portal throttled the stream to about 25 days of blocks per
hour; after two days it had reached 2021-05 (3.2k hourly rows, resumable from
`research_artifacts/onchain-b6/tron/bundle.npz`). The X5 vs X4 comparison was not made.

## Caveats

- Exchange labels are a 2026 snapshot (eth-labels' additions are dominated by three
  exchanges' deposit addresses); day-after activation removes only the "label before
  existence" look-ahead.
- Count-based structure features depend on label coverage, which is thin before 2019.
- The first test year of each track trains on 15 months (track A) or 9 months (track B)
  and uses the fallback ridge penalty; it dominates the few negative means above.
- Both sealed windows were spent before B6; nothing here is confirmatory.

## Reading

At hourly resolution, the whole-graph structure of ETH transfers and the identity of
counterparties (stablecoin split, DEX, bridge, MEV, fund flows, issuance) carry no
volatility information beyond the intensity of exchange flows that B4 already measured,
and at minute resolution very large transfers carry no price information at all. With
M2, B2, B3, B4 and B5 this closes the on-chain graph line of the programme: the chain's
usable short-horizon content is exchange-flow intensity, it predicts volatility rather
than direction, and it is largely priced by the option market.
