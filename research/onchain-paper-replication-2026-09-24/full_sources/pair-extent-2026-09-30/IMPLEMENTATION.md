# Policy-bound checkpoint extent verification

The new isolated extent.py addresses the declared-artifact-byte enforcement
boundary identified as J2 in the pair-journal component review. reserve_pair
computes max_checkpoint_bytes + 65536 from the exact positive integer PairSession
policy and records that whole-publication envelope before session allocation.
The journal separately charges compact events and the per-session owner manifest.
The ordinary Journal.reserve API remains caller-declared; it is not retroactively
changed or claimed to enforce extents by itself.

publish_pair joins the pending owner, exact path, identity and fixed session
parent, invokes extent verification, and only then appends the publication event.
A verification failure leaves the reservation pending and the saved artifact
untouched; it cannot authorize a new pair or implicit recovery. This wrapper is
not yet imported by a registered dictionary or MCM producer.

Verification admits only the fixed current PairSession layout and schema:
root/session/artifact-NNNNNN/manifest.json, its owner.json, and phase-appropriate
combined/annealing/hardening manifests and three or four NPY files. A complete
score publication contains no state files. The walk is limited to11 entries and
two nested directory levels. Metadata is limited to64KiB per file. Every metadata
hash join, owner, exact numerical identity, policy and fixed session parent is
checked. Integer/float identity distinctions are retained by canonical comparison.
The pinned float64 state/int64 rank arrays have128-byte NPY headers; declared
extents must equal8*n*m+128 and actual file lengths. Metadata/file inventory is
exact, shape-derived state and checkpoint policy envelopes are checked, and the
sum of all saved state files and pair metadata must fit the reserved envelope.

Symlinks, multiple hard links, unexpected or missing members and foreign devices
are rejected. Stat identities/sizes/timestamps/blocks are compared before and
after validation. Metadata opens use O_NOFOLLOW with before/after descriptor
checks. The exact layout is checked before metadata reads so owner.json stays
inside the declared root. A sole admitted writer and live resource guard remain
required; this is not a lock or defense against an external malicious concurrent
writer. There is no ResearchRun, workflow-purpose or predecessor-death admission.

No NPY bodies are opened or hashed. Array byte contents, greedy-prefix validity,
full numerical schemas and score correctness remain the numerical loader's job.
The returned array_contents_verified flag is false. File st_blocks are reported
separately as filesystem-reported allocation; directory blocks, ancestor files,
shared filesystem overhead and total free-space accounting remain outside that
quantity. No measured RSS/runtime or full-workload capacity claim follows.

Thirteen tiny tests pass in green05.log (.215s), including real annealing,
ranked-hardening and complete publications, exact inventory/extent corruption,
link/identity/policy/parent/hash refusal, before-read under-reservation refusal,
actual journal reserve/verified publish, and preserving an understated pending
reservation without publication. Array-open and np.load sentinels cover the
metadata-only path. A wrong-root sentinel forbids all metadata opens before
layout rejection. Tests use temporary synthetic pairs, not retained experiments.

red01 retains nine missing-component assertions; green01 retains eight passes
and one missing-file exception-type error. red02 reproduces permissive int/float
identity equality; corrected green02 passes ten. red03 records missing wrapper
APIs; green03 passes twelve. red04 reproduces owner metadata escaping a malformed
root scope; green04/green05 pass thirteen after strict layout correction. Earlier
source versions remain retained. No historical workload was rerun.

Next integration requirements remain: live claim-derived ownership/guard lease,
registered workload membership/backend/cache policy, exact failed-owner death and
source compatibility, cumulative workflow artifact accounting, bounded orphan
reconciliation, and actual dictionary/MCM routing. Existing maintained package,
178-file broad verification closure and Graph10 gate-v3 pins remain unchanged.
