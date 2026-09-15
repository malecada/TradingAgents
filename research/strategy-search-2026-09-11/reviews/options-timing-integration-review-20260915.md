# Independent integration review — options timing successor

September 15, 2026. Review in progress. No sixth allowance, new claim, market
request or financial outcome is approved by this document. The independent
information-value decision is `options-postfailure-information-value-20260915.md`;
its concrete candidate acquires hourly known sources at nominal N+2 seconds,
then selected sources, while all economic actions/deadlines remain N+5 seconds.

The proposed target is `options-timing-20260915`, isolated under
`tradingagents/research_options_timing`, with protocol schema 3 and fixed
`hourly_acquisition_delay_ms=2000`. All twenty terminal predecessors, four
historical runtime packages and the spent `research_options_capture` package
must remain immutable. The proposed data root is
`/opt/thesis-research/options-timing-20260915/data`; a later release review must
bind its exact assignment, source inventory and unique writer authority.

## Interface questions under review

- Shifted source slots have scheduled time N+2000 and deadline N+5000. Every
  economic consumer must use the validated nominal N for action, freshness,
  selection, expiry/exit, funding and benchmarks, while transport and source
  admission separately enforce the later acquisition gate. A generic five-second
  decode window starting from shifted scheduling would incorrectly admit N+7000.
- The old funding announcement freshness condition uses nominal time minus the
  frozen drift allowance. Replacing nominal time by shifted acquisition time
  silently tightens that rule by two seconds. Conversely, using nominal decode
  without an explicit phase gate could admit old early receipts. Both need
  adversarial tests with complete-looking raw clocks and unchanged cash actions.
- The old options verifier rejects same-mechanism descendants in its extra
  history. Once the successor claim exists, direct verification against the
  whole enlarged run tree is not equivalent to verification in the old target's
  exact bound history. The additive closed-history validator must preserve full
  old source/stop/quiescence/terminal semantics rather than silently substituting
  structural claim hashes for that validation.

These questions were sent to their respective implementation owners while the
new modules were still copies in progress. They are not claims that a finished
implementation contains an unresolved defect. Final findings, exact source
hashes and tested scope will be recorded after the implementations are ready.

## First independent checks, 09:24 UTC

An invented-source reconstruction compared all 17,144 old and new calendar
members. Exactly the hourly acquisition release shifts by 2,000 ms; every
request, cap, absolute deadline and non-hourly time matches the preserved
calendar. The nominal helper independently reproduces all old nominal times.
A complete-looking receipt in the new phase passes raw decode; coherent raw
clocks from the old early phase and a forged N+7-second deadline both fail.
No market data or financial engine was used.

The updated funding reader now converts each shifted hourly source specification
to validated nominal time and explicitly requests hourly phase admission.
Announcement age retains the old nominal-minus-drift test. All hourly entry,
assembly and benchmark decode call sites inspected use the explicit phase flag;
non-hourly rule/history reads retain their original windows.

The full `closed_history.py` diff was compared with the preserved independent
options verifier. Its original source/grant/history, control-phase timing,
external-quiescence and terminal checks are retained. An explicit certificate
adds the exact failed eight-unavailable/no-output/no-analysis boundary. Only the
named timing successor can receive the added same-mechanism-descendant exception,
and it must bind the supplied committed source, grant and parent and start after
the failed parent ended. No history directory filtering or old-package mutation
is used. Adversarial certificate/descendant tests and actual twenty-history
resource proof remain pending before admission.

A working-tree diff over all five spent runtime packages was empty. The timing
worker's first test pass had a reported bootstrap-namespace failure while the
new root-owned bootstrap was still being prepared; that unresolved integration
step and its subsequent tests cannot be treated as a passing release here.

## Subsequent source and resource evidence

Seven additional independent invented-source checks passed without calling a
cash engine: two old-versus-delayed receipt paths preserve exact funding-event
and expected-time projections and inventory-owner segments (including an event
seven seconds after an hourly boundary); three events at/within one millisecond
of the unchanged action remain ownership-unavailable; missing held forecasts
and old early-phase receipts produce no admitted funding engine inputs.
`analysis.py` remains byte-identical to the spent capture version. The inspected
funding diff is restricted to nominal conversion and explicit hourly admission;
the owned financial engine, accounting rules and action timestamps do not change.

The implementation owner subsequently reports 22 worker and five schedule tests
passing, including no transport child at or after the fixed N+5-second deadline.
The earlier bootstrap namespace failure is reported corrected. These are owner
reports, distinct from the independent checks above.

The source resource report `options-timing-resource-20260915.json` and its guard
were read. It retains the 17,144-slot arithmetic, 2 GiB logical ceiling and
7,045,762,942-byte pessimistic regular-file allocation bound. The guarded local
representative test passed in 40.102 seconds with 238,030,848 bytes sampled
aggregate RSS. Its maximum 5 MiB/10,000-row invented initial metadata case takes
1.831 seconds for known-body journaling, actual selection, selected-journal
construction and selected-body journaling. That leaves 1.169 seconds of the
shared three-second phase for unmeasured transport/HTTP work. The report
explicitly excludes HTTP latency, actual transport subprocess creation and VPS
storage timing; a positive remaining local margin is not proof of live viability.
The two sequential known/selected groups share that remaining time. Complete
maximum-size daily normalization and a universal latency guarantee are not
proved. Source/runtime failures remain fail-closed under the unchanged caps.

The updated closed-history validator also binds the exact sixth-grant schema,
cumulative counts, family, original consumed grant and committed independent
approval before its narrow descendant exception. This is additive verification;
none of the five spent packages is modified. Final target-specific source hashes,
complete lifecycle/return proofs, actual twenty-history/output costs and release
admission remain separate pending checks.

## Remaining admission scope at integration checkpoint

The coordinator reports 66 successor adapter/funding/returned/analysis tests
passing in 13.00 seconds. The worker owner reports 23 worker and five schedule
checks after adding both interruption boundaries: consumed known sources without
an immutable selection fail without retry, whereas an already published selection
can be revalidated from the identical receipts and proceed to still-unattempted
selected roles inside the same remaining deadline. Runtime bytes did not change
for those added tests.

A material **resource proof scope gap**, not yet an observed runtime failure,
remains before final admission: `control._validate` and independent
reconstruction now each execute full `closed_history.verify_parent` plus the
successor's twenty-history checks. The literal analysis CLI still reconstructs
history approximately seven times. Repeating only `control.inventory` eight
times, as in the old envelope, would omit repeated closed-parent protocol costs.
The final guarded proof must include the actual combined reconstruction pattern
or a clearly conservative component envelope with both costs and output
publication. The read-only actual twenty-history preflight (before inventory,
old protocol verification, after inventory) does not alone establish this bound.
This concern was sent to the coordinator and verifier owner before grant.

## Measured history-cost failure and permitted repair

The previously identified scope gap became an observed engineering failure.
`options-timing-history-output-envelope-20260915.guard.json` records termination
at 120.021 seconds, before the full repeated closed-parent/new-inventory envelope
completed; sampled peak aggregate RSS was 191,893,504 bytes. Progress records
show individual duplicate pairs taking approximately 15.8–21.5 seconds. The
invented eight-book output was retained as engineering evidence, not an empirical
result. This failed preflight is not an options market attempt and must remain
preserved; it does not justify raising the fixed 120-second analysis cap.

The proposed narrow repair is acceptable in principle: return the exact freshly
verified twenty-history inventory and claim objects from the closed-parent
reconstruction, then reuse them only inside the same successor validation
invocation instead of immediately repeating its old provenance/hash traversal.
Every subsequent controller/independent operation must still start a fresh
reconstruction. No persistent or cross-call cache is authorized.

The critical review condition is successor provenance. The parent proof checks
old objects and scientific pins relative to the old parent commits. Reuse must
not remove checks that those objects are preserved in the NEW registration and
that old physical registrations/scientific pins exist unchanged at the NEW
source/design commits. The exact parent controls, original grant, all twenty
bound predecessors and all recognized live extras must remain in the returned
boundary. A shortened implementation and repeated full-cost proof remain
pending; the resource finding is not closed merely because duplicate work was
identified.

## Completed source and return proofs

The corrected sequential-time full synthetic worker fixture completed through
three bounded segments after preserved compressed-calendar timeouts. The final
`options-timing-episode-20260915-v2-resume2.json` retains all 17,144 slots:
17,133 received, three unavailable and eight missed. All previously consumed
intents remained consumed and prior raw members remained unchanged. The final
segment took 110.999 seconds. This proves the declared resumption and denominator
behavior under invented responses; it is not an uninterrupted 45-day operational
or market-availability demonstration.

The independent return path subsequently reconstructed that exact assignment
(`441584fbd0648469251e52d3494cd2aba078529102b0c37e26e6a61f3d29df68`).
Its before/after inventory was identical: 38,676 raw members, 24,188,570 bytes,
inventory SHA-256
`1236c6d763fd127fdf446dc8de51fccacd9c978c27734f78cdfd3f063d1cca8e`.
The guarded return plus wrapper completed in 27.088 seconds, approximately
96.5 MB sampled aggregate RSS. All eight cases remained unavailable because the
invented settled funding history was deliberately incomplete. This is the
expected preservation of unknown cashflow, not eight completed economic books.

A separate pure known-input 1,057-hour fixture exercised eight cash-complete
books with 1,057 trades and 1,056 funding entries each. Its 11,618,712-byte output
has SHA-256
`43f5870a56b4c46a90fb06c1cb4ee435ee8deb865101edcd0c836b487d84d1a5`;
the guard completed in 5.902 seconds, approximately 81.0 MB sampled RSS. This
fixture explicitly bypasses capture admission. Its accounting/output size proof
does not repair the returned fixture's unknown funding or establish real fills,
fees, access, margins, profitability or independent episodes.

## Invocation-local optimization review

The actual three-module diff against engineering commit `c1c5133` was inspected.
`closed_history.reconstruct` creates a fresh inventory/claim mapping for the full
live tree, verifies retained historical terminals, and adds the failed parent's
actual control, output, claim and terminal hashes only after full protocol and
quiescence-certificate validation. Active/terminal unrelated later descendants
remain visible. The successor controller and independent verifier compare the
fresh mapping's denominator and exact twenty predecessor entries to the new
grant. The controller's separate public `inventory` still performs a complete
rescan.

Both successor paths retain the critical new-source checks: historical gate
objects in the new registration, old physical registration equality at the
history and new source commits, old scientific pins, family identity and runtime
ancestry. Only duplicate old reconstruction within the same call was removed.
No persistent cache, filesystem filtering or old-module mutation was found.
The owner reports six passing focused checks including omitted history, altered
output/control maps, missing claim mapping and byte mutation between calls.
This specific implementation change passes source review. The measured resource
failure remains open until a new guarded full repeated-operation envelope
passes; the implementation review alone is not target admission.

## Revised resource outcome

The v2 report was inspected together with its guard and workload script:
`options-timing-history-output-envelope-20260915-v2.json`, SHA-256
`5dbf6db980ffe591647eea8ef9dc69e66bbc0b270310b96c0f12ef08f01af8f9`.
At committed engineering source
`ad2be0c0f07e03e79af9b9585d5978c1b27b75c9`, it passed in 103.029 guarded
seconds with 190,263,296 bytes peak sampled aggregate RSS under the unchanged
120-second, 512 MiB, two-CPU limits. The remaining measured wall margin was
16.971 seconds. All twenty claim/terminal/output/control inventories and all six
runtime package maps matched before/after.

The seven repeated reconstructions match the actual analyzer's sequence:
initial independent verification, resume, analysis intent, two output writes,
finish and final independent verification. Each measured repetition includes the
actual closed-parent certificate/protocol verification and the successor's
new-source preservation work; both execution/design runtime reads are included.
Invented normalized serialization, all eight 1,057-hour books, immutable
11.62 MB output publication and a final independent twenty-history rescan are
also included. Successor-only target/grant/control metadata and repeated
normalized-input binding hashes remain separate synthetic checks, and full
source normalization is a separate pre-analysis operation. Therefore this is
accepted as a representative modular preflight with explicit scope, not a
universal worst-case bound or a literal new claimed analyzer run. Resource guards
remain mandatory and failures cannot authorize replay or a higher cap.

The measured duplicate-history resource finding is closed for this committed
implementation. The earlier timeout remains retained. Final named offline
verification, exact future target pins, separately committed sixth allowance,
claim uniqueness and deployment inventory/clock checks still precede admission.

## Final engineering disposition before exact target admission

The complete timing policy was reread at SHA-256
`64481187ed8c978048b918a8e867b7359b629830d9deff629762ba662d0e0d02`.
The N+2 acquisition phase, unchanged N+5 action/age boundary, fixed selector,
signed cashflow/cost rules, funding ownership and unavailable-case requirements
are consistent with the reviewed implementation. The narrow correction remains
scientifically justified by the parent's acquisition failure before contract
selection or financial outcomes. It does not support changing the phase after
observations or an automatic seventh allowance. No unresolved material timing,
cashflow, denominator or historical-preservation defect was found in the scoped
review. A final diff against the fifth episode commit confirms all five spent
runtime packages remain byte-unchanged.

The retained authenticated VPS preflight reports the dedicated Python 3.13.13
runtime unchanged across all 5,367 members, host `pck-preds-1`, the new actual data
root absent, 40,348,737,536 free bytes, 4,484,365 free inodes and 4,096-byte
allocation units. The separate inert round-trip proof verified all 38,686
package/data members (24,296,328 bytes) after remote extraction and returned an
archive with the identical SHA-256
`54f38f5c87ed3adfd9a4c64e03a59272b129e4ebed75fe2bf8dc0873803c18eb`.
No collector ran during that proof. These are evidence-transfer and installed
runtime checks; they do not measure actual three-second request latency or prove
future source coverage.

**Disposition: source/policy engineering passes, conditional on the named full
offline target passing unchanged source and a separate exact future target/grant
admission review.** This document grants no claim or launch. The final review
must bind one future UTC hour chosen for completed preparation, the exact
sixth-allowance target hash, all twenty predecessor identities and source/review/
resource hashes. Verified remote commit equality, unique actual claim, exact
release inventory, finite launcher and absolute lease checks remain necessary
before the sole capture. This integration document is now complete and should
remain stable; final target-specific admission belongs in a separate review.

Claims not tested: real account eligibility or fees; live source update/latency
reliability; actual fills and quantity availability; option margin/liquidation
or tail stress; profitable expected returns; independent-episode confidence;
and every maximum legal raw payload under all possible host contention. No
empirical financial experiment was rerun for this review. The unchanged strict
source, clock and resource failure rules preserve those uncertainties.
