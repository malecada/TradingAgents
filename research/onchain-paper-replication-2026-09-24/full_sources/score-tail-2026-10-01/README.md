# Durable per-score MCM tails

Maintained `score_tail.py` implements bounded append-only scalar persistence.
Each 80-byte record holds a global ordinal, an exact little-endian float64 score,
a 32-byte purpose hash and a 32-byte chained checksum. The start manifest binds
the owner, graph/dictionary/order/matching/workflow scope, global starting cell,
capacity and the exact ScoreBatches destination. No dictionary occurrence order
is inferred from an MCM row-major ordinal.

An append acknowledges success only after writing all bytes, fsync, live lease,
pinned root/file checks and readback. Partial writes poison the instance. Complete
but unacknowledged bytes following a late failure remain unacknowledged; failed
terminal records preserve their hash and extent without granting reuse. The
same directory cannot be reopened. Closing releases file descriptors only.
There is no automatic resumption, successor admission or deletion of any tail.

A complete tail can be sealed into its exact next ScoreBatches chunk. Both owner
leases run before final callback-free content checks on the retained tail and
destination. Any late failure retains all already-written files and refuses a
successful return. Verification is sampled and non-atomic; concurrent mutation
after the last read is outside the sole-writer contract. Metadata is capped at
8 KiB and a tail at 8 MiB. Reads/copies and numerical arrays also occupy memory;
these are not process RSS or filesystem-quota guarantees.

## Evidence

- `red01.log`: 12 missing-module failures, expected before implementation.
- `check01.log`: 12 passed in 0.22 seconds.
- `INITIAL_REVIEW.md`: ST1 withheld acceptance for tail ownership/content not
  being checked after destination publication.
- `red02.log`: reproduced ST1, one failed/12 deselected in 0.19 seconds.
- `check02.log`: 13 passed in 0.23 seconds.
- `FINAL_REVIEW.md`: preserved the reciprocal boundary concern: the late tail
  callback could alter the already-checked destination.
- `red03.log`: reproduced that case, one failed/13 deselected in 0.20 seconds.
- `check03.log`: 14 passed in 0.28 seconds.
- `REVIEW03.md`: accepted the corrected bounded tail/seal primitive, SHA
  `6714d22dd9aee4b1af93ab967c1984856695c5a1b8ffa1a5c93b54ccf01531b1`.

Both earlier implementation snapshots and all failing logs remain retained.
No registered research job, historical identity or financial outcome was read
or rerun by these synthetic checks.

## Storage consequence and remaining scope

Tails are deliberately retained even after sealing, so records and batch values
occupy 88 logical bytes per completed cell, plus metadata. `accounting01.json`
records source-pinned arithmetic from the nine retained graph inventories. At a
prospective 65,536 cells per chunk, the 577,498,112 cells require 8,816 chunks and
51,109,011,456 logical bytes including the capped metadata allowance. This is
not an adopted execution policy, measured disk/RSS/runtime/IOPS requirement, or
a hardware purchase recommendation. Physical allocation, existing per-pair
artifacts, live matching state, graphs, logs and other outputs are excluded.

The current MCM adapter wraps the existing numerical callback. It does not yet
remove the old per-pair artifacts or their reservations. A prospective replacement
must also retain convergence/iteration/source/policy evidence and progress/failure
checkpoints; a saved scalar alone cannot replace the complete matcher evidence.
Registered owner integration, storage/offload limits and successor disposition
remain required before empirical execution.
