# Independent F1 context and ownership review

## Scope and initial disposition

Changes are required in the first-owner proof and closure helper before final
F1 admission. The context preparation was not run against actual research roots.
Only this review file was written. No network, empirical financial values, active
F2 root/process, account or wallet was accessed. Synthetic filesystem fixtures
were temporary and did not use the research lifecycle or a real ledger.

The review covers `source_ownership.py`, `f1_context.py`,
`f2_closure_audit.py`, their integration in `protocol_financial_source.py`, and
the draft `f1-charter.md`. A complete final gate/main was not presented.

Reviewed initial SHA256 values:

- `source_ownership.py`: `23dad352c46e69c8c3676f935bcb7cc2c6c510c91a110edfdbfc3e529b5f46eb`
- `f1_context.py`: `1682429bf7cc6950bf7402069179c196ecf722f9d9e9da8e4b0a1ba1e6384889`
- `f2_closure_audit.py`: `d795213d7b8d223be828fe1be0c6cefdf35d0c47749462f11259ef7c813f2495`
- `protocol_financial_source.py`: `c2210a54981f958832db384168cb4b92188e56967bbc30ee19b0f02504e393b9`
- `f1-charter.md`: `22b20542854f4f85c9b0d8f478f1b3e08e94bc6e38bf3cde6b76b5ff031d8788`

## Actionable findings

1. **Exact suppressed-request proof — initial `f1_context.py:56`–68.**
   `verify_packet` checked attempted=false and the display ID but did not bind
   URL, JSON-RPC method/ID, header-height parameters or oracle calldata. An
   invented suppressed eth_call to an unrelated URL was accepted as proof for
   a new left-header request. Require the exact original F2 header request and
   the fixed original F2 oracle vector. For a suppressed oracle request, a
   missing tag is legitimate when F2 had no qualified bracket; a supplied tag
   must correspond to the frozen block. This must not retry F2's failed right
   header or convert a newly chosen vector into evidence of novelty.

2. **Reconstruct the inherited global exclusion union — initial
   `f1_context.py:83`–94.** Individual intent-file hashes and their recorded key
   lists were checked, but the global `all_base_request_keys` list was trusted
   without equality to their union. Reconstruct all actual/uncertain Base keys
   and compare, so an omitted list entry cannot silently permit another send.
   The existing retained metadata is consistent:358 references produce1,569
   unique keys, exactly the global list. Its full header subset has184 keys;
   the separately scoped `base_header_keys` has182. The two additional Q1 keys
   are Base block`0x1312d00` and`finalized`. Preserve that original narrower
   header-list scope; require subset consistency, not an incorrect184=182
   equality. Both additional header keys must remain globally excluded.

3. **Retained failed response classification — initial
   `f2_closure_audit.py:37`–41.** A mismatched-ID JSON error currently raises;
   JSON arrays/scalars raise AttributeError. These may be faithfully retained
   failed provider responses in a terminal source-unavailable run. Three
   independently constructed temporary terminal fixtures reproduced those
   errors despite matching claim/output/body hashes and intent/receipt identity.
   Classify malformed/nonmatching response envelopes as unqualified evidence
   while retaining their raw bytes and spent request keys. Successful header or
   price reuse must still pass the strict envelope and ABI parser. Source
   unavailability must not be confused with damaged local evidence.

4. **Charter/source numerical alignment.** State primary/doubled/frictionless
   native-sale fees as0.3%/0.6%/0 and adverse factors as10bp/20bp/0. The initial
   prose specified only the primary values and said doubled adds friction.
   State the ETH−50% component of the seven-day withdrawal-outage scenario and
   the fivefold adverse factor in the combined ETH−90%/credit−50%/USDC−20%/
   thirty-day scenario. These are prose corrections to already-reviewed code,
   not permission to change its economic recipe after outcomes.

## Positive findings and remaining admission conditions

The semantic exclusion helper expands both fixed Aave oracle getters into
block-hash/asset exclusions and normalizes address/hash case. A scalar attempt
therefore prevents another attempt hidden inside a changed vector. Failed and
uncertain attempts are exclusions too. Unresolved old price block tags refuse
proof of novelty. Three named invented ownership tests pass.

The collector recomputes that semantic inventory from the declared prior keys
and checks it before any proposed new price vector, including after learning a
new header hash. This is a useful second check; it does not substitute for a
complete provenance-bound prior-key inventory. Other literal method/tag aliases
remain the exact source builder's responsibility. Fixed canonical parameter
generation and complete terminal-history import are required.

Retained header reuse checks the fixed endpoint, actual acquisition, exact left
height and a strict raw response envelope before applying the actual timestamp
rule. The retained price path checks the exact F2 oracle calldata/vector and
same block hash before extracting positive ETH/USDC integer units. No synthetic
USD mark or price request is produced by these parsers.

The preparation entry calls the terminal audit first and requires a complete
terminal publication; it cannot legitimately run while F2 is active. Terminal
publication can still describe source/financial unavailability. It must not be
reported as a successful F2 strategy or a repaired old bracket. A failed or
uncertain attempted key remains excluded even when later numerical books need
it. Suppressed first acquisitions need exact immutable proof and prospective
F1 ownership under the existing financial allowance.

The final gate must bind the actual original claim, terminal receipt, source
commit, inherited history, per-intent/receipt references and prepared packet.
Comparing a packet's own key list with a design derived from it is not by itself
terminal provenance. Embedded raw body checks must ultimately connect to those
real pinned historical files. The reviewed `verify_packet` interface alone does
not yet establish that binding; exact main/gate integration is still pending.

The charter otherwise preserves the reviewed70% fixed lending allocation,
whole$10,000 capital and gas, exact receipt units, once-only interest, three fixed
cost scenarios, independent strict-cap/ceiling outputs,73-cell financial grid,
all fixed comparisons, unavailable adoption/confirmation and ordinary credit
loss inside market stress. Its actual-clock distinction, no F2 backfill, finite
new-key retries, endpoint stops and cumulative source/financial limits are
explicit. No new repair, documentary request or confirmation allowance follows.

The ledger/accounting helpers and result routing were separately reviewed; they
were not rerun with empirical data here. Actual F2 terminal counts, exact new F1
source inventory, final phase usage and a complete end-to-end admission remain
unverified at this stage.


## Correction disposition and builder/runner review

**PASS for terminal-only preparation and the reviewed integration; this is not
admission of an empirical F1 run.** The four original findings above are resolved
in the versions hashed below. The earlier findings are retained as review history.

The revised `f1_context.py:65` checks exact suppressed endpoint, JSON-RPC request,
ID, method, calldata and block parameters. `prepare:117` reconstructs all inherited
request keys from hash-checked original intent metadata and requires equality to
the global exclusion inventory, while preserving the narrower header subset's
original scope. `f2_closure_audit.py:37` now counts malformed/mismatched JSON
response envelopes without discarding their body bytes or spent keys. Raw reuse
still requires strict independent envelope/header/ABI qualification. The charter's
cost and stress parameters now match the reviewed numerical implementation.

`verify_registered_evidence` and `f1_source.main` bind embedded raw evidence to
separately registered exact input bytes before source capture. The builder pins
the original F2 claim/terminal, inherited attempt history, exact supporting
intents and receipts, six predecessor claim/terminal pairs, original benchmark
claim/results, phase grant and review documents. The terminal preparation route
checks complete publication first; an active root is not eligible. The complete
F2 publication may remain source/financial unavailable. No source omission,
failed key or semantic oracle-field overlap acquires a retry allowance.

The new builder computes the full source manifest before output creation, binds
its generated design/context hashes, and refuses existing preparation outputs.
The runner uses ordinary `ResearchRun.start`, verifies registered evidence,
reparses retained header/price bodies, captures the fixed source grid, then routes
only the fixed F1 financial/auxiliary/benchmark cells. It does not call a financial
function during preparation. Its source snapshot includes the new builder,
runner, context, ownership, transport, collector, results and book dependencies;
all19 source hashes inherited unchanged from the F2 gate matched the coordination
checkout when reviewed. Runtime hashes are obtained from the ordinary lifecycle.

A new narrowly defined lending family imports six direct source claims with
prior6/cap7 and no cross-family structural parent. This preserves the reviewed
mechanism distinction; it does not reset the umbrella phase, shared repair,
financial trial or original core/DeFi search history. The prepared actual gate
must still reconcile those counters and exact old evidence before admission.

### Independent verification

- Twenty named invented context/ownership tests passed, including altered
  suppressed-request endpoint/method/ID/parameters/attempt flags and malformed
  failed provider envelopes.
- An independent temporary builder fixture used the fixed366-date calendar,
  invented unsent ownership proofs and deliberately all-new header/price slots.
  It produced3,380 unique cells and15,879 unique outputs, with7,722 reserved
  physical requests and397,246,464 retained-prefix bytes. Generated design and
  context input hashes matched their actual temporary bytes; the design source
  hash also matched its input hash. This exercised the builder in memory and a
  temporary directory with patched invented historical references. It was not
  an empirical preparation, a lifecycle admission or a source request.
- No actual F2 root, source outcome, price array, financial result or live process
  was inspected. No network call, old experiment rerun, production mutation or
  change outside this review file occurred.

### Remaining exact-admission conditions

The actual terminal F2 counts, authoritative attempted/suppressed ownership
crosswalk, final generated F1 gate and committed input/source hashes were not yet
available for this review. They must be reconciled after terminal publication,
then admitted at a fixed detached execution HEAD. The synthetic all-new counts
above must not be reported as the actual F1 reservation. Source aliases outside
the fixed canonical request builder, proxy implementation history, real supply
capacity, execution routes, account terms and fresh confirmation remain unproved.
No implementability, profitability or promotion claim follows from this review.

Reviewed corrected SHA256 values:

- `f1_context.py`: `8e2790b1203d6097a9263b9f91f8f66ff62a243586685721d8bc48ad7ca2b862`
- `f2_closure_audit.py`: `688e4dd601a78c7fc3207f36de504d184402ffa9f3afc1185c6bfcefe00e756b`
- `f1-charter.md`: `1eecce2b32773923b61ec6621fb670c3ea2622c5ac2ab7f299ec34450cc7b63a`
- `prepare_f1.py`: `6809b2374621a85bb5fb2f489ac283d0eec5ce65e1ee124cb70609e56adedb84`
- `f1_source.py`: `1441ef0c551150280b0b9270cd14e234179784b9d3ab9f4d5d2e24bc3f0a6131`
- `protocol_financial_source.py`: `c2210a54981f958832db384168cb4b92188e56967bbc30ee19b0f02504e393b9`
- `source_ownership.py`: `23dad352c46e69c8c3676f935bcb7cc2c6c510c91a110edfdbfc3e529b5f46eb`
