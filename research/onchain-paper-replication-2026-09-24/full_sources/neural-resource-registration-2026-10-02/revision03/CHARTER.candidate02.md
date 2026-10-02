# Neural-only capacity measurement — candidate charter

This draft is nonexecutable. It proposes one new retained-data resource claim
under the reviewed cumulative 62-slot allocation proposal. The original family,
17 prior claims, 16 replication claims and their complete/failed dispositions
remain unchanged. The designated first adopter is eth-paper-neural-resource-20261002-01. Its
identity is specified in reviewed budget metadata; no namespace or launch is reserved.

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
owned observer attempts to reconcile uncatchable worker death while the original
live authority remains available. Loss of that authority prevents disk-only
recovery mutations; durable failed/remaining-cell publication may be unavailable.
Raw claim, partial outputs and guard evidence remain retained, and any recovery
authority requires separate review. Terminal/denominator publication is therefore
best-effort, never unconditional. Fatal errors retain their original
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


## Explicit physical route and remaining release conditions

This candidate selects the proposed version1 physical policy:8MiB per regular
file,256KiB per encoded JSON object,160MiB allocated and128MiB logical across the
exact three owned roots,128 entries and32MiB reserved for failure/terminal tail.
The active logical allowance is96MiB. The existing4MiB checkpoint and64MiB
producer/output limits remain additional limits. These are finite refusal
ceilings, not measured successful peaks or a kernel aggregate filesystem quota.
Independent source/limit review and measured synthetic control overhead remain
required before these proposed values can be admitted.

The selected route must bind the original live authority through the supervisor,
guard, worker and final observer. Root/claim births are established by that
authority, with bounded local messages and no mutable-disk recovery baseline.
If original authority is lost, mutations are refused and the attempt remains
spent; no automatic relaunch or namespace recreation is permitted. Missing or
ambiguous terminal closure requires independent reconciliation, never presumed
successful coverage. Library temporary/cache paths must be explicitly bound to
accounted control subdirectories before imports, with worker readback. This is
configured scratch containment, not a sandbox for arbitrary hostile file writes.
All three canonical parent scaffolds must already exist. Guard and observer final
writes, including failure records, are part of the reserved physical denominator.

The10GiB free-space floor follows the user's separately authorized instruction;
old20GiB profiles and all historical attempts remain unchanged. No input or old
output deletion is authorized. The reviewed cumulative extension preserves33
spent claims and allocates12 body,15 financial,1 neural resource and1 remaining
resource claim. This job uses only the neural resource slot. The unchanged1,420
financial fits receive no credit here. Category allocations require explicit
review even though the budget parser primarily enforces the cumulative ceiling.

The runtime/environment/workspace and immutable original parent bindings are
prepared. Final exact committed source/runtime closure, accepted corrected
physical code, kernel/file-limit smoke evidence, whole-job storage accounting,
independent final gate review, fresh unchanged-input checks and startup RAM/guard
readback remain release conditions. This candidate invokes none of them and is
not executable while source/runtime fields are null.
