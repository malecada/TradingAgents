# Fixed dated-contract daily mark admission

Proposed experiment dated-mark-20260911; same dated-basis family and mechanism,
parent dated-book-amended-20260911. This is a distinct source question after
five consumed total administrative attempts (one known prior and four program
claims, including two failures and the sole consumed repair amendment). A new
independently reviewed +1 information-value certificate is required. Neither
the original cap4/prior1 nor the old consumed +1 certificate can be rewritten.
Funding-carry ancestry and unknown broader multiplicity remain. No claim exists
for this proposed experiment yet.

## Information value and competing explanations

The negative spot/dated book does not measure a long-dated/short-perpetual book:
the latter has two collateralized derivative legs and one funding cashflow.
Matched quantities and a frozen notional ceiling would distinguish it from a
leverage or allocation rescue. At equal quantities and dates its gross cash is
algebraically related to the earlier funding and dated spot books, so it is not
independent confirmation. A separate development question could measure whether
funding offsets the relative-basis change and two-derivative costs.

Saved sources already support a conditional terminal-cash diagnostic for
BTCUSDT_260626 and ETHUSDT_260626 over May1 through June25,2026. Dated archives
contain trade bars, while the perpetual sources contain trade and mark bars
plus authentic funding events with event marks. The missing dated daily marks
prevent symmetric daily mark valuation. Two fixed requests can resolve that
specific data gap before implementing a new financial book. No new date, symbol,
expiry, direction or threshold is selected by results. Current expired-symbol
retention is unpromised; unavailable responses are not evidence against the
spread mechanism. Daily marks will not establish intraday liquidation or actual
account requirements.

This source question outranks another spot-carry, triangle or WBETH parameter
variant because it supports a distinct funded instrument structure. The options
entry prerequisite remains first in execution order. Detailed ancestry and one
primary documentation URL are retained in reviews/coverage-after-stream-options.md.

## Exactly two prospective source slots

GET https://fapi.binance.com/fapi/v1/markPriceKlines with fixed parameters:

- symbol BTCUSDT_260626 or ETHUSDT_260626, in that order;
- interval1d; startTime1777593600000; endTime1782431999999; limit100.

No retries, alternate host, redirect, proxy, credential, replacement symbol,
archive fallback, shorter interval or wider dates. A same-host denial suppresses
the second request while retaining its unattempted receipt. Each request has a
20second whole-request deadline and256KiB raw cap plus one detection byte, with
truncated prefix retained and never admitted as complete. Persist each raw
response receipt before schema parsing. A new narrowly scoped transport may
reuse reviewed bounded logic; do not mutate a frozen ancestor's constants.

Each of two source cells has56 fixed daily timestamp slots. Require strict JSON
array,12 fields per row, exact integer millisecond daily opens/closes, ascending
unique timestamps, no out-of-window rows, finite positive OHLC and consistent
low/open/close/high. Price literals are bounded to64characters and adjusted
exponent[-32,32]. Retain duplicate/unexpected/malformed observations as explicit
forensics. Missing days remain missing; no filling or dropping the denominator.
Fields5 and7–11 are documented ignored fields; retain their raw bytes but do
not use their zero values to reject mark bars as inactive trades. All56 rows
and no ambiguity are necessary for a complete source cell.

The source specification and its local document observation are frozen before
requests. Actual request/retrieval clocks belong to the new capture; historical
bar timestamps cannot stand in for observation time. Public availability does
not establish account access, historical fee/lot/margin rules or fills.

## Bounds and outputs

One foreground registered attempt, two CPUs,512MiB sampled aggregate RSS,
45seconds cooperative capture and120seconds hardwall including retention,
two requests and no retry. Four immutable
JSON outputs: btc-dated-mark-receipt.json, eth-dated-mark-receipt.json,
capture.json and admission.json. Limit actual lifecycle encoding to4MiB total;
bound each normalized source projection to512KiB before write. Keep two source
cells and112 daily subordinate
slots even for denial, timeout, overflow or malformed data. Stored raw bodies
must not be duplicated in every normalized row. No return, funding sum, price
spread, quantity, hedge, beta or performance calculation occurs in this source
run. Expected profit, confidence, power, relevance and graduation are unavailable.

Synthetic proof covers clocks, complete/partial/extra/duplicate/reordered bars,
ignored zero fields, OHLC errors, nonfinite/deep JSON, bounded transport prefix,
first-source denial, exact output/cell/slot counts and worst admitted payload
under the exact guarded lifecycle. Independent source and extension reviews,
committed gate/certificate and verified remote freeze precede actual acquisition.

## Decision and continuation

After the sole capture, independently reconstruct raw schema, chronology,
subslot/source counts, output hashes and resource use. Record what became
available and what remains unknown; update decisions/findings/state/map and
verify branch backup. A full source result supports a separately justified,
registered matched-quantity long-dated/short-perpetual development book.
An unavailable result still leaves the narrower existing-data terminal-cash
question for explicit information-value review; missing marks alone do not make
that arithmetic impossible. Neither outcome automatically grants another
attempt, implies the inverse-direction trade, changes the reserve/notional rule,
or supports confirmation. Reassess all mapped affordable gaps before stopping.
