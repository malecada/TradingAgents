# Retained ETH raw backup — complete

The 59,083 files in the frozen retained ETH inventory, totaling 103,524,489,043
raw bytes (103.52 GB), have verified external preservation in 195 successful
bundles. Packed archives total 103,571,036,160 bytes. There are no missing or
duplicate inventory rows. Continuation09 completed all nine phases; every guard
exited successfully with verified cleanup. No backup process remains active.

Each successful bundle was uploaded, downloaded back, and checked against its
archive and member hashes during transfer. Final reconciliation checked the
saved manifests, completion markers, transport and cleanup receipts; it did not
perform a second fresh 103 GB recovery or recheck all current remote bodies.
Independent findings are recorded in REVIEW.md.

## Recovery map

[recovery-index.json](recovery-index.json) records every successful batch,
its remote archive/manifest/completion paths, archive and manifest hashes,
local completion receipt and exact frozen inventory row range. Recovery spans
pilot02 and continuations03,05,06,07,08,09; failed attempts are not credited.
[reconciliation.json](reconciliation.json) binds the index and terminal09
controller/guard receipts. Paths in JSON are relative to the repository root.
The existing dedicated Storage Box SSH configuration provides access; this
index contains no authentication secrets.

To restore, retrieve the indexed archive and manifest into a new staging
location, verify both hashes, and validate each numeric `files/NNNNNNNN` member
against the manifest's expected SHA-256 and byte length. Use the manifest's
source/resolved paths as provenance for an explicit destination mapping; do not
overwrite originals. Retain the frozen inventory and this recovery map with
the repository evidence.

## Preservation and remaining scope

Original raw files, terminal failures, failed partial archives, historical
resource allocations and spent-sample history remain preserved. All closed
identities stay closed. Successful temporary local archives were removed only
after their roundtrip verification. About 33.7 GB of local disk remained free
at closure; this is not sufficient evidence for full graph/MCM scratch capacity.

This completes preservation of the existing retained ETH raw store only.
It does not complete BTC/full-history acquisition, graph admission, MCM
production, predictive fitting or paper replication. Implementation integration
and full paper coverage remain incomplete; numerical agreement is unevaluated.
All 1,420 financial fits remain pending, with no new financial claim consumed.
The next engineering work is the registered raw-to-graph producer and bounded
memory integration, followed by reviewed resource admission for empirical work.
