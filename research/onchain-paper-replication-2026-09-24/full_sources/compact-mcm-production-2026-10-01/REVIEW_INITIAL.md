# Independent initial review

Acceptance withheld pending CMCM1 correction and terminal evidence. This is a read-only source review; no tests, numerical jobs, or empirical array reads were performed. The nine-case producer check was still active at this review boundary.

## CMCM1 — cleanup uncertainty can become an ordinary recoverable error

`mcm_score_stream.py:184–209` closes the stream on callback failure, but `close()` sets `closed=True` before sequentially closing the active tail, batches, and root descriptor. A child close exception prevents the remaining attempts. `compact_mcm.py:247–249` subsequently skips a stream already marked closed. An ordinary `OSError` can therefore escape despite unresolved resources, permitting an outer ordinary-unavailable handler to continue the worker.

The same issue begins below the stream: `score_tail.py:144–159` invokes terminal cleanup and marks the child closed before closing its two descriptors; `score_batches.py:207–219` marks terminal before descriptor close. A failed internal `tail.finish()` or `batches.finish()` can leave a terminal-looking child which a later stream close cannot diagnose. Constructor cleanup also occurs before the child/stream assignment reaches its caller.

Required correction: establish a fatal `BaseException` cleanup contract at the actual primitive descriptor boundaries; independently attempt remaining owned descriptors/children, preserve the primary error and retained evidence, and propagate fatal uncertainty through stream construction/callback/finish and producer failure handling. A failed close must not be blindly retried using an old descriptor integer, because it may already have been released/reused. Terminal state must not imply successful cleanup. Fresh regression evidence should cover internal tail-terminal cleanup and batch-terminal/constructor cleanup, not only a directly injected outer close failure.

## Other inspected contracts

The producer derives the actual required graph from registered Training ancestry, ordered motifs from the actual Produced dictionary, and the same MCM workload hash used by the preserved kernel and score stream. It joins row/cell/byte accounting, captures the float32 matrix digest before seal callbacks, uses the stream terminal reference for stage sealing, and compares saved float32 bytes to the resident output. Final callback-free checks cover original ancestry, resident matrix, complete stage inventory/inode, producer receipts, and saved output wrapper.

The publication refactor retains public locking and the callback-free wrapper verification after the nested mapped-reader context exits. Private functions explicitly require the caller's owner transition lock; the new producer holds it throughout. This inspection did not identify a separate material scope/hash or wrapper-exit regression.

The admitted numeric policy covers the array-neighborhood buffer and resident float32 output only. Parent/sample/dictionary residency, dictionary readback, matching/stream scratch, mapped-page residency, Python objects and whole-process RSS remain excluded. No native selection, complete representation, complete calendar/price-label denominator, cold reuse, full-size resource feasibility, or empirical result is established.

## Source boundary

SHA-256 at inspection:

- `compact_mcm.py`: `e220e00e9df41f2a1806453c5d2eb15c60f3b0c1723f7df1bf407218d022904b`
- `compact_mcm_publication.py`: `068707321e7b2b05213e2dc0aeb06ea5f56e865eff5c2b2e03ea7dbd33828688`
- `mcm_score_stream.py`: `73daf274e788c0c46df6c1bd2a6ea203f1704b843458bb96632292432ef856d2`
- `score_tail.py`: `deb225ccb9d4002d619d4a09c23272ee93bcfa675a8c54d932fc4f3758420e88`
- `score_batches.py`: `079571b425e1fd04ecf46d8b34aa6fb5352ca2a2bdfda1d9f45982a1ced1f531`
- `test_compact_mcm.py`: `4b6ae3e16935de092f7cb694dbb138ffb10c38a28f060e7b8ca7247e9f30a6d3`
