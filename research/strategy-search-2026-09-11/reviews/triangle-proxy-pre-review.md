# Triangle static proxy runner pre-review

September 11, 2026. Final disposition: **PASS for the frozen proxy gate and
guarded run below**, after the preserved source-consistency fixes.
Review scope: `triangle_proxy_run.py` and `tests/research/test_triangle_proxy_run.py`,
invented source envelopes only. No saved live market inputs, network request or
empirical evaluation occurred. No implementation or shared gate/state was edited.
Eleven synthetic tests pass in 0.05 seconds. The previously reviewed engine is
unchanged: `triangle_bound.py` SHA256
`ff52dd58d2a60aa939997b64dde3ce77bc57857052257fc52820327501f9415a`.

## Required fixes before gate freeze

1. `decode_sources` checks only that an admitted parent cell's status is
   complete. It does not reconcile the parent's normalized metadata/quotes
   against the result reconstructed from the raw receipt. An independent
   invented probe inserted contradictory `quotes` into the ticker parent cell;
   all eight proxy cells still completed. The synthetic fixture itself supplies
   only id/status admission cells, so the existing suite cannot test substantive
   parent consistency. Raw reconstructed quotes drive the arithmetic, which
   avoids selecting those contradictory prices, but the claimed admitted-parent
   chain is not verified. Require exact comparison against the independently
   re-parsed complete result (including its id), or an equally explicit pinned
   content reconciliation. Preserve optional-cell unavailability instead of
   treating contradictory optional content as complete.

2. Receipt `body_complete` is checked by truthiness, and `attempted` is not
   checked. An invented ticker receipt with `attempted=False` and
   `body_complete="false"` still admits all eight proxy cases. Require literal
   true attempted/completeness markers for an admitted HTTP source, with proper
   numeric status/byte-count types. A fabricated malformed marker must not
   become a successful source merely because the embedded body parses. Add
   required and optional source regressions preserving all eight case identities.

These are source-integrity defects, not observed financial failures. The run has
not executed. Fixing them before gate freeze changes no hypothesis or outcomes.

## Other reviewed behavior

The runner verifies the frozen six-request specification and exact six-cell
parent identities. It decodes strict base64 and checks body SHA256/length/cap,
request identity and raw schemas through the pinned source parser. Duplicate or
missing parent identities fail the full denominator; recoverable exceptions
produce unavailable source status. The registered lifecycle is responsible for
exact input/source hashes and should pin all imported helper modules.

Exchange metadata and the batch ticker are the only required sources for this
forced static calculation. Optional time/depth failure stays explicit without
substituting prices, claiming alignment or blocking an otherwise defined ticker
proxy. Required failure marks all eight financial identities unavailable. The
fixed engine retains finite arithmetic checks and unavailable cases rather than
propagating invalid numeric results; it is not modified by the wrapper.

Every case retains no-graduation, execution-unavailable and inference limits.
Expected-return confidence, power, market beta, annual relevance and execution
frequency remain unavailable from one asynchronous snapshot. The output expressly
states that forced full-notional values are not upper bounds on wallet wealth
with abstention, partial sizing or residual cash. Both directions/capitals/fee
scenarios remain the fixed eight correlated proxies, not independent trials.

Final admission must freeze the exact repaired runner and imports, raw parent
input hashes, charter/gate, source exposure and eight cells. A source-only input
capture's successful receipt is not proof of economic viability. Optional depth
admission cannot establish simultaneous fills; no funding, current-price refresh,
lot-rule extrapolation or future return estimate is introduced by this review.

## Fix verification — both findings resolved

Reviewed runner SHA256
`2b5ffb4b9d109698fcb52ff345ff95d9840373e5f75e0d01471a09b7757d231e`;
tests SHA256
`ee56e7efb0525faaca0057b4e69dbcf213295349b0eb2de06d84549713e29840`.
Independent rerun: 22 synthetic tests pass in 0.06 seconds; no empirical
inputs or network calls.

Complete normalized parent cells now must equal the raw re-parsed result plus
the exact id under canonical JSON comparison. This preserves boolean-versus-
number distinctions that ordinary Python equality can erase. Required mismatch
invalidates all eight proxy cells; optional mismatch remains an explicit source
unavailability without inventing fills or substituting a different quote.
The fixture now carries full parser admission output rather than id/status only.

Successful source receipts require literal true attempted/completeness flags,
exact integer HTTP status 200 and body byte count, and error null. Hash/length/
identity checks remain. Required and optional malformed flags/normalization
regressions pass. The fixed calculation engine is unchanged. Both original
findings are resolved; final frozen charter/gate/source-input admission remains
a coordinator step before any real-data evaluation.

## Final source, resources and gate — PASS

Final runner SHA256
`0205b9ea53fde2125b774137fc20e811ebb276b7b3240d1a2f9016fb8a020fd8`
adds an actual lifecycle-pretty-encoded 2 MiB output check before publication;
the calculation engine remains the previously reviewed hash. Independent
synthetic rerun across runner and lifecycle files: **24 tests pass in 2.03
seconds**, including actual CLI/lifecycle writes from six padded invented 5 MiB
source envelopes under the 512 MiB/two-CPU/120-second guard. No live-source
arithmetic was run by this reviewer.

Gate `gates-triangle-proxy.json` SHA256:
`e5981da6917982c7d845e885ff552963f344a48cab3b67f815edce616a1b629b`;
charter SHA256:
`b84f308a8a53325fcbc64d2bd1cb7fc9b80241f0bb0fb563f40899b099cceb39`.
All pinned runner/engine/parser/helper/transport/guard/runtime/lockfile,
charter and raw input digests match local bytes. Every ancestor experiment,
family and dataset matches `gates-triangle-inputs.json` exactly. Parent is the
completed source capture; eight frozen direction/capital/fee cells and one
`proxy.json` output are declared. No old-family budget or source object changes.

Input window September 11, 09:10:25.404644–09:10:29.052054 UTC matches only
the saved parent's first request and last retrieval clocks; exposure is explicitly
`exposed`. Those clock fields were checked without inspecting quote fields or
computing market outcomes. Unlike the source-definition bookkeeping window, this
is actual first-observed parent-source timing, still not simultaneous matching-
engine quotes or fresh confirmation.

The frozen charter correctly distinguishes a conditional unit-factor screen and
forced full-notional cash proxy from a universal wallet-wealth bound. Optional
depth/time cannot establish fills; actual filters, residual cash, partial fills,
fee applicability, expected-return uncertainty and annual relevance remain
unavailable. Original inconsistency findings are resolved before any economic
execution. No remaining pre-result blocker was identified; coordinator commit,
remote preservation and independent post-result arithmetic review remain required.
