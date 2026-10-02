# Unselected one-pair restart retention primitive

Final candidate05 is frozen for independent review. check07 is CLOSED,
**44 passed in 2.05 seconds**, session98399, exit0. FINAL_CLOSURE_02.json binds the
exact Python runtime, all XML summaries, raw log/XML hashes and final source/test
hashes. git diff --check passed. No existing package/test file was edited.

## Implemented boundary

The new restart_retention.Store owns only a newly created canonical same-device
root for one fixed ordered pair. It binds owner/stage/source/runtime/policy hashes,
exact purpose/numeric identity, a frozen FIRST replay selection and positive limits.
Caller authority is checked by a lease; the lease cannot nominate a borrowed
namespace for retirement. Numerical advance, score computation and external
scientific admission remain outside the helper. These are standalone synthetic
progress/completion JSON events with pair-relative event ordinals, not an already
integrated compact binary PairLog interface.

checkpoint saves real engine state and applies the unchanged strict snapshot
verifier. It reads back an externally pinned exact progress event, rejoins original
body/inode observations after callbacks, and publishes immutable progress proof.
The selected FIRST snapshot is copied into separately reserved replay storage and
fully verified before any superseded retirement. Only original generated numeric
.npy bodies can be retired. All original engine manifest JSON bytes, inodes and
directory identities remain intact, along with reservations, progress proofs,
retirement intents/completions and exact dispositions. Retired generations cannot
be opened as restart checkpoints; their hashes are not recoverable backups.

finish requires an externally anchored exact expected completion and actual durable
event readback before retiring current numeric bodies. It records a no-checkpoint
completion disposition when the preselected comparison finished before checkpoint
cadence. Terminal verification is callback-free, checks exact original claim and
terminal references, reconstructs admitted record membership and monotone spending,
and checks every retirement/replay chain. A completed-store duplicate cannot mutate
successful evidence or spend again. Reconciliation only observes surviving bytes;
it needs original progress pins to verify surviving bodies and never authorizes
continuation, repairs an incomplete receipt or grants restart.

Reservations precede allocation and are never refunded. Each generation reserves
one maximum snapshot, eight16KiB control records and three64KiB engine manifests;
the latter explicitly cover metadata retained after numeric-body retirement.
FIRST replay reserves another maximum snapshot and a replay count. Claim/failure
and completion/terminal control allowances are reserved separately. These are
conservative logical reservations, not measured physical allocation or RSS. The
synthetic fixture uses2MiB retained-control capacity,4MiB cumulative reservation,
256KiB single-generation/replay payload limits and at most8generations/1replay.
Only current+candidate numeric bodies coexist; retained manifest/replay/failure
bytes are separate obligations.

## Evidence and failures

- red01: expected absent-module ImportError at collection, exit2; tests preceded
  implementation. Full collection log and XML retained.
- check01:9failed9passed0.97s, session94011, exit1. Original inode observations
  became tuples through immutable freezing while the comparison expected lists;
  a fixture also expected allocation despite an impossible initial cumulative cap.
  Representation comparison and that fixture expectation were corrected.
- check02:18passed0.94s, session93824, exit0.
- check03:37passed1.77s, session46518, exit0, including filesystem-failure matrix.
- A shell redirect typo prevented one launch before pytest ran. Exact diagnostic
  is retained in launcher-error01.txt; no synthetic fixture ran for that launch.
- review-red01:1failed37deselected0.54s, exit1. A duplicate completed-store call
  could poison/mutate successful evidence. Candidate01 preserves that implementation
  and the new failing assertion. Terminal refusal was moved before failure handling.
- check04:41passed2.02s, session63715, exit0. Candidate02 and the earlier CLOSURE.json
  preserve this intermediate reviewed checkpoint; it is superseded by this report.
- review-red02: the new original-engine-manifest assertion failed because initial
  retirement removed metadata with numeric arrays. Retirement was narrowed to
  numeric bodies only; no historical or externally owned path was touched.
- check05:42passed1.96s, session73684, exit0.
- review-red03: the retained-engine-metadata reservation assertion failed. The
  issue was reported to the coordinator. Conservative per-generation control
  reservation was increased by3×engine.LIMIT before allocation; the new synthetic
  fixture's positive control capacity was adjusted to2MiB. Candidate03 preserves
  the pre-correction source and failing assertion.
- check06:43passed2.03s, session60896, exit0. Candidate04 preserves this source
  and test snapshot. Earlier source snapshots cover the named candidate checkpoints;
  no pre-run hash attestation is claimed for the initial development attempts.
- review-red04 reproduced a callback replacing the store lock while a fatal primary
  was in flight: cleanup retained the fatal but released the mutable replacement,
  leaving the original lock held. The transition now captures and releases the
  original lock once, and refuses callback replacement before acknowledgement.
- check07:44passed2.05s, session98399, exit0. Candidate05 is the final source/test
  snapshot. FINAL_CLOSURE_02.json supersedes prior closure source-status only.

The reviewed pytest profile was retained with plugin autoload disabled,
PYTHONPATH=., RUN_ONLINE_TESTS=0, no cacheprovider and importlib import mode.
Every attempt used the checkout-local locked interpreter. Raw output explicitly
notes26withheld files; this is a focused module check, not the full offline suite.
No actual-owner fixture, empirical script, historical job, network or credential
read was used. The only imported test utility constructs invented tiny graphs and
reads the unchanged matching configuration.

## Assertions and limits

The tests force three snapshots and current/candidate rotation, verify FIRST replay
before first retirement, independently reload replay state, and compare numerical
arrays/iteration/convergence against unchanged engine execution. Literal zero-edge
score0.5 and directed rectangular/square score calculations are independent of the
new helper and production scorer; original C05/C06 tolerances remain unchanged.
Hardening snapshots exercise the real order.npy branch. Numerical provenance and
input identity are checked separately from synthetic source/policy bindings.

Failures are injected at candidate fsync, proof/replay publication, retire intent,
first/last numeric unlink, retirement completion, parent fsync, descriptor close,
completion and terminal publication. Surviving bytes and spent reservations remain;
all independent owned cleanup actions run once, and fatal primary identity is
retained with cleanup diagnostics. Tests refuse extra/missing/short/stale bodies,
hardlinks, symlinks, equal-byte directory substitution, simulated device mismatch,
and callback mutation using the real snapshot verifier. A device mismatch is a
stat fault injection, not a real cross-mount experiment. Count/control/cumulative/
single-generation/replay-byte exhaustion is tested; the fixed FIRST-only replay
count is structurally at most one, so its minimum positive count bound is exercised
without inventing a second replay selection.

This helper does not independently establish original source/owner/scientific
truth from supplied hashes or completion expectations. Those trusted joins, full
scientific input/replay body retention, exact stage populations, whole-stage and
workflow bounds, registration/dispatch, outer physical/RSS/free-space limits,
archive retention and neural/model replay remain integration responsibilities.
No BR13 full producer-to-terminal integration, C16 remote recovery, resource
admission or economic claim follows. Existing compact source and historical
checkpoint readers remain untouched; this version is not selected anywhere.
