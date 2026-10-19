# B5 charter — exchange flows against the option market

Registered 2026-10-19 before any B5 data read. Spec:
`docs/superpowers/specs/2026-10-19-onchain-b5-vol-trading-design.md`.

## Question

Do B4's hourly exchange-flow features (stablecoin and ETH flows to and from exchange
entities) add to price and option-market information when forecasting realised
volatility to a Deribit daily expiry, and does a cost-aware at-the-money straddle rule
built on the forecast make money, for ETH and BTC, 2022–2026?

## Framing

Exploratory with a pre-declared analysis plan (`PLAN.md`). The ETH 2025–26 window was
opened in B4 and the closed rviv-p0 study used 2025–26 implied and realised volatility,
so no B5 result is confirmatory. Confirmation is a later forward study.

## Disclosures

- Option prices come from executed trades (taker side gives ask or bid), not quotes.
- Deribit's current fee schedule is applied to all years.
- Settlement uses the Binance close at the expiry hour instead of Deribit's 30-minute
  delivery index.
- BTC and ETH volatility co-move; the BTC check is a generalisation check.
