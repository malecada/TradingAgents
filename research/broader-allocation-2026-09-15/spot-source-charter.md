# Fixed Binance USDC spot-source measurement

Experiment allocation-spot-source-20260915, admission3/6, discovery/exploratory.
Parent allocation-dex-source-20260915 must be terminal and preserved unchanged.
This is the next independently justified venue-source question, not a DEX retry.
No account, credential, VPN mutation, order, personal-data or paid request.

## Question and fixed requests

Does the single public Binance spot host supply the two fixed BTCUSDC/ETHUSDC
identities, current literal rule fields and two-sided depth snapshots needed to
prepare an unlevered USD-reported spot/cash book? Exact four URLs and order are
in spot-source-spec.json: server time, two-symbol exchangeInfo, BTCUSDC depth100,
ETHUSDC depth100. Four request cells and five outputs (four receipts,summary).
No extra pair, retry, substitute host, alternate quote asset or price-history fetch.
At most4HTTP requests. Each failed/unattempted cell is retained.

## Frozen field validation and dependencies

clock: positive integer serverTime in milliseconds, excluding booleans. This is
a clock observation only; it does not timestamp subsequent depth events.

symbols: exactly one each BTCUSDC/BTC/USDC and ETHUSDC/ETH/USDC; literal status
string and boolean isSpotTradingAllowed; unique filter names; valid nonnegative
Decimal strings for LOT_SIZE minQty/maxQty/stepSize and PRICE_FILTER minPrice/
maxPrice/tickSize (zero may disable a condition); NOTIONAL or MIN_NOTIONAL with
nonnegative minNotional and maxNotional if present. Retain all raw fields and
unknown filter types. These are literal syntax/identity checks, not a complete
filter implementation: applicability flags, disabled cases and range constraints
must be admitted for a later execution engine. No account-eligibility pass.

btc_depth/eth_depth: integer nonnegative update ID,1–100levels each side, exactly
two positive finite Decimal strings per level; bids strictly descending and asks
strictly ascending with unique prices; best bid strictly below best ask. Retain
full raw snapshot and summarize only level counts/top prices. No quantity/capital
sweep, cost estimate, round trip, realized fill, slippage or profit calculation.
REST depth has no admitted event timestamp; local request/retrieval time and
elapsed time are retained without claiming exact source age or simultaneous books.

Depth requests require both-symbol metadata validation and that symbol's status
TRADING/spot flagtrue. Missing/bad metadata, halt or false flag skips the dependent
request. Clock failure alone does not block other source fields. HTTP403/418/429/
451 stops further requests on the host. Other transport/schema failure is retained;
the next independent fixed request may proceed. Partial bodies never parse as
complete, and no case is dropped to manufacture source availability.

## Scope, accounting and cumulative allowance

Public USDC pair presence is not proof of Czech-account product access. The user
reports Finland VPN routing; no setting or account endpoint is inspected. Fees,
stablecoin USD valuation/yield, deposit/withdrawal, tax, historical spot/action
coverage, fill latency and capacity remain unavailable. Four complete fields
would support further source/engine work, not an implementability or financial
pass. Target10% and proposed2% benchmark value remain unchanged and unmeasured.
No PnL/log-return/convention calculation applies to this source-only check.

Retain179import and189cap verbatim from the DEX registration; the lifecycle counts
that claimed DEX attempt automatically. After this claim effective usage181/189,
admission3/6 leaves three admission, four development and one confirmation slots.
The original failed unclaimed custody launch remains charged and non-retryable.
The related44DeFi/178core histories and spent samples remain unchanged. No new
financial recipe or statistical comparison is admitted.

Follow source result classification: unknown/denied/bad data/source-qualified,
not economic failure or success. After independent result review proceed to
cash/FX/transfer-term admission using retained evidence. No repeated endpoint
probe or financial backtest follows from this snapshot alone.

## Execution, provenance and resource limits

Commit charter/spec/gate/sources before capture, then pass admission-only check.
Use existing resource_guard_v2.py at defaults120seconds/512MiB/twoCPU affinity,
main-thread synchronous helpers; cooperative65seconds,10seconds hard perrequest.
At most256KiB raw bytes perbody,2MiB total pretty-encoded receipts+summary. The
hard alarm spans DNS/connect/read; retain received prefixes on timeout/oversize.
No redirects,retries,application proxy variables,auth or decompression step.
System VPN remains as configured. Date/Content-Type headers only. All receipts
publish immediately before validation; raw bytes/base64/hash, status, endpoints,
attempt flags and UTC clocks survive later failure.

Inputs are the authored fixed spec and preserved core ancestry crosswalk, not
market observations. Registry window is the already exposed authored input
interval. New actual quote/clock observations are exploratory source outputs;
future financial registrations must import their observed timestamps as exposure.
Current depth is neither old backtest fill evidence nor untouched confirmation.
No raw store or historical gate is replaced.

Verify literal positive/zero-disabled filters, malformed/duplicate identities,
wrong quote asset, incomplete filters, booleans,NaN/nonfinite values, unordered/
locked/crossed books, denial propagation and all4cases. Complete no-network
synthetic lifecycle preflight under the same guard, independent source review,
then standard receipt verification plus independent reconstruction from raw bytes.
The broader offline suite and final targeted source tests retain actual scope;
no rerun of a historical empirical main is a test.

Primary documentation consulted before registration:
[General](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/general)
and [Market](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market).
These are public documentary schemas, not user-specific access or fee evidence.
