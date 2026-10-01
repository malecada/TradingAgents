# Compact graph artifact engineering result

Actual compact Features now produce exclusively owned component artifacts under
an explicitly selected registered policy. Exact NPY and manifest sizes are
checked before writing. Initial publication reads the saved bytes through the
strict component reader and compares their numeric values with the original
fixed tensors. Later reads retain the original saved hash and producer lineage.
Failed namespaces remain preserved and poison the current compact owner.

Callback-free `compact_owner.verify_current` rechecks the claim, configuration,
pinned binding metadata expectations, root identity and inventory, terminal
absence, stage membership and reservations after the preceding live guard lease.
This is a sampled final verification, not an atomic filesystem or guard snapshot.

## Retained checks

| Check | Result | Evidence |
|---|---|---|
| red01 | 1 missing-module failure, 5 deselected, 81.27s | red01.log, session25103 exit1 |
| check01 | 5 passed, 1 fixture failure, 568.26s | check01.log, session5268 exit1 |
| red02 | 1 real final-owner-revocation failure, 7 deselected, 97.43s | red02.log, session61277 exit1 |
| owner-red01 | 1 missing-helper failure, 8 deselected, 2.60s | owner-red01.log, session13223 exit1 |
| owner-check01 | 12 passed, 139.19s | owner-check01.log, session49820 exit0 |
| check02 | 5 passed, 4 deselected, 402.73s | check02.log, session15121 exit0 |

The initial growth fixture attempted to resize non-resizable PyTorch storage and
failed before changing its shape. Its original source and output are retained.
The corrected fixture actually replaces tensor storage, asserts the enlarged
shape and proves that the writer is not reached. Other final checks cover normal
saved readback, a valid rehashed artifact containing an incorrect numeric value,
final loaded-owner revocation and empty-edge component layout/readback. The four
unselected cases passed in check01 before the owner-helper correction; no combined
final nine-case run is claimed. Twelve owner checks cover the corrected helper,
including dangling terminal symlinks and changed metadata expectations.

## Scope and remaining work

The output policy reserves all required graph outputs conservatively. The resident
cap counts source numeric arrays, original feature tensors and one loaded numeric
payload. Other graph attributes, sample/dictionary data, provenance readbacks,
I/O/Python scratch, mapped pages, model state, RSS and repeatedly retained loads
require separate accounting. This does not close a representation, enable cold
reuse/native dispatch or admit an empirical pilot. All 1,420 financial fits remain
pending; resource coverage remains 77/109. Historical data and attempts are intact.

## Source hashes at terminal checks

- `tradingagents/research/onchain_replication/compact_graph_artifacts.py`: `fd1395b0c274b1b51dc26365fd0c2954f904492cf77ddb3d553ce40c6dc6bf8a`
- `tradingagents/research/onchain_replication/compact_owner.py`: `f9b84224a97acb7f1c78665799376b37cd324077024b0ac7fe5c6933da08c13b`
- `tests/research/onchain_replication/test_compact_graph_artifacts.py`: `66c1ac382a7d9b19de3aab1b7c505f26ab09c19ce6c527c10da865aa327736a0`
- `tests/research/onchain_replication/test_compact_owner_final.py`: `5873a34b54f95828382505d8eab84e4ab2227ca04695ca3c124161bdee578a22`
