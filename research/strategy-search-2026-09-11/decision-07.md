# Decision 07 — options metadata admitted, economics still unavailable

Completed once as options-metadata-20260911 from source
828884688b944b5cd2c33537fe4fcabc28325e66, committed, pushed and remotely verified
before acquisition. Four requests and cells are complete, zero unavailable;
six immutable outputs retain 1,069,263 raw bytes. Independent reconstruction
checked exact hashes, raw/aggregate equality, schemas, timing and all normalized
rows without importing the collector. The receipt verifier passed separately.
Observed request span: September11,2026 08:40:11.517399–08:40:16.763026 UTC.
The saved input document window never backdates these observations.

The current response contains1,678 symbol rows. Of1,230 explicit BTC/ETH targets,
654 are BTCUSDT and576 ETHUSDT. All have unit1,minQty0.01 and LOT_SIZE step0.01
in the observed response; all target quantity-rule checks agree. These are actual
current metadata, not earlier documentation examples or historical contract rules.
The literal contractType/underlyingType fields remain classified ambiguous by
the frozen parser, which did not admit enum meanings. That conservative label is
not silently changed after results. nakedSell=true appears in BTC/ETH
optionContracts, not in the individual symbol rows; neither is user permission.

A nontruncated listing of the exact daily archive prefix returns BVOLIndex and
EOHSummary. The separate initial20-object listing is a partial lexical slice of
BVOLIndex ZIP/checksum objects dated June20–29,2023. It is not representative
coverage, and does not establish absence of other object types. ETags are not
SHA256 and LastModified is not first-publication proof.

## Learning and next action

The data weaken two specific source concerns: current small quantity increments
are observed, and an official end-of-hour-summary namespace exists. Neither
establishes long-option affordability, seller access, applicable account fees,
historical bid/ask-size chains, dynamic hedge costs or margin/tail survival.
No premium, cash profit, beta, expected-return interval or strategy success was
measured. Zero strategies validated.

The separate bounded official-source investigation found no documented EOHSummary
field schema. Its BTC catalogue has147 ZIP/checksum pairs dated May18–October23,
2023 with12 missing daily keys. A deterministic earliest-listed BTC object plus
checksum schema probe is justified: it can resolve header/field/clock and quote-
size availability without choosing prices or computing returns. This would use
the second of three new options investigations and preserve old RVIV/spent-2023
ancestry. No catalogue name alone is promoted to executable historical evidence.

In parallel, prepare the fixed six-request BTC/ETH/USDT spot-triangle source
admission, followed only if valid by separately registered optimistic conversion
bounds. The new mechanism concerns linked exchange-rate consistency, not renamed
OFLOW or passive-liquidity forecasts. Dated-book failures remain deferred and
unchanged. The program is active/incomplete; interim coverage still has useful gaps.
