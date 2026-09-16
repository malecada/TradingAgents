# Independent exact-hash utility review

September 16, 2026. This is synthetic engineering review for possible future
panel preparation. It does not admit another source capture, decode actual
transactions or authorize a financial experiment. Reviewed `hash_audit.py`
SHA256: `e4c4c83c279dd3cfbd54be4c544ab7a773a8c946acf8716e257952afdd9447a2`.

No material exactness or preservation blocker was found. Partitioning uses the
first byte only for routing; NumPy `V32` sorting and equality compare every byte
of each complete identity. Equal identities therefore meet in the same bucket,
including identities repeated in different supplied chunks. Adjacent equality
counts excess occurrences, so a triple occurrence contributes two duplicates.
The comparison slices include the preceding item across each comparison-block
boundary. The stream hash remains sensitive to input order.

The 32 MiB input-chunk ceiling and 256 MiB bucket ceiling are checked before
writing a chunk. Total bytes and occurrences have separate caller-supplied caps.
The sort stage holds one bucket array and sorts it in place with heapsort;
there is no second sorted disk copy. The stated bounds describe array payload,
not aggregate process memory, Python allocation behavior or caller-retained
input chunks. An enclosing aggregate resource guard remains necessary. The
maximum-configured-bucket benchmark subsequently completed, as reviewed below.

Only a fresh `mkdtemp` child is written and removed. Existing parent/sibling
files are not selected for cleanup. All iterator, validation and I/O failures
inside the owned-directory scope run the cleanup path. A cleanup failure can
leave that new scratch child and supersede the original exception; the caller
must preserve the exception and inspect any surviving scratch, not treat it as
a completed audit. The utility intentionally returns an audit result rather
than retaining the temporary sorted identities.

Independent synthetic verification used Python `Counter` as the oracle for
75,005 occurrences, 15,005 exact distinct identities and 60,000 excess
duplicates. Every one of the 256 bucket totals and unique counts matched.
Fixtures included embedded zero bytes, differences in leading/middle/final
bytes, randomized chunk boundaries and 40,000 additional identical identities
crossing comparison-window boundaries. The independently computed input-stream
SHA256 matched. Pre-existing sibling evidence survived both successful auditing
and an injected source-iterator failure; only the newly owned child was removed.

## Maximum-bucket benchmark closure

The retained benchmark source and receipts were independently inspected. The
fixture encodes integers 0 through 1,048,575 in the final eight bytes of a
32-byte zero-prefixed identity, then supplies the same 32 MiB chunk eight times.
This establishes 8,388,608 occurrences, 1,048,576 distinct identities and
7,340,032 excess duplicates, all in one 256 MiB bucket. All other bucket totals
are zero. This reaches the configured bucket payload ceiling without opening
any actual transaction identities.

Independent reconstruction used ordinary Python integer byte encoding rather
than the benchmark's NumPy encoding and matched the full repeated-stream SHA256
`d2bd738e6732ae90315e2746314d71c0d84125d65b7a7154c902ed211a466a17`.
Both source hashes in `HASH_AUDIT_BENCHMARK.json` match the retained utility and
benchmark files, and all expected/result denominators reconcile. The original
benchmark was not rerun for review.

`HASH_AUDIT_BENCHMARK_RESOURCE.json` reports exit zero, no limit event,
4.8417 seconds total guarded execution and 345,997,312 bytes (329.97 MiB)
sampled aggregate peak RSS under the unchanged 8 GiB/two-CPU guard. This is one
maximum-sized bucket observation, not a full-history runtime estimate, an exact
peak-memory measurement or proof of whole-panel storage/integration feasibility.

## Operational qualification

`hash_audit.py:30` checks free bytes against the next payload write. Filesystem
allocation and directory metadata can consume more bytes than a short payload,
so this is not an exact physical 20 GiB reservation at the boundary. Concurrent
writers also remain outside this utility's control. Before a future contract
requires a strict physical floor, reserve filesystem overhead before scratch
creation/writes, in addition to an outer resource guard. This is not a blocker
for the bounded synthetic benchmark on ample free space.

Actual dataset hash extraction, transaction canonicality, duplicated overlap
semantics, full-panel row bounds, worst-case physical scratch allocation and
crash-recovery integration were not tested. In particular, the caller must
declare whether prior-hour overlap occurrences should participate in a global
transaction-identity audit; the utility counts every supplied occurrence and
does not infer those semantics. No prediction, return, fee or funding claim was
tested or produced.
