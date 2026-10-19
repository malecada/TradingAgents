# B6 charter — hourly graph structure, entity detail and minute-level events

Registered 2026-10-19 before any B6 pass output is read. Spec:
`docs/superpowers/specs/2026-10-19-onchain-b6-structure-entities-design.md`.

## Questions

Q1 Does hourly transfer-graph structure add volatility information beyond price history,
option-market information and B4's flow intensity? Q2 Do token-split flows, DEX / bridge /
MEV / fund flows and stablecoin issuance add beyond B4's flows? Q3 Do very large exchange
deposits or withdrawals move volatility or price within 5–60 minutes of their block, and
does the market move first? Q4 (side) Does Tron USDT exchange flow add beyond Ethereum flows?

## Framing

Exploratory with a pre-declared plan (`PLAN.md`); the ETH and BTC 2025–26 windows were
opened in B4 and B5. Targets are realised volatility only.

## Disclosures

- Exchange and class labels are a 2026 snapshot; each address counts as labelled only from
  the day after its first observed transfer, which removes the "label before existence"
  look-ahead but not the identity look-ahead.
- Exchange entities are labels only (no deposit inference); eth-labels' exchange set is
  dominated by three exchanges' deposit addresses (Bitget, Deribit, Bilaxy).
- USDT issuance is proxied by Tether Treasury transfers; USDC and DAI by mint/burn events.
- Binance 1-minute closes stand in for the market; the block timestamp has 12-second
  resolution; responses start at the next full minute.
