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
corpus under 8 GiB RSS. A separately implemented and tested hash-bucket/external
sort can compare complete 32-byte transaction identities exactly. At minimum,
unsorted identity storage is 32 times the actual total transaction count; sort
buffers, receipts and temporary copies require additional space. The 48 GiB
ceiling is not yet proven sufficient. Actual footer row counts and a synthetic
disk/RSS-bound demonstration are admission prerequisites; no truncated hashes,
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

Next engineering work: finish and independently verify the first source tranche,
measure its actual stored/metadata bytes, then freeze a full-cohort retention and
checkpoint design with exact byte accounting. The future numerical panel must
resolve completion-day boundaries and the interrupted pilot lineage before the
matched financial evaluation. No price outcome has been selected in this note.
