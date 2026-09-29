# Registered aggregate graph residency

The new graph_residency_input is an admitted execution policy, not a scientific
configuration. Its exact schema is version 1, mode mapped, positive integer
max_graph_file_bytes and max_open_arrays. Caller and producer-plan names must
match; all job policies are preflighted before population production. Completed
representation reuse rejects an unused graph policy. No existing empirical gate
is changed.

The job resolves only admitted immutable graph input manifests. Current-run
output graph loading remains explicitly refused, as in the previous job loader;
there is no guessed adjacent-array location. The new shared storage preflight
validates all graph/member identities and actual file sizes. Population limits
count each simultaneously opened array and its full NPY file bytes, including
headers, without deduplicating repeated storage. The pre-existing aggregate job
payload bound remains conjunctive. Entire-population admission precedes mapping
of the first graph. The per-graph loader independently rechecks admission.

The context issues a live MappedGraphPopulation with exact graph objects, manifest
paths/hashes, member handles and aggregate counts. A private in-process owner
registry binds the issued instance and original fields. Public construction or
dataclass replacement cannot relabel another population as admitted. Validation
occurs before descriptor hashing, rejecting stale/closed, foreign or eager
objects. Ordinary eager calls remain unchanged when no policy is supplied.
The producer claim records the graph-policy input name and admitted SHA-256;
scientific sample, dictionary, graph and feature identities are unchanged.

## Ownership and error handling

Every raw graph stays alive through synchronous representation construction,
including sampling and alignment. The loader reports each opened map to the
population owner, including maps created before a graph fails validation. The
context invalidates ownership and attempts all closures before model fitting.
Unresolved handles or a close exception raise GraphPopulationCleanupError, which
bypasses the job's ordinary unavailable-representation handling and aborts before
execute_batch. Completed numerical journals and published bindings are retained.
The original error remains in exception chaining if cleanup also fails.

Mapped graph repr now formats only metadata, because automatic dataclass repr
can inspect borrowed arrays after closure when reporting an earlier failure.
This does not make raw arrays safe outside their context; consumers still must
retain independently owned outputs. The owner registry is a cooperative in-process
boundary, not protection from hostile code that rewrites private module state.
Backing files must remain frozen for the context lifetime.

## Verification in progress

Red01 records 16 expected pre-implementation failures; green01 passed 57 tests
in 56.98 seconds. Independent review then identified a relabeled foreign-lease
provenance bypass and weak aggregate-limit tests. Red02 exited 139 while pytest
formatted closed mapped graph arguments; its traceback is diagnostic crash
evidence, not a clean provenance assertion. Red03 isolates both failures safely:
the forged lease reaches descriptor hashing, and a bounded child with core dumps
disabled exits -11 while formatting a closed graph. The corrected source adds
issued-owner identity validation and metadata-only repr. Aggregate tests now
choose a limit that admits each graph individually but not their sum, and also
exercise the independent legacy payload ceiling.

Expanded green02 passed 83 tests in 106.57 seconds. Green03 passed all 24
graph-residency checks in 32.22 seconds after extending the failed-parent test
with a registered successor under a newly bound storage allowance. The successor
reuses persisted samples without invoking the sampler, matches the uninterrupted
full binding and dictionary identity, and preserves the failed parent bytes.
Independent focused review accepted the corrected source and saved results.
The frozen-source named offline01 suite failed its disk-reserve guard after
1505.37 seconds. Standard verification passed 2,768 tests plus 97 subtests; the
neural phase was interrupted without a terminal summary. Cleanup is verified,
the owned monitor/cgroup are absent and all 132 bindings match. Peak sampled
memory was 1,899,073,536 bytes with zero memory limit events. Full offline
verification and release closure remain incomplete. The failed identity and
all partial evidence remain preserved; no automatic retry is admitted. Registered fixture tests execute actual graph
loading, sampling, dictionary and MCM production; final model batches are stubbed
when testing ownership/forwarding. They do not establish new full-size training
or CUDA parity. No real source data, financial fit or empirical claim is run.

## Complete successor verification

The user explicitly lowered the prospective disk reserve to 10 GiB. The reviewed
new offline02 identity preserves the failed offline01 receipt and unchanged
implementation. It passed 3,390 tests plus 97 subtests with two CUDA skips:
standard 2,768 in 1345.68 seconds and neural 622 in 519.14 seconds. Guard duration
1868.96 seconds, child exit 0, cleanup verified, sampled peak 2,657,550,336 bytes,
zero memory.high/max/OOM events. All 136 bound files match; monitor and cgroup
are absent. `offline02/closure-check01.json` retains the exact terminal/log hashes.
Independent terminal review accepted the engineering increment for release. The earlier failed
suite and cold-file offload remain separate failures, preserved without rerun.

## Remaining scope

Mapped-file bytes and mapping counts do not bound RSS, page cache, validation
temporaries, adjacency indices, matching, feature tensors or neural activations.
The 10,000-node neighborhood and 4,000,000-entry matching ceilings are unchanged.
Further full-neighborhood engineering and reviewed finite resource measurements
remain necessary. Budget stays 25/52 with all 1,420 financial fits pending; all
remaining claim allowances remain assigned. A new empirical resource claim needs
a reviewed cumulative extension or explicit reassignment before execution.
