# Next source question: Czech-account-compatible quote assets

Preparation only; no requests under this proposal until the DEX source question
closes and a separate exact gate/source packet passes review. Reuse the same
shared lifecycle, strict JSON/prefix-retention pattern and reviewed v2 guard.

Question: does the fixed public Binance spot API disclose BTCUSDC/ETHUSDC
instrument rules and finite two-sided depth, as inputs to later full-capital
spot/cash accounting? Public reachability from the user-reported Finland VPN
does not establish Czech-account access. No account endpoint, API key or VPN
change. USDT remains outside this current implementation-source request.

Four single GET requests, in order, with no replacement/retry:

1. https://api.binance.com/api/v3/time
2. https://api.binance.com/api/v3/exchangeInfo?symbols=%5B%22BTCUSDC%22%2C%22ETHUSDC%22%5D
3. https://api.binance.com/api/v3/depth?symbol=BTCUSDC&limit=100
4. https://api.binance.com/api/v3/depth?symbol=ETHUSDC&limit=100

Before execution freeze cells and validation: integer server time in milliseconds;
exact unique base/quote identities, spot-trading status and quantity/notional/price
filters; positive finite Decimal bid/ask prices and sizes, monotonic unique levels,
uncrossed book, integer update ID. Retain all original response fields/bytes and
unknown filter types, without implying all execution constraints are implemented.
A metadata failure blocks dependent depth admission. An HTTP denial stops the
host; preserve all unattempted cases. Requests are observation snapshots, not
simultaneous fills or historical depth. The REST depth update ID is not an event
timestamp; preserve clock uncertainty rather than asserting exact source age.

No order-size sweep, fees guessed as zero, capital/return optimization or economic
claim. Fees, source history, custody/FX/transfer and access remain separate. At
most4requests/10seconds each/256KiB perbody, bounded total output and wall limit
in its eventual charter. After DEX claim, preserve179import/cap189 and its terminal
parent; do not change imported history again just because a claim was added.
The helper counts actual new claims automatically. Category is admission3/6.

Primary documentation checked before this proposal:
[General endpoints](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/general)
and [market endpoints](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market).
Metadata time and book source clocks differ; primary documentation is orientation,
not captured market evidence.
