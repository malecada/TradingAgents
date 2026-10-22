# B7 charter — feature and target engineering on the hourly on-chain tables

Registered 2026-10-22 before any B7 table is built. Spec:
`docs/superpowers/specs/2026-10-22-onchain-b7-feature-target-engineering-design.md`.

## Questions

Q1 Do multi-scale, deseasonalised features of the same hourly series (plus event-time and
interaction terms) carry more volatility information than B4's two transforms, and does an
early-stopped, larger tree model beat B4's fixed trees? Q2 Do on-chain features forecast
tail moves (|return| > 3σ̂√k) and the size of the largest 5-minute move, beyond what price
history, intraday range and the option market give?

## Framing

Exploratory with a pre-declared plan (`PLAN.md`). The ETH 2025–26 window was opened in
B4–B6; nothing here is a sealed test. Targets are volatility-type only (levels, tails,
largest move); no direction or return targets.

## Disclosures

- Inputs are B4's and B6's hourly tables and B6's large-transfer records, so the label
  disclosures of B4 and B6 (2026 label snapshot, day-after activation, identity look-ahead)
  carry over.
- Binance 1-minute closes stand in for the market; the 4,111 missing minutes make the
  affected hours' range features and M targets missing.
- Minute closes start 2019-01-01, so track A′ starts 2019-04-01 (shorter than B6's track A).
- The 2025–26 group of track B is read with a sign-only criterion and labelled as such.
- Track B's option-market columns are B6's (`features_B.parquet`), not recomputed.
