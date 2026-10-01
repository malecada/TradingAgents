# Independent compact MCM synthetic integration review

Accepted as the tiny composition demonstrated by this test. No blocking mismatch was found between the inspected test and the stated MCM integration claim. This does not establish registered producer selection, resource coverage, historical recovery or an empirical result.

The actual path is the frozen array MCM kernel → MCMScoreStream → CompactMatcher → unchanged matching_checkpoint create/advance/score_only/close, with PairLog and retained tail/batch persistence. The stream callback dispatches the actual CompactMatcher; scalar reference matching is used for the independent expected MCM and the synthetic dictionary fixture, not as the tested MCM compute callback. Each actual occurrence therefore uses fresh direct-engine matching rather than a completed-score lookup.

The strengthened test checks all 14 purpose hashes in order, exact little-endian float64 bytes recovered from retained tails against the reference callback's saved scores, and complete final 7×2 MCM equality. Stream completion and verification traverse four chunks (4, 4, 4 and 2 cells). Separate PairLog terminal replay requires 14 completed pairs, 28 events, two event chunks and exactly 4,704 record bytes (`28 * 168`). It asserts zero progress events, an empty checkpoint directory and absence of per-pair owner.json/artifact-* paths. This is a positive completed-pair composition test; it does not exercise a progress checkpoint in the full MCM chain.

Both saved integration logs report one pass in 0.60 seconds. Their log bytes happen to be identical; the strengthened test source and preserved `integration01-test.py` distinguish the two versions. Only integration02's test includes the added exact float64/purpose comparisons, so those claims are not retroactively assigned to integration01. The reviewer read source and saved logs without rerunning either identity or inspecting numerical fixture files.

The test uses no-op leases, synthetic context/owner hashes and a prospective checkpoint schedule. The dictionary is already prepared by the reference fixture. Actual registered ownership/guard/source admission, a compact dictionary callback, failure propagation across this full composition, progress/resume, retained historical reuse, and process/storage scaling remain separate. The source-inspected engine still closes state before logging completion, but this integration test has no independent close instrumentation; that coverage belongs to the separate accepted matcher test. Temporary pytest fixture outputs are not an externally preserved numerical artifact set. No complete execution-closure manifest is inferred from these direct source hashes.

Exact reviewed SHA-256:

| Artifact | SHA-256 |
|---|---|
| current integration test | `3e186f7a0653d3a1ede6bfbda53f17ab950a9702660d0638b37f2037e751896f` |
| preserved integration01 test | `7363c4fcee470909ef396550acb6df277472638ba133de75a8117b8f58f88188` |
| integration01 / integration02 logs (same bytes) | `225099dbf4a44346a277030688f9ee77b2af6e74365dc9d69f6b8628fb03820b` |
| `compact_matcher.py` | `645925483675e5fb8bc0aad4c662fcff963db24125610928b532bb13f1b1b650` |
| `compact_pair_log.py` | `65dc775fddd98acc1221a84d03c0cf4fd6810c9ee1dfce2a6f9069e18c360e61` |
| `mcm_score_stream.py` | `73daf274e788c0c46df6c1bd2a6ea203f1704b843458bb96632292432ef856d2` |
| `score_tail.py` | `deb225ccb9d4002d619d4a09c23272ee93bcfa675a8c54d932fc4f3758420e88` |
| `score_batches.py` | `079571b425e1fd04ecf46d8b34aa6fb5352ca2a2bdfda1d9f45982a1ced1f531` |
