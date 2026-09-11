# Bitrue settled funding history: bounded source follow-up

Access date: September 11, 2026. **No official public settled funding-event
history route with event marks and verified clock/unit semantics was established
within the inspected scope.** This is an unresolved source dependency, not proof
that Bitrue has no such route or that cross-venue carry cannot work. No market
API body, rate/price series, private endpoint, credential or account was accessed.
No financial experiment, registration or provider contact occurred.

## Request denominator and temporal limits

Six additional distinct primary document URLs and four search queries were
requested. All six yielded relevant readable material. GitHub also displayed
generic loading/action-error page furniture; this did not prevent extraction of
the listed source text. Reopening/extracting already requested pages introduced
no seventh source URL. This counts explicit source URLs and search queries,
not unknown underlying web-tool cache/network transactions. Exact retrieval
clocks and source revision/effective dates were not established; blank latest-
commit fields do not prove current contract applicability.

| ID | Exact URL | Evidence and limitation |
|---|---|---|
| H1 | https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/tree/main/v2 | Directory establishes the inspected v2 documentation files; not an exhaustive API catalogue |
| H2 | https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/issues | Five open issue titles displayed; individual issue bodies and closed issues were not inspected |
| H3 | https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/v2/MarketControllerApi.md | Public depth, ticker and kline interfaces; no settled funding history documented in this file |
| H4 | https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/v2/PublicControllerApi.md | Ping, server time and current contracts; important request-schema ambiguity below |
| H5 | https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/v2/UserV2ControllerApi.md | Signed user/account, commission and transfer/liquidation history; not a public settled-rate archive |
| H6 | https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/v2/UserWebsocketStreamAPI.md | Authenticated account-stream listen-key lifecycle; no public settled-event route established |

Exact discovery queries:

1. `site:github.com/Bitrue-exchange "funding" "history"`
2. `site:bitrue.com "fundingRate" "history" API`
3. `site:support.bitrue.com "API" "funding" history`
4. `site:github.com/Bitrue-exchange "fundingHistory"`

Results included the previously inspected official v1 document and third-party
library/other-venue material. No third-party page was opened or adopted as
Bitrue semantics. Search indexing, wording and incomplete issue coverage limit
negative findings. No fabricated endpoint patterned after Binance was tested.
The earlier ten-URL/three-query comparison remains a separate denominator in
[venue-comparability-source-20260911.md](venue-comparability-source-20260911.md).

## Evidence versus unresolved dependencies

The v2 market file documents `/fapi/v1/depth`, `/fapi/v1/ticker` and
`/fapi/v1/klines`; the directory name does not mean every route uses `/v2`.
Klines have a default limit of 100 and maximum 300, and do not establish settled
funding cashflows or event marks. The example `idx` has a seconds-sized value
while prose calls it milliseconds: the contradiction remains unresolved.
[H3](https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/v2/MarketControllerApi.md)

The public controller documents `/fapi/v1/time` with an arbitrary-object
response, so neither a clock field nor its units are guaranteed there.
`/fapi/v1/contracts` exposes identity, type, direction, face-value multiplier and
unit, and order-volume/value constraints. Its parameter table marks
`contractName` required, while the displayed request omits it and the response
is an array. This discrepancy must be frozen as an admission uncertainty before
an unfiltered two-request contracts/time capture. An unfiltered failure must
not trigger undeclared symbol-specific retries. The E-BTC-USDT example is
documentary naming evidence, not a current listed contract or user permission.
[H4](https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/v2/PublicControllerApi.md)

The user controller's account record includes accumulated capital costs and
historical realized amounts. These are account aggregates, not a public series
of final rates with event marks. Transfer history is wallet transfers;
force-order history is liquidation orders. The commission endpoint is signed
USER_DATA and its sample numbers are not applicable current fees. None was
called. [H5](https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/v2/UserV2ControllerApi.md)
The account websocket requires a listen key; it cannot be treated as a free
unauthenticated public funding-event archive.
[H6](https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/v2/UserWebsocketStreamAPI.md)

The five displayed open issue titles concern general documentation, signatures,
a one-hour kline issue, websocket market/account updates and a generic API error;
their displayed dates span August 9, 2022 to October 12, 2024. No displayed title
identifies a funding-history route. Public reporter titles are neither maintainer
confirmation nor a comprehensive absence test.
[H2](https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/issues)

Previously inspected official v1 documentation provides `/fapi/v1/index` fields
for current/next funding estimates, countdown, index and mark-like prices.
Those contemporaneous observations do not by themselves identify the final
settled rate and event mark used in actual cashflows. Neither countdown polling
nor a rate transition should silently be relabeled a settled event.
[Previously inspected v1 source](https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/future_open_api.md)

## Finite next action

Proceed with a registered contract-metadata admission only if its frozen rules
retain the contracts-parameter and time-schema ambiguities above. This can
resolve current contract identity and unit comparability cheaply. It cannot
resolve return, funding settlement, current fees or account eligibility.

Defer historical cross-venue funding accounting until an admitted source supplies
final event time/identifier, rate, associated mark, contract/rate units and event
coverage. A prospective public-index capture could answer a narrower source-
observability question, but should not be preferred as a financial test merely
because retrospective history is missing. Any such capture needs a separate
finite registration and explicit proxy status until settlement semantics are
verified; no scheduler or waiting job is started by this note.

The documentary budget is exhausted for this question. A missing route in these
files is not a family-wide rejection, nor permission to reopen the 22 deferred
settlement-dependent cases. Broad funding/venue history and unknown prior
configuration multiplicity remain inherited; source work does not reset them.
