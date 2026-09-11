# Fixed spot-triangle public input admission

Experiment triangle-inputs-20260911. Source capture only, before any conversion
profit calculation. Six fixed public requests: exact BTCUSDT/ETHUSDT/ETHBTC
exchange information, server time, one batch best bid/ask response, then depth20
for BTCUSDT, ETHUSDT and ETHBTC in that order. No quote refresh, wider universe,
orders/test-orders, authentication, purchases or private account calls.

The economic lead is same-venue temporary inconsistency between directly linked
currency conversion paths. It differs from the historical OFLOW predictor and
passive adverse-selection strategies: no forecast or inventory-taking signal is
being renamed. Their failed outcomes remain inherited warnings about execution.
No prior exact triangle gate was established in the saved map/source review;
prior_attempts=0 refers only to this explicit static-conversion mechanism, not
all historical liquidity research. Its allowance is at most three new questions,
also charged to map row5's new-work allowance. Metadata capture is first; a fixed
conditional conversion bound would be second. Unknown broader multiplicity stays
unknown. No 22 deferred settlement case is reopened.

Question: do the exact public inputs support a later necessary static unit-conversion
proxy at 1,000/10,000 USDT while preserving source timing and limitations?
Competing explanations include unavailable pairs, invalid/stale/asynchronous
source observations, incomplete sizes/rules or excessive economic friction.
Only input availability/schema are tested here; no cash profit or expected return
is computed. Current prices are first observed at recorded capture clocks and
become exposed development then. They are not future confirmation.

## Frozen source and resources

triangle-request-spec.json fixes every URL, identity and request order. Reuse
frozen public_get: no redirects/proxy/auth/retry,20seconds and5MiB each, same-host
403/418/429/451 denial suppresses later requests. Up to30MiB received bytes,
100MiB total retained outputs and512MiB sampled aggregate RSS,120seconds hard
wall,two allowed CPUs. A90second cooperative collection deadline starts with
capture; do not begin a20second request with less than20seconds remaining.
This reserves time for complete normal serialization before the external guard.
No hidden pagination, symbol discovery, alternate host or asynchronous capture.

Publish exact raw/prefix bytes in six immutable receipt JSON files before parsing
or the next request, with URL, UTC request/retrieval clocks, HTTP status/header
metadata, body completeness/length/SHA256 and denial/error reasons. Keep the full
six-cell denominator. Recoverable parser failures become unavailable cells;
cooperative deadline suppression writes unattempted receipts. Uncatchable crash,
kill or allocation failure preserves the claim and any partial receipts; it is
not silently retried. Aggregate capture and admission are the other two outputs.
Use actual lifecycle pretty serialization for the100MiB bound; cap normalized
admission at12MiB. No raw response is truncated to fit a successful verdict.

## Admission rules and limitations

Use strict UTF-8 JSON without duplicate keys or nonfinite constants. Require a
complete200 response; error objects and empty data are unavailable. Exchange
information must contain exactly the three unique requested symbols with exact
base/quote assets: BTC/USDT,ETH/USDT,ETH/BTC. Retain raw current status, order types,
permissions and all filters. Only TRADING with isSpotTradingAllowed true passes
the conditional pair-availability prerequisite; this is not personal entitlement.
Filters require objects with named filterType; missing relevant lot/notional or
market-order-rule interpretation remains explicit rather than guessed.

The batch ticker must contain exactly the three symbols with positive finite
bidPrice/askPrice/bidQty/askQty and bid<=ask. Depth must contain a nonnegative
integer lastUpdateId and nonempty bid/ask arrays of at most20 positive finite
price/quantity pairs, strictly ordered distinct prices, descending bids and
ascending asks, with best bid<=best ask. Server time is positive integer Unix
milliseconds. No clock inference from lastUpdateId or fabricated exchange event
time. Preserve any supplied timestamps literally; actual local capture intervals
are the reliable recorded ordering, not proof of simultaneous matching-engine
observations. No interpolation or alignment of separately captured depth/ticker.

Depth20 is a bounded observation, not a full order book. This admission does not
establish fills, atomicity across three markets, fees/fee assets, lot rounding,
market-order notional references, user's account access or sustainable opportunity
frequency. Unknowns remain unavailable. Positive quantities at the displayed best
price are source facts only. No beta/power/annualization/PnL convention test is
applicable to this source-only question.

## Follow the result

Independently verify raw hashes/times/identities, all six cells and schemas, then
commit and remotely back up results. If inputs pass, separately register the
already fixed optimistic unit-factor and full-notional proxy design: both directions, both capitals,
zero fee and0.1% acquired-asset commission per leg. It must preserve quantities,
all costs, best-size insufficiency and asynchronous-only scope. A nonpositive
snapshot closes only that measured proxy; a positive one only motivates a
properly timed execution-data study. Neither establishes a tradable strategy.

The lifecycle's existing input window refers solely to observed saved request-
definition bytes, documented in a pinned local marker at freeze. It is registration
bookkeeping, not backdated market observations. Every live output has its actual
first-observed UTC timestamps. Source timing never establishes sample freshness.
