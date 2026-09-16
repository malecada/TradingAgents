# Independent protocol closure helper review

## Initial disposition

Changes required for failed-run uncertain attempts and their denominator.
The review used source inspection and invented temporary filesystem fixtures,
with the structural Git verifier mocked only inside those fixtures. No actual
F1/F3/F2 run, empirical financial value or live root was accessed. Only this
review file was written; no acquisition or experiment was executed.

## Material findings

1. **Unpaired intents bypass validation and spent-key accounting — initial
   `protocol_closure_audit.py:32`–36.** The missing-receipt branch continues before
   validating the canonical request key, physical slot, ID or retry grouping and
   before recording the logical key. An interrupted send is precisely where the
   record must remain conservative. Three independent fixtures demonstrated:
   a distinct uncertain key is omitted from logical/key counts; the same key
   under a second uncertain logical ID is accepted; and an uncertain intent with
   physical_slot99 plus an invalid logical_key is accepted. Validate and register
   every durable intent first, then distinguish paired response from uncertain
   send. Retain the actual-or-uncertain key union and its paths/identities for
   downstream exclusion. Check contiguous attempted physical slots across paired
   and uncertain sends together. Preserve separate paired actual, uncertain,
   suppressed and total committed request counts rather than treating absent
   receipts as unspent work.

2. **Failed registered denominator absent — initial final count/return block.**
   The structural verifier deliberately reports cell_count0 for failed runs; it
   does not mean zero registered cases. Return the frozen registered cell/output
   and physical-slot totals from the claim, retained/published counts and missing
   remainder. Distinguish unpublished cells from explicit unavailable cells.
   Keep the original failed terminal and its reason visible. Do not generate
   retrospective result cells or receipts to close these gaps.

## Positive checks and scope limits

The helper delegates committed registration/source/claim and terminal/output
hash checks to unchanged `verify_run`, which requires a unique terminal and
refuses active runs. Paired intents require exact method/parameters/key/slot,
request IDs, endpoint and timestamp identity. Base64 decoding validates retained
body hash and length; oversize retained prefixes and response bytes on suppressed
slots are rejected. A provider's malformed/non-JSON/error body can remain retained
failed evidence without being interpreted as corrupted local files. Complete
runs require all three physical slots for each observed logical request, while
raw source totals and unique reported dates are reconciled to the summary.

The initial four named invented tests pass. They cover two physical sends for
one logical key, raw-body corruption, absent third slot in a complete run, and
one uncertain receipt gap in a failed run. The independent counterexamples above
extend coverage to uncertainty-specific malformed and duplicated keys.

This helper currently reconciles physical receipts; it does not independently
prove retry eligibility from each prior HTTP/RPC response, enforced pacing or
Retry-After timing, ABI/header correctness, daily source flags, financial accounting
or economic inference. Qualified row counts are source-summary claims rather
than independently reconstructed observation qualification. Those limits should
remain explicit when reporting a closure pass. No full empirical audit or
lifecycle admission was tested here.

Initial reviewed source SHA256: `2ea2945f710b0e6500f315eda69acd59523210e9059d94139257cbd9bd4e21f5`.


## Correction re-review — September16,2026

**PASS for the bounded terminal reconciliation helper.** All durable source
intents now enter key/envelope/slot/Boolean validation and logical accounting
before the missing-receipt branch. The actual-or-uncertain request key union
includes interrupted sends; duplicate aliases are rejected and the physical
prefix check includes uncertain attempts. Registered cell/output/physical-slot
totals and unpublished output/intent remainder are now retained separately from
the structural verifier's zero cell_count on failed runs.

Five named invented tests passed on final recheck. The three independently
constructed counterexamples were also rechecked against the corrected helper:
a distinct unpaired key now raises the spent unique-key total to2 and total
actual-or-uncertain physical requests to3; a duplicate key under another unpaired
logical ID is rejected; an invalid unpaired key/slot is rejected. No actual run
was opened or audited.

The initially labeled SHA256 above was recorded while the author was applying
corrections in the shared checkout; it identifies the corrected source, not the
earlier deficient branch shown in the initial tool read. The original findings
refer to that earlier source read and remain preserved as review history.
Final independently re-read SHA256: `2ea2945f710b0e6500f315eda69acd59523210e9059d94139257cbd9bd4e21f5`.

Reporting limitations remain: `actual_unique_logical_keys` includes uncertain
sends in this revision, as made explicit by `actual_or_uncertain_request_keys`;
it must not be described as a count of confirmed network responses. The original
failed terminal retains its failure reason and remains necessary for full
closure reporting. This helper does not synthesize result cells from unpublished
outputs, establish response-based retry eligibility/pacing, requalify ABI/clocks,
or validate financial performance. Those are separate review claims.
