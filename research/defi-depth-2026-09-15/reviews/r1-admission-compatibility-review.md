# Independent R1 admission compatibility diagnosis

Disposition: **The reported historical-verifier defect is confirmed.** A narrowly
restricted additive R1 runtime is justified for review. This is not approval of
an unwritten patch or a replacement R1 certificate. No historical registration,
receipt, runtime, options worker or financial experiment was modified or run.

## Exact failure mechanism

`tradingagents/research_amended/verify_amendment.py:41` enumerates all other
same-mechanism claims currently present, without checking whether they preceded
the amendment being verified. At line49 it compares that set with the historical
certificate's prior-claim inventory and original exhausted budget.

The affected amendment is `dated-book-amended-20260911`, started at
2026-09-11T09:43:07.041240+00:00
(`research_runs/dated-book-amended-20260911/claim.json:217`). Its family is
`binance-btc-eth-dated-basis-convergence`, with prior1 and original cap4.
The certificate was read from its committed source and its hash independently
verified. It names exactly these three predecessors:

| Claim | Started September11,2026 UTC | Claim line |
| --- | --- | ---: |
| dated-archive-20260911 |07:59:20.863089|106|
| dated-book-20260911 |08:20:48.176650|138|
| dated-book-resource-correction-20260911 |08:29:08.357398|141|

Two later same-mechanism claims also exist:

| Claim | Started September11,2026 UTC | Claim line |
| --- | --- | ---: |
| dated-mark-20260911 |11:15:48.882475|219|
| dated-spread-book-20260911 |11:49:04.276789|322|

The historical certificate correctly describes three predecessors plus prior1
= original cap4. The current verifier instead includes five other claims,
making5+1 and a different inventory. Later legitimate work therefore makes the
earlier certificate fail reconstruction. The failure does not demonstrate an
unrecorded predecessor or a budget reset in that historical certificate.

## Bounded additive correction

Keep the original research_amended package and all historical receipts byte
identical. A separately hashed copy may change historical certificate
reconstruction so a predecessor must have a timestamp strictly earlier than the
claim being verified. Validate timestamp interpretation consistently; malformed,
timezone-ambiguous or equal-time same-family ordering should fail explicitly
rather than silently discard an ambiguous predecessor.

This chronological filter belongs only in reconstruction of that historical
certificate. It must not filter the main claim inventory or current cumulative
accounting. In particular, the full list feeding
`research_amended/admission.py:214` and same-mechanism accounting at line218 must
continue to contain later claims, failures, exposures and outstanding claims.
Keep all certificate identity, source, invariant, prior receipt/hash, exhausted
budget, failed-parent and anti-chaining checks.

The new copied runtime must reject new admissions except the exact
`defi-depth-r1-20260915` experiment and its `gates-r1.json` registration, with
the intended program/mechanism. Historical read-only verification remains
available to reconstruct its ancestry. This is not a general extension or a
second repair grant for another strategy.

Required focused checks before approval:

- A historically valid certificate still verifies after a later same-family
  claim appears, without changing its saved accounting.
- An omitted earlier predecessor, mismatched hash or invalid parent still fails.
- An earlier chained amendment still fails.
- Later same-family claims remain in overall present-day budget and exposure
  accounting; filtering the historical inventory grants no new present capacity.
- Every non-R1 new-admission request is rejected.
- The exact copied historical claim set reproduces the fixed reconstruction;
  the final R1 packet passes actual metadata admission before any source call.

## R1 accounting and approval status

The failure occurred during metadata admission before an R1 claim or RPC request.
Preserve its command/error logs as failed engineering validation. It does not
consume another empirical source attempt or create another repair slot. Failed
Q2 and its168 charged subcalls remain unchanged; the planned R1 still consumes
the same sole shared repair when its claim is admitted.

Changing the runtime/import and any corresponding charter changes R1's bound
contract. Regenerate the source/runtime hashes, preservation manifest,
certificate and synthetic preflight, then obtain an exact replacement review
and approval binding. The earlier approval for the original research_amended
packet must remain historical and cannot approve a different hash by inference.

No copied runtime patch, final replacement certificate or actual R1 result was
tested in this diagnosis. No financial values or options-worker state were
inspected.
