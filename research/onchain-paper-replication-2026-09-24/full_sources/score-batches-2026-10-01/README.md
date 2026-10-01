# Completed-score batch persistence — October 1, 2026

This engineering change implements a bounded completed-chunk storage primitive in
`tradingagents/research/onchain_replication/score_batches.py`. It does not execute
matching, consume financial inputs, admit an empirical trial or replace an old
journal. The historical per-pair files remain untouched.

Each store binds an owner and six independently supplied identities: graph, node
order, dictionary, ordered motifs, matching configuration and workflow. The
caller must derive and admit these identities and dimensions from actual inputs.
Cells are fixed-size row-major float64 chunks; the last chunk may be shorter.
Float64 preserves scalar results before the existing final float32 MCM conversion.
No matching calculation, motif count or numerical denominator changes here.

Publication uses exclusive files, payload hashes, chained compact chunk manifests,
file/directory synchronization, pinned directory identity and mandatory lease
checks. A directory identity cannot be reopened as another writer. Failed writes
poison the writer; pending bytes are retained and explicitly hashed by a terminal
failure where the lease still allows closure. Abrupt loss of ownership or failure
during terminal publication requires future external reconciliation. No automatic
restart, overwritten terminal, pending-file deletion or successor reuse exists.

Verification checks an externally supplied terminal hash, all chunk identities,
payload bytes, exact ordinal sequence and inventory. A constant-memory aggregate
of file signatures and content hashes is rechecked by a second bounded read of
every retained file after the final lease. This detects even late rewrites whose
metadata timestamps coalesce. It doubles verified payload I/O; mutation after an
entry's last read remains outside this sampled verification guarantee. This is a sampled, non-atomic check under a sole-writer/source-freeze
contract, not a lock against subsequent modification. File reads are capped at
8 MiB, metadata at 8 KiB; persistent verification memory does not grow per cell.
These are application-buffer limits, not a process RSS guarantee.

The prospective logical allowance is `8*cells + 8192*(chunks+2)`. It includes the
raw scores, one capped manifest per chunk and the start/terminal metadata. It
excludes filesystem allocation overhead, logs, numerical scratch, other outputs
and any predecessor evidence. The existing sampled storage guard remains needed;
this formula does not prove a whole-workflow disk budget.

## Verification history

- `red01.log`: 12 expected failures because the new module did not yet exist.
- `check01.log`: 12 passed in 0.23 seconds. Original source retained as
  `check01-source.py`.
- Independent `INITIAL_REVIEW.md` withheld acceptance for missing publication
  postchecks, late verification mutations and unsynchronized parent creation.
- `red02.log`: four targeted counterexamples failed, 12 prior cases deselected;
  session 99671 exited 1. No empirical attempt occurred.
- `check02.log`: corrected implementation, 16 passed in 0.25 seconds. Tests cover
  byte-preserving ordering, no replay, incomplete/nonfinite/wrong-dtype rejection,
  payload/hash/scope/owner corruption, missing/symlink files, retained partial
  writes, lease loss, root replacement, late file modification and parent fsync.

- `FINAL_REVIEW.md` retained the same-signature content-change limitation.
- `red03.log`: a deterministic coalesced-clock counterexample failed as expected,
  one failed and 16 deselected in 0.19 seconds; `check02-source.py` retained.
- `check03.log`: strengthened second content pass, 17 passed in 0.27 seconds.

- `REVIEW03.md`: independent acceptance of the corrected bounded primitive, SHA
  `f0a0717a95590265da80f36a3d46a34393dc025a85ecece16627573fa405e7a8`.

## Next executable integration requirement

The matching workload currently requires each completed score to be durable
before its callback returns. Whole-chunk publication alone does **not** satisfy
that contract for a partly filled batch and does not eliminate existing per-pair
metadata. The next adapter must durably retain each newly completed score and its
exact purpose in a bounded active chunk, then seal it into an immutable batch.
Interrupted tails and matching checkpoint state must remain attributable to their
failed owner; succession needs explicit admission and observed predecessor death.
The adapter must not buffer completed results only in RAM, silently remove old
pair artifacts, or claim numerical equivalence from these persistence tests.

After that adapter, integrate bounded live-pair scratch and the actual MCM
consumer, verify numerical/cell-order parity on synthetic graphs, and review the
full resource gate and cumulative amendment. Full-size capacity, paper coverage,
and all financial fits remain unestablished by this engineering work.
