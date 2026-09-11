# Independent pre-result review — carry input capture

Disposition: **source and charter pass for the bounded public-data measurement**.
Two material evidence-retention defects identified during review were corrected
before any capture. No unresolved source blocker remains in the reviewed bytes.
No network request or financial experiment was performed by the reviewer.

Reviewed identities:

| File | SHA256 |
|---|---|
| `carry_capture.py` | `323ea01ac0d8137288e6f72f697101db1884595e876622402c321f38367d6b12` |
| `carry-inputs-charter.md` | `3300905e8466a0752552007210c1b05019dd1de84868ffe44231f06369760615` |
| `tests/research/test_carry_capture.py` | `77374ab66c689871f3f477fa68c36f907b9d49142e7171b179099f40fca789fc` |

## Corrected findings and impact

1. **Previously received evidence could be lost after a later failure.** The
   initial implementation retained all raw responses in memory until every
   request completed. An unexpected later transport/parser failure or process
   interruption could leave a consumed run claim without earlier received raw
   evidence. In the final source, the per-cell persistence callback executes
   before semantic parsing or the next request
   ([carry_capture.py:278](../carry_capture.py#L278)); `main` supplies the
   lifecycle's immutable writer. The charter declares ten individual raw
   receipts plus the aggregate capture and admission outputs. Synthetic tests
   verify that an earlier persisted receipt survives a later transport failure
   and that persistence precedes a parser crash. A process killed during its
   current network read can still lose that in-flight prefix; earlier published
   receipts remain, and the failed/pending claim must not be automatically retried.

2. **Premature HTTP termination could escape handling or be labeled complete.**
   `http.client.IncompleteRead` does not inherit either original caught type,
   `OSError` or `ValueError`. The final transport catches HTTP protocol exceptions
   and retains the `IncompleteRead.partial` bytes alongside prior chunks
   ([carry_capture.py:106](../carry_capture.py#L106)). Independent reconstruction
   using an actual Python `HTTPResponse` over synthetic in-memory bytes also
   demonstrated that `read1()` returns EOF without raising when a nonchunked body
   is shorter than `Content-Length`. A declared length of 100 with body `{}`
   originally returned `body_complete=True`, `error=None`, with 98 bytes missing.
   The corrected EOF check
   ([carry_capture.py:93](../carry_capture.py#L93)) now preserves `{}`, reports
   the framing error and returns `body_complete=False`. The independent
   counterexample and added regression both pass.

## Reviewed boundaries

- The exact ten-request specification is checked before transport, including
  fixed symbols, hosts, endpoints, parameters and the exposed April–June 2026
  quarter. No authentication, account call, credentials, proxy fallback,
  redirect, retry, replacement window or hidden financial evaluation was found.
- HTTP 403, 418, 429 and 451 suppress subsequent requests to the same host. Every
  suppressed cell remains in the ten-cell denominator with a reason. Other
  transport/semantic failures retain raw prefixes and unavailable outcomes.
- Requests have a 20-second wall deadline; received bodies are bounded at 5 MiB.
  Raw bytes, hashes, HTTP status, exact request identity, local UTC request and
  retrieval timestamps and allowlisted source headers are retained. The charter
  accounts for duplicated base64 storage in its 150 MiB output allowance.
- Funding admission checks symbols, finite signed rates, positive event marks,
  ordered unique timestamps and a conditional 273-event schedule. Missing,
  unexpected and duplicate event identities remain visible on failure. The
  00/08/16 UTC schedule with five-second tolerance is explicitly conditional and
  cannot establish the historical funding calendar by itself.
- Bar admission checks all 91 daily UTC opens and closes, finite positive OHLC
  values and their ordering. Current exchange metadata and a current server
  clock within the local request/retrieval interval plus or minus five seconds
  are checks of current identity and clock plausibility. They do not establish
  historical terms, public availability timing or the user's eligibility.
- The source computes no cash profit, price exposure, economic gate or
  statistical significance. Downloading additional fields within the spent
  holdout does not make its dates fresh confirmation.

Focused verification: **31 synthetic tests passed**, using fake transports and
in-memory HTTP responses. The additional reviewer-run Content-Length
counterexample independently confirmed the final incomplete-body behavior. The
full legacy suite was not run.

## Remaining admission and untested claims

The coordinator must freeze the gate and exact request-spec bytes before any
capture, with all twelve output names, the reviewed source/charter hashes and
the existing family ancestry and incremental budget. This review does not
certify a gate that was still being prepared when the source was assessed.

Not tested: live endpoint availability, actual response authenticity/coverage,
historical event-calendar changes, source timestamp accuracy, published-versus-
revised values, achievable fills, account/fee/product applicability, signed-
quantity cash accounting, full-capital returns, margin paths, market beta,
maximum-resource behavior against a live slow server, or operating-system crash
and filesystem durability fault injection. Raw outputs require independent
post-capture reconstruction before any registered financial use.

No higher effort is needed to settle the two corrected source defects. The next
unresolved question is whether the fixed public acquisition actually supplies
complete event marks and matched prices; an unavailable answer must remain a
data limitation and trigger the frozen continuation rule.
