# Triangle stream independent engineering review

September 11, 2026. **PASS for the single frozen engineering/research contract identified below.**
The final addendum supersedes the earlier staged pending findings; execution still requires the registered source commit and verified remote backup.
Only source, documentary qualifications and invented frames were inspected.
No network request, live quote, stored empirical quote or financial experiment
was executed. Original helper, run, registration and ledger bytes were not edited.

## Material findings and disposition

1. The initial stream classification used a strict binary-float factor greater
   than one (`triangle_stream.py`, initial replay classification around lines
   287–294). Invented equal bid/ask prices BTCUSDT=1, ETHBTC=13, ETHUSDT=13 at
   1,000USDT and zero fees produced factor1.0000000000000002 and a positive
   cash shadow despite exact currency parity. This would inflate qualifying
   counts and adjacent-bin streaks. The unfrozen stream layer now uses exact
   `Fraction(Decimal(literal))` wallet sign and per-leg size comparisons;
   frozen float-helper bytes remain diagnostic. An independent explicit-path
   Fraction oracle passes40 case comparisons, including a size deficit rounded
   to equality by floats. Numeric input bounds are being frozen before outcome.

2. Initial handshake retention wording promised bounded handshake bytes while
   the implementation retained Response.body and normalized allowed headers.
   Root accepted precise scope: full bounded header-block hash/count, allowed
   raw header lines and body bytes; arbitrary header values are not retained.
   Final source/charter consistency and refusal/oversized-header tests remain
   subject to final review.

3. Initial replay classified serverShutdown as generic malformed JSON and
   transport errors collapsed distinct named failures into exception classes.
   The current draft names shutdown notifications and declared protocol/close
   causes. Final tests must establish their effects without assigning a shutdown
   timestamp to bookTicker or parsing economic JSON while the socket is open.

4. Initial maximum-output preflight generated65,536-byte opcode9 PING payloads,
   which violate the125-byte control-frame limit. Such a writer stress test does
   not establish the worst permitted application workload. Worker was asked to
   retain a valid maximal-payload workload, high-precision full-grid arithmetic,
   and separate tiny-frame/chunk-pressure tests before final approval.

5. Malformed nested JSON below the64KiB message limit can raise an uncaught
   `RecursionError` during replay (24,007-byte invented nested-object payload).
   This prevents the promised unavailable-bin outputs. Worker was asked to
   handle parser recursion failure at the new message boundary and prove the
   whole fixed denominator survives. No frozen helper change is needed.

6. Header failure before a parsed HTTP Response bypasses header projection
   retention. A malformed/oversized header without a body then leaves no
   bounded prefix hash/count. Worker was asked for explicitly incomplete
   hash/count evidence in this path, without exposing arbitrary header values.

## Checks already supported

`check_triangle_stream_synthetic.py` uses independent literal Fraction arithmetic
and explicit directional paths; it does not use the implementation's expected
wallet answers. Its40 cases cover exact parity, positive/negative planted quotes,
zero displayed size and a sub-float size deficit. It also verifies exact100ms
right boundaries, exclusion of a message arriving one nanosecond later, admission
at exactly one second age, stale next boundary, disconnect boundary/tail and
43,200 retained bin/case subslots. Current report:
`triangle-stream-synthetic-review.json`; its source hash identifies the tested
intermediate bytes and must be refreshed against final source.

The reviewed design uses a single first-resolved TCP address, verified TLS and
Sans-I/O parsing in the main thread; no retry, proxy, compression, client ping,
orders or pre-capture financial JSON parsing appears in the inspected code.
Persisted raw chunks are reloaded one at a time with hash, count and sequence
checks. Duplicate IDs do not refresh age; fragments become observable at their
final fragment; stale/invalid/tail bins remain in the denominator. The separate
600-second wrapper invokes the previously reviewed sampled-RSS guard with512MiB
and two-CPU affinity. Sampling retains the guard's stated overshoot/lifecycle
limits; it is not a hard resident-memory ceiling.

## Claims not tested or admitted

No live availability, server timing, account applicability, latency, fills,
atomic conversion, expected profit, beta, annual frequency or strategy graduation
was tested. A positive local observation remains a conditional sampled state.
Missing/zero counts cannot reject timeless arbitrage availability. The full
fixed stream gate, unchanged ancestry/budget, all dependency pins, final35-output
lifecycle, worst permitted payload and60-second finalization proof remain pending.

## Post-fix staged addendum

The incomplete handshake prefix now has a count/hash-only receipt, and schema
`RecursionError` is caught by the new stream message boundary. Six targeted
synthetic tests passed for real Sans-I/O over fake socket/TLS, refusal/oversized
headers, parity, and deep-JSON full-output preservation. The independent40
wallet/fee/size oracle cases and chronology checks also pass after these fixes.
No identified code blocker remains in this inspected revision. Full current-
hash resource preflights and exact registration review are still pending.

Inspected stream SHA256: `6670aa4962d781c93b8cb674655e33d1172dd07faaed17120363da69fb89383b`.
This staged hash is not a final source-freeze approval.

## Final frozen-contract disposition

**PASS.** All six identified pre-result findings are resolved in the reviewed
new stream layer or precise charter scope. No frozen financial helper, previous
gate object or original lifecycle source changed. This disposition covers only
the named third/final triangle attempt after source commit, remote equality and
normal lifecycle admission. It does not approve another attempt or trading.

Exact reviewed identities:

- Gate SHA256: `ce6e02d9f789fac3cb289fa6371327c6d7403975ec1b32001ec27bd60be652cd`.
- Stream source: `6670aa4962d781c93b8cb674655e33d1172dd07faaed17120363da69fb89383b`.
- Test source: `78b9cdb21cc10975b2fb664ebd5f71f8fefa3adde3980e2f21e5afb75b830d56`.
- Charter: `de75b45038fc4516ae8f8ca360692bdad3a65a694725dacf776c70cdea40cc5b`.
- Canonical specification: `e7ff99c76a966c60dc84da630ec2d29bb4eb2a8597901f83078897452b639613`.

The serialized specification exactly equals the source default. All nine source
pins, three input byte hashes, charter hash and six original runtime pins match.
The predecessor news gate's existing families, datasets and experiments compare
unchanged. The new stream-definition dataset documents a local specification
observation, separately from the already exposed metadata window and future
actual connection clocks. Neither documentary window is fresh confirmation.
The two preceding triangle runs retain claim/complete files; unchanged family
cap3 and prior count0 allow this third claim only. Previous broader liquidity
search exposure remains recorded. The new gate declares exactly9cells and35
outputs; every one of eight series retains5,400subslots.

The final independent checker again passes40 explicit Fraction wallet, fee
drag and size comparisons plus chronology/denominator checks. Six targeted
real-Sans-I/O/fake-network, malformed-header/JSON and parity regressions passed
during review; the worker's full23-test result is supporting evidence, not an
independent financial evaluation. No synthetic preflight was silently rerun as
a real experiment.

All three durable preflight guard/result files were checked against the original
disposable ResearchRun output directories and pinned synthetic source bytes:

| Invented lifecycle | Outputs bytes | Raw receipts | Valid bins per case | Peak sampled RSS bytes | Finalization seconds |
|---|---:|---:|---:|---:|---:|
| Full grid, maximum admitted coefficient precision |31,741,039|16,200|5,400|96,989,184|3.5385|
| Valid application text to raw-byte cap |43,761,521|1,748|5,399|155,254,784|2.8983|
| Tiny controls to chunk cap |30,181,471|86,941|0|71,528,448|0.7699|

Each retains35files/43,200subslots, every chunk is at most1MiB, total outputs
are below64MiB and the exact600second/512MiB sampled guard exits successfully.
The raw-cap fixture retains20,961,635payload bytes and a named dropped event;
its final boundary is unavailable. The tiny-control fixture reaches the chunk
cap before100,000frames, as expected from serialized receipt overhead; no absent
bins are promoted. The explicit frame-count guard has a separate synthetic
check. These stress axes are bounded workload evidence, not an exhaustive
proof against every possible operating-system failure; hard failures preserve
the failed claim and already written chunks under the declared contract.

All source/admission, arithmetic and timing claims are limited as stated above.
Actual server behavior, quote freshness at the exchange, account fees/access,
execution and expected returns remain untested. Qualification uses exact
rational sign/size; displayed floating scalars can differ at roundoff boundaries
and must not replace the exact status or become aggregated trading PnL.
