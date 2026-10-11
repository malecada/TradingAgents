# Neighborhood index initialization: source-only diagnosis

Exactly three frozen files inspected: array_neighborhoods.py, neighborhoods.py and contracts.py. No empirical input, live process/receipt, scientific import, test, benchmark or patch. Prior driver report2ca19ae32671c8f77de85f0ad276bfc3e743b2dbcdda542bf8998def6506429e supplies call ordering. No claim that active pilot34 is inside this constructor.

## Exact constructor work

array_neighborhoods.py:16–44 first checks its numeric buffer allowance, then calls graph_hash(graph) at:32. Only after that returns does it construct adjacency indexing (:36–41): for each of two endpoint rows, one stable np.argsort, one np.bincount(minlength=N), and one cumsum into an int64 offsets array. There is no authority callback argument or call inside the constructor, its hash helper, validation, or cleanup. Driver has one ordinary poll immediately before construction and one immediately after; no between-sort or per-chunk authority poll exists in these bodies. Context entry only checks closed status.

neighborhoods.graph_hash:26–67 first calls validate_graph and then streams canonical JSON for EVERY dataclass field into SHA256. Arrays and IDs are traversed in bounded chunks; even bounded-memory hashing serializes every scalar. Ordinary narrow2D arrays use up to1024 scalar cells per temporary list; wide arrays recurse by row and then chunk by1024. It neither reuses an authenticated digest nor skips unchanged arrays. Constructor does not separately call node_order_hash: node IDs are already a graph field.

contracts.validate_graph:91–138 performs node-ID validation (mapped sorted-string blocks of65536 with overlap, or sorting ordinary IDs), endpoint min/max, duplicate-edge detection, numeric finite checks, optional aggregate checks and conservation checks. _duplicate_edges:81–88 calls np.lexsort on both full endpoint rows and checks adjacent pairs in65537-column blocks. It does not assume sorted input. Optional aggregates cause additional isfinite/nonnegative/log1p/allclose traversals. Thus successful constructor setup contains exactly THREE graph-wide sorting API calls: one duplicate-edge lexsort and two endpoint stable argsorts. These sorts serve different outputs; they are not interchangeable merely because all visit edges.

## Time and space

Let N=nodes, E=edges, F=total graph feature/aggregate scalar count, and J=canonical serialized graph byte length. Setup includes two endpoint min/max reductions, duplicate checking, finite/aggregate validation, full JSON generation/hash, two endpoint orders and two bincount/cumsum pairs. A conservative comparison-sort model is O(E log E + F + N + J), plus O(N log N) for ordinary nonmapped node-ID sorting. NumPy may choose specialized integer sorting implementations; no exact backend complexity, constant or elapsed value is established. String/JSON cost also depends on string and number encoding lengths, represented by J.

Retained numeric index memory is two int64 edge orders plus two int64 offset arrays:16E+16(N+1) bytes under the component's stated index-width assumption. Source numeric allowance is exactly:

16(E+N+1) + 16E + 40(N+1) + 4N + edge_chunk*(64+2*node_width+2*edge_width).

This is an additive allowance including later extraction scratch, not measured RSS or an actual peak. Validation adds an edge permutation, bounded duplicate-comparison blocks, finite masks and optional aggregate temporaries. Graph inputs, Python metadata/IDs, validation internals and caller-retained outputs are explicitly outside that allowance (array_neighborhoods.py module contract). Hashing uses bounded JSON chunks rather than a whole-graph Python list, but validation arrays are not all chunked. No actual graph dimensions or allocations were read.

## Repeated work and legitimate optimization scope

The prior driver already calls graph_hash and node_order_hash before publishing journal pending. Constructor then calls graph_hash again after pending, repeating full validation and canonical serialization. This is proven repeated work, NOT a proved removable redundant check: the intervening producer boundary and publication callbacks are mutable-currentness boundaries. Passing the earlier digest without fresh validation would change observation semantics.

Within constructor, duplicate detection's lexsort and endpoint argsorts traverse the same endpoint storage for different purposes. A future specialized index builder could investigate retaining validated sort products, but must preserve original stable edge order, duplicate refusal, complete directed adjacency, buffer limits, mutation observation and failure behavior. No equivalent substitution is established here; bypassing graph_hash or validation is not proposed.

The concrete scheduling risk is an unpolled whole-graph validation/hash plus index build. Bracketing polls do not guarantee completion within the frozen authority interval. Future segmentation would require reviewed genuine callbacks at responsible boundaries, with mutation/identity rejoins and unchanged numerical order; each indivisible native sort/validation step still has unmeasured duration. No grace, late refresh, threshold widening or active-run intervention follows from this report.

Outcome: the constructor is a plausible expensive unpolled phase by source structure. Its actual pilot34 duration, current execution location, CPU/I/O share and optimization benefit remain unknown.

## Exact source SHA256
514ef8993d962c29b81777791303904f79a31e695cb0b5d152b27bdd02e2cf3f  tradingagents/research/onchain_replication/array_neighborhoods.py
4f41912aa5d91e449eea4a30d813e5b57b65cbd7445e5ba153725e7bbe7ee00a  tradingagents/research/onchain_replication/neighborhoods.py
3f88e9e56f2bfca059e2ef9da2b01ae593444b05e1067154653ea6a5479fea1a  tradingagents/research/onchain_replication/contracts.py
