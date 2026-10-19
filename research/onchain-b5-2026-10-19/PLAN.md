# B5 pre-declared analysis plan (committed before any B5 model or backtest)

All items are run once and reported in `RESULTS.md`, including negatives. Groups:
2022–24 (test years 2022, 2023, 2024) and 2025–26 (already opened; shown alongside).

## Q1 forecast comparison
For each asset (ETH, BTC) × schedule (S6, S24) × family (linear, trees):
M1 vs M0, M2 vs M1, M2 vs IV — mean squared-error difference of log realised
volatility to expiry, 95 % block-bootstrap interval, years better, per group.

## Q2 straddle backtest
For each asset × schedule × family × variant (M1, M2) × θ ∈ {0.05, 0.10, 0.20}, and the
sign-flipped rule: per-group mean P&L per trade (USD per coin) with interval, total P&L,
trades, hit rate, Sharpe on decision days, maximum drawdown, P&L per premium, long and
short sides separately. Benchmarks: always buy, always sell.
Read as positive only if the M2 rule beats the M1 rule and both benchmarks after costs
in 2022–24.

## Q3 BTC
Q1 and Q2 for BTC with Ethereum-chain flows.

## Q4 event study
ETH and BTC; inflow events, outflow events, placebo activity events; responses k = 1 … 12
h: realised-volatility surprise against the out-of-fold M0 forecast, pre-event surprise,
change in near-expiry implied volatility, signed return; means with intervals; groups
2019–24 and 2025–26 (implied volatility from 2021-04).

## Q5 Tron
`TRON_PROBE.md`: free full-history source for USDT TRC-20 transfers and Tron exchange
labels — go or no-go with a cost estimate.
