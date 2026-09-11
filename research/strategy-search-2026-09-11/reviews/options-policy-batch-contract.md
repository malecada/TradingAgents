# Offline options-policy batch: sixteen-source contract

September11,2026. Source support for a pure offline adapter and invented tests.
No live batch, selected quote, Greek arithmetic, economic output, registration
or future observation is authorized or performed by this note. The coordinator
owns implementation. This Markdown file is the sole edited artifact.

## Evidence and documentary denominator

Inspected `options_entry.py:127–187`, `carry_capture.py:170–235` and existing
options-policy/source notes. These frozen parsers are reference behavior, not
complete clock/hedge admission for the new policy. No observed receipt bodies
were read. One additional official URL opened, zero search queries:
[USD-M market-data schema](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data).
AccessSeptember11,2026; publication timestamp unavailable. Cached finds do not
add requests. Retained [options market-data schema](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-options/api/rest-api/market-data)
and the existing parser supply the EAPI fields; that page was not re-opened.

Literal FAPI fields are summarized below. Admission rules are proposed checks,
not stronger venue guarantees about freshness or fills.

## Exact fixed request slots

All GETs are a proposed request-definition contract, never requests made here.
`BTC_CALL`, `BTC_PUT`, `ETH_CALL`, `ETH_PUT` mean four **already fixed, admitted
contract IDs** from the separate metadata/selection stage. No batch chooses or
replaces them. Do not manufacture a put symbol by changing a call suffix without
admitting that exact instrument. Parameters below are encoded exactly once.

| IDs/count | Endpoint | Parameters |
|---|---|---|
| `eapi-time` /1 | `https://eapi.binance.com/eapi/v1/time` | none |
| `btc-index`, `eth-index` /2 | `https://eapi.binance.com/eapi/v1/index` | `underlying=BTCUSDT` or `ETHUSDT` |
| `btc-call-depth`, `btc-put-depth`, `eth-call-depth`, `eth-put-depth` /4 | `https://eapi.binance.com/eapi/v1/depth` | exact fixed `symbol`, `limit=10` |
| corresponding four `*-mark` /4 | `https://eapi.binance.com/eapi/v1/mark` | exact fixed `symbol` |
| `fapi-time` /1 | `https://fapi.binance.com/fapi/v1/time` | none |
| `btc-perp-depth`, `eth-perp-depth` /2 | `https://fapi.binance.com/fapi/v1/depth` | `symbol=BTCUSDT` or `ETHUSDT`, `limit=10` |
| `btc-perp-mark`, `eth-perp-mark` /2 | `https://fapi.binance.com/fapi/v1/premiumIndex` | `symbol=BTCUSDT` or `ETHUSDT` |

Denominator is16, even when suppressed, absent, truncated or invalid. There are
11EAPI and5FAPI slots. One asset's missing response must not erase the other
asset's source facts. Shared-clock failure affects its dependent slots. Keep a
global batch-skew diagnostic plus per-asset required-source admission; neither
may be silently recomputed using only successful sources to hide a late failure.

## Literal fields and normalized contract

**Both time responses:** object with positive integer-int64 `serverTime`.
Reject bool-as-int, errors and duplicate JSON keys. Keep its own request and
retrieval UTC/monotonic times. EAPI time is not a substitute FAPI calibration.

**EAPI indices:** object with positive bounded decimal-string `indexPrice` and
positive integer `time`. Underlying identity is supplied by the exact request;
a response underlying field is not guaranteed. If one is present and conflicts,
reject it. `time` is a source timestamp, not proof of index publication latency.
Keep it distinct from serverTime and receipt time. Index is neither a hedge bid
nor a terminal settlement price.

**All option depths:** object with integer `T`, nonnegative integer
`lastUpdateId`, `bids`, `asks`. Response symbol is not documented as mandatory;
bind request identity, rejecting any conflicting optional symbol. Each side is
a list of at most10two-string price/quantity rows. Prices must be positive,
quantities nonnegative, finite and bounded. Preserve zero sizes; a zero best
quantity fails a size-dependent action rather than being silently skipped.
Bids descend strictly, asks ascend strictly, best bid must not exceed best ask.
Empty sides are unavailable for their required transaction; do not fabricate a
price or discard the corresponding source slot. Nonempty two-sided depth can
be the adapter's stricter declared admission rule, as in the old parser.

**All option marks:** the frozen EAPI parser admits an array containing exactly
one object for the requested symbol. Require positive finite literal
`markPrice` and finite literal `delta`. Retain `gamma`, `theta`, `vega`, `markIV`,
`bidIV`, `askIV`, `riskFreeInterest`, `highPriceLimit`, `lowPriceLimit` with each
field's present/absent status; absence of a diagnostic Greek must not be
converted to zero. Delta can be negative or zero. Call/put theoretical delta
ranges, if enforced, are a declared policy-model check, not a parser fact.
Only delta is required for the proposed hedge signal; markPrice is needed for
option liability/margin valuation. There is **no documented EAPI mark event
clock**. Preserve `event_time_unavailable`; never substitute depthT or arrival.

**FAPI depths:** fields are `lastUpdateId`, transaction time `T`, message-output
time `E`, and price/quantity bids/asks; symbol is not mandatory. Limit10 is
supported; RPI orders are excluded. Proposed checks: typed integer clocks/ID,
request-bound identity, ordered bounded rows and `T<=E`. Never replaceT withE
or treat either as a fill. Preserve inconsistency rather than repairing clocks.

**FAPI premiumIndex:** documented object/array variants contain symbol,
markPrice/indexPrice, lastFundingRate, interestRate, nextFundingTime,
estimatedSettlePrice and generic `time`. Proposed admission: exactly one matching
object, finite bounded numeric fields and typed time. Do not discard extra
symbols from an array. Auxiliary-field absence can remain separate from valid
mark valuation. Neither latest funding nor estimated settlement is actual cash;
retain missing values rather than zero substitution.

Preserve literal strings alongside normalized decimal values and all field
unavailability. The old `options_entry.number/decode/integer/parse_response`
helpers provide bounded strings, duplicate/nonfinite rejection and source
shapes, but they do not implement this batch's cross-source age model. Its old
`admit` also does not itself verify body hash/length; do not reuse it as a full
receipt-integrity check.

## Receipt integrity and clock calibration proposal

Before schema interpretation, verify each receipt against its exact slot and
request definition: attempted literally true, integer HTTP200, complete body
literally true, error null, strict base64, actual bytes/length/SHA256 agreement,
bounded body and URL parameters. Suppressed/failed receipts remain unavailable.
Validate timezone-aware request/retrieval UTC clocks and monotonic ordering;
retain actual elapsed time and detect inconsistent wall/monotonic durations.
Receipt completeness, schema completeness and action admissibility are separate.
No live transport belongs in the pure adapter.

For each server calibration, let local request/retrieval milliseconds be a/b
and serverTime be S. The offset interval is [S-b,S-a], assuming the timestamp
was generated during that response and offset stable over this short batch.
Retain midpoint and half-round-trip uncertainty as derived metadata, not exact
clock truth. Require plausible S against the old±5second local bounds and
calibration round trip<=5seconds. Reject local backward clocks; no rescaling
seconds/microseconds into milliseconds to obtain a pass.

For a source returned at local time r, its venue's possible clock interval is
[r+offset_low,r+offset_high]. Conservative transaction age uses its upper bound
minus depthT. Require this age<=5seconds andT no more than1second beyond the
upper clock bound, with explicit future-timestamp status. Retain FAPIE separately
for message-delay consistency. Use the same interval machinery for generic
index/premium timestamps only as timestamp plausibility/age diagnostics, without
claiming their field labels establish execution freshness. Keep mark-event age
unknown for EAPI marks even when the HTTP receipt is recent.

The proposed policy's overall earliest-request/latest-required-response span is
at most5seconds. Specify exactly which sources are required for each action;
using a shorter span after dropping failed dependencies is invalid. A16way
concurrent invocation is an implementation possibility, not a simultaneity
guarantee. Calibration uncertainty, source-age results and local skew should be
exported independently so a failed derived criterion is diagnosable.

## Source requirements depend on the action

| Action | Required batch evidence and missing-data consequence |
|---|---|
| Initial option sale plus hedge | Fixed admitted external metadata; both venue calibrations; relevant index; both option depths and deltas/marks; perpetual depth/mark; external wallet/fee/rule inputs. If required entry evidence fails, the planned book is unavailable. No replacement contract or delayed selected entry. |
| Nonterminal hedge decision | Both option deltas for that asset, eligible perpetual side/size and clocks; current index/marks where required by the frozen reserve check. Missing signal, price or required risk input means no new trade and unchanged prior inventory, with a recorded missed decision. It does not mean the modeled intended hedge was filled. |
| Valuation only | Option markPrice, perpetual markPrice and known signed inventory/funding. Missing marks leave that NAV/risk point unavailable; don't use an unexecuted bid/ask as an undisclosed replacement valuation. Diagnostic gamma/theta/IV absence need not block a complete cash valuation. |
| Terminal close | Both option BUY asks/sizes, signed hedge closing side/size, applicable clocks, index/fee inputs and known prior inventory/funding. Closing known quantities does not require fresh delta to determine the close. Missing delta alone must not unnecessarily erase otherwise reconstructible terminal cash. Missing required prices/fees/funding leaves final cash unavailable; model marks cannot substitute. |

Full terminal cash additionally depends on every earlier executed inventory
change and final funding events, which are outside this batch. A source-only
adapter should export capability/dependency facts; it must not compute a Greek
hedge, fee, trade size, cash return or fictional fill as part of this preparation.

## Sources deliberately outside the sixteen-slot denominator

Initial/versioned EAPI and FAPI exchangeInfo provide exact instruments, unit,
tick/lot/minimum notional, status, margin and settlement metadata. They need
separate frozen observation/admission before policy selection; no repeated
selection occurs inside an hourly batch. Retained current metadata does not
establish future rule constancy. Future changes require an explicit policy,
not unregistered refreshes or silently ignored filters.

Authentic final fundingRate events with marks, periodic checks for missing
events, and the hedge-event ownership convention are separate acquisition and
accounting inputs. premiumIndex's latest/next funding fields do not replace
them. Historical intrahour marks, account fee/permission facts, actual maintenance
tiers and liquidation mechanics also remain outside this source batch. No
credentials, account mutation, provider contact, new venue or paper operation
is required or authorized by the offline adapter task.
