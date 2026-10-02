# Neural-only capacity measurement — unadopted charter

This draft is nonexecutable. It proposes one new retained-data resource claim
under the reviewed cumulative 62-slot allocation proposal. The original family,
17 prior claims, 16 replication claims and their complete/failed dispositions
remain unchanged. Neither an experiment identity nor a launch is reserved.

The question is whether each of the nine original retained ETH weekly graphs
can complete the original synthetic neural update and checkpoint roundtrip under
a fresh enforced resource contract. All nine cells and their prior unavailable
reasons remain in scope. No historical job is rerun. This is a new resource
measurement; it does not change financial fit counts, sample exposure or the
interpretation of earlier capacity refusals.

Each cell uses the exact original model configuration, CPU float32, seed11,
synthetic PCG64 MCM(N,32), a single identical graph-item object repeated over
16×28 inputs, original synthetic prices/labels, one cross-entropy backward pass
and Adam(lr0.001) update. Graph activation checkpointing is explicitly false.
The saved model/optimizer/RNG/cursor must roundtrip exactly without another
optimizer update. Actual MCM computation and financial labels are not inputs.
There is no hyperparameter search, outcome-based selection or best-seed choice.

The graph union, exact seven-day windows, original requirement IDs and metadata
hashes are enumerated in plan.draft.json. Input array bodies require fresh
unchanged-byte checks under the final registered source. No graph rebuild,
resampling or silent field substitution is allowed. Existing exposed/spent ETH
history is exploratory development data, never fresh confirmation.

Proposed hard whole-job controls remain memory_max6GiB, memory_high5GiB, zero
worker swap,3GiB host reserve,9GiB startup available RAM,10GiB disk floor and
7200seconds. Two Torch threads and the existing guard's CPU containment apply.
The600second per-cell budget is cooperative; an in-process Torch call is not
promised immediate interruption. Current host memory may fail startup admission;
no automatic cap/reserve relaxation is authorized by this draft.

The1GiB per-graph declared payload ceiling covers the largest721,044,472byte
saved graph in the metadata inventory; it is not a resident-memory bound.
The4MiB checkpoint-file and64MiB retained-output ceilings are proposed refusal
limits. The corrected tiny runner test reports493,424 serialized bytes with the
original unshrunk model and one Adam update; final identity metadata and
filesystem/metadata accounting still need independent review. Nine maximum
checkpoint files reserve36MiB. This size observation does not bound graph memory.
Graph loading, full edge/head tensors, backward state and checkpoint decoding
can exceed the6GiB cap; this is an unknown to measure, not a promised fit.
Whole-encoder checkpointing or model/GAT changes require a separate explicit
prospective configuration; they are absent here.

Cells run sequentially, retaining completed outputs. Any error, OOM, guard
expiry or uncertain cleanup stops later scientific work. Best-effort immutable
cell evidence records the failed cell and all later cells as unavailable; the
owned observer reconciles uncatchable death. Fatal errors retain their original
identity/cause and cannot become an ordinary successful return. No retry,
automatic resume, deletion or refund is permitted. A later successor needs a
new reviewed cumulative reconciliation and fresh identity.

Record the full cell ledger, model/source/graph/runtime/plan identity, enforced
guard readback, process/cgroup peak measures, elapsed phases, checkpoint sizes
and hashes, exact state reload and all failure dispositions. Process-lifetime
RSS is not an isolated per-cell peak; allocator release is not established by
Python garbage collection. Hard guard outcomes and output accounting must be
reviewed independently before assigning any of the nine original requirements
new coverage. A passing cell supports repeated-one-graph capacity only, not
chronological multiweek fitting, prediction accuracy, GPU parity or an economic
edge. There are no PnL, fee/funding or trading results in this measurement.

Before admission: freeze accepted corrected source and runtime closure, final
identity, workspace/environment bindings, exact charter/config/source hashes,
accepted budget extension/review, complete history and graph-preservation joins,
physical limits and fresh host startup checks. The final gate must use the real
lifecycle API and owned supervisor/guard route. No unknown-kind fallthrough,
direct unguarded producer call, historical phase entrypoint or paid resource is
authorized. Current drafts and earlier resource outcomes remain preserved.
