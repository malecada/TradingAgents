# Actual two-View fixture candidate02 — frozen preparation

Candidate01, proposal01 and its hash manifest are preserved. Independent static
review found the failure-case archive-policy remote names exceeded the actual
20-character gate. Candidate02 uses sv1-ok/sv1-fail and sv2-ok/sv2-fail, all short
and distinct. The longer outer context namespace stays within its separate
80-character gate. No production validation was relaxed.

Tracing selected() also found candidate01 changed r2 binding/journal names only
on the producer plan. Candidate02 sets those names on BOTH producer item and
selected job. All registered outputs remain distinct. This is fixture wiring,
not a production defect or scientific method change.

Independent review identified insufficient durable first-result preservation
proof. Candidate02 snapshots exact first ledger file membership and bytes, compact
owner complete, scientific representation complete, publication complete and
registered binding/journal outputs. First-view-carry-forward.json is exclusively
published with fsync before dispatching the first r2 local child. It records
original file hashes, first ledger counters and completed first command count.
The context counters are explicitly labeled as INCLUDING the already-reserved
first r2 command/operation; they are not misreported as first-view-only spend.
After closure, exact ledger membership and every captured file byte must still
match. This supports independent post-run raw reconstruction in both cases.

Only the new second-view files and new proposed source root were changed. No
shared package, previous fixture/source snapshot, closed identity or results were
edited. This fixture has not been imported, compiled or executed.

## Source and launcher

The immutable-by-convention snapshot is exported from committed source
c51e868f8338ee0a8310251afaefe9e0695daf4f plus the ONE explicit corrected candidate
installation at tests/research/onchain_replication/test_archive_dispatch_second_view_proposal.py.
All1,883 file hashes were checked after export:18,889,605 logical bytes and
24,768,512 allocated bytes including directories. Source-manifest02 records Git
blob provenance for1,882 committed files and the exact local candidate overlay.
Ordinary owner can chmod; pre/worker/post hash checks remain the enforcement.
No .venv symlink or shared-source link is created.

Distinct launcher02 derives from the accepted one-view launcher with only new
identity, source base, test path, cases and release environment variable names.
The old launcher bytes remain baseline-launcher01.py. Nine pure tests against
that baseline had eight passes and one meaningful failure: it accepted its own
old identity spec, which this new route must reject. Corrected launcher had all
nine pass. No cgroup, guard, numerical imports or empirical claims ran.
Metadata runtime-check01 passed Python3.13.13/local locked .venv versions and
isolated package origins; third-party modules resolve in that .venv. Numerical
packages including Torch were located without importing them. This is not a
binary/ABI attestation.

Controls preserve accepted semantics:3GiB maximum,2GiB high,zero swap,3GiB host
reserve and6GiB TOTAL startup availability. Systemd runtime ceiling1800s covers
the worker unit, not the entire coordinator invocation.4MiB hard/soft file limit
applies to all unit regular-file writes, including logs/Git/fixture files, not a
sum over logs.1GiB allocated/logical stop and10GiB free floor are sampled;
overshoot, concurrent Git rename refusal and blocked metadata-call delays remain
possible. The bounded StorageWatch walks at most12000 entries/depth32 with a
2second traversal deadline, not a bound on blocked kernel syscall latency.
The original guard stops its whole unit and verifies empty descendants. No hard
aggregate quota, arbitrary-filesystem sandbox or fulltransport capacity is claimed.

Prior one-view three-case execution passed731.72s. This two-case proof has one
complete pair of representations plus a completed first representation and
partial second in the failure case. Its elapsed time and exact output footprint
are unmeasured;1800s remains a finite refusal limit, not a completion guarantee.
The current resource contract is unchanged; failures retain evidence/no retry.

The spec is deliberately NONEXECUTABLE PREPARATION. Root must freeze/review a
NEW released spec and actual expected shared HEAD after its commit; the snapshot
provenance stays c51 plus exact overlay. Do not edit this prospective spec into
a release. No attempt_root/reservation/guard/ResearchRun identity has been created
by preparation. Two real Views remain UNPROVED until that actual single isolated
invocation and independent raw review complete. Financial fits remain zero.
