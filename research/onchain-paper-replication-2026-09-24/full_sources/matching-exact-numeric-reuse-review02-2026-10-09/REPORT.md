# Exact numeric reuse02 — accepted changed engineering seams

Reviewed numeric_reuse.py SHA04f809dbd56deedde50fd4c8b1169fc3f652bbfe94e3a86e9834700bde2fb237. All candidate manifest file hashes match; inverse.patch reconstructs literal predecessor01. Acceptance is limited to this frozen source and its declared exclusive trusted-runtime, explicit batch-boundary contract. It is not acceptance of a joined runtime, empirical result, expected hit rate, capacity or speedup.

## Focused evidence

Eighteen checks pass in TEST01.log/RESULT01.json. Actual candidate definitions were AST-extracted into a stdlib-only harness. Numerical dependencies and exact key production were explicitly synthetic routing fixtures, not fabricated authority or numerical-equivalence evidence. This isolates changed control/cache logic without importing the newly modified Main numerical runtime. Prior unchanged numerical evidence is reused. Numeric framing, immutable eligibility, configuration framing and raw JSON functions match predecessor01 AST exactly.

Checks cover: refused calls outside batch; fresh public graph identity calls and occurrence purpose on a cache hit; exact origin purpose retained separately; provisional receipts with old-execution credit false; no source scan on hit; final attestation; close clearing; three equal routing hashes distinguished by full exact bytes; correct LRU eviction after touch; independent retained-object accounting; oversized-entry refusal; source mutation refusal/clear at final boundary; per-occurrence config refusal; original callback exception identity and poison/clear; checkpoint runtime mutation rejection; and failed close still clearing retained entries. CPU affinity was [0,1] (two logical CPUs, no isolation claim), nice10, 30s timeout, 256MiB AS and 4MiB FSIZE. No numerical runtime, empirical arrays or original graph bodies were imported/read.

## Source assessment

Construction, begin_batch, end_batch and actual checkpoint callback brackets call full attest. Per-occurrence guards intentionally check a smaller fixed roster and bindings. Source mutations outside those lightweight checks can remain undetected within the declared interval; successful end_batch is mandatory before final batch credit. last_receipt stays provisional even after end_batch; the caller must independently anchor batch completion. The wrapper creates no durable/Owner/representation authority and does not promise continuous verification. Arbitrary hostile private-state or native mutation is excluded by its declared contract.

Fixed slot, bucket-chain and LRU arrays keep retention bounded by max_entries and measured object allowance. Exact key comparison decides a hit after routing hash comparison. Eviction updates both bucket chain and LRU/free lists; accounting adds/subtracts the same measured entry components. Collision worst case remains finite linear lookup in one bucket. Key construction, source buffers, counters, runtime pins, original numerical state and Python allocator arenas are explicitly outside the cache-object allowance; no process RSS cap is established by that number.

Fresh purpose is validated before both computed and reused occurrences; result score bits/iterations/status are retained independently of purpose. Reused calls skip original numerical checkpoint work by explicit operational deviation, not by claiming original per-occurrence execution. Failures within the call clear cache/receipt and poison wrapper and executor; unchanged PairExecutor retains original engine close/primary-exception handling. Invalid API entry calls refuse without clearing an otherwise inactive cache, which does not grant usable batch credit.

## Frozen source pins and future integration

At review time, frozen SOURCE_PINS.json disagreed with current Main matching_checkpoint.py (4287d59c → d5d24aeb) and matching_annealing.py (c04a2633 → 2037c5bb), following the independently adopted session work. RESULT01.json retains full hashes. The original attestation therefore refuses construction against that Main; this is correct fail-closed behavior. No pins were updated, no candidate was installed and no joined numerical run was attempted. A separate explicit joined source, repin and changed-seam integration review is required before adoption with ImmutablePairSession02.

No blocking defect was found in the reviewed changed seams under these constraints. Main, STATE, Git and all old evidence were untouched.
