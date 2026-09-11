# EOHSummary official-source and catalogue review

September 11, 2026. No EOHSummary ZIP, checksum body, option quote, candidate
performance or financial result was opened. The official material inspected
does **not establish an EOHSummary field/clock specification or an executable
historical chain**. A single separately registered object/checksum schema probe
is justified to resolve that narrower dependency; it cannot resolve the complete
historical execution-input gap.

## Exact request denominator

Four explicit document/catalogue URL retrieval attempts were made, against three
distinct URLs. One web-tool catalogue attempt was rejected before usable content;
three attempts returned readable primary-source content. Two separate web search
calls used four query strings for discovery only. Search engine backend traffic
and web-tool cache/network behavior are not independently observable. No other
source/body requests or pagination were performed.

| ID | Exact requested URL | Outcome |
|---|---|---|
| E1 | https://github.com/binance/binance-public-data/blob/master/README.md | Readable official README; 114 source lines; web tool supplies no exact request clock |
| E2 | https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data%2Foption%2Fdaily%2FEOHSummary%2F&delimiter=%2F&max-keys=1000 | Web tool internal safe-open rejection, no usable catalogue body; counted as an attempted retrieval |
| E3 | https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data%2Foption%2Fdaily%2FEOHSummary%2F&delimiter=%2F&max-keys=1000 | Direct catalogue-only HTTP 200, 734 bytes, nontruncated |
| E4 | https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data%2Foption%2Fdaily%2FEOHSummary%2FBTCUSDT%2F&max-keys=1000 | Direct catalogue-only HTTP 200, 79,956 bytes, nontruncated, 294 object keys |

E3 was requested at 08:42:43.048930 UTC and retrieved at 08:42:43.885088 UTC;
response SHA256
`8cdf48f80421f796a66316470f931f38816c0b333daab00a404ea11b9279aa94`.
E4 was requested at 08:43:06.198390 UTC and retrieved at 08:43:07.674860 UTC;
response SHA256
`426d5296742f017162388f2ac1d3359126328dfc6152b3fdac8f9701613f0f2f`.
These hashes and extracted catalogue facts are retained here; the full raw XML
bodies were not separately archived by this read-only source investigation.
Future empirical source admission must preserve its own raw receipts.

The four discovery queries were `EOHSummary schema columns timestamp bid ask
site:binance.com`, `EOHSummary site:github.com/binance`, `"EOHSummary" "Binance"
"timestamp"`, and `site:binance.com "Historical" "Options" "Data" "bid"`.
Results included third-party schema/coverage assertions; none was adopted as
official schema evidence, and no third-party page was opened. Search absence is
not proof that no official schema exists elsewhere.

## What primary sources establish

The [official archive README](https://github.com/binance/binance-public-data/blob/master/README.md)
documents spot/futures formats and general archive distribution, checksum and
revision procedures. Its inspected contents do not define EOHSummary columns,
clock units, snapshot timing or option lifecycle. Its general statement about
archive availability cannot establish complete options-chain coverage. The
document warns that archived files can later be revised, so integrity hashes
and retrieval-time provenance remain necessary.

The [EOHSummary child-prefix catalogue](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data%2Foption%2Fdaily%2FEOHSummary%2F&delimiter=%2F&max-keys=1000)
returns exactly five child prefixes: BNBUSDT, BTCUSDT, DOGEUSDT, ETHUSDT and
XRPUSDT. The listing is not truncated. This establishes current namespace
presence only, not the columns or contents of any member. ETH object dates and
coverage were not opened in this bounded investigation.

The complete returned [BTCUSDT catalogue](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data%2Foption%2Fdaily%2FEOHSummary%2FBTCUSDT%2F&max-keys=1000)
contains 147 ZIP keys and 147 corresponding `.CHECKSUM` keys. Every ZIP key has
its paired checksum key. Filename dates run from May 18 through October 23,
2023, with twelve missing calendar-date keys: September 8–18 inclusive and
September 25. This is current object-key coverage, not proof of 147 complete
daily chains, historic publication completeness, or permanent feed retirement.
There is no listed later BTC object in this nontruncated response. That fact
cannot be generalized to all option data products or other underlyings.

The earliest BTC ZIP key is
`data/option/daily/EOHSummary/BTCUSDT/BTCUSDT-EOHSummary-2023-05-18.zip`,
listed size 402,333 bytes, LastModified `2023-06-06T13:24:13.000Z`; its checksum
key has listed size 100 bytes. The last BTC ZIP key is
`data/option/daily/EOHSummary/BTCUSDT/BTCUSDT-EOHSummary-2023-10-23.zip`,
listed size 402,437 bytes, LastModified `2023-10-24T09:28:38.000Z`.
LastModified is object metadata, not market event time or proof of first
availability. ETags do not replace verification against retained checksum bytes.

## Still unknown

No inspected official schema establishes any of the following for EOHSummary:

- Literal header names, column types, null encodings and units.
- Event-clock versus snapshot-clock meaning, timezone, hour start/end convention,
  publication delay, quote age or synchronization with an executable hedge.
- Presence of actual best bid/ask prices **and quantities**, their simultaneity,
  freshness, quote validity and distinction from IV/mark/last-trade fields.
- Complete available strike/expiry universe at each observation, listing/delisting
  times, expiry cutoffs, exercise/settlement identity and missing-row semantics.
- Historical fees, common lot applicability, margin paths, user access, latency
  and fill feasibility for the old product generation.

The EOHSummary name is insufficient to infer an end-of-hour clock or executable
order-book semantics. The earlier 20-object BVOLIndex lexical slice is also
insufficient to establish the presence or absence of another feed. This review's
stronger BTC key-coverage statement comes from its separate nontruncated prefix
request, not that initial slice.

## Narrow next investigation and ancestry

A schema-only probe can freeze BTCUSDT, the lexically earliest ZIP in the saved
BTC listing (May 18, 2023), and its exact checksum path before body acquisition.
This deterministic metadata rule is unrelated to prices, strikes, liquidity or
performance. It deliberately tests format availability, not a representative or
profitable day. Do not substitute another day on denial, mismatch or bad schema.

Under a separately committed gate, obtain exactly those two objects, preserve
received bytes before parsing, verify checksum/member identity and bounded ZIP
expansion, then inspect header, column counts, raw time/identity formats, missing
fields and within-object coverage. Keep every attempted/unavailable cell. Record
whether quote-price and quote-size fields actually exist without treating IV,
marks or OHLC as replacements. Observed clock patterns remain conditional until
their semantics have documentary support. Do not calculate candidate returns,
screen strikes by favorable quotes, create fills or claim complete history.

If the object lacks usable bid/ask prices, quantities or clocks, that specific
execution-input route remains blocked. If it contains them, the result supports
further source admission only: one day cannot establish a historical chain,
instrument lifecycle, simultaneous hedge execution or economic viability.

The inherited `predlab_rviv_p0` history remains one known administrative bundle
with twelve ledger rows and its original failed gate; unknown statistical
multiplicity is not reset. Its June 2022–March 2025 sample exposure includes the
2023 catalogue dates. The new options metadata capture consumes the first of
three newly allowed investigations. A registered schema probe would consume the
second, leaving one under the unchanged family budget. This is a source question,
not a fresh volatility hypothesis. No budget extension, acquisition registration
or archive-body execution was performed by this review.
