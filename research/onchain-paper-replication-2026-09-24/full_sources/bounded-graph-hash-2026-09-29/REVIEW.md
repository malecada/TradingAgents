# Independent bounded graph-hash review

Status: **no correctness defect identified in the reviewed serialization
increment.** Canonical identity preservation and the limited temporary-list
claim are supported by source inspection and retained synthetic results. This
does not establish bounded total graph memory or empirical capacity.

The delta in `tradingagents/research/onchain_replication/neighborhoods.py`
changes only `graph_hash` serialization. Multidimensional arrays recursively
emit array brackets and row separators. Flat rows and tuple/list identities are
serialized in slices of at most1024 elements. Each slice's outer brackets are
removed; a comma separates consecutive nonempty chunks. Thus their concatenation
is the same flat JSON sequence as the former complete-row/list serialization.
Empty arrays/lists retain their brackets without extra commas. Existing mapping
key sorting, scalar serialization and complete GraphSnapshot field membership
are unchanged.

This reasoning covers the admitted GraphSnapshot structure: two-dimensional
numeric arrays, flat string identity/source tuples, scalar clocks/counts/hashes
and the exclusion-count mapping. Float formatting still comes from the same
canonical JSON encoder after NumPy scalar conversion. Unicode, escaping, signed
zero and small/large finite float values therefore retain the prior encoding.
No source/config/graph identity is deliberately revised.

The tests independently reconstruct the complete canonical payload using
`graph_to_dict` and `canonical_bytes`, rather than calling the new chunking helper
to generate its own expected answer. Ten parity cases cover ETH/BTC, empty
arrays,4097 node IDs,3000 edge columns and4097-wide feature rows; changing the
publication timestamp must still change the hash. Three serializer-boundary
probes reject list/tuple arguments exceeding1024 elements. Duplicate-edge
rejection remains explicitly tested and `validate_graph` still executes before
hashing.

Saved `red01/child.log` retains the three expected oversized-list failures and
eleven passing parity/validation cases. The subsequent shared
`../activation-checkpointing-2026-09-29/review-green01` command includes this test
module and records30 passes/1 CUDA skip overall; all fourteen bounded-hash cases
are included. Its guard records child0, verified cleanup and no memory events.
The reviewer did not execute these tests. Broader `neural02` verification is
outside the evidence assessed here.

The bound is on the number of elements in temporary serializer lists, not on
total process memory or bytes per arbitrary string. `validate_graph` still
creates complete identity/edge sets and whole-array validation temporaries;
GraphSnapshot construction, neighborhood selection and eager population loading
still have their existing allocations. No end-to-end peak-memory reduction,
real-data throughput, full-history completion, numerical model agreement or
profitability was tested or inferred.

Independently recomputed identities:

| File | SHA256 |
|---|---|
| neighborhoods.py | `a9969f010903272c0dc497a2241c7ea865286f4bd381e2f10599a95418202898` |
| test_bounded_graph_hash.py | `40fd9d6eb62124bb10cd5d4c02f265004f644816f529fa23acbb03e099d4244c` |

Only source and compact receipts were read. No tests, real arrays, network calls,
empirical jobs, historical reruns, source edits or registration/ledger writes
were performed by this review.
