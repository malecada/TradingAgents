# Disposition of AC1 and AC2

AC1 and AC2 are closed for the bounded local copy/readback primitive. Original REVIEW_INITIAL.md and original source are preserved. The correction and targeted assertions were inspected without rerunning checks.

Both completion paths now publish expected completion bytes, invoke the live lease again, then perform callback-free exact metadata/content/root checks before return. Exact small phase inventories reject foreign names and conflicting regular or dangling failed markers, including the receipt root used by a fresh retrieval. The enumerator rejects an unexpected member before accumulating additional names. Late failures preserve complete+failed evidence.

Saved check02.log reports **31 passed in 1.19 seconds**: the baseline and 15 new cases. Six cases inject lease revocation, payload damage or completion-byte damage immediately after the real completion writer for preserve/retrieve. Nine cases add a failure marker, foreign member or dangling failure link to preservation, retrieval or the prior receipt root. These directly exercise the original findings. No claim of atomic protection against mutations after the final observation follows.

This disposition retains the original transport-owned finite/bounded I/O and frozen-source assumptions. It does not admit external transport, durable remote storage, source eviction, archive-backed compact readers, descriptor-cleanup completeness or empirical execution. External transfer accounting and guard placement require their own review.

Inspected SHA-256: archive_chunks.py `f26f1cb62334497494f9b02579f53be9e2238889a81f56c04fd4e781542b38fe`; test_archive_chunks.py `2bb299c23ba7daa5f22a3403b9da66860b01c694a9a140fc7c10365f634bd60f`; check02.log `debf62b5188b7281bebecaf6240bf345487105ba06695fb10c02ce7da1d013d0`.
