# Synthetic dated-carry accounting example

This is an invented-price engineering example, not a quote, financial trial or profitability observation. No market data, account, strategy or measurement ledger was accessed. The arbitrary one-contract order cap makes quantities transparent; it is not a Binance filter assertion. All rates are registered unrounded scenario assumptions, not verified account commissions.

The budget is 1,000 USDT, with spot asks 100 and futures bids 110. Buying gross 1.002 base units costs 100.2 USDT. The 0.1% BASE commission removes 0.001002 units, leaving 1.000998. Shorting one contract of multiplier one hedges 1 base unit; the extra 0.000998 spot unit is retained and valued. Futures entry notional 110 produces **no cash proceeds**; the 0.05% entry fee is 0.055. Full futures reserve is 110. The remaining cash is 789.745. Principal, fee and reserve total 210.255; none is silently reused as additional capital.

At expiry the scenario sets the spot disposal price equal to settlement index X. The literal independent terminal-profit check is:

```text
1.000998*X + 110 - X - 100.2 - 0.055
  - X*0.0005 - 1.000998*X*0.001
```

The independent terminal wealth check is:

```text
789.745 + 1.000998*X*(1-0.001) + 110 + (110-X) - X*0.0005
```

The base commission is embedded in the spot units and is not deducted again as cash. The reserve is released, not charged as an expense. Net return uses the entire 1,000 budget, not the smaller futures reserve or entry commitment. Holding time is exactly 90 days. The 0%, 3%, 5% simple cash benchmarks use the same budget and period, and are retained separately from paid financing and credited interest (both zero in the stated scenario).

| Terminal index | Spot sale gross | Futures settlement PnL | Expiry fee | Spot exit fee | Net cash profit | Terminal NAV | Terminal futures reserve |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 50.0499 | 60 | 0.025 | 0.0500499 | 9.7198501 | 1009.7198501 | 169.975 |
| 100 | 100.0998 | 10 | 0.05 | 0.1000998 | 9.6947002 | 1009.6947002 | 119.95 |
| 200 | 200.1996 | -90 | 0.1 | 0.2001996 | 9.6444004 | 1009.6444004 | 19.9 |

All three rows agree exactly with the literal independent profit and wealth formulas. Positive terminal reserve is not evidence of pathwise margin survival or maintenance compliance. The scenario has no adverse exit mismatch; the tests separately cover valuing the entire spot quantity under such a mismatch, insufficient one-third reserve, and doubled fees.

An explicitly invalid diagnostic replaces only gross fixed-quantity price PnL with logarithmic returns while retaining entry BASE-fee loss and the same cash fees. It gives different hedge profits; its values are preserved in the JSON under `invalid_log_cash_profit_diagnostic`, never used for sizing or economics. The correct cash formula contains no log returns.

The [JSON example](accounting-example.json) retains every component, residual quantity, benchmark, the independent arithmetic and calculator source hash. The [test log](math-tests.txt) records 40 passing synthetic tests. Initial missing-module RED evidence is in `math-red.txt`; arithmetic/format regressions and the ambient-rounding regression are in `math-arithmetic-red.txt` and `math-context-red.txt`.
