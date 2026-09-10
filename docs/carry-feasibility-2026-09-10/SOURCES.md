# Official sources for the dated carry feasibility measurement

This source review supports the [registered scope](charter.md): Binance BTC/ETH USDT-margined dated futures paired with spot, with Bitrue restricted to product-documentation review. It does not establish account eligibility, executable fees, live contract availability or profitability. No market API, account endpoint or live quote was requested for this evidence collection.

The [receipt manifest](source-evidence/manifest.json) records 13 single-attempt requests on September 10, 2026: six HTTP 200 bodies, six empty HTTP 202 responses and one HTTP 403 challenge. Raw entity bodies and individual JSON receipts preserve request/receipt UTC times, URLs, parameters, response headers, status, byte counts and SHA-256. Requests were serial, unauthenticated, limited to 30 seconds and 8 MiB per document; failures were retained without retry or circumvention. A retrieved document reflects current availability, not its historical publication vintage. All interpretation below is paraphrased.

## Binance contract and settlement evidence

The [current USD-M delivery specifications](https://bin.bnbstatic.com/static/cms/cg08ou2ak0tn7mcplvfg/file/4489bc1615baa27b297ca0b4a321ead7690dbe725a72e5793731b0fc9db89824.pdf), published January 5, 2026, concern contracts admitted to Binance RIE and cleared on Binance RCH. Clauses 4, 8–9 and 23–25 specify quarterly expiry, USDT/USDC settlement assets and cash settlement. The stated 12:00 UTC+4 expiry corresponds to 08:00 UTC; a short processing delay or exceptional postponement is possible. Clauses 32–34 refer to applicable fee tables, relate expiry settlement charges to taker fees, and allow participant-specific differences. These clauses do not prove that a particular account is served by these entities or has the required product access. The measurement remains restricted to USDT, with actual instrument identity selected from registered metadata rules.

- Saved PDF: [binance-contractspecs.pdf](source-evidence/binance-contractspecs.pdf), 174,427 bytes; SHA-256 `4489bc1615baa27b297ca0b4a321ead7690dbe725a72e5793731b0fc9db89824`.
- [Official specification landing page](https://www.binance.com/en/about-legal/contractspecs-usdsmquarterly): empty HTTP 202 response locally; the independently supplied PDF URL was fetched directly and retained.

The [clearing procedures](https://bin.bnbstatic.com/static/cms/cg08ou2ak0tn7mcplvfg/file/53197b612332da02c20b5b7d19b81ff53ee5f4938c6330c72a30a1ca4f91049f.pdf), Procedures 120–122, specify cash settlement and averaging the index sampled each second over the final 30 minutes, with exceptional postponement provisions. Procedure 123 prints a USD-M P&L expression whose settlement-fee term is dimensionally unclear under the usual interpretation of a fee rate. Procedure 190 references the COIN-M fee table for delivery settlement, although the USD-M specification points to that procedure. These are unresolved document/applicability questions. No guessed correction, inverse-contract formula or favorable fee interpretation is substituted. A settlement index also differs from the eventual executable spot-sale price; the charter explicitly retains that mismatch.

- Saved PDF: [binance-clearing-procedures.pdf](source-evidence/binance-clearing-procedures.pdf), 716,997 bytes; SHA-256 `53197b612332da02c20b5b7d19b81ff53ee5f4938c6330c72a30a1ca4f91049f`.

## Fee evidence and its limits

The following official routes were requested and preserved, but all returned empty HTTP 202 bodies in this collection. They remain source pointers, not captured proof of any current fee rate:

| Official source | Receipt stem | Required distinction |
|---|---|---|
| [Quarterly futures FAQ](https://www.binance.com/en/support/faq/detail/3ae441db4ae740e19af3fe9228eb6619) | `binance-quarterly-faq` | General product explanation versus applicable current contract terms. |
| [Spot trading fees](https://www.binance.com/en/fee/trading) | `binance-spot-fees` | Published tier reference versus exact account/pair commissions. |
| [Futures trading fees](https://www.binance.com/en/fee/futureFee) | `binance-futures-fees` | Dynamic table, product type, fee tier and entity applicability. |
| [Futures fee FAQ](https://www.binance.com/en/support/faq/detail/360033544231) | `binance-fee-faq` | Illustrative examples cannot establish an actual account rate. |
| [Spot commission FAQ](https://developers.binance.com/en/docs/products/spot/faqs/commission_faq) | `binance-spot-commission-faq` | Commission asset, discounts, special/tax commissions and actual trade charges. |

The charter's fixed fee values and doubled-fee case are **scenario assumptions**. They are not verified current commissions, guaranteed worst-case charges or an admission of the terminal settlement-fee basis. Spot purchase fees in base units, spot-sale fees in quote units and the absence of third-token discounts are explicit model assumptions. Fee rounding, pair exceptions, tax/special commissions, account jurisdiction and settlement applicability remain required before an executable strategy evaluation.

## Bitrue: dated-product availability remains unknown

The captured [USDT perpetual guide](https://support.bitrue.com/hc/en-001/articles/28937381289881-Bitrue-USDT-Perpetual-Futures-Comprehensive-Guide) describes contracts without expiry and funding charges. The [COIN-M beginner guide](https://support.bitrue.com/hc/en-001/articles/9535446031769-Beginners-Guide-to-COIN-M-Futures) was identified during web research but the raw request returned HTTP 403; its local body is a challenge, not an accepted guide capture. Neither route establishes a currently available dated BTC/ETH contract.

The captured [USDT-M API documentation](https://www.bitrue.com/api_docs_includes_file/futures/index.html) describes `/fapi/v1/contracts`, `/fapi/v1/time` and `/fapi/v1/depth`, against `https://fapi.bitrue.com`. Contract metadata includes type, status, direction, face-value multiplier, multiplier currency and order limits. Type `E` means perpetual, `S` test, with remaining types only described as mixed. The schema does not provide a dated expiry timestamp. Depth requires `contractName`, supports up to 100 levels and represents price/quantity levels with a millisecond time field. Public operational availability and exact quantity interpretation were not tested by market requests.

The captured [COIN-M API documentation](https://www.bitrue.com/api_docs_includes_file/delivery/index.html) presents analogous `/dapi/v1/` routes and contract-type fields. Its location under a `delivery` URL does not establish an expiring product: the navigation labels it COIN-M. No expiry calendar or applicable final-settlement rule was established here.

The captured [marketing article](https://www.bitrue.com/blog/how-long-hold-crypto-futures-contracts) claims availability of traditional as well as perpetual futures, but supplies no named dated BTC/ETH instrument and corresponding binding specification. This discrepancy is retained. The conclusion is **availability unknown**, not categorical product absence. Bitrue receives no dated quote or cash-flow row without a separately registered source/adapter amendment and verified product terms. No current Bitrue fee or Czech/EEA derivative-eligibility claim is made.

## Scope qualifications

The user's statement that Binance is available does not substitute for product-specific account, jurisdiction or fee evidence. Public documentation and readable market APIs do not establish trading permission. Other venues from the initial documentation scan are outside this measurement. No historical settlement case, paid data route, support contact, account inspection or alternative-venue quote has been reopened.
