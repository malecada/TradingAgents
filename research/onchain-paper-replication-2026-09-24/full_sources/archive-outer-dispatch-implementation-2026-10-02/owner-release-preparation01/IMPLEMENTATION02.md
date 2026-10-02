# Owner fixture launcher 02 — prepared, not admitted

Launcher02 replaces the superseded hard-aggregate-quota proposal. The original
prospective-release-spec.json, test_launcher01.py and red01.log are preserved.
The five original RED failures describe an unimplemented quota-only admission
proposal; that proposal was abandoned when the coordinator explicitly selected
reviewed sampled storage semantics. They are not passing tests. Spec02 is new
and deliberately retains PREPARATION_ONLY_NOT_RELEASED, which refuses launch.

The source snapshot is now materialized from exact824489a Git blobs, independently
rehashed and read-only:1,873 files,18,815,116 logical bytes,24,662,016 allocated
bytes including directories. The receipt records ordinary-owner chmod remains
possible; there is no adversarial immutability claim. All source files are checked
before the guard, again before the worker and after closure. Source/test bytes in
the checkout were not edited. Only these new preparation files were added.

Launcher02 uses snapshot resources.guarded_run unchanged, with an external narrow
subprocess adapter adding LimitFSIZE=4194304, RuntimeMaxSec=1800s and explicit
worker environment to its systemd-run argument list. Systemd property readbacks
are checked before the original guard releases its waiting child. The original
lease, cgroup control readback, host reserve observation, descendant unit stop
and cgroup empty verification stay intact. The original guard is legacy sampled
storage mode, not the neural physical RPC route; the latter requires a different
admitted lifecycle/root layout and cannot simply be grafted onto this fixture.

Exact requested memory limits are3GiB maximum,2GiB high and zero swap. Startup
availability is6GiB TOTAL (3GiB maximum plus3GiB host reserve), with zero waiting
and no retry. Runtime host reserve remains3GiB. The independent systemd wall
limit is1800s after unit start; original guard wall observations begin earlier.
On any guard failure, success is withheld; original unit cleanup must report
verified. The exclusive reservation marker is durable and never removed. Fresh
attempt directories and existing case-level exclusive identity gates reject
reruns. Failed partial evidence remains retained.

The4MiB hard and soft RLIMIT_FSIZE applies to EVERY regular file written by the
unit and descendants, including guard-child log, Git objects/index, fixture
source copies and arrays. It is not merely a log truncation policy, not a combined
sum over multiple logs and not an aggregate quota. Oversized fixture writes may
fail with EFBIG/SIGXFSZ; such a result is retained, never retried under the same
identity. Exactly reaching the main child-log ceiling makes launcher success
fail closed. No large actual fixture has tested compatibility with this limit.

StorageWatch scans the entire owned root (source snapshot, reservation, guard,
case attempts, TMPDIR, HOME and cache) every original guard boundary: requested
sample interval.25s, bounded traversal12000entries/depth32/2seconds. It checks
both allocated and logical file bytes against1GiB and includes directories in
allocated counts. Disk free is sampled against10GiB. This is not an atomic
snapshot or kernel aggregate quota: growth between observations, races with
Git renames/deletions and blocked metadata calls can cause overshoot or a
fail-closed observation error. Scan limits bound traversal work, not uninterruptible
kernel syscall latency. Ordinary fixture code is trusted to use its mapped owned
paths; arbitrary/malicious filesystem containment is not claimed. External
unrelated processes can reduce free space between checks. No hard aggregate
quota, complete transport capacity or physical filesystem sandbox is proved.

Shared interpreter/runtime mapping is explicit: checkout-local3.13.13 .venv,
locked snapshot uv.lock, exact installed distribution-version metadata, snapshot
package paths and shared .venv third-party origins. Metadata-only runtime-check01
passed without numerical imports. Binary hashes/ABI are not fully attested.
No venv symlink or incorrect standard-check-root assumption is used. A later
fixture imports Torch as part of inherited environment inventory but performs
zero model/financial fits. The runtime check removes shared checkout/script
paths before snapshot imports; exact snapshot sys.path precedence is retained.

Evidence: red02 has8 meaningful missing-implementation failures. check01 has
8passing tests, covering unreusable reservation/preservation, source mutation,
symlink/unlisted source rejection, finite command controls, conflicting controls,
readback mismatch, preparation refusal and first-fatal retention. Only tiny
unittest cases and metadata inventory ran. There is no actual cgroup/guard,
source-admitted owner fixture or child transport execution result here.

Release still requires independent exact launcher/spec review and coordinator
admission with fresh resource/HEAD observations. Root must create a separately
reviewed released spec; this prepared spec must stay unchanged. The three cases
remain success/late_failure/local, each with ONE representation. Actual second-
View cumulative spending remains unproved. Real SSH and full archive transport
capacity remain outside this synthetic fixture.
