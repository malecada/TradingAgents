# Independent options metadata pre-review

September 11, 2026. Final disposition: **PASS for source-only admission under
the frozen launcher and final gate below**. Original blocking findings and their
resolution history are retained.
Reviewed `../options_metadata.py`, `../options-metadata-charter.md`,
`../options-request-spec.json`, `../../../tests/research/test_options_metadata.py`,
the reused public transport and research lifecycle serialization. Collector
implementation was not written or changed by this reviewer. No real API request,
quote, price input, archive body or financial calculation was performed.

Reviewed collector SHA256:
`355b74dd3958e271f1dc582290f629b34deaeb067beefa7bd9ace4975d6d20de`;
test file SHA256:
`aad5760a36e00eb54d8e8c95d1a936b204297891036e59ccdc5969ced633ad99`.

The 26 named synthetic tests pass (`.venv/bin/python -B -m pytest -q
tests/research/test_options_metadata.py`, 0.07 seconds). Independent invented
serialization probes below expose a missing boundary despite those passes.

## Blocking findings

1. **Compact-size accounting does not enforce the 80 MiB retained-output cap.**
   Collector lines 242–247 and 251 count compact JSON. The lifecycle writes
   sorted, indented JSON (`tradingagents/research/lifecycle.py:20`). With 17,000
   invented empty symbol objects, the parser admits 24,758,250 compact bytes
   under its 24 MiB allowance; actual indented serialization is 36,131,303
   bytes. Valid JSON/XML bodies may each be whitespace-padded to 5 MiB, retaining
   the same decoded data. Four such receipts, duplicated in the capture report,
   require 55,924,064 base64 bytes. Together this already exceeds the cap:
   92,055,367 > 83,886,080 bytes before output envelopes and nesting. This
   synthetic probe serialized incrementally for counts, fetched nothing and
   wrote no output files. Count actual final serialization and reserve envelope
   overhead, or prove a smaller allowance against worst-case indentation.

2. **The exact 256 MiB / one-CPU / 120-second execution envelope is not yet
   enforced by the reviewed launch path.** `main()` enters ResearchRun directly.
   Internal checks bound request admission and some normalization, not process
   resident memory, final serialization or total elapsed runtime. The existing
   `resource_guard.py` defaults to 512 MiB and two CPUs; its CLI exposes no
   corresponding override. A separately frozen, reviewed launch path must
   enforce this charter's bounds and record its resource evidence. An ordinary
   successful small synthetic input cannot establish the adversarial bound.

3. **Failure/resource closure can lose the four-cell receipt denominator.**
   The parser exception list excludes unexpected RuntimeError and MemoryError;
   the existing `test_receipt_written_before_unexpected_parser_failure` proves
   exactly one receipt survives such a parser failure before the function exits.
   The immediate received raw evidence is correctly preserved, but remaining
   three unattempted receipts and four result cells are absent. An external
   resource termination can leave the same incomplete denominator. The charter
   explicitly requires unattempted receipts for resource-stopped cells. Provide
   a bounded coordinator/runner closure path that preserves existing raw
   receipts, distinguishes partial from unattempted, never retries or falsely
   fabricates body completeness, and retains the four registered identities.
   Do not label a killed run successful merely because closure records exist.

## Checks that pass within the reviewed implementation

The canonical request-spec hash rejects mutation before transport. The four
URLs are fixed; public_get disables retries/proxies/redirects/authentication,
uses a 20-second wall deadline and retains received prefixes at its 5 MiB cap.
HTTP 403/418/429/451 suppress later requests on the same host; the second host
remains independently attempted. Raw receipts are published before parsing and
before subsequent requests. Known malformed JSON/XML and incomplete responses
produce unavailable cells, rather than empty successful universes.

Strict JSON rejects duplicate keys, nonfinite constants, non-object roots and
API errors. All symbol rows/raw fields remain represented. Literal underlying
identity alone selects BTCUSDT/ETHUSDT targets; names alone do not. Unknown
crypto discriminators remain ambiguous, so no unconditional crypto identity or
seller permission is admitted. Quantity conflicts, duplicate identities/lot
filters, invalid numbers and missing fields remain explicit. Overall source
status `complete` is structural only; it must not be reported as complete
crypto-rule or capital feasibility.

S3 parsing rejects DTD/entity declarations, wrong namespaces, mismatched query
scope, out-of-prefix keys, duplicate identities, malformed booleans and excess
key counts. Both truncated listings retain a partial flag and continuation
metadata without pagination. Catalogue names never establish body schema,
historical coverage or executable option chains. LastModified/ETag limitations
are retained. No fee, payoff, Greek, option premium, affordability or financial
return is computed.

Execution gate review is pending: four source-only cells, six declared outputs,
actual current capture timestamps, exposed/nonconfirmatory dataset designation,
and exact collector/transport/request/charter/resource-launch hashes must be
checked after the implementation and launch blockers are resolved. Do not
acquire real metadata under this pre-review disposition.

## Fix re-review — implementation issues resolved, final contract/gate pending

Collector SHA256
`d95c6a68edf987db3112d01e6aa74883488f02077970681fa2c7a1154e02c48f`
and launcher SHA256
`5d876d486b6e8e5e3abec853c498fd7e579ed842b32faca65600fb1bf9f1eb4e`
were independently reviewed. All 31 synthetic tests across
`test_options_metadata.py` and `test_options_resource_launcher.py` pass in
1.30 seconds. No real source was contacted.

Finding 1 is resolved: the collector now uses the exact lifecycle encoder,
including final newline, budgets nested pretty-serialized rows with a 12 MiB
normalization allowance, and checks the actual combined six-output size before
publication of aggregate reports. Oversized normalization becomes unavailable
while received raw metadata remains preserved. The new disposable Git/lifecycle
test uses four invented 5 MiB bodies and performs actual writes under the guard;
all four cells and six outputs remain, and normalization is correctly withheld.
The preceding 17,000-row compact-versus-pretty counterexample is preserved as
the reason for the fix rather than deleted from review history.

Finding 2 is resolved for the required launcher path: its exclusive report
reservation prevents a repeat launch, it reduces affinity to one CPU before
starting the child, and it explicitly passes 256 MiB and 120 seconds to the
reviewed `resource_guard_v2`. The collector also sets one-CPU affinity before
capture. The guard samples aggregate child-tree RSS rather than virtual address
space; sampling can briefly overshoot the threshold, as its report discloses.
The disposable full-write test verifies one CPU and successful bounded RSS.
Direct collector invocation is not the admitted execution route.

Finding 3 is partially resolved in code: recoverable parser exceptions now
produce unavailable cells and continue the four-cell denominator. MemoryError,
BaseException and external process termination intentionally remain fatal;
the test preserves the first received raw receipt and does not pretend all
later receipts were published. A coordinator charter clarification is still
required to distinguish cooperative four-cell closure from abrupt failure's
registered intended denominator plus available partial outputs. At this
re-review snapshot the charter had not yet changed and the execution gate did
not exist. Final source/charter/transport/launcher/guard hashes, four cells and
six outputs remain pending final gate review; no acquisition admitted yet.

## Final contract and gate review — PASS

The amended charter now distinguishes cooperative resource/parser failures,
which retain four receipts/cells, from abrupt termination or MemoryError, which
may retain only partial outputs plus the immutable claim's four intended
identities. Failed/pending claims cannot be retried silently. This resolves
finding 3 by explicitly documenting the enforceable failure contract before
real observations, not by claiming a killed process can publish absent bytes.

Final gate `../gates-options-metadata.json` SHA256:
`328358c2d5f5a12d4118d0f8526e26d41a811d8eaf47677bad8b9b3e2f1eb406`.
Final charter SHA256:
`d53ae61bc086c0c386b47657d099943f0facecc408216fecf01c2a89177a3f05`.
Collector and launcher match the fix hashes above; guard v2 SHA256:
`feb2c1ed2984100b069261cceaf6d7a1bdac4406eff3dee5b18fdc51f6965298`.

Independent checks match every declared source, transport, request-spec,
observation-marker, uv.lock, charter and runtime hash against local bytes.
All ancestor experiment/family/dataset objects match `gates-dated-correction.json`
exactly. The new family preserves one known RVIV administrative bundle plus
three new investigations (cap four), separately from 12 historical ledger rows
and unknown statistical multiplicity. Four exact request identities map to the
four receipt outputs plus capture/admission reports, six outputs total.

The existing-input window 08:38:02.442372–08:38:02.442471 UTC on September 11
describes only the local observation of static request-definition bytes. Its
marker expressly is not independent timestamp attestation or a live metadata
observation. Actual live response availability will begin at the real future
request/retrieval clocks retained per receipt; none may be backdated to this
input window or called fresh financial confirmation. Stage development/reuse
exploratory and null selection are appropriate to source admission.

No remaining pre-result blocker was identified for this exact source-only
capture. Commit/push and remote equality remain coordinator admission steps;
this review neither performed acquisition nor establishes resulting data quality,
option eligibility, executable chains or strategy viability.
