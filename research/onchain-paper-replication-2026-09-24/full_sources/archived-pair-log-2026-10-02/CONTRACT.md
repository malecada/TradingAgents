# Explicit archive event replay

New archived_pair_log.verify streams unchanged compact pair-log bytes from a
caller-supplied bounded reader. Trusted terminal hash, owner, scope and the
terminal-bound start must match. Every event hash chain, ordinal, pair identity,
purpose, score, convergence kind and iteration bound is replayed using existing
compact event semantics. Complete totals, chunk extents (including a partial
last chunk) and full payload digest must agree. The result includes ordered
score and checkpoint-reference digests for later scientific joins.

The concrete synthetic integration creates an actual local PairLog, preserves
both full/partial chunks using archive_chunks, then reads through archive_consume
with the disposable local originals absent. Returned semantic state agrees with
the prior full local replay, and independent struct arithmetic checks the score
and checkpoint-reference digests. Corruption, order, type, absence, revocation,
foreign binding and malformed denominator cases must refuse.

This does not verify the actual checkpoint trees/MCM score stream/graph sources,
or register an archive-backed owner, stage or terminal. The old writer and local
reader are unchanged. No original empirical file is evicted. Caller controls
finite/guarded transport, manifest admission, cumulative reads/metadata and
returned-buffer lifetime. No network operation is performed by these tests.
