# Isolated owner fixture release mapping — preparation 01

Status: preparation only, not a release, launch or synthetic result. No fixture
was imported or executed and no isolated checkout was populated. Source/test
bytes remain frozen. The prepared spec deliberately has a status that the
fixture rejects. Source commit is 824489afa2aa5eba39ebf1af456681120ac9e0fb;
shared HEAD observed during preparation is
91b45091966ab37e1f70aec6d8a04e5a62d340e9. The latter contains later neural launch
preparation and is not silently substituted as the archive fixture source.

## Exact source accounting

`source-manifest.json` binds 1,873 regular Git blobs totaling 18,815,116 bytes,
including executable modes, SHA-256 and Git object identity. Selection is the
accepted owner05 conservative source set plus every committed Python file under
tradingagents/, tests/research/, scripts/ and the study full_sources/ directory,
all study configs JSON, root conftest, pyproject, lock and Python version.
Every selected working-tree file matched the committed bytes at observation.
The absent tests/__init__.py and tests/research/__init__.py are recorded as
absent namespace-package files, not invented or required sources.

This conservative set covers the complete onchain package and research parent
required_sources enumeration, fixture transitive modules, and dynamic local
helpers: sampler core, component reader, pair-workload kernel, MCM kernel,
feature boundary, denominator validator, native_map and adjacent seal plus
recursive publication/closure helpers. All historical helper Python in the
study is included, avoiding unsupported claims that static import parsing
identifies every dynamic source. Extra scripts are copied evidence, never
executed. Runtime third-party modules are separately accounted below; this
manifest is not a claim of complete binary-runtime attestation.

## Snapshot and invocation contract

After coordinator release, exclusively create the proposed isolation root from
`prospective-release-spec.json`. Export each named regular blob from the exact
commit using Git object reads, write independent files, retain modes and verify
all sizes/hashes. Refuse symlinks, hardlinks to live source, existing targets,
unlisted Python source and package-set mismatches. Retain snapshot manifest and
construction receipts. A full clone is unnecessary; the export has the exact
recorded source commit as provenance, while each test constructs its own real
synthetic Git repository and registered source commit. Do not fabricate a Git
HEAD for an exported directory. If release requires an outer Git HEAD, use a
separately reviewed detached isolated checkout at the exact commit instead.

The shared HEAD/source freeze is checked before construction and launch against
the coordinator-selected current HEAD. A changed shared HEAD is a scheduling
review condition, never permission to change the pinned export. Hash the copied
source before and after execution; retained output lives outside that source.

Use the checkout-local locked Python 3.13.13 interpreter with cwd and PYTHONPATH
pointing to the isolated source, PYTHONDONTWRITEBYTECODE=1 and pytest cache
disabled. Retain offline conftest auditing and disable automatic third-party
pytest plugin loading. Before admission, verify package/test/helper origins are
inside the isolated source; the editable installation must not route imports
back to the shared checkout. The exact planned test target is
`tests/research/onchain_replication/test_archive_dispatch_owner_proposal.py`.
No `--run-network`, `--run-account` or financial execution is requested. Only the
reviewed spec and its SHA-256 may populate the two fixture release environment
variables. A newly reviewed release spec must retain the exact source_files
mapping and cases; do not alter this preparation record into a release.

## Runtime, generated configuration and limits

The manifest records Python prefix/executable and installed distribution
versions without importing numerical packages or invoking runtime sync. Lock,
pyproject, Python version and runtime-check script bytes are pinned. Shared
runtime binaries, system libraries, Git executable and kernel are not fully
hashed here. Before release, the coordinator must validate the locked runtime
and isolated import origins, freeze the actual invocation/environment and
record the relevant runtime/system versions. The usual runtime script expects
its interpreter prefix inside its own root, so invoking that script on an
export with the shared .venv is not itself a valid isolated-runtime check; this
mapping needs an explicitly reviewed check, not a symlink workaround. Existing
neural environment receipts are historical corroboration, not a fresh check.

The committed proposal test binds transport config and generated registration
mutations. The fixture derives the rest from the pinned helper/config closure;
actual generated registration/input files and their source pins must be retained
under each case directory. The existing helper inventories Torch, so the later
fixture has a Torch import even though no model is fit. This preparation did
not import Torch or generate graph arrays.

Prospective hard limits: 1,800 seconds for the complete invocation, 3 GiB worker
memory.max, 1 GiB cumulative created-file allocation, 4 MiB combined log and
10 GiB disk-free floor. Enforce the memory limit through an externally verified
cgroup because the fixture mocks the internal guard. Enforce the other limits
with a reviewed independent process-group watchdog, bounded log sink and disk
accounting covering snapshots, attempts, temporary files and logs. Polling alone
is not a hard disk allocation bound; require a quota or other reviewed bounded
allocation mechanism. No such launcher has been prepared or admitted here.
Capture startup, limit events, descendants, terminal status and cleanup proof;
terminate/reap all owned children on any limit. No auto retry. Capacity admission
and exact enforcement are remaining release requirements, not claims made by
this metadata. Prior owner05 took 543.85 seconds for three different cases;
600–1,200 seconds remains an unmeasured estimate for this proposal.

## Proof scope and remaining gap

Execute success, late_failure and local once each in fresh retained directories.
Each has one representation, tiny invented population, actual admission and
execute_fit_payload through dictionary/MCM/publication/owner/outer terminals.
Only transport command vectors become explicit local Python children; original
receipt anchor, rounded no-refund accounting and dictionary-to-MCM cumulative
spending stay real. Internal kernel guard and batch preflight/financial fitting
remain mocked. Local and post-close behavior must invoke no transport. Late
failure retains original dictionary spend, failed MCM attempt and failed outer
terminal. Existing synthetic helper cleanup records a failed synthetic lifecycle
closure even when owner/outer terminal checks succeed; it does not complete a
financial fit.

Actual cumulative spending across a second View/representation is still
unproved. These three cases do not close that requirement; a distinct bounded
fixture and review are needed later. Real SSH behavior, whole-route physical
admission, complete replication coverage and financial/model fits also remain
outside this synthetic proof. No previous terminal identity may be reopened.

Remaining release steps are independent review of this mapping plus concrete
launcher/runtime/source isolation, completion of the active neural job,
coordinator capacity decision and fresh one-shot admission. Nothing in this
preparation authorizes concurrent substantial work.
