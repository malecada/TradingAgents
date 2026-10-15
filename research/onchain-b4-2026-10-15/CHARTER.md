# B4 charter — ETH exchange flows, daily and hourly

Registered 2026-10-15 before any B4 data read. Spec:
`docs/superpowers/specs/2026-10-15-onchain-b4-exchange-flows-design.md`.

## Question

Do exchange flows — ETH and stablecoins moving into and out of exchange entities —
measured daily by Coin Metrics or hourly from the chain add out-of-sample information to
price/volume history for ETH direction, return and volatility (next day to next week;
next 1–24 hours)?

## Design

- Stage 1 (daily): Coin Metrics exchange inflow, outflow, net flow, exchange supply;
  MVRV, active addresses, fees, stablecoin supply and ratio; one-day lag; 28-day
  z-scores and one-day changes. Sets D0, DF, DA; targets T1, R7, V7.
- Stage 2 (hourly): own pass over transactions, token transfers (USDT, USDC, DAI) and
  blocks, 2017-01-01 → 2026-10-11; exchange entities = 4,961 labels plus causally
  inferred deposit addresses; 15 hourly series, 32 features. Sets H0, HE, HS, HA;
  targets R1, R6, R24, V6, V24.
- 42 comparisons, one screen, ≤ 3 selected, one holdout (`gates.json`).

## Disclosures

- Exchange labels are a 2026 snapshot applied to all years (look-ahead in coverage).
- Coin Metrics exchange history reflects its current labels (revised history).
- ETH moved inside contracts (`traces`) is not read; contract-based deposit forwarders
  are detected only when they move stablecoins.
- Four earlier studies used ETH 2017–2024 (M2, B2, B3, now B4); the sealed window
  2025-01-01 → 2026-10-12 has never been read. If B4 opens it, it is spent for later
  ETH studies.
- An arXiv study (2411.06327) motivated the design; its claims are not assumed.
