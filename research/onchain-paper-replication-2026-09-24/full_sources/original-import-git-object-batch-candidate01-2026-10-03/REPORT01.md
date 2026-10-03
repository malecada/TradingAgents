# Original source blob batch candidate01

Status: frozen source-only candidate for later independent review. Excluded from the next canonical-only successor. No empirical or engineering claim, actual Git subprocess, numerical import, array load, capsule installation or production mutation was performed.

The only proposed integration delta is `original_source_blobs` and its two private helpers in `resource_fixture.py`. The copied baseline contains historical parent routing, which is not proposed for adoption. Full-module AST parity proves every other body unchanged. Existing admission and matching-owner source authentication already use batch reads; this candidate does not accelerate the repeated matching lease hotpath. It replaces the preflight helper's 26 size plus 26 blob subprocess invocations with one fresh batch process per invocation. No cross-call cache is introduced.

The original claim reader, exact historical commit c6b568d4b1c177ab94ac37fbad462c2decc721c0, 26-entry source map, sorted order, each SHA256, positive extent, 2 MiB member ceiling and 4 MiB aggregate remain enforced. Binary blob bodies may contain newlines or NULs. Missing/non-blob records, malformed headers, trailing/partial responses, wrong hashes, excessive output and nonzero exit refuse. The batch object ID is syntax-checked; the admitted SHA256 authenticates each body independently. Existing runtime, current-worktree, Binding, Owner and claim authentication paths are untouched.

## Deliberate operational changes

The new helper has a 10-second whole-process read deadline, followed by bounded cleanup wait, rather than 10 seconds separately for each of 52 old commands. It is not a hard whole-invocation wall guarantee. Errors differ from the old subprocess exception sequence; failed exit and protocol errors become explicit refusal values. CR/NUL path names are newly rejected to protect line framing; the original admitted source names do not contain them. Git remains local with GIT_NO_LAZY_FETCH=1. No network retrieval is authorized.

Requests are capped at 65,536 bytes; collected stdout at 4 MiB plus 3,328 bytes of framing; stderr at 65,536 bytes; each read at 65,536 bytes. The output bytearray and final bytes coexist transiently, approximately twice the wire ceiling plus buffer overallocation, read chunk and stderr/request storage. This increases transient aggregate retention relative to one-body-at-a-time reads; no measured RAM or speed claim is made. Parsing uses memoryview for hashing. Selectors multiplex all pipes. Cleanup attempts kill-if-live, reap, each pipe close, and selector close independently through the exact accepted owned_io reducer; stdin ownership is marked released before close and not retried. Process wait may be called after an already completed wait; descriptors are closed once.

## Retained checks

All checks used the checkout-local `.venv/bin/python -B` and AST-extracted actual candidate functions with explicitly substituted stdlib transport doubles, not fake research authority. No package numerical imports occurred.

- `RED01.log`: tests first run against the original helper fail because there is no batch implementation.
- `GREEN01.log`: three parser/source tests pass, including ordered binary bodies and malformed, missing, wrong-type, truncated, trailing, wrong-hash and size refusal cases.
- `process01.log`: four tests pass for one fresh process per call, partial writes, caps, nonzero exit, timeout, incomplete response and exact first MemoryError identity despite later close uncertainty; all pipes and selector close once.
- `parity01.log`: complete baseline AST equals candidate after restoring the original helper and removing only its two added helpers.

Commands: `.venv/bin/python -B <this-directory>/test_batch01.py`, `test_process01.py`, and `check_parity01.py`; original RED selects baseline with BATCH_SOURCE.

## Remaining proof and adoption boundary

Independent source review and a separately released genuine local Git fixture are still required, including actual process/pipe/timeout cleanup behavior and the selected original26 object store. Synthetic transport tests do not prove native cleanup, real capsule source authority or whole-run capacity. No original samples or historical Git objects were changed. This is optional later preflight preparation, not a prerequisite for the canonical-validation successor, and not progress on financial fit or numerical replication acceptance.
