# Dated carry decision — September 10, 2026

**The measured Binance BTC/ETH dated carry setups do not justify a strategy evaluation at either 1,000 or 10,000 USDT under the registered fee assumptions.** All four asset/capital combinations fail the necessary economic screen. The base-fee reference cases already lose money before adverse settlement mismatch or a cash opportunity-cost hurdle is introduced. Increasing the budget does not turn the observed spread into an adequate net return.

This is a decision about the fixed current measurement, not permanent rejection of all dated carry opportunities. Three closely spaced observations of one maturity cannot establish historical profitability, opportunity frequency or a stable expected return. The 432 scenarios are arithmetic sensitivities of those observations, not 432 independent strategy trials.

## What was measured

The approved order begins with economic feasibility and a complete hedge accounting example. Both stages are complete. Registration commit `57149c6bfeefe3a1a76e5103d21dbd598d10080c` preceded implementation and results. Reviewed execution source `62bcf8bf4bdb2c57e8b78d4443427863e287d692` was committed and pushed before the single capture. Sixteen public requests ran from September 10, 2026 16:11:14 through 16:12:16 UTC, retaining three scheduled quote batches without replacement.

The calendar selection rule chose BTCUSDT_260925 and ETHUSDT_260925, both expiring September 25, 2026 at 08:00 UTC, approximately 14.66 days after observation. Each asset is an alternative use of the entire capital budget. The calculations assume USDT already on Binance; the user's approximate dollar amounts are not verified fiat conversion proceeds.

The table reports ranges across all three observations for the fixed reference case: full futures-notional reserve, base assumed fees, terminal index unchanged and spot sold at that index. The amounts are modeled cash profit through expiry, not daily profit, realized fills or an annual return.

| Asset | Capital already on venue | Modeled net cash through expiry |
|---|---:|---:|
| BTC | 1,000 USDT | −0.58 to −0.55 USDT |
| ETH | 1,000 USDT | −0.90 to −0.80 USDT |
| BTC | 10,000 USDT | −6.49 to −6.05 USDT |
| ETH | 10,000 USDT | −9.90 to −8.26 USDT |

The stronger preregistered screen retains all nine required cells per asset/capital: three snapshots × terminal index half/unchanged/double, using full reserve, doubled fees and spot exit 10 basis points below the settlement index. None of the four combinations passes. The [generated report](RESULTS.md) and [screen summary](screen-summary.json) retain the exact dimensions. Illustrative 3% and 5% cash benchmarks remain separate; removing them does not rescue the negative base-case cash profits.

All 432 saved net cash outcomes are negative across the entire registered grid. Every one of the 48 entry cases is budget-limited, not exhausted-book-depth limited. These are descriptive counts of the fixed outcomes; no additional parameter search or result calculation is introduced.

In the same reference cases, the future-versus-spot entry premium is approximately 10–18 basis points of matched spot notional, while the modeled four-fee drag is approximately 30 basis points. The larger budget buys a deeper, slightly worse future bid price and mostly scales the negative per-unit economics. There is no fixed setup charge being amortized away. The [saved-only descriptive breakdown](verification/supplemental-descriptive-check.md) retains the exact ranges and reconciliation, including the small residual spot value.

## Why the hedge calculation is more reliable

Spot purchase principal, received-base commission, lot rounding, futures entry commission and collateral all fit within the same budget. Short futures notional is not received as spendable cash. The short's settlement PnL offsets the matched spot price move in explicit base units; the small residual spot quantity remains exposed and is valued. Reserve principal is released in terminal cash reconciliation rather than deducted as an expense. Every fee and settlement leg is visible in the saved ledger.

The [synthetic accounting example](verification/accounting-example.md) independently reconciles down/flat/up terminal prices using invented inputs. Its positive illustrative profits are not observed returns and must not be cited as evidence for the measured opportunity. A separate exact-fraction checker reconstructs all 48 entry quantities and 432 terminal cashflows directly from retained books without importing the calculator or making market requests. All checks passed, following 127 pre-result tests.

## Continuation decision

Step 3, a separately registered strategy evaluation, is not economically justified by these observations. Step 4, paper execution, has therefore not begun. No account access, orders, paid data, provider contact or production changes are needed to complete this conclusion.

Reopening dated carry would require a new, explicit research question and registration before new economic outcomes. It would also require evidence for the exact account commissions and fee assets, applicable settlement fee treatment, product access and contract/entity terms, and margin requirements and liquidity through adverse price paths. The user's minimum acceptable net return and tolerated loss would need to be made concrete before any adoption gate. These are prerequisites for a future evaluation, not a request to provide credentials or resolve every issue for the currently rejected setup.

The one-third-reserve cases only measure a capital-efficiency sensitivity. A hedged combined terminal value does not prevent the isolated futures leg from running short of collateral; terminal reserve sufficiency is also weaker than survival throughout the holding period. Public depth does not demonstrate simultaneous fills, and the spot API's missing event timestamp leaves spot freshness unverified. Actual fee rates, exchange rounding, legal settlement fee basis, fiat/transfer costs and stablecoin/counterparty risk remain qualifications. The assumed absolute-notional expiry charge is not an authenticated Binance fee rule.

All 72 one-third-reserve scenarios with a doubled terminal index have a negative terminal futures reserve. All 216 full-reserve scenarios have a positive terminal reserve within this limited grid; no maintenance-margin or intrahorizon liquidation model has been verified. Lower collateral therefore provides neither positive modeled cash profits nor established margin survival here.

Bitrue remains a documentation-only alternative with unverified eligible dated-product availability. Its perpetual documentation does not establish a comparable dated contract. The [official-source review](SOURCES.md) retains both successful and unavailable retrievals. The earlier spot/perpetual carry verdict, spent holdouts and 22 deferred settlement-blocked configurations remain unchanged.

**Zero validated strategies remain.** The useful outcome is a checked cash accounting model and a retained negative feasibility measurement, with no basis for deploying this setup at the observed quotes.
