# WBETH independent raw/source review

September 11, 2026. **PASS for the frozen source-schema question.** Both
requests completed; all 91 daily bars pass the specified clock, field, OHLC and
nonnegative-volume/trade-count checks. No zero-activity row was identified by
the frozen volume-or-trade-count rule. No return, ratio, hedge quantity, PnL,
staking attribution or executable-liquidity calculation occurred.

Independent checker: [check_wbeth_inputs.py](check_wbeth_inputs.py), using only
the earlier independent checker's strict JSON/hash helpers, never the collector.
Machine result: [wbeth-inputs-review.json](wbeth-inputs-review.json).
The checker issues no network calls. Its read-only Git calls verify committed
source bytes, not remote-preservation status.

Source `ea63d7b1aa9176faeddd7640eef09af1a2bdecc5`, frozen gate
`38f0038210d7e368c7bf807473500f1accb723c9741b2ef7e322cb6fa1a0d4ea`
and all pinned source/runtime/charter/spec hashes match local and committed
bytes. Individual receipts equal the aggregate, and exact registered URLs,
literal attempt/completeness flags, HTTP status, body byte counts, strict
base64/SHA256, strict UTF-8 JSON and ordered request/retrieval clocks verify.
The four output files match completion hashes and the two-cell denominator.
Receipt bytes establish content consistency; immediate-write ordering is
supported by the pre-reviewed implementation and synthetic lifecycle.

Raw bodies total **20,794 bytes**, four outputs **69,105 bytes**. Actual capture
spans **09:39:02.312942–09:39:03.433509 UTC**. This is distinct from both the
local request-definition window and historical bar time. Bar opens cover
April 1–June 30, 2026, with exact consecutive daily millisecond boundaries and
July 1 exclusive end. The quarter remains exposed exploratory data; new
acquisition does not create a fresh holdout or prove historical publication time.

The sole metadata symbol is WBETHUSDT, base WBETH/quote USDT, TRADING, with
literal spot-enabled true. All raw symbol fields and **11** distinct filter
objects are retained. Selected literal current values are:

| Filter | Literal returned fields |
|---|---|
| LOT_SIZE | minQty `0.00010000`, stepSize `0.00010000`, maxQty `92233.00000000` |
| MARKET_LOT_SIZE | minQty `0.00000000`, stepSize `0.00000000`, maxQty `19.80402541` |
| NOTIONAL | minNotional `5.00000000`, maxNotional `9000000.00000000`, applyMinToMarket true, applyMaxToMarket false, avgPriceMins 5 |
| PRICE_FILTER | tickSize `0.01000000`, minPrice `0.01000000`, maxPrice `999996.00000000` |

No zero-valued market-lot field is converted into an assumed order increment.
Current filters, symbol permissions and precision do not establish historical
filter applicability, the user's account eligibility, fees or fill conditions.
Taker-versus-total consistency was not part of the frozen admission rules and
is not implied by this pass.

The saved resource report verifies exit zero, no limit reason, elapsed time
below 120 seconds and sampled aggregate RSS below 512 MiB. Exact measurements
are preserved in the machine review and original resource report.

These inputs can support a separately registered conditional market-value
book with a spot-sale exit, subject to its own financial accounting and risk
review. They do not validate contractual ETH delta, redemption valuation,
validator reward attribution, profitability or low future crypto exposure.
No alternative dates, interpolated bars or replacement sources were used.
