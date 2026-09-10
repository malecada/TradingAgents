# Dated BTC/ETH carry feasibility — September 10, 2026

The current public-book measurement is complete. It is a conditional quote-to-expiry calculation, not a strategy backtest or a promise that both legs can be filled. The user specified approximately 1,000 initially and 10,000 potentially, with Binance and possibly Bitrue. Calculations use 1,000/10,000 **USDT already available on venue**; fiat conversion and stablecoin exposure are not priced.

Execution source: `62bcf8bf4bdb2c57e8b78d4443427863e287d692`. The fixed grid retains **432 scenario rows**, of which **432** are calculable. All 48 entry-size cases, three scheduled snapshots, raw bodies and failures are retained. The original 820-row financial ledger is unchanged. **Zero strategies are validated.**

## Contract inventory

Binance selection is the earliest eligible conventional linear USDT expiry between seven and 180 days, separately for BTC and ETH. The rule never chooses the highest basis. Other eligible maturities remain in the inventory but are not alternative financial trials.

| Asset | Selected future | Spot pair | Expiry (UTC milliseconds) |
|---|---|---|---:|
| BTC | BTCUSDT_260925 | BTCUSDT | 1790323200000 |
| ETH | ETHUSDT_260925 | ETHUSDT | 1790323200000 |

Bitrue dated-product availability remains unverified. Its documented perpetual products and a URL named `delivery` do not establish an eligible expiring contract. [Official-source review](SOURCES.md).

## Conditional entry and terminal economics

The following table retains all three observations. Its displayed scenario uses the full futures-notional reserve, the registered base fee assumptions, a terminal settlement index equal to the initial spot ask, and spot sale at that same index. This is one fixed reference scenario; fees and sale/index alignment are not verified future outcomes. Annualization is arithmetic on the full capital budget and does not imply repeated opportunities.

| Snapshot | Asset | Capital (USDT) | Modeled net cash (USDT) | Return on full capital | Simple annualized return |
|---:|---|---:|---:|---:|---:|
| 0 | BTC | 1000 | -0.5780 | -0.058% | -1.439% |
| 0 | BTC | 10000 | -6.4067 | -0.064% | -1.595% |
| 0 | ETH | 1000 | -0.8009 | -0.080% | -1.994% |
| 0 | ETH | 10000 | -9.1849 | -0.092% | -2.287% |
| 1 | BTC | 1000 | -0.5468 | -0.055% | -1.362% |
| 1 | BTC | 10000 | -6.0496 | -0.060% | -1.506% |
| 1 | ETH | 1000 | -0.9028 | -0.090% | -2.248% |
| 1 | ETH | 10000 | -9.8956 | -0.099% | -2.464% |
| 2 | BTC | 1000 | -0.5723 | -0.057% | -1.425% |
| 2 | BTC | 10000 | -6.4936 | -0.065% | -1.617% |
| 2 | ETH | 1000 | -0.8165 | -0.082% | -2.033% |
| 2 | ETH | 10000 | -8.2563 | -0.083% | -2.056% |

## Necessary economic screen

The preregistered screen requires positive net cash across all three snapshots and all three terminal-index levels (half, unchanged, double), using full reserve, doubled fees and spot liquidation 10bp below the settlement index. Passing this screen only supports considering further design. It does not admit a strategy, settle the cash-benchmark question, or establish margin survival.

| Asset | Capital (USDT) | Complete required cells | Positive in every required cell | Executable admission |
|---|---:|---:|---|---|
| BTC | 1000 | 9/9 | No | No |
| BTC | 10000 | 9/9 | No | No |
| ETH | 1000 | 9/9 | No | No |
| ETH | 10000 | 9/9 | No | No |

## Complete sensitivities and limitations

The [measurement ledger](../../data/carry-feasibility/2026-09-10/measurement_ledger.jsonl) contains every terminal-price, 0/10/50bp adverse-exit, base/double-fee and full/one-third-reserve case. Each row reports net cash separately from illustrative 0%, 3% and 5% annual cash benchmarks on the same full capital and exact holding period. These benchmark rates are sensitivity assumptions, not observed available deposit yields or a retrospectively chosen hurdle.

Future bid proceeds are not credited at entry. Spot principal, entry fees and total futures reserve must fit inside the stated budget. Spot base commission is deducted before measuring the hedge, with lot rounding and the small residual explicitly retained. Capital efficiency from a one-third reserve is not a risk reduction. A positive terminal payoff can coexist with an earlier collateral shortfall.

Public depth is neither simultaneous execution nor demonstrated fills. Spot responses lacking an event timestamp cannot prove freshness. Future timestamps, request spans and clock uncertainty are checked; failures remain unavailable. Exact current account fees, fee rounding, contract/entity applicability, settlement fee basis, maintenance margin and transfer constraints are still unverified. The modeled absolute-notional expiry fee is not substituted for the ambiguous official legal expression. [Sources and applicability gaps](SOURCES.md).

## Next stage admission

A separately registered strategy evaluation can start only after actual product access, both-leg commissions and fee assets, settlement treatment, margin/liquidity behavior and the user's return/risk hurdle are resolved. Reuse the synthetic quantity/cash tests when implementing that contract. No old holdout can be made fresh, no historical delisting record is being recovered, and no paper account or order is started by this report.

The [pure cashflow implementation](../../scripts/carry_feasibility_math_2026_09_10.py) is deliberately separate from the derivative-only event book, which does not debit spot principal or manage cash wallets. Its hand-derived down/flat/up examples verify the arithmetic without claiming an exchange liquidation model.

## Retained unavailable outcomes

No scenario row is unavailable; all executable-admission qualifications above still apply.
