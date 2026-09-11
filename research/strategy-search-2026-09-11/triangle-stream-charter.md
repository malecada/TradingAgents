# Fixed local triangle observation persistence

Proposed experiment triangle-stream-20260911, parenttriangle-proxy-20260911,
familyspot-triangular-conversion. Third and final new triangle/MAProw5 claim.
The old static snapshot and all OFLOW/passive/H6/liquidity search history remain
exposed. No budget, fee assumption or statistical multiplicity is reset.

## Distinct question

The one-off REST proxy found a small positive gross discrepancy erased by
assumed fees, but cannot describe temporal availability. Does a single fixed
interval contain locally observed, cost- and visible-size-qualified triangles,
and do qualifying sampled states appear at adjacent100ms grid boundaries?
This is an observation/persistence premise test, not a filled-trade book or
long-run frequency estimator. A locally positive factor can result from genuine
relative-price differences, asynchronous arrival, delayed delivery or an
unusable top quote. Absence in this interval cannot prove timeless absence.

The primary documentary design in reviews/triangle-stream-design.md identifies
self-contained bookTicker quotes for the exact same three pairs. Full depth
reconstruction is unnecessary for this narrow top-level test, so one bounded
stream is more informative than another isolated snapshot without constructing
a trading system. Best quantities do not prove fills or an atomic conversion.
No additional statistical pair, venue, fees or quote selection is introduced.

## Exact capture

Exactly one initial TLS WebSocket attempt to the URL in the frozen specification,
containing btcusdt@bookTicker, ethusdt@bookTicker and ethbtc@bookTicker at
stream.binance.com:9443. No live probe before registration, alternate host/port,
proxy, credentials, HTTP redirect, reconnect, REST bootstrap or orders. Use only
the first resolved TCP address; connection refusal is not permission to try
another address. Normal protocol-required pong and close traffic is permitted. The documented
server ping is every20seconds; echo its payload in pong within one minute.
Compression/extensions and implicit client pings are disabled. The frozen
Sans-I/O library runs in the main thread over a verified TLS socket; no hidden
worker thread, unbounded queue or financial parsing during capture.

Capture540seconds from immediately before the initial connection attempt,
including DNS/handshake delay, with60seconds reserved for closing, replay and
finalization. Overall guard600seconds,512MiB sampled aggregate RSS, two CPUs.
The stream source specification pins handshake/line/header/body/socket limits,
64KiB maximum application message,20MiB cumulative raw bytes including control
and handshake,100,000 frame events and32raw JSON chunks capped at1MiB each.
Any exhausted cap or protocol/disconnect error ends acquisition and leaves the
remaining planned grid unavailable; no data-driven stopping or retry.

Retain exact incoming application/control-frame payload bytes, frame opcode/finality,
monotonic arrival, UTC observation and sequence before schema/economic use.
These are decoded frame payloads, not retained TLS or WebSocket wire headers.
Write immutable raw chunks throughout capture and flush the final partial chunk
on ordinary termination; emit explicit empty placeholders for unused chunks.
A hard-killed process may retain only its claim and completed raw chunks, which
is a failed attempt rather than a silent replay. Preserve bounded handshake
body bytes and allowlisted raw response header lines. Retain byte count/hash
of the whole bounded header block, while unallowlisted header values are not
published; do not claim the full header block was retained. All JSON
schema and conversion calculations occur only after the socket is closed.
The serverShutdown application JSON event is consequently recognized during
replay; an actual protocol/socket closure can end acquisition earlier.

## Frozen source and replay rules

Revalidate the saved hash-pinned triangle metadata identity and its raw/schema
receipts. The old quote snapshot never substitutes for stream prices. Every
selected stream envelope must match its symbol. Require nonnegative integer
updateId no greater than2^63−1, finite strictly positive decimal-string prices, nonnegative decimal-
string best quantities and noncrossed quotes. Numeric strings are at most64
characters, with adjusted decimal exponent within[−32,32] (zero quantities
permitted); out-of-scope representations remain unavailable. These bounds keep
exact arithmetic/resource use finite; they are not a fitted price filter. The official rendered numeric
example conflicts with its string schema; numeric wire fields remain typed
unavailable under this fixed string-only rule. No type coercion after outcomes.

No exchange event timestamp exists in the documented payload. UpdateId is not
a clock; nonconsecutive jumps do not establish message loss. Identical repeated
IDs/payloads do not refresh observation time. Conflicting repeats or regressions
invalidate the symbol until a strictly greater valid ID arrives. Malformed or
unmappable events conservatively invalidate all three states until each receives
a new valid update; retain every raw event and diagnostic reason. Fragmented
messages become observable only upon complete reassembly at the last fragment's
arrival. Protocol control data is retained but does not refresh quote states.

Use5,400 fixed100ms samples at right boundaries after the original capture
start. At each boundary use only fully received messages whose arrival is no
later than that boundary. No forward fill from a future message or warm-up drop.
All three quotes must have last valid local arrival at most1second old. No
additional arrival-skew filter is selected. These are latest locally observed
states, not a contemporaneous exchange snapshot. Quiet unchanged quotes may
be excluded by the age rule; this is not proof of a feed outage. Disconnect,
invalid, stale, missing, resource and source-identity causes remain separate.
No bin after acquisition ends may reuse the last known quote as live evidence.

## Conversion and denominator

Use the unchanged triangle_bound.py directional wallet algebra: both cycles,
1,000/10,000 initial USDT, fees0 and0.001 on each acquired asset. Zero fee is
only a diagnostic. Continuous full-notional conversion prices every leg at the
observed best side; required base quantity is compared with that side's best
quantity. Zero displayed quantity makes the size screen fail, while the unit
factor remains calculable. No lots/dust, partial sizing, rebates, deeper-book
fills or abstention wealth claim is introduced.

There are nine top-level lifecycle cells: one transport result and eight fixed
case series. Each series retains all5,400 planned subslots, totaling43,200
bin/case subslots. A series is structurally complete only if at least one bin
has calculable admitted quotes; otherwise it is unavailable. Every subslot
keeps its own status/reason; structural completion is not a profitable verdict.
Transport success and conditional calculability of leading bins are separate,
so an early disconnect cannot erase previously captured evidence or its tail.

For each admitted bin retain gross/after-fee factors, same-snapshot simple cash
proxy and invalid log-factor arithmetic shadow, fee decomposition and required/
available best-size checks. Size-insufficient bins remain calculable but fail
the necessary condition. Qualification and all per-leg size comparisons use exact rational arithmetic
from admitted literal decimals and exact fees0 or1/1000. The unchanged helper
float cash/factor/log/fee outputs are diagnostic approximations; a float
rounding artifact at exact parity cannot create a positive sample or streak.
Qualified means exact after-fee factor>1 and all three exact sizes sufficient. No summing overlapping bin proxies into PnL/trades.
Retain counts against both the full planned and quote-admitted denominator,
missing reasons, and longest consecutive sampled qualifying streak. Missing or
unqualified bins break streaks. A streak is a grid property, not uninterrupted
exchange opportunity duration or measured execution latency.

No expected-profit interval, power, BTC/ETH beta, annual relevance or strategy
graduation can be inferred from overlapping quote observations. Full-capital
intermediate BTC/ETH inventory, partial-fill exposure, actual fees/access and
execution risk remain unverified. A positive sample justifies at most a
separate execution-evidence dependency; it does not authorize orders or paper.
A zero count closes only the sampled episode's necessary-condition claim.

## Output/resource proof and continuation

Thirty-five JSON outputs:32rawchunks, capture.json, bins.json and summary.json,
capped at64MiB combined actual lifecycle encoding. Replay must stream one raw
chunk at a time; compact bin evidence must not retain every repeated full trace
in memory. Raw-byte, frame-count, chunk-size and global-output bounds are
separate and all tested. Source/spec/charter/gate are committed and remotely
verified before the only real connection.

Synthetic tests must prove both directional wallet/size algebra and preserved
fee conventions; planted qualifying/negative/insufficient-size states; exact
right-edge chronology; stale/duplicate/regression/fragment/malformed/clock-gap
handling; handshake refusal/oversized/control frames; single connection/no
retry; early-resource tail; fixed9/43,200denominators and all35outputs. Run the
exact guarded lifecycle at full5,400-bin scale and worst permitted payload before
independent engineering/gate review. No actual network fixture is permitted.

Afterward independently reconstruct raw/replay/conversions and receipt/resource
proof, diagnose results, update decision/map/findings and verify branch backup.
This consumes the last triangle allowance; it does not imply a fourth attempt.
Reassess the complete map and remaining affordable dependencies with independent
review. Do not call one interval strategy validation or research exhaustion.
