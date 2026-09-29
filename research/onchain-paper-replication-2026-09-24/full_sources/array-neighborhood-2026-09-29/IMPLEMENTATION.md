# Optional array-based complete neighborhood extraction

ArrayNeighborhoodIndex preserves weak hop reachability, directed induced edges,
self-loops, center identity, ascending global node-index order and original edge
column order. Node-ID lexical order is not substituted for index order. Each hop
reads a frozen previous frontier. Large neighborhoods are rejected at the supplied
explicit capacity; they are never truncated. The historical 10,000-node study
configuration is unchanged. A separate synthetic configuration admits the full
10,002-node star used to exercise the component beyond that earlier ceiling.

The component replaces Python membership sets, per-node mapping dictionaries and
edge tuple lists with boolean membership arrays, int64 local maps, stable sparse
adjacency, bounded gathers and preallocated output arrays. The sampling-compatible
selected method returns independent ascending index arrays. It validates Python
integer centers/chunk sizes/configuration bounds strictly; it is not claimed to
accept every loosely typed input accepted by the legacy API.

Before building owned arrays, the constructor checks a conservative allowance:
16*(E+N+1) retained index bytes, plus 16*E+40*(N+1)+4*N scratch bytes and
chunk*(64+2*node_attribute_row_bytes+2*edge_attribute_row_bytes) for bounded
gathers. Counts/cumulative offsets, sorting workspace, frontiers/masks, selected
indices, local mapping and retained-edge indices are covered additively, even
when not simultaneously live. Before allocating full outputs, twice the exact
numeric payload is additionally required for mutable construction arrays and
immutable AttributedGraph copies. This is an array allowance per index/invocation,
not measured total RSS. Input graphs, Python ID/metadata objects, validation
internals and caller-retained prior outputs require separate accounting and the
outer guard. It is not a whole-workload memory claim.

A nonblocking ownership lock refuses overlapping/reentrant extraction, selection
or close. Context close drops the graph reference and owned index arrays without
closing a caller-owned mapped graph. Selected indices and immutable attributed
outputs remain valid across later calls and after both index and mapped graph
contexts close. Partial index-construction failures clear owned state; refusal
or extraction errors release the lock and permit later valid calls.

Red01 retained 15 missing-module failures. Green01 initially passed 18 checks.
Red02 demonstrated the missing busy-owner refusal, then green02 passed 52 checks
including sparse legacy and mapped graph checks. Green03 passed 53 checks with
mapped-input/output-lifetime evidence and constructor admission sentinel.
Red03 retained the missing public selected method failure plus passing injected
partial-index cleanup check. Final focused and broad verification follow.

No existing sampler/MCM consumer or empirical producer uses this optional
component yet. Registered execution-policy integration, capacity/configuration
lineage, accounting for all retained neighborhoods, full-size resource pilots,
intra-pair matching checkpoints and GPU parity remain separate requirements.
The initial mapped-graph and score-only improvements do not remove these needs.

Final focused green04 passed 55 tests in 14.23 seconds. It includes public selected
index lifetime and injected partial-construction cleanup with the failed object
still retained by the test, in addition to mapped graph and legacy parity checks.
Broad named verification remains pending; the prospective launcher retains the
previous 3 GiB max/2.75 GiB high, zero swap, 3 GiB host reserve, 6 GiB startup,
10 GiB disk reserve, two CPU affinity and 3,600-second wall limit.

## Broad closure

Offline01 passed 3,448 tests plus 97 subtests, two CUDA skips. Guard duration
1,548.36 seconds, child exit zero, cleanup verified; peak sampled memory was
2,415,431,680 bytes with zero memory.high/max/OOM events. All 139 source bindings
and frozen HEAD match; monitor/cgroup are absent. Independent terminal review
accepted this optional component. No registered consumer or empirical capacity
change is implied. Raw evidence is pinned by closure-check01.json.
