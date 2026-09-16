# Full-history retention feasibility — preparation only

The new Data partition makes a lean full-history layout plausible. It does not
make the old pilot's retained intermediate layout suitable for every day.
No full-history acquisition or numerical gate is supplied by this note.

Initial Data free space was 164.058 GiB. A conservative 1.6 GiB checkout allowance
and 20 GiB free-space floor leave 142.458 GiB for new retained data and scratch.
The metadata extrapolation is 140,388,550,362 selected-column bytes; applying
the measured .743960122 compression ratio yields 97.271 GiB. Neither the
quarterly projection nor one-day compression ratio is an upper bound. Full
block objects, source receipts and boundary additions differ from that estimate.

The old January 1 artifacts contain 16,197,798 event-shard bytes, 630,369 prefix
bytes, 35,247,718 exact-hash bytes and 50,332,153 Local40-vector bytes. Repeating
those representations for 1,096 days would add about 104.5 GiB. All existing
artifacts remain preserved; new full-panel processing needs a different,
predeclared retention contract.

## Proposed capacity envelope

| Location | Proposed ceiling | Content |
|---|---:|---|
| Data partition | 120 GiB | Immutable compressed source bodies |
| Data partition | 2 GiB | Receipts, manifests, daily aggregates, integrity and forecast evidence |
| Data partition | 16 GiB | Newly generated, explicitly recomputable per-day scratch |
| Original workspace filesystem | 48 GiB | Proposed external-memory exact transaction-hash check scratch |

The Data ceilings total 138 GiB, below the initial 142.458 GiB budget. The
original filesystem had about 76 GiB free before evidence import; 48 GiB scratch
would leave more than 20 GiB only if subsequent usage remains bounded. Every
volume needs its own current free-space check; these ceilings are candidate
admission limits, not a promise that every date will fit.

For a future run, raw bytes and daily summaries should be retained, while newly
generated decoded events, overlap lists and per-address vectors are designated
recomputable scratch before execution. Canonical raw stores and existing pilot
outputs must never be deleted. The successful one-day motif evidence and source
hashes permit independent reconstruction; a production feature must still pass
its declared independent numerical checks before ephemeral values are released.

The existing Python-set cross-day uniqueness helper is unsuitable for the full
corpus under 8 GiB RSS. The new `hash_audit.py` helper compares complete 32-byte transaction identities
exactly using bounded buckets and in-place heapsort. Thirteen focused synthetic
tests and an independent Counter oracle passed. The retained maximum-bucket
benchmark checked 8,388,608 occurrences in one 256 MiB bucket, with 1,048,576
unique identities and 7,340,032 excess duplicates. It completed in 4.842 seconds
at 345,997,312 bytes sampled peak process-tree RSS under the unchanged 8 GiB
guard. This is synthetic utility evidence, not full-panel integration. At minimum,
unsorted identity storage is 32 times the actual total transaction count; sort
buffers, receipts and temporary copies require additional space. The 48 GiB
ceiling is not yet proven sufficient. Actual footer row counts and a synthetic
disk/RSS-bound demonstration are prerequisites for the full numerical identity
audit; bounded raw capture can proceed without allocating that scratch; no truncated hashes,
probabilistic uniqueness claim or silently discarded identity column is allowed.

## Recovery status

Data and the workspace are partitions of the same NVMe device. Local copies are
not independent recovery. Source/code and the bounded first tranche can use the
existing reviewed Git backup route. A roughly 100 GiB raw corpus should not be
assumed to fit the shared local Git object store or be appropriate for that route.

A prior VPS receipt verified an 83,368,599-byte archive, not capacity for this
corpus. A new read-only filesystem check of the documented host on September 16
reported 40,106,426,368 available bytes (37.35 GiB) under /opt/thesis-research.
The hostname alias did not resolve; the recorded host address succeeded. No
remote files, services or account settings changed. That existing volume alone
cannot hold the proposed 122 GiB retained ceiling. A full-corpus external backup
destination remains unresolved; local retention and external recovery must be
reported separately rather than claiming an unverified backup.

The first tranche is independently verified and preserved: 940 source files
total 754,265,130 bytes, and the full 990-file import totals 754,630,488 bytes.
Commit `3454966e7e33ee655d4df0a065e099d594b9e978` was pushed and its remote
branch hash verified. That backup covers the first tranche, not future captures.
The [remaining-cohort capture contract](BULK_CHARTER.md) now specifies
1,084 dates, existing-source reuse, aggregate byte accounting, independent daily
raw checks and immutable checkpoints. It allocates no numerical scratch and
stops if storage is insufficient. Numerical panel assembly remains subsequent
work; completion of that raw job is not assumed. The hash utility checks a free-space threshold, not a
physical reservation: filesystem overhead and concurrent writers need explicit
allowance in that future design. The future numerical panel must
resolve completion-day boundaries and the interrupted pilot lineage before the
matched financial evaluation. No price outcome has been selected in this note.
