# Exact neighborhood census engineering

This prototype is isolated outside the 141 files frozen by neighborhood-policy
verification. No empirical graph body, financial label or price is opened.

Each directed edge is canonicalized to min(endpoint)*N+max(endpoint), with -1
for self-loops. A strict signed-int64 endpoint domain and N<=3037000499 prevent
key overflow. In-place heapsort orders a mapped key array with constant sorting
workspace. Chunked adjacent-key deduplication carries the previous key across
boundaries, then increments both endpoint counts. All N counts begin at one;
reciprocal edges and duplicate columns count once, loops add nothing and isolated
nodes retain one. Full cardinalities, histogram, all maxima indices and the
count above unchanged 10,000 are preserved. No node is truncated or sampled.

The logical output/scratch envelope is 8E+32N+131072 bytes, admitted before
creation. Four numeric arrays have at most 8E+32N payload bytes. The remaining
128 KiB covers headers and the bounded identity serialized into checkpoints and
summary. Exact encoded completion metadata and existing file sizes are checked
before either final summary or completion checkpoint is published. Filesystem
allocated blocks are distinct and must be measured by the registered wrapper.
The retained completed graph is outside the new-output allowance.

Array workspace includes mapped keys/cardinalities, chunk endpoint/key/difference
buffers, maxima or histogram arrays; source mapping/validation and Python/runtime
memory remain separate. A conservative numeric upper bound of 8E+64N+64*chunk
plus small metadata is suitable for prospective review, not measured whole-RSS
feasibility. Maps close independently; cleanup errors retain a primary failure
as the primary exception with attached notes. Existing output paths are refused.
Durable phase checkpoints retain file hashes; no automatic same-identity restart
or intra-sort resume is implemented.

Red01 records missing implementation. Green01 passed seven independent set-oracle
checks. Red02 reproduces maximal-identity metadata overflow; green02 passes nine
checks after the reserve correction. Red03 reproduces primary-failure masking
and skipped second cleanup; green03 passes ten tests after independent cleanup
and prepublication accounting. Tests include directed/reciprocal/duplicate/loop/
isolated graphs, exact chunk invariance, a 10,002-node hub with no truncation,
invalid domains and existing-identity refusal. Independent review accepted the
prototype corrections; this is not empirical execution admission.

A separate guarded synthetic01 uses a shuffled three-million-node directed ring
with four million columns including duplicate edges. Its independent full-array
oracle requires cardinality three everywhere, all nodes as maxima, N unique
pairs and one histogram bin. Guard: 1 GiB max, 0.75 GiB high, zero swap, 3 GiB
host reserve, 4 GiB startup, 10 GiB disk floor, two CPU affinity, 180 seconds.
It is not a general graph-runtime guarantee and may share CPU time with the
separate offline suite. Exact seven-file bindings are in scale-bindings.json.

Before empirical execution: finish scale evidence; integrate the reviewed engine
and registered producer/job kind after the active source freeze is lifted; test
exact graph/config/node-order/plan and output bindings, environment and failure
routing. The generic job currently requires a 20 GiB floor and does not forward
a lower floor to its worker assertion. Explicit prospective 10 GiB policy support
and worker forwarding require tests/review; historical gates remain unchanged.
The proposed actual whole-job wall limit is 540 seconds (stricter than the
charter's 3,600 maximum), including graph hashing/mapping and output finalization.
The outer guard and cleanup margin must be independently reviewed; this is a
fail-closed deadline, not a promise of successful completion. If this cannot meet
the requirement, implement finer durable progress before release.

Prepare the exact full-ancestor lifecycle gate with the accepted one-claim budget
extension, source/runtime and inputs, independently review it, then commit and
freshly admit before touching empirical graph bodies. Budget remains 25/52 until
that adoption. This census closes no original nine-week/109-cell resource
requirement and does not establish induced-edge, dense-pair, MCM or fit feasibility.

Synthetic scale01 completed: guard 5.751070 seconds, peak 198,012,928 bytes,
zero memory events, child zero and cleanup verified. All seven bindings and
HEAD match and owner/cgroup are absent; exact closure is scale-closure01.json.
The worker duration 5.205721 seconds includes generation, census and oracle.
The engine internal 1.384061-second snapshot precedes final hashing/publication
and cleanup and must not be called end-to-end census runtime. Census files
occupied 80,002,799 logical bytes and 80,039,936 allocated bytes before the
verification receipt was written. Draft census/job objects name exact metadata
and stricter 540-second whole-job containment, but no gate admits them yet.
