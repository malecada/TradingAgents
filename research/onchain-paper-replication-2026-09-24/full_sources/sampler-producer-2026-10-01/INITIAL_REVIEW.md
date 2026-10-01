# Initial independent sampler-producer review

Acceptance is withheld for three material resource/ownership boundary gaps.
Source and synthetic fixtures were inspected without executing tests, jobs or
numerical file reads. Only this review file was written.

1. **SP1 — publication reload can retain three payload copies under a two-copy
   allowance.** `producer.py:161,164` retain the original sampled graphs and
   their payload references through artifact admission at line 174. That call
   retains newly read arrays while constructing immutable AttributedGraph copies.
   The bound at line 171 reserves only twice the numeric payload. Reserve all
   three copies, or save the necessary compact identity metadata and release
   both original sample and payload references before reload. The author also
   identified this issue. Add a regression at the reload boundary that proves
   the selected lifetime/accounting correction.
2. **SP2 — successful proof publication lacks a final ownership check.**
   `producer.py:176–183` writes complete.json and returns immediately. A guard,
   live journal, source or retained artifact change during proof publication
   can therefore return a successful result despite the preceding lease being
   stale. Perform the final full lease after the proof write/read, before return.
   Inject live-directory or guard loss at that boundary and require refusal.
   If failure follows creation of complete.json, preserve failure evidence;
   subsequent proof admission must reject conflicting completion/failure markers.
3. **SP3 — reservation creation follows potentially long work without a fresh
   lease.** The lease at `producer.py:130` precedes full parent graph hashing at
   line 131 and filesystem setup through line 136. Ownership lost during hashing
   can still create an attempt directory and durable reservation. Recheck the
   lease immediately before exclusive attempt creation; demonstrate refusal
   before reservation with ownership loss injected after the parent hash.

The fixed attempt path and exclusive same-experiment mkdir prevent ordinary
redraw of existing identities. A possible cross-experiment sibling race was
considered but is not admitted as a separate finding: the actual first-owner
Binding already rejects representation siblings for that workflow, so a
supported two-valid-owner counterexample was not established.

The inspected size calculator mirrors numeric component tree encoding and
computes NPY header plus payload and canonical manifest sizes before feature
publication. The existing tests exercise a small write-cap refusal before
checkpoint creation, but do not independently compare the estimated encoded
size with every resulting file size. Logical reservations remain distinct from
physical storage and process-memory bounds. No claim of either is accepted here.

Saved check01 now reports six tests passing in 59.614 seconds. It covers actual
tiny registered production, oracle sample identity/records, proof references,
partial/failed/complete redraw refusal, write/reservation/route refusal and lease
loss after a saved draw. That pass does not cover SP1–SP3. Actual kernel guard
observations are mocked. The missing-component red result remains retained.

Inspected source SHA256:

- producer.py: `cc0bc85168e5da2cbfcb7678dbc61b5e263bff2fe85708b460c27084ddddfbae`
- test_producer.py: `8385671d9307c6a4ced3f9835d17c3b7bab4f79fc34540aae66c6712d7e29e01`

Completion-proof admission by downstream consumers, exact resume, historical
artifact reuse, measured full-scale resources and empirical release remain
separate requirements. This review does not rerun sampling or change scientific
configuration, financial trial budgets, original results or maintained source.
