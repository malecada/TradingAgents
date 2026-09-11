# Neutral alternatives: source comparison, September 11, 2026

Recommendation: a fixed public spot-triangle necessary-feasibility capture has
the highest immediate information value. WBETH reward capture remains a distinct
economic hypothesis, but historical conversion ratios and redemption conditions
are not admitted public inputs. Neither mechanism has been financially tested
by this review; no familywide rejection follows from its source gaps.

## Exact source denominator

Eight distinct official document URLs were requested: six supplied substantive
documentation, one returned questions with untranslated answer placeholders,
and one returned an internal retrieval error. No search, quote/API measurement,
authenticated request, archive body, purchase or provider contact occurred.
Subsequent open/find operations extracted already opened references; eight is
the distinct-source denominator, not a claim about web-tool internal traffic.
All access dates are September 11, 2026. Exact retrieval clocks and document
publication/update times were not exposed; crawl date is not publication time.
Saved context was read from `../SOURCES.md` and `../HISTORY.md`.

| ID | Requested official URL | Outcome and final route |
|---|---|---|
| T1 | https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints | Readable; redirected to https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market |
| T2 | https://developers.binance.com/docs/binance-spot-api-docs/filters | Readable; redirected to https://developers.binance.com/en/docs/products/spot/filters |
| T3 | https://developers.binance.com/docs/binance-spot-api-docs/rest-api/trading-endpoints | Readable; redirected to https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/trade |
| T4 | https://www.binance.com/en/fee/trading | Readable regular-user and BNB-discount columns |
| W1 | https://developers.binance.com/en/docs/catalog/investment-and-services-staking/api/rest-api/eth-staking | Readable signed rate-history, staking, reward and redemption interfaces |
| W2 | https://www.binance.com/en-GB/earn-faq/light/eth-staking/faq | Questions readable; answers are `FAQ...Content...` placeholders; substantive current rules unavailable from this extraction |
| W3 | https://www.binance.com/en/wbeth | Internal retrieval error; no substantive evidence; no retry |
| T5 | https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/general | Readable public exchange-information and server-time documentation |

## Same-venue spot conversion

Public `https://api.binance.com/api/v3/ticker/bookTicker` accepts a symbols array
and returns bid/ask prices and quantities. Public `/api/v3/depth` supplies
price/quantity levels and `lastUpdateId`; limit 1–100 has request weight five.
The displayed response schema does not supply a common matching-engine clock
across symbols. One batch response is not proof of simultaneous execution.
[T1](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market)

`/api/v3/exchangeInfo` documents current symbol/rule information and accepts a
symbols array. Actual BTCUSDT, ETHUSDT and ETHBTC status, base/quote identity,
permissions, order types and filters need admission; documentation examples do
not establish current tradability or the user's entitlement.
[T5](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/general)
Per-leg checks must include actual price tick, LOT_SIZE/MARKET_LOT_SIZE and
MIN_NOTIONAL/NOTIONAL rules, including market-order applicability. Unknown rules
remain unknown; rounding creates inventory dust rather than free proceeds.
[T2](https://developers.binance.com/en/docs/products/spot/filters)

The published regular-user spot maker/taker rates are 0.100%/0.100%; the BNB
discount column is 0.07500%/0.07500%. A baseline can declare 0.100% taker per
leg without claiming that it is the exact account/promotion-specific commission.
Do not presume BNB holdings, rebates or zero-fee pairs.
[T4](https://www.binance.com/en/fee/trading)
The order interface is authenticated TRADE. IOC/FOK are available order flags;
they do not establish all-or-none settlement across three different markets.
The inspected order-list interfaces do not document an atomic three-currency
cycle. Partial/failed later legs can leave BTC or ETH inventory even when the
initial intention is neutral. This is an execution-risk inference, not an
observed failure rate. No order/test-order endpoint is needed for source capture.
[T3](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/trade)

### Proposed finite experiment, not a registration

One fixed six-request capture could obtain: exchangeInfo for the three exact
symbols; server time; one three-symbol bookTicker; and depth limit 20 for each
symbol, in a precommitted order. No refresh, conditional retries or wider symbol
search. Freeze 20 seconds/5 MiB per request, at most 150 seconds/256 MiB overall,
same-host denial suppression and six retained receipts before execution. The
depth limit is an observation bound; insufficient captured liquidity is
unavailable at that size, not zero impact or proof of no deeper liquidity.

Preserve both cycles, independently at starting balances 1,000 and 10,000 USDT:

1. USDT buys BTC at BTCUSDT asks; BTC buys ETH at ETHBTC asks; ETH sells at
   ETHUSDT bids, returning USDT.
2. USDT buys ETH at ETHUSDT asks; ETH sells at ETHBTC bids; BTC sells at BTCUSDT
   bids, returning USDT.

Both directions and both capitals remain four base cells. Each reports gross
and the frozen 0.100%-per-leg cost scenario, eight correlated result cells total,
never eight independent hypotheses. A simple received-asset commission model
must be explicitly conditional and cannot silently stand in for actual fee
asset rules. Use quantities, cash balances, executable-side depth, floor-to-step
rounding and retained residual balances. Dust is disclosed separately and cannot
rescue terminal USDT underperformance through optimistic marking.

Ignoring depth, fees and rounding, the necessary displayed gross factors are
`bid_ETHUSDT / (ask_BTCUSDT * ask_ETHBTC)` and
`bid_ETHBTC * bid_BTCUSDT / ask_ETHUSDT`. These are proposed identities, not
measured outcomes. A factor above one is only a candidate prerequisite. The
depth-constrained ledger must conserve each asset and deduct three fees; an
independent synthetic reverse-direction/unit test should catch inverted pairs.

Preserve request clocks, observed capture span and cross-source disagreement.
Never select whichever book snapshot is favorable. The bookTicker serves as a
separate top-of-book diagnostic; depth supplies the fixed size calculation.
All outputs remain asynchronous displayed-quote scenarios with execution
unavailable, even if capture span is short. Snapshot negativity can close only
this measured window/cost configuration, not all triangle opportunities.
Positivity would justify a separately frozen event-timed observation and
residual-inventory design, not orders, paper start or a profitability claim.
No full historical strategy backtest should be inferred from this one capture.

## WBETH rewards with an ETH hedge

The proposed mechanism is validator-reward accrual in the WBETH-to-ETH claim,
hedged against ETH price movement. This is a different income source from a
perpetual funding premium. The ETH hedge still inherits funding/basis/collateral
accounting and previously exposed ETH data; renaming the income leg does not
reset that ancestry. Saved history does not establish a complete WBETH financial
trial count, so a future registration must audit it rather than claim zero.

The documented `/sapi/v1/eth-staking/eth/history/rateHistory` is signed USER_DATA
and requires an API key. Fields include `exchangeRate`, `annualPercentageRate`
and `time`; maximum requested interval is three months, with pagination size up
to 100. Displayed response values are examples, not historical observations.
Staking quota, redemption history and reward-history routes are also USER_DATA;
subscription/redemption are TRADE operations. These interfaces do not establish
a public historical ratio feed under the no-credentials scope.
[W1](https://developers.binance.com/en/docs/catalog/investment-and-services-staking/api/rest-api/eth-staking)

The current FAQ extraction contains questions about ratios, rewards, quotas,
redemption timing and additional risks, but not usable answer text. Earlier
saved prose summarized variable redemption and ratio mechanics; this fresh
extraction cannot independently corroborate the exact current rules. The failed
WBETH landing-page fetch supplies no missing answers. Public historical
conversion-ratio availability, redemption waits and slashing-loss allocation
therefore remain unverified, not established absent across all public sources.
[W2](https://www.binance.com/en-GB/earn-faq/light/eth-staking/faq)

Accounting requirements inferred for any later test:

- Pay for WBETH principal, fund hedge collateral and retain an explicit reserve
  from the same 1,000/10,000-dollar capital budget. A hedge notional is not free
  deployable capital. Public availability does not establish account access.
- If `r` is ETH claim per WBETH and holdings are `q`, the first-order ETH hedge
  is approximately `q*r`, subject to admitted market basis. Reward accrual and
  basis changes require a frozen rehedging policy. Fixed `q` ETH hedging assumes
  a one-to-one claim incorrectly.
- Separate changes in reward claim, WBETH/claim discount, ETH hedge price PnL,
  trading fees, funding or borrow, collateral and redemption cashflows. Do not
  add both a ratio-derived reward and the same reward's token appreciation.
- A short perpetual requires complete event funding, margin marks, liquidation
  and reserve constraints. Borrow-and-sell ETH instead requires actual borrow
  availability, rates, recall/repayment rules and collateral; these are missing.
- ETH delta hedging does not remove WBETH depeg, redemption delay, validator
  penalties/slashing, custody or contract risk. Applicable loss allocation and
  compensation cannot be assumed. During redemption, use documented claim,
  reward and cash-availability timing rather than instantaneous ETH receipt.

No historical net-return test is justified until timestamped ratio events,
tradable WBETH/ETH observations and hedge cashflows are admitted together.
A future bounded documentation/contract-provenance investigation could establish
whether an official public on-chain rate-event route exists. Contract address,
ABI, deployment history and free archival completeness are currently unverified;
no chain, RPC provider or paid prerequisite is assumed here.

The immediate named gap for triangles is executable synchronized fills rather
than public price-source existence. For WBETH it is the public historical claim
ratio plus redemption/risk rules, before execution can even be modeled. These
different bottlenecks support prioritizing the small triangle measurement while
retaining WBETH as a source-dependent lead.
