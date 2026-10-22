# B8 charter — hourly per-token on-chain panel for perp-listed ERC-20 tokens

Registered 2026-10-22 before any day of the pass is read. Spec:
`docs/superpowers/specs/2026-10-22-onchain-b8-token-panel-design.md`.

## Questions

Q1 Across tokens, do hourly exchange-flow and transfer-activity features improve next-6 /
24-hour volatility forecasts beyond the token's own price and volume history? Q2 Do they
forecast which tokens will be more volatile than the others over the next 24 hours? Q3
(reading) Is a per-token effect, if any, of the same kind as ETH's activity proxy?

## Framing

Exploratory with a pre-declared plan (`PLAN.md`); no sealed window; volatility targets
only, no return or direction claim.

## Disclosures

- Universe and token map are 2026 snapshots (148 tokens with ≥ 2 years of hourly perp bars
  and a mainnet contract; delisted tokens kept where the kline store kept them).
- Exchange labels and activation are B6's (identity look-ahead disclosed there).
- USD values use the perp close of the block's hour; token-hours without a bar have missing
  USD series and `big_cnt` 0.
- §82 (smw_xs) tested DEX-swap smart-money features for next-day returns on this kind of
  universe and closed; B8 uses exchange transfers and volatility targets only.
