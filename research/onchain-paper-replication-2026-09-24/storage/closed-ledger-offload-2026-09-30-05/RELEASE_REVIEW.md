# Independent conditional release review — storage05

Decision: accepted for one sequential preservation attempt only after committing/pushing the exact reviewed dependencies and passing fresh preflight. This review did not hash the ledger body, run tests/helpers/preflight, contact remote storage, launch a job or remove a file. No execution identity was reserved by the reviewer.

All original 30 and contextual 37 hash entries independently match. Five paths overlap with matching hashes, yielding **62 unique bound paths**. Of these, 61 must match committed bytes at the launch HEAD; the only allowed local/untracked exception is the exact manifest `connection_path`, SHA-256 `d79023381eb9f2788709a7a4c043046d8998c30bb4abab678cb41caaf4dc70ef`. This entry was checked by hash only, without reading or printing its contents. The later release review itself is separately checked against the commit by the prepared preflight. No additional untracked dependency exception is accepted.

## Actual prerequisites and source

Storage04's accepted ten-evidence recovery set, acceptance receipt and compact closure are pinned. Source graph07 and preceding graph08 independently accepted verifier closures are also pinned, including their exact four-evidence review sets and acceptance receipts. The graph08 original claim, terminal, launch/owner/observer/final guard and independent compact producer closure are included. Their hashes match; predecessor guards report successful cleanup and their exact owner PIDs/cgroups are absent. These are now actual closures, not assumptions from the preparation draft.

The sole candidate remains the original closed graph07 ledger, 3,760,664,576 bytes, expected SHA-256 `57e300bd8f5edd7870958bea51660c8a8691775b6e46a4aea7e99a1d74008cc2`. Original artifact-index hash and manifest metadata remain unchanged. Current stat-only identity still equals `[66310, 7920522, 3760664576, 1790750965016210774, 1790750965016210774]`. It is untracked, nonsymlink, single-linked, with no journal/WAL/SHM or restoration sidecar. Expected body hash remains attributed to the original producer until the guarded preservation rechecks it.

The release's preparation snapshot of 18,390,093,824 free bytes is below the December requirement of 22,103,159,134 by 3,713,065,310 bytes. Full local recovery scratch requires 14,514,860,032 bytes. A later reviewer stat snapshot also remains below the December requirement and above scratch capacity; neither reading substitutes for the immediate preflight. Potential reclaim is close to the planning shortfall and is not reserved capacity. Do not infer that December is launchable until actual accepted eviction and a fresh disk check. The deferred 192 MB synthetic checkpoints must not be treated as already accommodated in that narrow future margin.

## Preflight and guarded ordering

The new preflight is the reviewed storage04 route with precise changes: accepted predecessor storage04, a locally pinned graph08 prerequisite helper, and the accepted December projection. That local helper is byte-identical to graph09's separately inspected graph08 helper. It verifies accepted exact graph08 result/review hashes, source claim/terminal joins, complete eight-cell producer and absent producer/verifier owners. The preflight also verifies exact current branch and pushed HEAD, the complete binding union, committed source bytes except the single connection exception, committed release-review bytes, absent new attempt identities and no active replication unit.

It requires a current deficit before proceeding; if free space meets the December requirement, it refuses the unnecessary transfer. It independently requires the entire source-sized recovery copy plus 16 MiB above the 10 GiB floor and at least 3.5 GiB available RAM, then applies source eligibility. These are necessary external checks; the unchanged worker alone does not enforce the complete contextual release. Any intervening producer, verifier or synthetic profile must close before this one launch.

The guard remains 256 MiB maximum, 192 MiB high, zero swap, 3 GiB host reserve, 3.5 GiB startup, 10 GiB disk floor, two-CPU affinity and 14,400 seconds. Transport retains the 4 GiB file scope, 8 GiB charged payload allowance, 5,400-second operation deadlines and no automatic retry. The previously reviewed upload/full recovery/hash and restoration-metadata roundtrip precede durable verified receipt/sidecar, source revalidation and unlink. Completion metadata roundtrip precedes final completion publication. Preserve partials and all failure evidence; do not restart a reserved identity.

## Consumers and limits

Graph08 producer and verifier are now closed. Their retained dependencies on graph07 are compact lineage/review evidence and graph arrays, not the graph07 SQLite body. The future graph09 build uses its own seven daily source mappings; its prospective helper requires compact accepted predecessor/preservation proofs. The isolated matching profiles use fresh synthetic graphs. No current body dependency was identified in these reviewed routes. The worker's active direct-input check remains a useful additional safeguard but is not a universal indirect-dependency resolver; fresh release preflight and the no-concurrency condition remain mandatory.

Historical ledger-body verification or future forensic consumers must first restore into a new temporary file, verify the full recorded bytes/SHA-256, and restore the absent original path without rerunning the old graph job. The original artifact index must remain untouched. Only this exact ledger is eligible; raw files, graph arrays, other ledgers and financial state are outside this release. No graph09 gate or new empirical budget adoption is implied.

| File | SHA-256 |
| --- | --- |
| `RELEASE.md` | `0ed00578f9da47ee3363a970027b3896900d950526d4ab5c10be304b4e215600` |
| `preflight.py` | `ac34eb2fd812d624acbb34064b614da900ffbfc98d21bd072638adaa1e033f22` |
| `previous_graph_requirement.py` | `9ee7f1c516c05c2b60f34aeeaf214c02ec904e947a0a7fee1d471829ceac34e7` |
| `release-bindings01.json` | `8b78f24fee7c9bb97cc730362dcf96b72170f7d393d075167048d989792ec544` |
| Original `bindings.json` | `55c5dbb9265688a7b322b40e8b8e70c02da1fcf6886fbc1402393ba74683c226` |
| `manifest.json` | `9b1f35a22c620e95a6db696e167f9aae8b02cb8fe2d7db604c4f6b1c7282a5c7` |

At this inspection, intent, guard, preflight, complete and failed identities are absent and no replication unit is active. Actual terminal recovery, durable sidecar/source absence, aggregate completion and owner cleanup require a later independent closure review; this conditional acceptance does not claim any new remote backup already exists.
