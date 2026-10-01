# Independent corrected-source review — content-boundary qualification remains

SB1 and the parent-directory synchronization requirement are addressed. SB2 is improved but is not fully closed as a content-consistency guarantee. Acceptance for such a guarantee remains withheld; the current implementation supports the narrower explicitly sampled signature check under a sole-writer contract.

Creation, append and terminal publication now perform a fresh lease/root check and bounded content readback against their prebound hash after writing. An append failure poisons the writer before counts advance. A terminal post-write failure closes the descriptor and preserves the terminal file rather than returning its hash or retrying the identity. The parent directory is synchronized before start publication. Read signatures now exclude atime, avoiding false failures caused by reading. Filename capacity is checked before creation.

The four saved red regressions cover chunk/terminal post-write lease loss, a late earlier-payload change, and parent synchronization. `check02.log` reports **16 passes in 0.25 seconds**, not 0.23 seconds. The original source snapshot matches the initial reviewed SHA. No tests were rerun by the reviewer.

## Residual SB2 — final signature aggregate is not a content recheck

`score_batches.py`, final `verify` inventory loop: the constant-space sum of hashes of `(name, stat signature)` catches added/removed entries and signature-changing late writes, including the supplied late-mutation regression. It does not read content again. A same-size overwrite that preserves the observed modification/change timestamps, inode, mode, links and blocks leaves exactly the same aggregate and passes, even when it occurs in the final external lease before the final scan.

This is more specific than the documented limitation about mutation *after* the final scan. Earlier retained `representation-publication-2026-10-01/snapshot-check01.log` and its INITIAL_REVIEW already document an actual same-size rewrite passing a signature that included nanosecond mtime and ctime; those records do not separately establish which fields coalesced. Adding mode/blocks to the signature does not address an equal-extent in-place overwrite with unchanged values for those fields. The current green test only demonstrates the signature-changing case.

For a final content claim, add a bounded streaming content/chain check after the last external callback, retaining the O(chunk_bytes) working-memory requirement and explicit non-atomic limitations. A deterministic unchanged-signature counterexample can establish which boundary the correction exercises without relying on filesystem clock timing. Alternatively, explicitly restrict this primitive to callers guaranteeing no content mutation throughout verification and report only the sampled signature guarantee; such a restriction cannot itself establish immutable-content admission under a weaker caller contract.

## Integration and accounting limits

The chunk logical bound remains valid for this writer's admitted files: eight bytes per cell plus one 8 KiB metadata allowance per chunk and two fixed metadata allowances. O(chunk_bytes) working memory is retained by the two-integer aggregate; the aggregate is not a retained per-file list. It remains a logical encoded-byte bound, excluding input/copy/validation residency, filesystem overhead, logs and numerical scratch.

This whole-completed-chunk primitive does not ensure that an individual matching score is durably saved before its callback returns. An adapter accumulating scores in memory can lose the unflushed tail; a later caller must not silently recompute or claim replay protection for that tail. The primitive also does not remove the existing per-pair PairSession artifacts/reservations, admit successor ownership, reconcile failed scratch, establish actual graph/node/motif membership, or make full-fold storage/runtime feasible. Those requirements remain separate and must be tested at the actual callback/persistence boundary. Finite values outside [0,1] are still allowed here; numerical-domain correctness remains the caller's responsibility.

Reviewed SHA-256: source `01471f1ccd1420602bf66ab7f44ec98f0be8ad6bac31239797cf72bf559c58d6`; tests `a24c7fd1fc24732fb5ae45dbff633e3f286417ab0fe21caf2b02213dda8b79bb`; check02 `dddb27592ce48ade0d0b3aeca0ac9c2d06833a6891450e4d2f238465607fa7c2`; red02 `1ef7328582255bd0c12a10f0b241fb0101281d119f33ad31e9e618f9057d8b53`.

No financial data, empirical execution, old journal mutation, registration change or ledger write formed part of this review.
