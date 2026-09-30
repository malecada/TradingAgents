# Durable ordered-pair journal component

This isolated artifact layer retains a hash-linked reservation/publication chain,
exact per-purpose latest references, ancestor-inclusive logical byte/count/event
charges, deterministic per-owner/purpose pair-session names, exclusive metadata
owners and failed-parent replay. Numerical arrays are not opened by journal reads.
The shared pairs directory supports the maintained PairSession containment
contract across failed journal owners. A session can publish multiple checkpoints;
a child uses a new session owner and preserves the exact latest predecessor.

Fourteen tiny tests pass in green05.log, including two actual PairSession progress
publications followed by child-journal resume and completion. Completed-pair
repetition is refused. A missing journal publication leaves a charged pending
reservation and blocks successor construction pending explicit reconciliation,
even when the numerical artifact is complete. A publication-write failure poisons
the live journal and preserves the artifact and reservation; it cannot continue.
Original ancestor bytes are checked unchanged in the fixtures.

red01.log records nine missing-component assertions. green01 records nine passes.
red02 exposed two defects: reservation could consume the final event slot before
completion publication, or name an existing artifact. Both are fixed; green02
records eleven passes. red03 records the missing shared-root target API; green03
records twelve passes including actual matcher integration. Pre-correction source
and test snapshots are retained. red04 reproduces an artifact continuity defect: a successor publication could
claim continuation while its actual PairSession parent was null. The journal now
joins exact inherited parent reference/owner, preserves the fixed session parent
across later same-session publications, and verifies the relation during replay.
green04 records13passes; green05 records14passes including real child-create
rejection and two real publications from a correctly resumed child. No
registered/empirical job or historical retry occurred. The named 3559-pass full-suite result belongs to the maintained package,
not this newly added dated candidate.

## Explicit remaining boundaries

This is not ResearchRun admission. Owner/workflow/purpose declarations still need
binding to current claims, registered backend/config/runtime, exact dictionary or
MCM membership, live guard lease/cgroup and the whole failed-owner death chain.
Ancestry replay validates supplied exact failed journal references, not omitted
research attempts or sibling ownership. Source compatibility remains enforced by
PairSession; the new artifact journal does not license cross-commit reuse.

Quotas are conservative logical reservations, not physical allocation proof.
The API field is explicitly declared_artifact_bytes: it records a caller-declared
reservation. It does NOT assert or enforce the whole numerical artifact's logical
extent; publication checks only the compact outer manifest's bytes. The future
admitted caller must derive this declaration from the registered pair policy,
verify the full saved extent envelope, enforce its actual byte bound and shared
filesystem containment before
numerical allocation, and account other workflow artifacts. The layer precharges
two compact events per reservation, start/terminal metadata per journal and the
PairSession owner file per new session; partial reservations are never refunded.
The finite guard remains required for metadata dictionaries, ancestry and native
allocation. Compact manifests are limited to64KiB and ancestry to8, so a large
workload will require measured bounded ledger segmentation before admission.

Unknown partial/orphan publication states currently stop recovery. A bounded,
claim/death-admitted reconciliation checker remains to be implemented; it must
never pick the largest filename, trust an unjournaled completed pair or silently
rerun it. Fatal cleanup propagation, observer gap enumeration, backend-aware
cache identities, directional dictionary and partial-row MCM remain unconnected.
No empirical matching readiness or full-paper completion is claimed.

Graph10 gate-v3 source closure is unaffected: maintained package and its178
verification bindings remain exact. This dated artifact component is not imported
by any empirical consumer or added to required_sources.
