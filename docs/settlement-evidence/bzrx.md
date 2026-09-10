# BZRXUSDT historical settlement evidence

**Disposition: exact terminal accounting remains unavailable.** This investigation recovered pre-event delisting, mark-price protection, fee and funding rules, plus a notice captured one day after the event. It did not recover the executed settlement price, event-specific override/rounding, automatic-settlement fee treatment or final funding valuation. No price estimate, numerical bound, portfolio metric or financial replay was produced.

The investigation follows `audit_settlement_evidence_2026_09_10`, committed at `506373e`. Its exclusive namespace is `data/settlement-evidence/2026-09-10/bzrx/`. Eighteen serial requests retained **864,145 bytes**: 17 HTTP 200 responses and one CDX timeout with an empty failure receipt. Each request used a 30-second timeout and one attempt. The 25 MB quota was respected. No new market-price payload, authentication or provider message was used.

## Historical evidence recovered

The [May 7, 2021 delisting FAQ](https://web.archive.org/web/20210507051628id_/https://www.binance.com/en/support/faq/dd60dfbf654d4055aa6b217ea6d5ddba) predates BZRX closure and supports the old default: last-hour averaging of 3,600 second-level index observations, a ten-minute reduce-only period, and a trading fee on automatic settlement. The previously preserved December 24 capture has the same economic default but different wording. The two captures bracket the event; they do not prove every intervening rule state or its exact application to BZRX.

The [December 20, 2021 notice capture](https://web.archive.org/web/20211220080457id_/https://www.binance.com/en/support/announcement/dff27dc6bcbb432c902bcbea5e24ddfa) has an article body **byte-identical** to the earlier saved current CMS response: `d3e18f7f6035f4f652d83bf1121d9841ed9fbac27cabb05608095469de910fa7`. It schedules closure, automatic settlement and order cancellation for **December 19, 2021 at 02:00 UTC**, links the delisting procedure, and records a December 17 clarification. It also reserves index-constituent changes and Last Price Protected intervention. The separate 1:10 BZRX-to-OOKI token conversion does not transfer the futures position. The capture is after the event and gives no completed transaction or settlement print.

The [October 10, 2021 mark-price FAQ](https://web.archive.org/web/20211010211426id_/https://www.binance.com/en/support/faq/360033525071) establishes that protection mechanisms existed before closure. It describes removing a source with excessive deviation, replacing multiple divergent sources with a median, stale-feed handling, and temporarily referencing the contract's last transaction when reliable index/mark inputs are unavailable. It does not identify which mechanisms were activated for BZRX, the applicable fallback limit, or the resulting settlement value.

The [October 24, 2021 fee FAQ](https://web.archive.org/web/20211024165506id_/https://www.binance.com/en/support/faq/360033544231) gives ordinary USD-M VIP0 examples of **0.02% maker / 0.040% taker**, a quantity-times-trade-price notional basis, and a conditional 10% BNB discount. It does not classify perpetual automatic settlement as maker or taker. Its separate **0.015% settlement fee applies expressly to quarterly delivery contracts** and is not evidence of the BZRX perpetual fee.

The [October 10, 2021 funding FAQ](https://web.archive.org/web/20211010151718id_/https://www.binance.com/en/support/faq/360033525031) gives the historical default valuation as mark price × quantity × rate, scheduled at 00:00/08:00/16:00 UTC. It states that Binance takes no fee from funding transfers and that a position must exist at the funding event. It also warns that actual funding transaction time can deviate by 15 seconds. These defaults do not establish BZRX's actual final charge or any closure-specific adjustment.

## Field matrix

| Required field | Evidence status | Exact remaining requirement |
|---|---|---|
| Original instrument | BZRX/USDT futures closure is supported; OOKI is separate | Original exchange instrument identifier, contract multiplier and settlement specification; no BZRX row remains in the previously archived current exchange metadata |
| Scheduled terminal time | December 19, 2021, 02:00 UTC | Completed settlement timestamp/event identifier, rather than the schedule alone |
| Executed settlement price | Not recovered | Actual price in USDT, or fully applicable historical calculation and inputs |
| Default averaging rule | One hour / 3,600 index observations, supported before and after the event | Actual applied field, sample timestamps, inclusion/endpoints, weights, missing-sample handling and rounding |
| Protection overrides | Historically documented and expressly reserved in the near-event notice | BZRX activation/deactivation records, index constituents/weights and any applied fallback price/limit |
| Reduce-only restriction | Default ten minutes implies 01:50 UTC, conditionally | Event-specific restriction and order/cancellation/settlement sequencing |
| Settlement fee exists | Generic historical delisting procedure says fees apply | Perpetual-specific basis, maker/taker treatment, rate/tier, discount eligibility, asset and rounding; quarterly rules cannot substitute |
| Last pre-closure public funding row | `2021-12-19T00:00:00.031Z`, rate `0.00010000` | This is a published record, not proof of the account charge; its `markPrice` is empty |
| Funding valuation and cutoff | Historical default and timing tolerance recovered | Actual funding-event mark, held quantity, charge identifier, ordering and any final prorating/waiver; later published rates cannot justify continued exposure |
| Precision/rounding | Not recovered for this settlement | Applied price/quantity/commission precision, contract multiplier and cash rounding |
| Actual settlement bound | Not established or calculated | Authentic required observations and proven rule/override applicability; no midpoint or last close is admitted |

## Endpoint and archive limits

The prior bounded public probes were reused without repeating them. The quarterly-delivery endpoint returned no BZRX settlement record. The preserved three-minute mark/index bars are OHLC observations that continue past closure; neither a close nor the next opening mark is an executed settlement field. Existing funding history continues after closure and omits BZRX funding-event marks. None of those facts proves absence of a historical settlement transaction.

The [official archive browser](https://data.binance.vision/) identifies its public S3 listing endpoint. Complete daily/monthly product listings contain trade, candle, index, mark and related products, but no named settlement-record product. The complete BZRX daily index listing contains 15 intervals, with **1m minimum and no 1s**. The exact December 19 one-minute ZIP and checksum exist; the listing records a 30,966-byte ZIP last modified December 22, 2021. Only metadata was retrieved. The [official archive documentation](https://github.com/binance/binance-public-data) also discloses that historical objects may be revised. Archive existence is not proof of exact second-level settlement coverage or contemporaneous vintage.

The API documentation route was coordinated with the LUNA investigation. Its preserved [May 2, 2022 official API capture](https://web.archive.org/web/20220502133908id_/https://binance-docs.github.io/apidocs/futures/en/) is later than BZRX and is qualified accordingly. It documents a symbol-only `estimatedSettlePrice` interface, not a historical completed-settlement lookup, and the prior retirement of the public forced-order route. A BZRX-specific nearest-capture lookup returned January 2, 2022, also after the event. No live price request was made. Authenticated income/export interfaces are potential account/provider evidence only: ordinary income-history retention must not be extrapolated to asynchronous export availability, which was not tested.

The historical fee-table availability query returned no snapshot; the older fee FAQ succeeded instead. The notice CDX query timed out; a distinct availability query located the December 20 capture. These failures remain in the manifest. All four bounded routes—announcement, historical rules, documented interface and official archive—were investigated, and acquisition stopped.

## Precise unsent evidence request

The consolidated [provider request draft](provider-request-draft.md) is appropriate. For BZRX, it should request an authoritative automatic-settlement record for the **original BZRXUSDT perpetual at December 19, 2021, 02:00 UTC**, including:

1. Executed settlement price, effective timestamp, event/trade identifier, quote/settlement unit, original instrument identifier, multiplier and rounding.
2. The actually applied averaging window, second-level observations and weights, boundary convention, index constituent changes, protection activations and resulting override, if any.
3. The perpetual automatic-settlement fee basis, rate/classification, tier/discount eligibility, fee asset and rounding. A quarterly-delivery fee or ordinary maker/taker example is insufficient.
4. The final funding transaction(s), actual timestamp, rate, valuation mark, quantity, charge/waiver/prorating rule and event ordering, including the historical 15-second timing tolerance.
5. Where available only through account exports, the fields needed to match `DELIVERED_SETTELMENT`, `COMMISSION`, `FUNDING_FEE` and `REALIZED_PNL` records to the actual closure, separately from liquidation or voluntary trades. This identifies evidence requirements; no account credentials or full private history are requested or accessed.

No request has been sent. No actual-settlement bound is inferred from minute data while sampling and protection applicability remain unresolved.

## Verification and cross-review

All 18 response-body hashes and receipt contents, the collector hash and five unchanged-body extractions were checked. Earlier raw receipts and outputs were only read. The machine-readable [field matrix](../../data/settlement-evidence/2026-09-10/bzrx/evidence.json) references the finalized [acquisition manifest](../../data/settlement-evidence/2026-09-10/bzrx/manifest.json).

The read-only cross-check of [accounting admission](accounting-admission.md) and the provider draft found no substantive error: conditional OHLC formulas are expressly distinguished from actual settlement bounds, unknown protection/weights block admission, and portfolio Sharpe is not assumed monotone in a terminal cashflow. A clarification was sent to the parent to state explicitly that quarterly-delivery settlement fees cannot substitute for perpetual delisting fees. No shared document, accounting code, gate, earlier result or financial metric was changed by this investigation.
