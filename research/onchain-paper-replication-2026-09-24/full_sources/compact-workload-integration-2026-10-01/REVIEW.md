# Independent compact workload integration review

Accepted for the bounded synthetic integration claims below. No material blocker was found in the inspected test or its implementation joins. This is not registered producer selection, successor admission, resource coverage or empirical release.

The saved `check01.log` reports **4 passed in 0.72s**. The test has three functions, with the final function expanded into checkpoint-stop and cleanup cases. The log also retains the named-profile qualification that 26 encountered files were withheld. No tests, numerical jobs or historical experiments were rerun for this review.

## Evidence and actual assertions

- `test_compact_workload_integration.py:39–70` invokes the actual workload dictionary algorithm with CompactMatcher and its unchanged checkpoint engine. The inherited fixture has seven samples, target size two, partition threshold/size four and seed 11. It exercises multiple partition blocks and a nonempty hierarchy. Forward/reverse ordered sample and typed-graph identities are distinct; purposes match the scalar callback sequence. Dictionary identity, memberships, hierarchy and every returned distance matrix match. Persisted completion purposes and little-endian float64 scores match the independent `match_reference` scores byte for byte. Terminal replay requires all requested pairs complete, no pending pair, exactly two events per pair, and no progress events or per-pair owner/artifact directories.
- Lines 73–91 fail the second actual engine construction, after the first directional score completed. The failed terminal retains one completion and the next pending begin (three events). A subsequent invocation is refused before further allocation. This proves preservation and no retry by the poisoned consumer; it does not prove reopening, automatic replay or reuse by a successor.
- Lines 94–125 invoke the actual array MCM kernel through MCMScoreStream and CompactMatcher. The checkpoint-stop branch executes real advance/save/close, retains a progress wrapper bound by the event hash and the numerical checkpoint file, and records no completed pair. Both branches confirm the engine state was released, the first tail contains zero acknowledged score records, stream completion is absent, and a failed pair-log terminal can be verified. The cleanup branch raises an injected error **after** real engine close succeeded; it exercises fatal propagation, not a real failure to release a mapping or buffer.

## Limits

The dictionary comparison runs the same workload orchestration twice, once with independent scalar matching and once with the checkpoint engine. It directly supports callback integration and numerical parity, not an independent proof of clustering/partition correctness. This fixture covers one seed and one partition-reduction level; larger/deeper hierarchies are not established here. The MCM negative cases stop at the first cell, not after a completed score chunk. Successful full MCM composition belongs to the separate retained compact-matcher integration evidence.

Owner/context values are synthetic and all leases are no-ops. No actual ResearchRun, guard, registered compact policy, source transition, failed-owner continuation, full-population quota or concurrent mutation is tested. Checkpoint existence and its wrapper/event hash are asserted here; independent checkpoint reload is covered by another focused test, not repeated by this fixture. Temporary numerical artifacts are not retained as an externally recoverable archive by this log. There is no financial return, timing, exposure, fee or funding claim.

## Reviewed byte identities

These hashes identify the files inspected at review time; the compact pass log alone is not an execution-time complete dependency manifest.

| File | SHA-256 |
| --- | --- |
| `tests/research/onchain_replication/test_compact_workload_integration.py` | `14981ea21cc848bc4671059a098205bc5aa24626ee5737a633bff65da53b708a` |
| `check01.log` | `c054db534e0608e86b21c016d0728372f5c74b12e6059dc92e76665804a1bc06` |
| `compact_matcher.py` | `645925483675e5fb8bc0aad4c662fcff963db24125610928b532bb13f1b1b650` |
| `compact_pair_log.py` | `65dc775fddd98acc1221a84d03c0cf4fd6810c9ee1dfce2a6f9069e18c360e61` |
| `mcm_score_stream.py` | `73daf274e788c0c46df6c1bd2a6ea203f1704b843458bb96632292432ef856d2` |
