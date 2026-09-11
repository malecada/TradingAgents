# Binance–Bitrue perpetual comparability: source review

September 11, 2026. Disposition: **a bounded contract-metadata admission is
justified; a cross-venue funding-profit experiment is not yet admitted**. Exact
live Bitrue BTC/ETH contract sizes, historical funding cashflows, current fee
applicability and user eligibility remain unknown. This is a source result, not
a financial experiment or exhaustion proof.

## Requests and provenance

Ten explicit primary document URLs were requested, once each. Nine returned
readable material, but the Binance fee page had no rate records; Bitrue `/fee`
returned an internal retrieval error. Three search queries were issued; cached
reference open/find operations extracted existing documents without introducing
additional source URLs. The ten-URL denominator is not a claim about the web
tool's underlying network/cache traffic. No live price, funding-rate series,
market API body, private endpoint, account record or credential was requested.

Access date for every source is September 11, 2026. Exact retrieval clocks were
not supplied by the web tool. Publication/update dates below are displayed
document metadata, not the dates a historical trading rule necessarily began.

| ID | Exact requested primary URL | Outcome/date |
|---|---|---|
| B1 | https://www.bitrue.com/api_docs_includes_file/futures/index.html | Readable; latest displayed changelog May 9, 2025 |
| B2 | https://www.bitrue.com/api_docs_includes_file/delivery/index.html | Readable; extraction repeats the futures API text/line count; URL label alone does not prove inverse/delivery specifications |
| B3 | https://www.bitrue.com/fee | Internal retrieval error; no current fee evidence |
| N1 | https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data | Readable; publication date unspecified |
| N2 | https://www.binance.com/en/fee/futureFee | Readable page shell, “No records found”; no numeric fee schedule obtained |
| N3 | https://www.binance.com/en/support/faq/detail/360033525031 | Published September 9, 2019; updated March 6, 2026 07:01; warns guidance may be outdated |
| B4 | https://support.bitrue.com/hc/en-001/articles/4409416662937-Beginners-Guide-to-USDT-Futures | Readable; updated March 24, 2023 08:53 |
| B5 | https://support.bitrue.com/hc/en-001/articles/29475614739609-Reduction-in-USDT-Based-Futures-Trading-Fees | Readable; updated March 4, 2024 11:33; historical adjustment announcement |
| B6 | https://www.bitrue.com/static/futures-agreement/BitrueFuturesServiceAgreement-en_US.pdf | Readable four-page agreement; exact revision/effective date not established |
| B7 | https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/future_open_api.md | Readable official repository linked by B1; version applicability must be retained |

Search strings: `site.bitrue.com futures funding fee USDT contract funding 8 hours`;
`site:bitrue.zendesk.com futures funding fee trading 0.02 0.06`;
`site:bitrue.com USDT margined futures prohibited countries`. The first string's
`site.bitrue.com` is recorded literally; it was not a valid domain-filter syntax.
Incidental third-party/exchange results were not used as Bitrue/Binance evidence,
and no third-party page was opened. Public API sample credentials appearing in
documentation were neither used nor reproduced in this report.

## Contract, funding and collateral comparison

Binance documents `/fapi/v1/exchangeInfo` with contractType, base/quote/margin
assets, status, onboarding and lot/notional filters. Precision fields explicitly
are not substitutes for tick/step sizes. `/fapi/v1/fundingRate` exposes settled
fundingTime/rate and associated markPrice, with start/end and limit up to 1,000.
`fundingInfo` describes interval/cap/floor adjustments, not a complete historical
event calendar. Exact BTC/ETH rules require admitted returned metadata rather
than generic response examples. [N1](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)

Bitrue documents base `https://fapi.bitrue.com` and public
`/fapi/v1/contracts`, with status, type, side, multiplier, multiplierCoin,
minOrderVolume/minOrderMoney and maxima. Type E is described as perpetual;
side 1/0 as forward/backwards. Contract name and multiplier determine units;
BTCUSDT-like naming alone does not establish a Binance-sized contract.
Its websocket guidance says volumes require contract-size conversion. Do not
copy an HT example or assume one order-volume unit is one BTC/ETH. The guide
labels NONE endpoints public while USER_DATA requires signatures.
[B1](https://www.bitrue.com/api_docs_includes_file/futures/index.html)

The intended comparability target is same-underlying USDT-linear perpetuals.
Inverse/coin-settled or mixed products are not interchangeable hedges: a
base-denominated collateral/PnL book would need a separately derived conversion
and stress model. B2's repeated documentation cannot establish a coin-margined
contract just because its path says `delivery`.
[B2](https://www.bitrue.com/api_docs_includes_file/delivery/index.html)

The Bitrue beginner guide describes separate USDT futures funding, cross versus
isolated margin, and funding transfers at 00:00/08:00/16:00 UTC. Its formula
multiplies position quantity, contract value, mark price and funding rate;
these unit factors must be matched to actual contract metadata. This older
general guide does not establish an exception-free BTC/ETH event calendar or
current margin requirements. [B4](https://support.bitrue.com/hc/en-001/articles/4409416662937-Beginners-Guide-to-USDT-Futures)

Binance describes transfers between long/short holders, funding deductions from
available balance and then margin, and adjustable funding intervals. Its FAQ
discusses one-hour transitions effective May 2, 2025 and reversion rules effective
January 2, 2026. Thus eight-hour synchronization cannot be assumed. The FAQ
itself defers to applicable exchange/clearing rules effective January 5, 2026
and contract specifications; no user's entity is established here.
[N3](https://www.binance.com/en/support/faq/detail/360033525031)

## History and fee gaps

The official Bitrue repository documents public `/fapi/v1/index` with
currentFundRate, nextFundRate, remainingSecond, indexPrice and tagPrice. That is
a current-state interface, not settled funding history. Its REST klines have a
300-row maximum and no documented historical funding-event calendar in the
inspected material. The example `idx` values look seconds-sized while prose
says milliseconds; resolve units instead of silently guessing. The HTML guide
also documents websocket historical bars via endIdx/pageSize up to 300, without
proving retention depth or historical mark/funding availability.
[B7](https://github.com/Bitrue-exchange/USDT-M-Future-open-api-docs/blob/main/future_open_api.md),
[B1](https://www.bitrue.com/api_docs_includes_file/futures/index.html)

The March 2024 Bitrue announcement displays post-adjustment opening maker/taker
0.02%/0.06% and closing maker/taker 0.02%/0.02%. The asymmetric closing taker
entry is preserved, not silently replaced with a familiar fee. The announcement
permits amendment; it is not verified current BTC/ETH account pricing.
[B5](https://support.bitrue.com/hc/en-001/articles/29475614739609-Reduction-in-USDT-Based-Futures-Trading-Fees)
The requested current Bitrue fee route failed, and Binance's current fee page
returned no numeric records. Therefore **neither venue's applicable current
regular fee is established by this review**. No fee from memory, promotion,
VIP example or another product is substituted.
[N2](https://www.binance.com/en/fee/futureFee)

## Eligibility and funded neutrality

The Bitrue agreement restricts listed jurisdictions and gives the platform
identity-verification/service-discretion rights. Its exact current effective
version remains unverified, and absence of a country from one inspected list
does not prove the user's eligibility. This is documentary applicability
evidence, not a legal conclusion about the user. Binance availability asserted
by the user likewise does not identify derivatives entity, permissions or
commissions. No private account check occurred.
[B6](https://www.bitrue.com/static/futures-agreement/BitrueFuturesServiceAgreement-en_US.pdf)

Accounting implications, not measured outcomes: two opposite futures legs need
prefunded collateral/reserves on both venues from the same 1,000/10,000 total
capital. Profits on one venue cannot instantly meet a margin call on the other.
Match signed underlying quantities after multipliers; separately book each
venue's marks, fees, settled funding, wallet cash, liquidation and transfer
costs. Differential funding can reverse, and basis divergence remains even
with matched nominal delta. Borrow is unnecessary for a pure futures/futures
pair but cannot be assumed available for alternative spot legs. No expected
profit, low-risk designation or sustainable differential follows from these rules.

## Highest-value finite next question

A two-request **Bitrue contract-metadata/time admission** is the cheapest next
source step: freeze `/fapi/v1/contracts` and `/fapi/v1/time`, no index/rate/price
endpoint, retries or fallback. Retain all metadata raw rows; identify BTC/ETH
only from actual contract identity/type/side/unit fields, preserving ambiguous
mapping. Compare against the already admitted, hash-pinned Binance exchange
metadata with its original capture clock; do not silently refresh it. If an
additional Binance metadata capture is needed, declare it beforehand as a third
request, not as an uncounted replacement.

This can settle current contract comparability and quantity granularity, not
economics. The next named blocker is **Bitrue settled funding-event history with
event marks and verified unit/clock semantics**. A separate bounded official
documentation review of versions/history routes may resolve it; no public
history endpoint is fabricated from Binance URL conventions. If unavailable,
defer the historical cross-venue route and compare a prospectively registered
source collector against other affordable mechanisms. Do not infer that all
public Bitrue history or all venue segmentation opportunities are impossible.

The mechanism inherits broad funding/venue search history and unknown statistical
multiplicity; it does not reset closed single-venue configurations by renaming.
Exact cumulative family registration is a coordinator task before acquisition.
No gate, empirical capture, account action or paid prerequisite was created by
this review; the 22 settlement-dependent cases remain deferred.
