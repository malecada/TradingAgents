# Independent Q1 actual-result review

Disposition: **PASS for the qualified source observations.** No measurement
defect requiring another Q1 execution was found. This result does not admit a
financial book, yield estimate, chain ranking or implementable strategy.

Reviewed run: `research_runs/defi-depth-q1-20260915`.
Committed source: `4c098578eccdb6736b99dd0005b15a9719ff0ee5`.
Review date: September 15, 2026. No network request or financial experiment was
executed during this review. Only this separate review document was written.

## Independent reconstruction

The review decoded all129 retained raw response bodies directly from base64,
without calling the capture parser or rerunning the source experiment. Checks
covered raw lengths/SHA256, unique JSON keys, envelope IDs, literal registered
URLs/methods/calldata, ABI word lengths and canonical padding, canonical block
hash arguments, request/retrieval chronology and result classifications.

All129 requests returned complete HTTP200 bodies. Forty contained explicit
JSON-RPC historical-state errors:36 with code -32000 and4 with code -32603.
An HTTP success therefore did not become an admitted state. The eighty successful
state payloads contained160 independently decoded ABI words; all expected
identities and decoded result artifacts matched. The remaining nine successful
request cells were chain identities and block headers.

| Scope | Complete cells | Unavailable cells |
| --- | ---: | ---: |
| Ethereum |25|22|
| Base |47|0|
| Arbitrum |25|22|
| Total |97|44|

The forty unavailable historical calls were twenty Ethereum and twenty
Arbitrum state calls. Four dependent coherence cells were also unavailable.
Every registered chain, epoch and field remains in the141-cell denominator.

Reconstructed raw bytes total100,951. The129 attempt records,129 receipts,
129 parsed request results,12 coherence results and summary give exactly400
outputs. All400 file hashes match the terminal manifest; all141 separate cell
results match the summary and terminal status inventory. No extra or omitted
output file was found.

## Anchors and source coherence

Historical block number/hash/timestamp matched the exact predecessor anchors:
Ethereum21,000,000; Base20,000,000; Arbitrum280,000,000. The finalized responses
were Ethereum25,983,967, Base51,349,610 and Arbitrum505,471,842. Their clocks
followed the corresponding historical anchors and did not exceed receipt time.
All120 state requests used the appropriate hash with requireCanonical=true.
Finality remains the provider's assertion; it was not independently proved.

All admitted Aave and LP identity/configuration comparisons matched their fixed
values. Recomputing scaled supply times normalized income using quotient and
remainder arithmetic gave these total-supply residuals in base units:

| Node | Residual |
| --- | ---: |
| Ethereum finalized |-1|
| Base historical |0|
| Base finalized |0|
| Arbitrum finalized |-1|

All fall within the frozen one-base-unit tolerance. This establishes only the
registered supply identity. The one-unit differences reinforce the need to
establish deployed aToken rounding conventions before financial accounting;
they are not evidence of withdrawable profit or a Q1 measurement defect.

The four available LP coherence nodes passed the registered sqrt-price bounds,
tick domain and oracle cardinality/index checks. The reported active-liquidity
flags matched the raw integers. Full tick/sqrt consistency, boundary invariants,
historical fee accounting and executable withdrawal or swap capacity were not
established by those limited checks.

## Timing and preservation

The first request began at2026-09-15T16:24:02.670365+00:00; the final receipt ended
at2026-09-15T16:32:58.981051+00:00. Every request followed the preceding receipt;
all clocks lay inside the claim's start/end interval. The reported capture
duration was541.412582527 seconds, with no aggregate elapsed-time kill.

The actual claim source and design source agree. Registered source files match
both committed bytes and current bytes. Charter, inputs, ordinary runtime,
registration and claim hashes match their frozen bindings. The original DEX
claim/output, old allocation closure and both ancestry crosswalks remain exactly
the pinned input bytes. This is not a new audit of all81 original preservation
anchors or an external-backup verification.

Exactly one actual claim exists in the new source family. Its imported prior1
plus Q1 gives2/3 source-family attempts used; successor source slots are1/6.
The original allocation remains188/189. The imported DEX predecessor is already
inside188 and is not added again. Related44 DeFi records remain overlapping
history; these administrative counts are not independent statistical trials.

## Qualified Q2 progression

Base supports a cheaper next source question: test a fixed complete historical
state panel through the same endpoint, with canonical timestamps and all missing
dates retained. One successful old block does not establish full archive coverage
or any annual cohort. Ethereum and Arbitrum demonstrate unavailable state at
their tested old anchors, not a chain-wide absence of archive data.

Prefer direct state reconstruction where available before implementing an event
replay. Freeze cohort, sampling, cost/mark/version prerequisites, worst-case
requests and unavailable rules before Q2 acquisition. Base may be prioritized
for demonstrated source availability; no observed index level or growth should
select a chain or window. Preserve the other chain/protocol coverage gaps.

Aave event reconstruction remains a separate conditional route within the same
Q2 allowance: complete mutation coverage, deployed versions, exact timestamps,
integer rounding and independent anchor checks are required. An event rate alone
cannot substitute for realized claim accounting. LP requires sufficient admitted
historical state or a materially larger validated replay; unavailable coverage
must remain explicit rather than become an economic failure.

Actual user access, fees, gas, cash conversion, withdrawal restrictions,
protocol losses, USD marks, financial performance, risk and statistical power
remain untested. No Q1 rerun or additional source-family allowance is justified
by this review.
