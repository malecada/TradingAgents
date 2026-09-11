# Triangle bookTicker stream: bounded documentary design

September 11, 2026. **A single finite local-observation/persistence screen is
feasible without full depth reconstruction or orders.** It is a distinct
premise test from the earlier one-off REST proxy. It cannot measure exchange
latency, prove simultaneous executable opportunities, estimate long-run event
frequency or validate profitability. No stream, quote, market API or account
was accessed. This is a proposed design, not a registration or implementation.

## Primary sources and exact scope

Two distinct official document URLs opened; zero search queries. Both returned
readable documentation. Cached find/extract calls added no new source URLs.
Access date September 11, 2026; precise retrieval clocks and source revision
dates were unavailable. No market outcomes or numerical example quotes are
adopted as evidence.

1. https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams
   redirects to
   https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-streams/~
2. https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/web-socket-streams.md

The endpoint-specific developer schema lists `u` updateId, `s` symbol, `b/B`
best bid price/quantity, `a/A` best ask price/quantity. It does **not** list
exchange event/trade time in this stream. The rendered example uses JSON
numbers for price/quantity despite schema string labels; the raw official
example uses strings. Freeze this typing discrepancy rather than silently
coercing unexpected data after capture. Best-price or quantity changes trigger
real-time updates, not a guaranteed fixed interval. Each message provides the
top level, so a local depth-delta reconstruction is unnecessary for this narrow
source question. No documented guarantee says successive bookTicker update IDs
are contiguous; jumps alone cannot establish packet loss.
[Endpoint schema](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-streams/~)

The raw official guide specifies lowercase stream names, slash-separated
combined streams and a stream/data envelope. Server ping interval is20seconds;
copy-payload pong is required within one minute. The limit is five incoming
client control/ping/pong messages per second, not five received quotes. A
connection lasts at most24hours and may receive serverShutdown before closure.
These protocol facts do not guarantee complete delivery or connectivity.
[Official raw guide](https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/web-socket-streams.md)

## Proposed fixed connection and capture

Exactly one TLS WebSocket connection attempt to:

`wss://stream.binance.com:9443/stream?streams=btcusdt@bookTicker/ethusdt@bookTicker/ethbtc@bookTicker`

Use URL subscription only. No extra subscription queries, REST bootstrap,
alternate port/host, proxies, credentials, reconnect, data refresh or orders.
Normal ping/pong/close protocol responses are permitted and documented as
control traffic, not hidden source attempts. ServerShutdown, denial, close,
frame/parse/resource error ends acquisition; retain the remaining planned bins
as unavailable. Do not obey generic reconnect recommendations by silently
adding a second attempt. Client library default auto-reconnect and unbounded
queues must be disabled; handshake response metadata, compression and frame
limits must be frozen and synthetically tested.

A concrete budget fitting the proposed ten-minute maximum: **540seconds from
the initial connection attempt**, followed by at most60seconds to close,
replay and finalize, under a hard600second/two-CPU/512MiB sampled-RSS guard.
The start includes handshake and first-message delay. Twenty MiB raw cumulative
application payload cap,64KiB maximum reassembled message, bounded control
payloads/queues and separately capped serialized outputs. Raw cap exhaustion
is an unavailable tail, not a sample that quietly shrinks until favorable.
No endpoint probe before the registered attempt. All financial/cycle arithmetic
runs only after the fixed acquisition phase closes, even if capture fails early.

Persist each received complete application message with exact bytes, receipt
sequence, monotonic arrival and UTC observation clock before schema use; retain
malformed/control/unknown events rather than discarding them. Prefer a bounded
append-only binary/framed raw file plus compact receipt index to avoid duplicating
base64 payloads repeatedly. Raw20MiB does not imply all outputs20MiB: freeze a
separate total-output cap, for example64MiB, and prove actual serialized sizes
in the full synthetic lifecycle. Abrupt process failure retains claim/partials
and the intended denominator without pretending final bins were written.

## Frozen admission and time denominator

Use exact envelope/symbol mapping for the three streams. Require literal
integer nonnegative updateId, positive finite prices, nonnegative quantities
and noncrossed bid/ask. A zero best quantity is retained as unavailable for
positive required size, not interpolated. Accept decimal strings only if this
schema choice is frozen; numeric wire fields can instead be retained as typed
unavailable according to the documented discrepancy. Unknown fields remain
raw. Repeated IDs with identical payloads are duplicates, not new observations;
conflicting repeats or regressions must follow an explicit invalidation rule.
An ID jump is diagnostic only. Update IDs cannot align the three symbols.

There are **5,400 fixed100ms bins**, starting at the initial connection attempt;
none is dropped for warm-up, silence, overflow, disconnect or missing symbols.
For each bin, replay only messages already received by its right boundary.
Choose a single predeclared maximum local quote age, such as one second, with
no later age/window sweep. Before a symbol's first valid update its state is
unavailable. A stale or invalid state makes the whole triangle unavailable.
Record missing/invalid/stale/resource/disconnected reasons separately.

This is age since local observation, not age of the exchange quote or measured
network latency. A quiet stream can represent an unchanged book; excluding it
after the age limit is conservative source qualification, not proof of an
outage. Generic timestamp defaults cannot create absent bookTicker timestamps.
UTC/monotonic clocks can diagnose local jumps only. Best quantities are base
quantities for the pair, to be checked against literal saved asset metadata.

## One registered post-capture screen, not a new profit book

Retain both cycles, both1,000/10,000 starting-capital scales and unchanged
zero/10bp-per-leg cases: **43,200 intended bin/case cells** if all eight cases
are represented per bin. Zero fee is diagnostic; the primary premise is the
unchanged cost-qualified condition. Freeze the previously reviewed directional
conversions and exact fee-in-output-asset convention, with continuous required
base quantity tested against the relevant best bid/ask quantity on every leg.
No lot rounding, account entitlement or full-depth fill is implied; if those
are needed for a stronger claim they are explicit missing inputs.

Report qualified/unqualified/unavailable bins using both the full planned and
observed-valid denominators. Consecutive qualifying bins are **local sampled
state persistence**, not guaranteed uninterrupted exchange opportunity duration;
conditions may change inside a100ms interval. Do not multiply overlapping bins
by capital to create repeatable PnL, independent trades or annual returns.
Missing bins break streaks. Retain all states, not only positive conditions;
report a size-unavailable condition separately from a negative unit factor.

This resolves an information gap the one-off proxy cannot: whether cost- and
visible-size-qualified local observations recur or span adjacent fixed samples
within the one declared interval. Existing fee failure does not make that
question logically uninformative because the earlier sample supplies no
temporal frequency estimate. Conversely, a ten-minute zero count would only
bound this sampled episode, not prove economic impossibility; a positive count
would justify at most an execution-evidence dependency, never orders or
strategy graduation. No expected-return CI, beta, power or annual relevance
claim is available from overlapping quote bins.

## Admission recommendation

Reasonable as the **third and final triangle/MAProw5 question**, if root can
freeze and independently verify transport, replay, byte/resource limits and
the denominator in one lifecycle. Source capture and post-capture premise
screen must be registered together as this single investigation; no uncounted
live probe or subsequent rescued book. Its purpose is observability and
conditional persistence, not true latency/fill measurement. This narrower
design avoids the substantial depth-reconstruction requirement discussed in
the interim coverage review while preserving the reasons it cannot establish
profitability. No new family budget is created by calling it a stream test.
