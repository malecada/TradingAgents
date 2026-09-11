# Triangle stream charter: documentary consistency check

September 11, 2026. Reviewed root draft `triangle-stream-charter.md` against
the two primary sources already recorded in `triangle-stream-design.md`.
Zero new document, stream, quote or API requests. No financial arithmetic,
implementation execution or independent accounting approval occurred.
Inspected draft SHA256:
`46f29be25a12b39a6727971eebbab9c28dc52e0c97211e4caeb4a745736df259`.

**Documentary scope is consistent**, subject to the explicit transport wording
clarifications below. The charter accurately treats bookTicker as self-contained
best-price/quantity updates, without a documented exchange timestamp. UpdateId
is not a clock, and nonconsecutive values do not prove message loss. The one-
second arrival-age rule is a declared local qualification, not exchange latency,
true quote age or an outage test. Adjacent100ms samples are a grid property,
not uninterrupted exchange persistence. The numeric rendered example/string
schema discrepancy is preserved through a predeclared string-only admission
rule rather than resolved after outcomes.

The fixed combined-stream symbol set and single connection are compatible
with the official URL/envelope protocol. Choosing one resolved TCP address,
disabling compression/client pings, refusing reconnects and bounding raw chunks
are research implementation constraints, not exchange guarantees. A denial or
failed connection legitimately consumes this fixed attempt. The9top-level
cells and43,200subslots are transparent source/conditional-evaluation accounting,
not43,200 independent trades or profit observations. No long-run frequency,
economic sign, expected return or graduation is implied by the documentation.

## Clarify before source freeze

1. State the documented protocol duty explicitly: server ping every20seconds,
   prompt pong copying the ping payload, with disconnection if a pong is not
   received within one minute. These protocol responses may occur during capture
   even while all JSON schema/economic parsing waits until socket closure.
2. State that `serverShutdown` is an **application JSON event**, not a WebSocket
   close frame. Under this charter it will be recognized only during replay.
   Capture can still end on the actual protocol/socket close; no early JSON
   inspection or automatic reconnection is implied. In replay, distinguish the
   saved shutdown notification from a selected quote and preserve its diagnostic
   effect without assigning its event timestamp to bookTicker quotes.
3. Match raw-retention language to implementation: Sans-I/O may expose frame
   payload bytes and frame metadata, not the complete wire header/masking/TLS
   record bytes. If only payloads are retained, say **exact received payload
   bytes plus opcode/finality and local clocks**, rather than claiming complete
   wire fidelity. Preserve fragment boundaries if that is what raw receipts
   claim; complete-message observability remains last-fragment arrival.

These clarify transport/provenance claims; no change to symbols, fees, elapsed
window, financial cases or statistical interpretation is requested. The source
specification was not yet present at the inspected expected path, and no
transport implementation or gate was reviewed here. Byte/chunk/output limits,
DNS/socket deadline enforcement, control-frame handling and full synthetic
lifecycle remain separate engineering-review requirements. Documentary
consistency does not certify resource bounds or cash algebra.

Primary source identities remain:

- https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-streams/~
- https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/web-socket-streams.md

No economic outcome, stream availability or account access was observed by
this check. It is not permission for a fourth triangle attempt.
