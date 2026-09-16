# Independent exact F1 crash-recovery adapter review

## Disposition

**PASS for the single manual empty-output attachment defined by the reviewed
adapter/decision/config, after commitment and source verification.** This does
not admit a fresh empirical claim or any nonempty-state replay. The original F1
claim, source commit, gate, inputs, economic recipe, physical request reservations,
cell/output denominator, exposure and spent family/phase/repair counts remain
unchanged. No actual F1 attachment, source request or financial calculation was
performed in this review. Only this new review file was written; the initial
recovery investigation is pinned and was not edited.

## Material finding and correction

The first adapter version held a session-long lock shared by the original root,
but its durable event directory lived under the adapter checkout. A second
checkout could acquire a new empty external directory after an interruption and
attach again while the original scientific outputs were still empty. Per-object
factory reuse and concurrent locking did not prevent that sequential case.

The corrected `reserve_attachment` creates the exclusive immutable
`research_runs/.<experiment>-recovery-attachment.json` in the original root under
the shared session lock before attachment. It records original claim/source,
recovery source/config and external receipt directory. A later adapter location
cannot acquire a second marker, even after power loss or lock release. The
full external started/completed/failed receipts remain separate operational
evidence. The marker is hidden runtime metadata, outside the original claim
and scientific output grid; unchanged `claims()` explicitly ignores such hidden
entries. The new sequential different-checkout fixture confirms the first marker
survives and the second reservation is rejected.

## Exact attachment and source safeguards

The config hard-pins original root, experiment, full source commit, registration,
runner, start time and claim SHA256. `empty_live_claim` requires exactly the
original claim and an empty nonsymlink outputs directory; terminals, unexpected
members and pending outputs reject attachment. `restore` repeats that check
under the original lifecycle lock, reconstructs committed claim provenance,
performs exact own-claim admission, compares original input/experiment/family,
and checks every input hash before returning a restored object. It neither
creates nor rewrites `claim.json` or its timestamp.

The restored published-output map is empty only because the entire output
inventory is required to be empty. The original main receives an exact-once
factory for the exact root/registry/experiment/source arguments. Its ordinary
input/source checks, writer, context failure handling and final denominator
verification remain active. No source or financial code is copied into the
adapter. It re-enters the original startup path before first publication.

The recovery source guard requires the separate checkout's HEAD to equal the
supplied full commit, checks committed/local adapter/decision/review hashes and
exact config bytes, and is added to every original source check. Original runtime
hash comparison and scientific-source checks remain in force. The initial
original-process check is conservative for the documented f1_source.py launch;
a nonzero pgrep result other than confirmed absence rejects attachment. The
shared session lock prevents simultaneous adapters. A future attempted launch
outside the reviewed entrypoint is not authorized by this pass.

## Provenance and exception handling

The original-root durable marker and external started receipt precede attachment.
The latter names the original claim and scientific source alongside the additional
recovery source/config. After original completion, the recovery completion receipt
links the original terminal hash. Exceptions during restoration/original-main
execution retain an external failed receipt and the observed original terminal
status. If the original main has entered its normal context, original failure
handling remains responsible for its scientific failed receipt. Before that
point the claim may remain nonterminal, but the durable recovery marker prevents
a silent repeat.

A filesystem interruption around external receipt publication can leave an
incomplete operational event. Preserve it and inspect both namespaces; do not
interpret the missing external terminal as permission to attach again or as
proof of economic failure. The one-shot marker deliberately makes such cases
require manual assessment. No automatic general resume API is introduced.
Future F1 closure and F3 handoff must retain the marker and external recovery
receipts with both source identities. Reporting only the old F1 source would
omit material execution provenance.

## Independent verification

Eight named invented tests passed in disposable Git/lifecycle fixtures. They
cover unchanged original claim and one spent trial through successful completion,
original structural verification, nonempty/pending outputs, changed inputs/claim,
terminal refusal, shared concurrent lock, repeated factory use, cross-checkout
one-shot persistence and continued recovery source checks.

An additional independent full-entrypoint synthetic test used two disposable
Git roots: one original fixed two-integer sum/count claim and one committed
recovery adapter/config checkout. The adapter's real `main` ran with only its
process-absence probe injected. It restored the same claim, invoked the original
synthetic main through the factory, completed with exactly one trial and unchanged
claim bytes, and passed the unchanged original `verify_run`. Shared attachment
marker and external started receipt agreed; the external completion hash matched
the original terminal. No market provider, financial model or actual run was
involved. This exercised the real source guard, config binding, receipt order,
factory integration and terminal publication together.

All configured source-file hashes match the reviewed bytes. The original F1
empty-state/claim/input findings remain those in the separately pinned initial
investigation; actual launch must recheck them as this adapter requires.

## Limits

This pass is scoped to the explicit user-requested restart after an empty-output
interruption. It does not allow changing the 70% recipe, source calendar, API
policy, fees, stress, benchmark grid, budgets or original execution HEAD. It does
not authorize another recovery event after a nonempty/uncertain acquisition.
No strategy, source availability or profitability claim follows from synthetic
recovery verification. No orders, accounts, paid resources, production mutation
or new recurring task is authorized.

Reviewed SHA256 values:

- `f1_restart_recovery.py`: `eee1a21a9c2149d132e1dc12a4eb104770d7fa39710c31973f68707c18e0f99e`
- `F1-RESTART-DECISION.md`: `2b43ad4433830625590d4755ff27e16ef88cfe915a940c1363b1896f4183cf21`
- `f1-restart-recovery.json`: `e7a9a76ebdf0335c14562d37f407b4afe679e84aafbbe3ce7e67c9c52fdbc4a2`

Final named-suite update: all9 invented tests passed after the author added
a separate full-entrypoint test. The reviewed adapter/config/decision bytes
were committed at `e91889c4f7a94d02c7032d1bf164f30f9d398ed8`; this update adds
verification coverage without changing the pass or authorizing a new claim.
