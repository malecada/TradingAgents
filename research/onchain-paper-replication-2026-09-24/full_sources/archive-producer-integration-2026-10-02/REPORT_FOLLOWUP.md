# Producer integration review correction

This follows REPORT.md without rewriting any closed attempt. check04 is CLOSED:
12 passed in 366.83 seconds, session30978, exit0. Its public archive regressions
and late writer/MCM preservation results remain separate from later source.

review-red01 is CLOSED: 3 failed, 5 deselected in 413.84 seconds, session66432,
exit1. All failures matched the additional requirements: coherent closed.json
plus runtime expected-map modification was accepted; a late MCM failure left the
ledger open; a fatal training cleanup cause became ordinary CompactProducerError.
The full log, XML and review-red01-source retain these failures and source bytes.

Candidate04 changes only compact_native_producer.py and archive_owner_seal.py
relative to candidate03 package source. The producer retains the attached ledger
and original lock, revokes its authority under that exact transition, checks the
original namespace and attempts close once. It never rewrites a closed ledger.
Invalid bindings refuse ledger mutation; a replaced namespace revokes the
original runtime authority without writing to replacement evidence. Failure
journal/attempt evidence is attempted separately. A fatal primary is rethrown
unchanged with cleanup notes; fatal cleanup following an ordinary primary is
raised with the original cause.

Successful terminal ledger metadata is reconstructed canonically from the
original ledger record and reserved spending. The original terminal membership
pin independently binds that ledger identity and spending. The mutable expected
map alone cannot establish authority over changed closed bytes. Validation is
callback-free and does not reopen remote payloads.

review-green01 is ACTIVE at this report checkpoint, session50473. It selects the
new test module except the previously checked local full chain and late writer
case. Its scope is the fresh complete archive chain, independent six-cell MCM
count (three nodes times two motifs), original closed-byte refusal, late poisoned
closure without refunds, original fatal/ordinary primary with uncertain close,
policy refusal, expired/wrong-thread tokens and invalid close authority. Final
status must be read from a later closure record; no green outcome is asserted.

Candidate04 manifest SHA256:
1d816a8d3d9ede6748816688131e95b6462aa9adf3149e8e363cc3b767f00ca3.
This binds all eleven changed package files and the test module. No transport or
admission code changed. Independent review is pending terminal corrected evidence.

The scope remains injected in-process local transport. Outer job_payload still
omits archive_transport. SSH dispatch, credentials, empirical fits, whole-workflow
physical accounting and real remote retention have not been exercised. Synthetic
fixtures mock resource guards; this establishes no machine admission or economic
result. The accepted local successful chain is check01; it is not represented as
a rerun under candidate04. The changed generic failure handler is exercised by
both ordinary and fatal archive failures, while the unchanged success body retains
that prior local-route coverage.
