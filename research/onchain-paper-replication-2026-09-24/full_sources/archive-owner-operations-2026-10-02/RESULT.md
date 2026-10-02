# Current-owner archive reservations

archive_owner_operations consumes a registered archive Selection under the
actual owner's transition lock. A deterministic exclusive namespace retains
writer and finite read intents for actual owned stages. Writer reservations
cover maximum event payload and three member passes; read reservations cover
one further pass. Caller-reported completion references do not validate content.
No producer, archive writer, publication or terminal dispatch is changed here.

The prospective policy capacity now includes an explicit additional control
allowance of (4 + 3 * stages * (1 + read_limit)) * 8192 bytes. These are logical
metadata reservations, not filesystem allocation or a transport upper bound.
Actual immutable-upload charging and diagnostic overread remain separate work.

## Retained development evidence

- red01 CLOSED4 missing-module failures57.63s/session58850exit1.
- check01 CLOSED3failed1passed131.14s/session54994exit1: the aggregate metadata
  counter selected a nonexistent max_metadata_bytes field. The registered field
  is max_workflow_metadata_bytes. Original source/tests retained.
- REVIEW_INITIAL SHAadd69b115854316d90260a48acc08fda79e6ec89e5e8df83381d7941cc4c181c
  identified AOO1–4: limit key, nested attachment-cleanup lock, late callback
  state and fatal descriptor cleanup.
- review-red01 CLOSED3failed6deselected78.94s/session41865exit1 reproduced public
  close during live lease, masked attachment failure and ordinary handling of an
  uncertain owned close. Source retained as operations-review-red01.py.
- Corrected source added post-callback state checks, a locked public lease,
  internal attachment cleanup and fatal descriptor-close handling.
- REVIEW_CORRECTIONS SHA1fa201c970be2a6b0ab320e244f0509db3629bacafa96f5071840125b3277948
  identified residual fatal cleanup propagation and mutable lock release.

Tests construct actual fresh ResearchRun/Binding/Owner fixtures with mocked OS
guards. No historical job, empirical outcome or external transfer is replayed.
Constructor-close fault injection occurs after a real close; it demonstrates
fatal signalling, not recovery from an actual leaked kernel descriptor.

check02 CLOSED9passed309.78s/session21984exit0. This covers the initial actual
writer/read population, exhaustion/no-refund, intent drift, owner transition
locking, first three review regressions, completion-write failure and actual
owner revocation after claim publication. Its source/tests are retained as
operations-check02.py/test-check02.py. Final correction evidence follows.

review-red02 CLOSED2failed9deselected66.66s/session74181exit1 reproduced the
remaining two findings against the preserved check02 source. Final corrections
propagate failed-marker CleanupFailure chained to the primary cause, capture the
acquired transition lock for release, and recheck callback-free owner/lock
bindings. The reservation counter includes its fixed4metadata records; the full
writer/four-reader fixture checks literal3,555,648 metadata bytes. The late-lock
injection explicitly releases its deliberately leaked synthetic lock in test
cleanup; it does not repair a production lock leak.

check03 CLOSED5passed6deselected196.09s/session10179exit0. Final targeted cases
cover the complete finite writer/read population and metadata total, public
close during lease, attachment failure preservation, failed-marker fatal cleanup
and replacement-lock rejection/release. This is separate from the earlier
nine-case baseline; no final eleven-case or full legacy-suite result is claimed.
No process or source freeze remains.

Independent REVIEW_FINAL accepted AOO1–5 within the stated scope, SHA256
f2f130ae60d1b62888b4c4e11313be4637bd313062f0ac032cbd8300d38dda87.
