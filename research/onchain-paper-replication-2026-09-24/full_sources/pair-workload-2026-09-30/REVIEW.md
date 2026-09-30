# Independent isolated pair-workload review

Initial acceptance withheld for W1, the finite-score conversion boundary below. No other material blocker was identified within the stated pure scalar-workload and in-memory completed-score replay scope. This review does not admit an actual journal, PairSession, ResearchRun/guard, empirical consumer or ranked backend. Only this review was written; no tests, jobs, arrays/raw bodies, source changes or commits were performed.

## W1 — finite callback score can become an infinite output

`workload.py:39–41` accepts any finite Python float or integer. At line135 the accepted value is assigned directly to a float32 MCM cell. An exact-purpose callback reply containing `score=1e100` passes the explicit finite check but converts to infinity. The function can therefore return a nonfinite MCM despite receiving only accepted finite replies. Similarly, averaging sufficiently large finite dictionary scores at line87 can overflow before clustering refuses the matrix. The current invalid-score fixture covers NaN, infinity, boolean and text, but not finite out-of-range values.

Require the scalar similarity domain at the callback boundary, consistent with the selected oracle, or explicitly validate representability and post-arithmetic finiteness before publishing/returning numerical values. Do not silently clip. A joined finite-out-of-range callback fixture should be refused; zero remains valid. This does not require proving callback score truth or durable completion, which remain delegated to the future adapter. No runtime counterexample was executed during this read-only review; the finite float64 to float32 overflow follows directly from the accepted value and destination dtype.

## Independently inspected behavior

Dictionary loop order matches the maintained scalar implementation: original-index sorting, PCG64 reset to the sample seed, permutation advancement, partition boundaries, two directional calls in the same order, float64 averaging, average linkage, medoid tie order, expanded original memberships and recursion. The complete ordered-subset matrix cache follows the existing oracle. Matrix entries are counted cumulatively before each new allocation; the bound is not a total process-memory or graph-index bound.

Each dictionary workload namespace includes workflow/backend/configuration, sample identity, seed and typed graph contents. Block identity includes ordered indices, expanded owners, level/partition location, RNG state and hierarchy prefix. Directional sample indices and typed graph identities distinguish the two solver requests. The callback receives a deep purpose copy, and its response must join the precomputed key. Replay reconstructs the original deterministic control flow; a test-only completed-score map can suppress repeated solver calls without suppressing RNG advancement.

MCM identity includes full graph, node order, dictionary and ordered typed motifs, matching configuration and float32 output dtype. Every requested cell includes center index/ID and motif index; a reversed dictionary creates different purposes. The private output is returned only after all cells receive callback replies. Missing is represented by absent callback completion rather than a numerical zero. The supplied valid-zero/partial-row fixture preserves that distinction.

The dictionary's explicit backend and changed matching/configuration identity prevent silent reuse by the old consumer. Sample-record checks bind retained membership dimensions and typed contents, but do not independently reconstruct training provenance from source graphs. The implementation correctly leaves that admission to later composition. The simple NeighborhoodIndex and in-memory test cache are disclosed limitations rather than production resource or crash-recovery evidence.

## Evidence

All1223 bindings independently match current bytes; all1217 inherited frozen bindings remain present and unchanged. Six additions are the prior source manifest and this candidate's source, test, implementation and two logs. Initial `bindings.json` SHA-256 is `89355c70e4daf7d6aecef3c48fad14bbb0853c66e7c6250239038fadeff0845c`.

`red01.log` retains11 missing-module failures. `green01.log` reports11 passes in0.335seconds, SHA-256 `17da5c9bdfb96671e83b3014762ea48e84a89f7fdd475f2ae5a60bf23936d35e`. The tests compare complete distance matrices, hierarchy/memberships/medoids, interruption after one direction, exact request/computation order, MCM scalar values and reversed motifs, zero-valued completion replay, changed context and callback/size refusal. These are tiny scalar-oracle/in-memory tests, not ranked-backend parity or durable journal integration. No suite was rerun for this review.

Initial source SHA-256: `3965808ace3e9cb7441fef794bff8e73d655f97f73070c579005d8a0f8d9ba2b`.
Initial test SHA-256: `125494a972bbd3cfd5a3582b75ab5774425948d2b8eb8977e9db825998fcb856`.
Initial implementation SHA-256: `6ad7771d35d97c58ae843decdd77260e157f04d448fedc155ccb1401dcc222ab`.

The separate maintained owner-integration offline01 was still active and its standard child log contained failure markers without final diagnostics at inspection. This candidate does not supersede that failure, release its source freeze or justify relaunch. Actual source/runtime/current-owner admission, durable pair reference/body integrity, orphan reconciliation, ancestor-inclusive quotas, full-feature checkpoint reuse and numerical consumer routing remain untested/deferred. No financial fit, empirical allowance or validated strategy follows from this review.
