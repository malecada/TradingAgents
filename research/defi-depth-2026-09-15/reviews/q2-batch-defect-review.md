# Independent Q2 batch-defect classification and repair review

Disposition: **Eligible for the reserved R1 source-compatibility repair.** This
is approval of the repair classification and route, not approval of an unwritten
repair implementation or permission to alter Q2. The exact amendment, repair
harness, gate and synthetic preflight still require independent review before
execution. No network request or financial calculation was made in this review.

## Literal evidence and stopped claim

The retained September2 and September3 state receipts contain HTTP200 bodies
with JSON-RPC error -32014 and the message `maximum 10 calls in 1 batch`.
Their respective payloads contain29 and15 members. All eight retained state
responses contain that same batch rejection. The one-member chain batch and
two-member header batches were accepted. This is a concrete collector/provider
batch-format incompatibility, not an observed HTTP access denial, unavailable
historical state or economic failure. Smaller batches conform to the stated
limit; they do not evade authentication, access restrictions or a rate limit.

Q2 is terminal failed at source
`1dce226c4a37791a96dc0fabe04c20ebe8d558c0`, with reason
`KeyboardInterrupt: ` and end2026-09-15T16:49:55.575505+00:00. Stopping a known
faulty acquisition is justified by this measurement defect; it is not an
elapsed-time or unfavorable-outcome stop. No successful financial state value
was obtained in the eight published daily vectors.

Independent checks verified the failed claim hash, all46 preserved output hashes,
and every retained raw receipt's base64, byte length and SHA256. Accounting is:

- 19 durable HTTP attempt intents, charging168 logical RPC subcalls.
- 18 completed raw receipts, totaling37,336 bytes.
- 8 daily result vectors, containing166 cells:24 complete header/bracket cells
  and142 unavailable state/coherence cells. The chain result is separately
  complete. Later raw headers remain preserved even without a daily vector.
- September10's state attempt has no receipt. Its15 members remain charged;
  response outcome and any received-but-unpublished bytes are unknown.

The registered20,890-cell denominator remains in the claim. Unvisited cells
were not evaluated and must not be turned into completed unavailable findings.
All raw errors, partial outputs and original criteria remain evidence. The
failed Q2 attempt cannot be erased, reopened or counted as zero attempts.

## Narrow repair contract

Retain the exact1,096 dates, cohorts, field identities, calldata, candidate-height
formula, causal brackets, source endpoint, decoding/rounding rules and source-only
scope. Split each15-member ordinary state payload deterministically into10+5;
split each29-member boundary payload into10+10+9. Keep the existing chain and
two-header payloads. No adaptive smaller-batch search, alternate endpoint,
additional fields or economic selection is justified.

Each physical chunk needs its own immutable pre-transport intent and raw receipt.
Do not fabricate an aggregate raw response or hide physical requests behind one
batch receipt. Missing/duplicate/unknown IDs, partial bodies and denials retain
their defined handling. A later access denial still stops the endpoint.

For the simplest full fixed replay, reserve18,689 new logical subcalls and3,293
HTTP requests. Its worst-case raw reservation is863,240,192 bytes. Including Q1
and failed Q2 gives18,986 charged logical subcalls, leaving6,014 of25,000, and a
combined raw reservation of863,378,479 bytes, below2GiB. All duplicate calls are
charged. Reuse of prior successful headers could reduce requests only through
an exact reviewed hash-bound reuse manifest, not informal substitution.

## Existing amendment route

The unchanged `tradingagents/research_amended/amendment.py:38` permits one extra
attempt through an explicit certificate. Its rules require exactly exhausted
original budget, complete prior-claim inventory, the latest failed parent,
unchanged family/program/history and immutable historical experiment objects.
Q1 plus failed Q2 plus imported prior1 exhausts this source family's original
cap3. R1 can consume the phase's single shared repair slot and produce effective
cap4, while leaving the original family object unchanged. Original allocation
188/189 and the44 related DeFi records are unaffected.

At `amendment.py:14`, inputs, windows and cells are outside the mutable fields.
Preserve Q2's original spec input and complete logical recipe. Freeze derived
physical chunk/output/resource bounds in a separately hashed repair harness and
charter; do not silently replace the original spec or edit the old runtime to
make an amended gate pass. Reuse the frozen parser/clock/accounting primitives
where practical. The preservation manifest must partition genuinely unchanged
semantics from changed transport machinery rather than labeling everything a
harness to bypass invariants.

The certificate must bind Q1's terminal receipt, Q2's failed receipt, this defect
review, the exact target contract, preservation manifest and passing synthetic
repair preflight. The preflight should include a fake provider enforcing the
observed ten-member ceiling, all boundary and ordinary chunks, chunk-level
failure/denial/ID handling, exact full denominators and physical request charges.

## What this review does not establish

The initial synthetic fixture accepted oversized batches and therefore did not
test the actual provider limit. This failure is retained; the earlier preflight
is not retroactively described as having established compatibility. Ten-member
requests, archive continuity, oracle semantics, gas/withdrawal feasibility and
financial performance remain untested against the provider. No R1 code, final
amendment certificate or repaired empirical result has yet been reviewed here.
