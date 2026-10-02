# Neural resource physical admission — source and metadata audit

**No-go for empirical admission remains.** The current 64 MiB draft covers the
neural producer and three lifecycle outputs only. It does not bound child.log,
guard/observer receipts, the lifecycle claim or terminal metadata. The existing
single-root sampled storage option cannot provide exact fresh-attempt coverage
across those separately created trees. Neither small historical files nor a finite
wall time proves a maximum log/receipt extent. No physical upper bound is invented.

This report uses six source hashes/snapshots and stat-only observations of four
closed prior guard directories. No model/graph array or child.log body was read;
no guard, model, empirical job, external request or test was run. Source observations
are dated engineering state while another integration owner edits other package
files. The accepted neural source itself remains frozen for this audit.

## Exact roots and current enforcement

Let R be the finally admitted canonical checkout root and E the fresh experiment
identity, which remains unreserved. The following are three distinct roots:

| Root | Creation and writes | Current coverage |
|---|---|---|
| R/research_artifacts/onchain-paper-replication-2026-09-24/sources/E | Producer exclusively creates directory; intent, up to nine checkpoint files and nine cell receipts, result and optional failure ledger | Each checkpoint stops before registered 4 MiB file limit; allocated producer bytes checked between cells with 1 MiB metadata margin; final allocated producer + outputs checked against 64 MiB |
| R/research_runs/E | ResearchRun.start exclusively creates claim and outputs directory; worker writes three JSON outputs; lifecycle writes complete or failed terminal | outputs included in final 64 MiB check; claim, terminal and directory blocks outside outputs excluded |
| R/research_artifacts/onchain-paper-replication-2026-09-24/runs/E | launch exclusively creates base, writes launch; monitor writes owner; guard exclusively creates guard/; observer later writes observer/postmortem/unsealed-journals and possibly guard/observer-death | Free-disk floor sampled for root volume; no dedicated byte ceiling unless selected via existing storage_budget; child.log append has no byte ceiling |

The shared research_runs/.lock and ancestor directory growth also consume blocks.
Existing graph inputs and evidence remain retained and consume capacity but are
not newly generated outputs. No input deletion/offload is part of neural admission.
No notebook, numerical MCM, dictionary, matching archive or financial fit tree is
needed by this scope.

Producer success has at most 20 regular files: nine checkpoints, nine cell rows,
intent and result, with ten directories including its root. Failure-ledger adds
one file; a failed cell can retain a partial checkpoint. Each `_immutable` write
briefly owns a pending file and then a second hard link until unlink, so transient
metadata allocations must be reserved. `_immutable` has no general encoded-byte
limit. Count alone is not a bound on JSON bytes or filesystem allocation.

The current plan reserves nine maximum checkpoints plus 1 MiB before admission:
9 × 4,194,304 + 1,048,576 = 38,797,312 logical reservation bytes, within 67,108,864.
The actual accepted tiny original-model checkpoint was 493,424 bytes; nine such
files would total 4,440,816 logical bytes. That observation excludes variable
production identity text and every non-checkpoint file, and is not a RAM estimate.
The draft's 4 MiB checkpoint allowance is an enforced refusal boundary, not a
promise that all possible metadata or checkpoints fit. The 64 MiB check is final
allocated accounting with bounded checkpoint writes, not a kernel filesystem quota.

## Supported storage_budget and its precise limitation

job.resource_policy accepts optional storage_budget exactly as
`{"root":"absolute-existing-canonical-directory","limits":{...}}`. Limits are
positive integer max_allocated_bytes, max_logical_bytes, max_entries, max_depth
(at most64) and max_scan_seconds(at most5). StorageWatch descriptor-anchors one
existing directory, refuses cross-device entries, symlinks/special files and
regular files with link count other than one, and measures allocated blocks,
logical file bytes, entries, depth and scan time. Sampling is not an atomic snapshot,
hard quota or bound on growth between checks; blocked metadata syscalls cannot be
preempted by the scan-time check.

It is constructed by job._admitted/resource_policy **before launch creates E**.
The guard also constructs its watcher before creating guard/. Precreating either
exclusive launch base or the later claim/producer directories defeats their
once-only creation contract. No such precreation is acceptable.

An existing ancestor can technically be selected. For example the existing runs
parent includes later guard trees, but also all historical runs and concurrent
new guards; it omits the sibling producer and lifecycle trees. The common ancestor
of all three roots is R itself, so a checkout-wide watcher could in principle
account all trees if it satisfied traversal limits/type rules and a separately
reviewed historical baseline. This is **not impossible ancestor accounting**; it
is unavailable exact fresh-attempt-only accounting under the current schema.
Checkout-wide traversal would include unrelated historical/input/source/runtime
content and possible rejected links, and a limit cannot be represented honestly
as this job's 64 MiB increment. No existing ancestor mapping is silently selected.

Additionally, existing `_immutable` publication has a transient two-link inode.
A StorageWatch scan observing that interval can refuse a valid in-progress write.
A future multi-root route needs a reviewed coordination rule for these owned
publication transactions; merely expanding the roots does not establish compatibility.

## Guard/log/lifecycle overhead from source and stat

resources.guarded_run sends both StandardOutput and StandardError directly to
`append:guard/child.log`. No cap, rate limit or bounded pump controls those bytes.
PyTorch/library messages and exception traces therefore have no source-enforced
finite log upper bound. A two-hour wall ceiling cannot be converted to bytes without
a bounded write rate or file limit; successful historical log size is not that limit.

Guard live.json is replaced atomically using live.tmp, not appended for every poll.
Retained live/final plus one temporary snapshot can coexist. Other fixed receipts
include cpu_ready, release and child_exit with their atomic temporary files; the
observer may add observer-death. The state includes bounded task count64 but also
runtime strings, error text and observations without an encoded-byte guard. No
uniform file-size cap is established for all success/failure states.

The last observe_storage call precedes final publish(live.json) and final.json.
After guarded_run returns, monitor/reconcile can add observer.json,
postmortem-cells.json, unsealed-journals.json, guard/observer-death.json and a
lifecycle failed terminal. Thus the final guard sample does not close the complete
physical denominator. A complete correction must reserve bounded terminal writes
and account the observer tail, not just add roots and child.log containment.

Metadata01 stat observations (bytes; directory blocks included in allocated):

| Prior closed run | Files | Directories | Logical file bytes | Allocated bytes | child.log logical / allocated |
|---|---:|---:|---:|---:|---:|
| neighborhood census 20260930-01 |9|2|15,489|53,248|2,311 / 4,096|
| hub-edge census 20260930-01 |9|2|18,462|57,344|5,328 / 8,192|
| graph resource 20260930-09 |8|2|10,153|36,864|0 / 0|
| graph resource 20260930-08 |9|2|13,001|49,152|0 / 0|

These are retained local allocations, not fresh neural overhead bounds or proof of
external recoverability. Aggregate allocated bytes are196,608. Original files were
not modified. Individual paths, device/inode, logical and allocated values are in
metadata01.json; file bodies were not read.

## RAM, CPUs and source freeze

Latest unreserved observation: MemAvailable9,220,202,496 bytes versus required
9,663,676,416 for 6 GiB memory.max plus 3 GiB reserve: **443,473,920 bytes short**.
memory.high remains5 GiB, swap0, runtime host reserve3 GiB. Root free space was
19,752,546,304 bytes; subtracting the10 GiB floor leaves9,015,128,064 before new
writes/concurrent activity, not reserved capacity. Filesystem allocation unit was
4,096 bytes. These observations do not replace fresh guard readback/startup checks.

Twelve CPU IDs0–11 were allowed at observation. The existing guard chooses the
first two, configures CPUQuota200%, TasksMax64 and inherited affinity, then checks
exactly two allowed CPU IDs and every contained thread's affinity before release
and during execution. Two schedulable IDs/readback remain required; a set of12
observed now does not reserve two later. Neural Torch thread count is2. RAM/high/
CPU controls do not prove the full unchunked graph fits; OOM is an admissible failed
resource observation only after registration, never a successful capacity claim.

job.required_sources dynamically includes every package .py and parent research
.py plus tradingagents/__init__.py. Source must be current committed HEAD; complete
source/runtime/input checks recur at admission, producer/cell/finalization and
lifecycle publication. Another owner adding/editing a package source can invalidate
closure, even when the changed module is not used by the neural graph. A coherent
reviewed commit and source freeze spanning the whole neural attempt is required,
or a separately admitted isolated checkout with its own exact input/environment/
physical mapping. The latter has no automatic input-storage exemption. No source
freeze is claimed while integration remains active; no empirical launch is allowed
from these mixed in-progress sources.

## Smallest complete prospective correction boundary

No numerical/model change is needed. A new explicit versioned physical route must
leave existing job/resource contracts and all historical artifacts unchanged:

1. job.py declares an exact three-root manifest tied to E, original source/claim,
   canonical covered-device ancestors and explicit per-root/write allowances.
   Existing roots must be refused; roots transition once from absent to exclusively
   created identities. No forbidden launch-base precreation or unrelated ancestor
   scan substitutes for ownership. A focused new watcher/helper can support these
   declared roots; existing StorageWatch semantics need not be silently weakened.
2. resources.py/new guarded-I/O helper bounds child.log at the write boundary and
   emits a durable overflow/failure disposition. Append/close failure is fatal and
   primary-aware; no hidden truncation, refill or retry. A sampled stop alone is
   insufficient. A kernel per-file limit with verified readback or a finite owned
   byte sink are implementation options requiring synthetic failure tests; no limit
   value is adopted by this report.
3. Source-backed exact encoded size reservations for claim, launch/owner, bounded
   guard snapshots/errors, lifecycle terminal and observer/postmortem records must
   exist before their writes. The new route must cap these writes or refuse before
   allocating them; include atomic temp coexistence/directory blocks, failure-tail
   reserve and one final observer accounting of all three roots. Existing unbounded
   `_immutable`/guard JSON writers cannot by themselves establish those caps.
4. The same change must resolve owned publication/scan coordination and final-tail
   coverage. On breach preserve partial bytes and spent claim, stop the unit, publish
   bounded failure evidence best effort, and grant no automatic retry or coverage.

Likely bounded ownership is job.py plus resources.py and a new physical-accounting/
I/O helper with synthetic tests. Lifecycle.py or its narrow neural-specific caller
must participate only if claim/terminal write limits cannot be enforced before the
existing helper; this exact API decision remains for implementation review. No
algorithm, model/GAT, old guard profile or empirical source reader changes are needed.

A finite *policy cap* may deliberately fail a resource pilot; that is different
from a proven successful peak upper bound. The existing4 MiB checkpoint/64 MiB
producer-output limits are concrete reviewed candidates. Additional log/receipt/
terminal limits remain **null, pending bounded-writer design and reviewed exact
serialization accounting**. The four observed guard sizes do not justify silently
turning64 MiB into a complete-workflow allowance. Current missing enforcement,
startup RAM and dynamic source freeze are explicit blockers for root reconciliation.
