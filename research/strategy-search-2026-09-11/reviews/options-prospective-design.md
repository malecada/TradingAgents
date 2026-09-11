# Fixed current minimum-lot options prerequisite: seven requests

September 11, 2026. Concrete proposal for the third/final options investigation.
Not registered, implemented or executed. No saved strikes/market observations
were inspected to choose contracts. No private access is required. The output
would concern a representative minimum-lot **option entry-resource prerequisite**,
not affordability of a complete delta-hedged strategy or expected profitability.

This narrows and replaces the earlier illustrative nine-request suggestion in
`options-prospective-gap.md`: use the already admitted metadata, exactly seven
new public request slots and no hedge quote request. Unknown hedge collateral
remains unknown rather than guessed from leverage or model delta.

## Bound existing inputs before acquisition

Bind the raw exchange-info receipt, aggregate and admission from
`research_runs/options-metadata-20260911/outputs/`, using their existing hashes
and original clocks. Revalidate their exact raw/normalized consistency before
any request. The original ambiguous crypto-enum classification remains intact;
a new selection rule must explicitly describe literal base/underlying/type
mapping and documented contract unit, not silently overwrite the old result.
No metadata refresh or selection based on newly appearing contracts is allowed.
Saved metadata is potentially stale: a failed selected-symbol response does
not permit replacement, and current account eligibility cannot be inferred.

## Exact seven-slot request recipe

| Slot | Exact URL or fixed construction |
|---|---|
| options-time | https://eapi.binance.com/eapi/v1/time |
| btc-index | https://eapi.binance.com/eapi/v1/index?underlying=BTCUSDT |
| eth-index | https://eapi.binance.com/eapi/v1/index?underlying=ETHUSDT |
| btc-depth | https://eapi.binance.com/eapi/v1/depth?symbol=BTC_SELECTED&limit=10 |
| eth-depth | https://eapi.binance.com/eapi/v1/depth?symbol=ETH_SELECTED&limit=10 |
| btc-mark | https://eapi.binance.com/eapi/v1/mark?symbol=BTC_SELECTED |
| eth-mark | https://eapi.binance.com/eapi/v1/mark?symbol=ETH_SELECTED |

BTC_SELECTED/ETH_SELECTED are placeholders, never literal requests. Substitute
the percent-encoded exact metadata symbol from the frozen algorithm below.
All endpoints and fields are documented in the
[current market API](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-options/api/rest-api/market-data).
No eighth call, retries, redirects, fallback host, replacement contract or
authenticated commission query. A missing prerequisite produces unattempted
unavailable dependent slots. Same-host denial suppresses remaining calls while
retaining seven intended receipts. Raw receipt persistence precedes parsing.

Selection uses valid captured serverTime as the reference instant; if its
meaning/format cannot be admitted, retain unavailable selection rather than
substituting a local clock silently. For each underlying independently, filter
saved metadata to literal CALL, matching BTCUSDT/ETHUSDT, USDT quote/settlement,
positive finite unit/minQty/step and internally consistent identifiers. Require
metadata TRADING if present in the frozen admission schema; missing status is
unavailable rather than assumed. Candidate expiries are7–45days after reference
time, inclusive; choose nearest30days, then earlier expiry. At that expiry,
choose positive strike minimizing absolute strike-minus-captured-index distance,
then lower strike, then lexical symbol. No option premium participates in
selection. A failed index leaves that asset's selection unavailable.

Only this predeclared selection arithmetic may occur before dependent requests.
No premium, fee, seller-margin or capital comparison occurs until capture has
closed. Preserve selection candidates/counts/tie rule and source hashes as
evidence; no outcome-based adjustment of expiry, strike, quantity or asset.

## Source and entry calculations

Require strict JSON, finite numbers, correct symbol identity, ordered noncrossed
positive best prices and nonnegative visible sizes; missing sides remain
unavailable. Preserve all depth rows and literal server/transaction/local clocks,
with no claim the separate responses are synchronous. Mark is a model value,
delta a model sensitivity; neither substitutes for an executable ask/bid.
Use minQty only when its step and bounds are valid; do not round it down or
invent a lot from quantityScale. Top size must cover that quantity for the
top-price prerequisite; otherwise report insufficient visible size, no deeper
book optimization or smaller lot.

The useful account-independent result is minimum-lot quoted ask expenditure
plus explicitly assumed transaction charge. Denote quantity q, option ask A,
index S and contract unit U. Under the FAQ's price/quantity convention, premium
outlay is A*q and charge is min(r*S*U,0.10*A)*q. Freeze one primary illustrative
rate r=0.00024 from the fee FAQ, with no claim it is the user's rate. A second
0.00030 scenario may be included only if registered explicitly as the unresolved
fee-table alternative already documented; retain both, no favorable selection.
Do not multiply premium by U a second time. Every1,000/10,000 comparison means
**option-entry component fits/does not fit under this scenario**, never total
hedged-account affordability. Missing mark need not invalidate a valid buyer
premium component, but must invalidate dependent seller/model calculations.
[Fee convention](https://www.binance.com/en/support/faq/detail/5326e5de61c34fed98abe28d2f175a23)

Seller illustration is optional and lower priority. If frozen, it may compute
the public FAQ's conditional short-position initial requirement
`[max(0.10*S,0.15*S-OTM)*U + M]*q`, with call OTM=max(K-S,0), mark M;
maintenance uses0.05/0.075 coefficients. This is not the sell-to-open order
check, which also depends on bid/order price, fees and existing position.
Do not present a position formula as the account balance needed to open.
Without a separately reviewed zero-existing-position order formula and cash
timing convention, leave seller **entry** affordability unavailable. Ratio
fields in saved metadata differing from FAQ constants require explicit conflict
status; do not silently choose one. Long-option margin-free holding does not
mean a short futures hedge is margin-free.
[Seller guidance](https://www.binance.com/en/support/faq/detail/1ceb77f837344e3085ecf98d9a6a8097)

## What remains unknown

Personal long/short mode, product/entity access, applicable commissions,
portfolio netting and current collateral requirements are not established by
public API access. The FAQ requires mode upgrade for selling and describes
separate default wallets; formal rules/specifications prevail. No institutional
netting or account upgrade is assumed. No actual hedge quantity, liquidation
buffer, dynamic rebalance cost, funding, expiry payoff, loss distribution,
true delta or return confidence is evaluated. Private account delta/margin
code is unnecessary for the buyer entry-component question precisely because
it does not claim those missing quantities.
[Contract scope](https://bin.bnbstatic.com/static/cms/cg08ou2ak0tn7mcplvfg/file/443bcc67fde7274898ff8e3f7af23c7d89e654c5e609d250772e0ddaa96409be.pdf)

## Limits and interpretation

Suggested bounds:7requests,20seconds/5MiB each,180second cooperative capture,
240second hard wall,512MiB/two CPUs,192MiB total serialized outputs. Demonstrate
actual maximum-payload lifecycle before freezing. Source seven-slot denominator
and each asset/capital/fee/component slot must be fixed; no missing slot dropped.
One registration includes capture, deterministic selection and post-capture
component screen, consuming the final allowance even if unavailable.

This is worth doing if the objective is to remove the still-unmeasured public
premium/visible-size prerequisite before considering future options research.
It is not a direct test of the user's return objective. A positive component
result only names the next hedge/access/time-path requirements; a negative
result applies to these representatives and scenarios, not all contracts.
No current-data result repairs2023EOH semantics or resets RVIV/older multiplicity.
The explanatory source review has four primary URLs/three queries; this design
added only cached extraction of that same API page, no new URL/query/data call.

## Saved-schema correction and narrowed resources

September11,2026: a permitted structural-only inspection of the already admitted
`options-exchange-info-receipt.json` counted field presence and key names. No
strike, expiry, index, premium, contract selection or financial value was read
for this check. There are1,678 symbol rows and10 parent contract rows.

| Field group | Presence |
|---|---|
| Symbol status, side, underlying, quoteAsset, unit, minQty, maxQty, filters, expiryDate, strikePrice, contractType, underlyingType | Each present in all1,678 symbol rows |
| Symbol settleAsset and nakedSell | Absent in all1,678 symbol rows |
| Parent baseAsset, quoteAsset, settleAsset, underlying, nakedSell | Each present in all10 parent contract rows |
| Parent status | Absent in all10 parent contract rows |

Thus an all-missing symbol-status trap is **not present in these saved bytes**;
this check does not inspect status values or prove current trading availability.
Root's proposed conditional rule remains sound: require literal TRADING when
status is present; if absent, retain status unknown and permit only a public
quoted-representative selection, never infer account tradability. Freeze that
rule before selection, not after observing which symbols pass.

Settlement must be resolved from the uniquely matched parent optionContracts
row keyed by underlying, with its literal base/quote/settle identities checked.
Do not require nonexistent per-symbol settleAsset or nakedSell, nor silently
copy a parent when mapping is absent/duplicated/conflicting. Parent nakedSell
is product metadata, not personal seller permission. Per-symbol quoteAsset and
underlying can be checked directly. This is consistent with the documented
parent/symbol schema separation and preserves the original admission's scope.

Resource narrowing supersedes the earlier5MiB/192MiB suggestion: exactly seven
HTTP slots, **256KiB maximum per response and12MiB total actual serialized
outputs**, with a separate small normalization bound proven synthetically.
The selected depth10/index/single-symbol mark sources are deliberately narrow;
oversized responses retain a bounded raw prefix and become unavailable, without
retry or source substitution. Existing parent receipts remain hash-pinned
inputs, not recopied through this response allowance. A proposed1MiB parent
file limit must be checked against actual already-known file size before freeze;
do not truncate an existing parent or redefine its hash to fit. No new metadata
request is introduced. Guarded worst-payload/normalized-expansion preflight
must establish the final limits before any capture.
