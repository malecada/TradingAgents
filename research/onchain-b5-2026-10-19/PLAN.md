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

## Amendments before any B5 model, backtest or decision table (2026-10-19, fresh review)

1. **Positive reading metric.** Q2 is read as positive only if, for the same family and
   θ, the M2 rule's total P&L after costs (USD per coin, 2022–24) exceeds the M1 rule's,
   always-buy's and always-sell's. Every θ is reported.
2. **Implied spread.** Half-spread = max(0, (IV_ask − IV_bid)/2) when both sides trade;
   otherwise the median of the previous 30 rows' half-spreads; execution IVs are
   IV_mid ± half-spread. Raw ask/bid medians come from different trades and were
   negative for about a third of probed decisions. The share of negative raw spreads is
   reported.
3. **Zero-IV trades.** Trades with iv ≤ 0 (executed at or below intrinsic) are ignored in
   decisions and in the hourly IV series.
4. **Settlement.** S_T = mean of the thirty Binance 1-minute closes from 07:30 to 08:00
   UTC on the expiry day, following Deribit's 30-minute delivery TWAP; the 08:00 point
   price would favour long straddles by about 1.4 % of the expected payoff at 6 h.
5. **Signal scale.** z = ŷ − b(τ) − log IV_mid, with b(n) = ½(ψ(n/2) − ln(n/2)) the
   small-sample bias of log realised volatility from n Gaussian hourly returns (−0.088
   for 6 h, −0.021 for 24 h). The mean z per rule is reported.
6. **Event-study alignment.** The pre-event window ends the hour before the event; the
   implied-volatility change is measured from the hour before the event.
