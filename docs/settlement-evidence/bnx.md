# BNXUSDT historical settlement evidence — September 10, 2026

The default settlement formula applicable before BNX's March 17, 2025 closure is now supported by a dated Binance notice: the final 30 minutes of one-second index prices, comprising 1,800 observations. The exact final price, historical perpetual-settlement fee treatment and rounding remain unidentified. The recovered index candles support conditional data envelopes, not an unconditional bound on the actual settlement. No portfolio result or replay was produced.

This investigation follows `audit_settlement_evidence_2026_09_10`, registered at `506373efe210ed06bb6a1c1a48a8ba26ff382bb1`, and the [committed charter](2026-09-10-charter.md). It concerns the BNXUSDT perpetual launched in February 2023, not its earlier settled namesake. Original stores and outputs remain preserved.

## Established and unresolved fields

| Field | Evidence and admission |
|---|---|
| Instrument and closure | The previously archived [BNX-to-FORM announcement](https://www.binance.com/en/support/announcement/detail/2f963977c7274e0583f16f2e26987b61) schedules automatic closure/settlement for March 17, 2025 at **09:00 UTC**, with no new positions from **08:30**. Its current body has later spot-scheduling amendments; metadata is not historical immutability proof. |
| Successor rights | The notice's 1:1 BNX-to-FORM conversion concerns token balances. It does not carry outstanding old perpetual positions into FORM futures. Prior receipts distinguish the February 2023 BNX incarnation from `BNXUSDTSETTLED`. |
| Applicable default formula | The [November 4, 2024 Binance notice](https://www.binance.com/en/support/announcement/detail/4bcabddf0e81423ebca242e185bf157d), effective **November 11, 2024 at 08:00 UTC**, changes one-hour/3,600-index settlement averaging to **30 minutes/1,800 indices**. It explicitly includes contracts subject to delisting. Applying the stated relative window to BNX gives 08:30–09:00 UTC. The notice is stronger evidence of historical applicability than today's FAQ. |
| Actual final price | No final settlement-price print was recovered. The dated rule establishes the default calculation, but the minute candles do not reveal the exact one-second mean. Exact complete observations plus applicable calculation/rounding rules could establish it without an account receipt; such observations were not recovered here. |
| Emergency provisions | The BNX notice allows funding-parameter and index-constituent changes and Last Price Protected mark adjustments. A genuine index series should already reflect constituent changes. Mark protection is not itself proof that the contractual settlement-index mean was overridden. No BNX-specific settlement-formula override was found or assumed. |
| Historical settlement fee | The [December 5, 2024 fee FAQ archive](https://web.archive.org/web/20241205112302id_/https://www.binance.com/en/support/faq/binance-futures-fee-structure-fee-calculations-360033544231) gives ordinary regular-user USD-M examples of **0.02% maker / 0.05% taker**, charged on quantity times trade price, with a conditional 10% BNB discount. It does not classify automatic perpetual settlement as maker or taker. No event-specific rate, discount eligibility or rounding rule was established. |
| Funding treatment | The [December 21, 2024 funding FAQ archive](https://web.archive.org/web/20241221102959id_/https://www.binance.com/en/support/faq/introduction-to-binance-futures-funding-rates-360033525031) gives USD-M funding as mark price × quantity × rate, contingent on an open position at actual funding processing. It permits up to one minute of timing deviation and says the internal funding mark can differ from the displayed one-second mark. |
| Last published pre-closure funding | The preserved public funding response's last pre-closure entry is **March 17 at 08:00 UTC**, rate **0.00427083**, associated mark **1.81798982**. This is an observed funding-history entry, not a position-level cash receipt. No special 09:00 funding adjustment was established. Later published rates cannot justify charges to a closed position. |
| Precision | The exact averaging endpoint convention, missing-update handling, price rounding, commission rounding and final funding/settlement ordering are not established by the recovered BNX-specific evidence. |

The [March 6, 2024 archived delisting FAQ](https://web.archive.org/web/20240306085115id_/https://www.binance.com/en/support/faq/delisting-of-futures-contracts-dd60dfbf654d4055aa6b217ea6d5ddba) still describes one-hour averaging, already with a 30-minute restriction. The November notice explains the later averaging change; the March FAQ is not applied unchanged to BNX. Today's FAQ adds explicit taker-settlement wording but was updated in February 2026, so that fee wording is not backdated.

## Index data and conditional envelopes

The official [March 17 index-candle archive](https://data.binance.vision/data/futures/um/daily/indexPriceKlines/BNXUSDT/1m/BNXUSDT-1m-2025-03-17.zip) passes its separately retrieved [SHA256 checksum](https://data.binance.vision/data/futures/um/daily/indexPriceKlines/BNXUSDT/1m/BNXUSDT-1m-2025-03-17.zip.CHECKSUM). It contains 1,440 minute rows. A bounded public `indexPriceKlines` request for 08:30 through the 09:00 boundary returns 31 rows that match all 12 archive fields numerically. The final pre-closure window has the expected **30/30 minute rows**.

That complete minute grid does not prove complete second-level coverage. The archive's `count` field totals **1,798**, with **59** at 08:40 and 08:46 and 60 elsewhere. The [archived official API schema](https://web.archive.org/web/20220502133908id_/https://binance-docs.github.io/apidocs/futures/en/#index-price-kline-candlestick-data) identifies this field as the number of basic data points. It does not supply their individual timestamps or explain missing-update/fill handling. No two missing values were invented.

Let `L_i`, `H_i` and `n_i` be each minute's reported low, high and count. The deterministic [coverage artifact](../../data/settlement-evidence/2026-09-10/bnx/index-coverage.json) records two distinct conditional calculations:

| Interpretation | Index-price interval in USDT | Limitation |
|---|---:|---|
| Mean of the represented observations: `Σ n_i L_i / 1798` through `Σ n_i H_i / 1798` | Approximately **[1.7856600394, 1.8575355687]** | Requires the reported extrema to enclose the observations represented by each count; this is a bound on their 1,798-observation mean, not the contractual 1,800-observation mean. |
| Hypothetical complete, equally sampled 30-minute window: `mean(L_i)` through `mean(H_i)` | Approximately **[1.7856616517, 1.8574754240]** | Requires all 60 relevant one-second values per minute to lie within the reported extrema, the same settlement index, `[08:30,09:00)` endpoints and accounted-for rounding. The two counts of 59 leave completeness unestablished. |

These intervals are rounded displays of the decimal calculations, not outward-rounded certified cash bounds. Neither is admitted as an unconditional bound on BNX's actual settlement. The familiar pre-closure trade close, mark close, index close and subsequent FORM price are not substitutes for the settlement mean.

## Route coverage and stopping decision

| Required route | Coverage and outcome |
|---|---|
| Official announcements | Prior BNX closure and identity receipts were reused. A new public CMS receipt preserves the November 2024 rule change, including publication metadata and full body. A historical archive lookup for that announcement returned no capture; the current published notice is identified as such. |
| Historical rules, fees and funding | Recovered March 2024 delisting, December 2024 ordinary-fee and December 2024 funding pages. Three bounded CDX requests timed out. Availability lookups also retained empty results and post-event HTTP-202 capture metadata; those are not readable historical rule evidence. No identical empty query was retried. |
| Documented public endpoints and web history | Reused the prior empty BNX `/futures/data/delivery-price` response, whose documented scope is quarterly contracts; no repeat query. The official API archive describes `premiumIndex`/`estimatedSettlePrice` as a current, symbol-only estimate, not historical final cash. Public web discovery did not establish an additional perpetual settlement-history route. Account history/export routes are distinct and were not called. The only new market API request was the bounded index window above. |
| Official data archive | Preserved complete directory/type and BNX index-interval listings, the explicit event-day ZIP/checksum keys and both files. The listed BNX index intervals start at one minute; no second-level index or settlement-print dataset appears in those inspected listings. This is a statement about the inspected archive routes, not all possible Binance internal data. |

Search stopped after all four routes were covered. The namespace contains **23 direct public requests, 1,219,027 downloaded body bytes**, including 20 HTTP-200 responses and three recorded 30-second timeouts. Requests were sequential, with one attempt per exact URL/parameter set, below the 25 MB allowance. Search-engine snippets were discovery only. All primary claims use archived official responses or previously preserved receipts.

The [receipt manifest](../../data/settlement-evidence/2026-09-10/bnx/manifest.json) preserves request and retrieval UTC times, exact URLs/parameters, response status/headers, body hashes, prior receipt references and derived-artifact hashes. `derive-index-coverage.py` reproduces the integrity checks and conditional algebra without financial calculations. SHA256 verification covered every new response and derived extraction; no existing output was rewritten.

## Remaining evidence request — unsent

The remaining request is for the February 2023 BNXUSDT incarnation's final settlement price/time and precision; the exact 1,800 index observations or certified aggregate with endpoint and missing-update handling; any effective event-specific amendment; historical perpetual-settlement commission category, rate/basis, discount and rounding; and final funding valuation/timing and any special adjustment. A provider-certified calculation record or sufficiently complete official observations could resolve these fields. Authorized historical income/order exports are another possible corroborating source, not a route exercised here. The [combined draft](provider-request-draft.md) remains unsent.

This evidence update does not change the preserved two conditional measured failures and 22 unavailable accounting cases. A subsequent financial use requires its own committed registration and reviewed accounting treatment.
