# Isolated ranked full-matcher composition

The accepted scalar normalization checkpoint engine is composed with the reviewed
ranked-hardening checkpoints and accepted sparse scalar objective. Production
matching, dictionary, MCM, cache dispatch and all registered gates are unchanged.
The paper's declared literal annealing schedule/objective, float64 semantics and
original4Mpaircap remain unchanged. Outer checkpoint schema2 deliberately refuses
the earlier composite schema1; no historical checkpoint is migrated silently.

Phases are annealing, hardening and done. Once annealing completes, matrix identity
hashing and stable ranking occur atomically within that advance. Interruption
there poisons the composite; recovery uses the preceding annealing checkpoint.
Ranking creation cannot resume internally. After ranking, advance consumes at most
min(max_operations,hardening_chunk_entries) entries, with chunk bound65,536.
Annealing operations and ranked entries are different work units, not a common
runtime measure. Existing normalization-axis requirements remain unchanged.

Retained numeric allowance now explicitly reserves32*n*mbytes: three float64
annealing matrices plus one int64 ranking. The annealer receives the total allowance
minus8*n*m. Creation also checks the separate ranked scratch allowance
17*n*m+n+m+16*min(n,m), default80MiB; it is not the old8MiB hardening workspace.
At2000-square, retained numeric state is128,000,000bytes and conservative overlap
of annealing matrices with ranked explicit allocations is164,036,000bytes.
These exclude original graphs, validation/hash objects, Python pair/container
costs, native sort workspace, runtime/allocator and I/O buffers. A process guard
is still required; no capacity-size measurement of this composition has occurred.
The logical checkpoint allowance reserves32*n*m+512+3*65,536bytes for four NPY
headers and three manifests:128,197,120bytes at2000-square. Actual extents, disk
allocation and peak residency still require measurement. No old bound is reused.

The readonly ranking checkpoint is loaded first, followed by the original
annealing loader; matrix identity is then independently rehashed and matched.
Any post-rank failure or interruption closes its actual mapping while preserving
the original error. Explicit close(state) invalidates the composite, closes rank
mapping and drops dense-state ownership. Exclusive ownership is required; no
external alias may be used afterward. Every restored state in parity tests is
explicitly closed before replacement and on exit. Structural validation is not
an adversarial greedy-prefix replay. Trusted outer hashes/source provenance and
unchanged exclusively owned graphs/states remain necessary.

Score-only finalization constructs just the injective int64 pairs and calls the
accepted sparse scalar objective. It reserves80*min(n,m)+32*min(chunk_edges,Eright)
explicit numeric bytes and propagates that component's conservative arithmetic
domain refusal. It returns MatchScore without dense assignment or soft copies.
The dense result helper remains a small-fixture diagnostic, outside score-only
memory claims. Final scoring and checkpoint publication remain atomic.

Eight focused tests pass in green02.log(1.095s), with the initial missing-module
failure and five-test green01 retained. Coverage includes exact float64 soft
bytes/assignment/score/iteration/convergence parity against scalar reference on
three nonzero-edge/tied/rectangular fixture pairs, restore after every advance,
explicit map closure, pre-allocation total/scratch refusal, corrupted order and
policy refusal, changed restored matrix identity, interrupted ranking/scanning
recovery, post-map loader interruption cleanup, and score-only limits/domain
propagation. No raw graph, price, label or historical profile was read or rerun.

Next: independent review, new bounded capacity-scale checkpoint profile with
actual extents/peak/restore evidence, then explicit backend/cache/source lineage
and production integration under a new reviewed release. Real hub/nonzero-edge
full schedules, complete dictionary/MCM/neural feasibility, GPU precision and
financial/paper-scope results are not established by these synthetic tests.
