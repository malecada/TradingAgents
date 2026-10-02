# Independent initial cold-reader review

Acceptance withheld for four bounded corrections below. Current source, test assertions, dependencies and saved logs were inspected. No tests, network transfers or empirical jobs were rerun. The source inspection for this candidate is complete.

1. **APR1 — source close obscures the primary cause.** `archive_pair_reader.py:206` uses shared `_cleanup` in a finally block. If replay/transport has already failed and source descriptor close also fails, the resulting fatal error is explicitly chained to the close error rather than the primary operation failure. Fatality is preserved, and Python context may still retain the earlier failure, but the declared failure-preservation contract should retain the primary as the explicit cause and annotate the close uncertainty. Capture the in-flight exception before closing and preserve it without retrying the descriptor. Test simultaneous primary failure and source-close uncertainty.

2. **APR2 — late source failure markers permit additional reads.** `live()` at lines172–176 checks failure markers only in the new attempt. Adding `failed.json` or `cleanup-failed.json` to the source after initial snapshot admission does not stop subsequent remote consumption. Final `source.check()` rejects the conflicting source, so this is unnecessary transfer and disposal of fresh cache after authoritative failure evidence, not false final acceptance. Check both source marker paths using lexists after each external lease; include dangling links and a test proving the next transport call is suppressed.

3. **APR3 — claim uses a stale preflight lease.** The lease at line154 precedes the entire retained metadata/inventory scan, budget checks and capacity check; line166 then creates the fresh claim without refreshing authority. A valid initial lease does not authorize creation after authority was revoked during this potentially lengthy preflight. Invoke a fresh lease immediately before claim, followed by callback-free source-root and failure-marker checks. A targeted regression should revoke during the last preflight boundary and assert no new attempt exists.

4. **APR4 — metadata allowance omits failure combinations.** The minimum `(3*max_chunks+4)*META_LIMIT` at lines159–160 covers successful child receipts and ordinary root metadata but is not conservative for cleanup failure. A consumed child can retain three normal receipts plus failed and cleanup-failed records, while the parent retains intent, failed and cleanup-failed: at full chunk count that is `3*count+5` files. Summing independent maximum child and root terminal conflicts gives a conservative `3*count+6`; a margin8 is sufficient. Preserve the logical-only qualification and reject insufficient allowance before claim. This is not a physical quota and does not cover arbitrary foreign injected files.

The core cold path otherwise uses the caller's archive-completion hash, owner, scope and explicit archive policy to join canonical start/terminal/archive metadata, ordered mappings and exact copy/old-read inventories. Fresh consumption and event replay verify every chunk; final checks after the last callback recheck both source metadata and the newly retained read receipts. The source is opened read-only, and failures do not reopen or mutate the original writer. Those checks do not substitute for current-owner/scientific admission, checkpoint bodies or score-stream joins.

Saved check01 reports **112 passed in2.57s**, comprising17 new reader cases and95 prior archive checks. The missing-module red01 is retained separately. Current tests cover full/partial positive replay, trusted-input and budget refusal, changed metadata, initial source failure markers, failed downloads and final callback refusal; they do not cover the four cases above. No CONTRACT.md existed in the evidence directory at inspection; source docstrings and the assigned brief define this review's bounded scope.

Inspected SHA-256:

- archive_pair_reader.py: `9d7539cd207d18fd53db9ff4d7e5aa47158869e872aed2f84b0ecdf4562387bd`
- test_archive_pair_reader.py: `45118ba9b871b60976726e2f15d7bb1c3b900bd13ba23f718e1ef22ea360fe6a`
- check01.log: `18d53f731ef8f4c15a003d7ebd1725ab946b55dd44bc8802f97f98c3d3723308`
- red01.log: `e4e45203b20223e42a81a58a14bc08e6a8f957e231b3d5496f3d1b62fa570712`
