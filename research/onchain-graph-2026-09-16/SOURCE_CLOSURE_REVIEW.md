# Independent source closure review — September 16, 2026

Reviewer: independent onchain_review research-reviewer, read-only; no collection implementation ownership, additional network requests or financial calculations.

**Verdict: the bounded source audit completed correctly. No material collection or preservation defect was found. The single source allowance is consumed.**

Independent reconstruction reconciled all 25 output hashes, 11 base64 response bodies and their SHA-256/lengths, durable intents, timestamps, URLs, conditional headers, six nontruncated one-object listings, four exact HTTP 206 ranges and ETags, the downloaded block object's identity and both Parquet footers. There were 11 requests and 6,216,363 raw response bytes. The unavailable transaction sample and unused request slot 12 remain explicit. Eight complete metadata cells do not mean transaction extraction succeeded.

The downloaded 7,107 blocks have unique hashes, consecutive heights 18908895–18916001, continuous parent links and January 1 timestamps (00:00:11 through 23:59:59). Their transaction counts sum to 1,101,465, matching the transaction footer. These are provider-internal consistency checks, not independent canonicality or complete-day proof.

The exact source commit, preflight bindings and resource receipt reconcile. The failed initial shared-environment check was retained; the local locked environment passed before capture. Successful exit took 60.88 seconds with sampled peak process-tree RSS 305,504,256 bytes and no elapsed-time kill. All 33 imported files, including all 27 run members, are byte-identical to execution evidence.

The independently reconstructed projection totals 118,730,958 compressed bytes and 140,629,568 encoded uncompressed bytes for nine columns across 13 row groups; the largest selected group is 11,176,553 compressed bytes. These are metadata-derived sizes, not measured decoded memory, transfer costs or graph performance.

Next dependency: a separately frozen one-day column-range extraction, event/block integrity check and graph-resource benchmark. The complete denominator must retain failed/reverted transactions, null recipients, duplicate/order checks and boundary treatment. Floating `value` cannot establish exact wei or cashflow accounting. Historical publication timing, independent canonicality/full-day completeness, full history, transaction decoding, motif performance and predictive/economic value remain unestablished.

Reviewed anchors:

- `source-import-manifest.json`: `ffec59e7ee04c63a7f55c320af246eafc52a19a859656c3f9393c249e007a5b8`
- `projection-plan.json`: `e17f6fb06945f589eadafbda567a818060b3c97b45f586aba4c2174c514c98e3`
