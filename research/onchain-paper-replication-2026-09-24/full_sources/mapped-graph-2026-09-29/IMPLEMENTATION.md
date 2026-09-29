# Optional read-only mapped graph loading

The existing loader maps NPY inputs but expands node IDs into Python strings and
then copies numeric arrays in GraphSnapshot. Loading a complete fold therefore
retains eager per-week data. The optional open_mapped_graph context preserves
read-only numeric and Unicode NPY maps instead. Its GraphSnapshot subtype has
exactly the existing dataclass fields; canonical scientific identities are
unchanged. The default load_graph and ordinary immutable snapshots remain eager.

Admission checks a maximum 64 KiB manifest, exact member/metadata denominator,
positive integer total file-byte allowance, exact member filenames, non-symlink
regular files, actual versus declared sizes, all hashes and NPY magic before any
mapping. NumPy headers are capped at 10,000 bytes. Mapping requires the NPY data
extent to consume exactly its file. Numeric members must be real numeric arrays;
IDs must be one-dimensional Unicode maps in existing strict sorted order. No
reordering is performed. Eager unique unsorted IDs remain supported.

Every repeated graph validation checks mapped IDs in overlapping blocks, avoiding
full Python-string materialization/sorting. Feature lineage uses streamed
node-order hashing with the same canonical JSON bytes as the old tuple hash.
Other validators still allocate edge-sorting indices, finite checks and aggregate
transform/comparison temporaries; adjacency and model working memory are also
unchanged. The mapped-file ceiling is not an RSS, virtual-memory or full-workload
capacity guarantee. Full-size resource pilots remain required.

## Ownership and preservation

Maps are borrowed only while the context remains open. Callers must keep all
required contexts open while raw arrays/views are referenced, including embedding
alignment ancestry. Saved bodies must remain frozen: read-only mapping does not
protect against external writers, truncation or hostile replacement races. The
context closes every successfully opened map on success and failure; no flushing,
scratch, repair, deletion or empirical restart is involved. All closes are
attempted after one fails; the actual primary exception is retained with a cleanup
note, or cleanup raises on an otherwise successful exit. An unrelated handled
exception cannot hide cleanup failure.

Synthetic producer tests compare eager and mapped sample records/RNG, learned
dictionary, MCM values and full feature bindings, and inspect independently owned
outputs after raw maps close. This is not additional neural-training or GPU parity.

## Retained verification

Red01 records 18 missing-API failures and one unchanged-default pass. Green01
passed 42 focused checks. Independent review then identified the possibility
that np.load accepts NPZ bytes under a .npy filename and an ambient-exception
cleanup ambiguity. Red02 proves complete NPY preflight was absent: it fails at
the first valid earlier member, not by measuring a leaked NPZ handle. Red03
directly demonstrates a hidden cleanup failure during a normal exit inside an
unrelated exception handler. Both paths were corrected. Expanded green02 passed 96 tests in 56.73 seconds.
Independent review accepted the corrected source for frozen-source named offline
verification. The full named suite subsequently passed as recorded below.
No empirical gate selects this API, and no registered job wiring is added in
this increment.

Graph population admission needs a separate explicit residency policy and bounded
aggregate mapping/lifetime integration before actual-data use. The current byte
ceiling applies to one context, not the sum of a fold's contexts. The 10,000-node
neighborhood and 4,000,000-entry matching ceilings remain unchanged. Budget is
25/52 and all 1,420 financial fits remain pending.

## Named offline terminal evidence

Offline01 passed 3,366 tests plus 97 subtests, with two CUDA skips: 2,768
standard tests in 1036.06 seconds and 598 neural tests in 444.71 seconds. The
guard completed in 1484.10 seconds with child exit 0, verified cleanup,
2,475,028,480 sampled peak bytes and zero memory.high/max/OOM events. All 130
frozen source/test/runtime/launcher bindings still match. The monitor and owned
cgroup are absent; the execution session returned exit 0. Independent final
review is recorded separately in CODE_REVIEW.md.

This closes bounded synthetic verification of the optional loader. It does not
establish full-fold graph residency, full-size MCM or model capacity, CUDA parity,
source availability, empirical admission or prediction performance.
