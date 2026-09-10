# Unsent request for historical Binance perpetual settlement records

**Draft only. No message has been sent and no account access is requested.**

Subject: Historical automatic-settlement prices and rules for BZRXUSDT, LUNAUSDT and BNXUSDT

Historical Binance USD-M linear-perpetual accounting is being reconstructed for academic research. Official delisting announcements establish the scheduled events below, but the public trade candles and funding histories do not establish the final cash-settlement records.

| Original perpetual | Announced automatic settlement, UTC | Official announcement |
|---|---|---|
| BZRXUSDT | December 19, 2021 at 02:00 | https://www.binance.com/en/support/announcement/detail/dff27dc6bcbb432c902bcbea5e24ddfa |
| LUNAUSDT | May 12, 2022 at 15:30 | https://www.binance.com/en/support/announcement/detail/ef3ce76d5c2d45ee9b6dc3f281cde744 |
| BNXUSDT, the contract launched in February 2023 | March 17, 2025 at 09:00 | https://www.binance.com/en/support/announcement/detail/2f963977c7274e0583f16f2e26987b61 |

For each original contract, please provide or identify an authoritative historical record containing:

1. The actual automatic-settlement price in USDT per contract unit and its effective UTC timestamp; the contract multiplier, precision and rounding applied; whether the event completed at the announced time.
2. The exact rule applied to that event, including averaging interval, sampling frequency and price field, and any emergency protection, index-constituent or last-price override. If no explicit final price is retained, please identify the complete observation dataset from which it can be reproduced.
3. The automatic-settlement commission basis and rate schedule effective on that date, including whether maker/taker classification, account tier or discounts applied. Please distinguish perpetual delisting from quarterly delivery: the historical quarterly settlement fee does not by itself establish the perpetual event's fee. This is a request for the historical schedule, not any individual's account details.
4. The last funding charge applicable to an open position before settlement: timestamp, realized rate, valuation price/basis and rounding, plus any special final funding adjustment. Please clarify whether later published funding-history rows imply any charge after contract termination.
5. The ordering of automatic settlement, pending-order cancellation, funding and any restriction on increasing positions at coincident timestamps, together with the original historical contract identifier used in settlement records.

A public CSV/JSON record, archived official notice, event report or documented historical API is preferred. Please distinguish a final settlement price from an estimate, last trade price, mark/index candle, or successor token's conversion rate. Current generic rules may differ from the rules applicable in 2021, 2022 and 2025.

If these records are available only in historical account exports, please specify the export type and field names needed to identify automatic settlement and associated commission/funding. No API key, login credential, full account history or personal information is being requested.

The historical API documentation lists income categories `DELIVERED_SETTELMENT` (the documented spelling), `FUNDING_FEE`, `COMMISSION` and `REALIZED_PNL`. Useful matching fields include original symbol, UTC time, asset, income category/amount and transaction or trade identifier; a corresponding settlement trade record would additionally need quantity, price and commission. Please identify which records actually represent automatic delisting settlement, as distinct from voluntary trades or an earlier liquidation. The ordinary income-history API and asynchronous transaction export have separate documented limits, so the ordinary history limit should not be assumed to govern older exports.

Thank you.

---

Internal acceptance note: a provider response must be archived with its original receipt, source, effective date and contract identifier before admission. A response that merely repeats the announced closure or current FAQ does not resolve the missing historical cashflows. Any response containing private account information requires separate handling; it should not be committed to the public-source evidence branch.
