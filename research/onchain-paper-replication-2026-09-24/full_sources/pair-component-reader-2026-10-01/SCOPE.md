# Strict resident numeric component reader

This isolated prerequisite preserves the existing component_store implementation.
It reads the numeric array/scalar/string-key dictionary/list/tuple subset of its
manifest format. Tensor, object, structured and nonnumeric array data are refused.
No np.load, memory map, archive or pickle is opened. The intended next consumer
is exact admitted sampler/dictionary/MCM artifact loading, which is not yet joined
by this module.

Before any np.empty allocation, the reader checks the complete bounded manifest
and tree, unique exact member coverage, same-device regular single-link paths,
NPY magic/version/header schema, declared shape/dtype, exact file extent and hash,
and aggregate encoded-file and array-payload limits. NPY versions1/2 are supported;
header length is checked against16KiB before reading the header body. Manifest
size is explicitly bounded to at most2MiB. Unknown directory entries are rejected
as they are encountered, without eagerly collecting an unbounded inventory.

max_artifact_bytes counts the manifest and every declared NPY file including its
header. max_array_bytes counts all resident numeric payloads; repeated array
references are forbidden. These are artifact/array limits, not a bound on Python
metadata, temporary objects, whole-process RAM, total repeated I/O or physical
workflow disk usage. The outer admitted guard and resource policies remain due.

All member headers and hashes pass before the first array allocation. An explicit
lease runs after preflight, before each allocation and at final return. Flat
arrays are filled through readinto loops and reshaped in the declared C/F order;
non-native-endian values and zero-length arrays retain their bytes and shapes.
The hash includes the header and exact bytes loaded into the array. Every opened
file descriptor is context-managed, O_NOFOLLOW and O_NONBLOCK. FIFO/device files
are refused by fstat without waiting for a writer. Hash reads stop at admitted
extent plus one byte, so concurrent growth cannot turn the check into an
unbounded EOF read.

Final verification rehashes immutable files, then rechecks exact inventory and
all saved compact signatures after the last digest, before the final lease.
These checks detect the tested changes across the read. They do not create an
atomic filesystem snapshot against arbitrary continuous external mutation; the
outer owner contract must preserve immutable artifacts.

## Preserved evidence

- red01:8missing-implementation failures/0.002s.
- check01:8passes/0.086s; original source/tests retained. Independent
  INITIAL_REVIEW nevertheless withheld acceptance for unbounded EOF hashing,
  blocking FIFO opens and eager unbounded inventory enumeration.
- red02:1failure in3cases/0.040s. A growing array caused1,000,176bytes to be read
  instead of at most177. Endian and oversized-header checks already passed.
- red03:1FIFO failure and1test-double error in2cases/1.065s. The FIFO child was
  stopped and reaped by its one-second parent deadline. The inventory test double
  initially lacked DirEntry.path; that error is not claimed as proof of CR3.
- red04:after correcting only that test double, the intended premature inventory
  consumption failure was reproduced in1case/0.015s.
- check02:13passes/0.158s after the three corrections. Source/tests retained.
  Subsequent review found a return-boundary gap during the final rehash loop.
- red05:2failures/0.026s reproduce a late foreign entry and alteration of an
  earlier member while the last member is rehashed. Exact test retained.
- check03:15passes/0.176s, exit0 after final compact inventory/signature checks.
  Final independent acceptance is recorded separately in REVIEW.md.

All tests use tiny synthetic files and the pinned standalone test interpreter.
No empirical source arrays, model fits, historical jobs or resource pilots were
run. Direct-file bindings document this component, not complete empirical source
closure or a replacement broad offline-suite receipt.

## Remaining integration

Actual OwnedJournal/FeatureJournal owner-event binding, the registered read-policy
input, sampler publication/source/RNG provenance, exact historical artifact reuse,
dictionary/MCM publication and full representation reuse remain outstanding.
Mapped full-fold feasibility, scalable verification, whole-workflow physical
accounting and orphan reconciliation are separate mandatory requirements.
No scientific protocol or empirical budget was changed; all1420fits remain pending.
