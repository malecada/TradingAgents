# Pilot37 next-update memory: source and metadata investigation

The selected checkpointed streamed GAT still has substantial whole-graph tensor
cost. For the largest of the actual seven declared graphs, one first-layer
projection and one aggregate output each require579,963,136bytes (553.1MiB).
A conservative simultaneous first-layer payload subtotal is2,103,190,208bytes
(1.959GiB), excluding backward and allocator/native workspaces. This is not a
measured peak or an assertion that the six-GiB guard will pass or fail.

Only source and public JSON metadata were read. No arrays, NPY headers, labels,
model/numerical imports, empirical claims or native execution were performed.
All new bodies are in this directory; source freeze998d353 remains unchanged.
`calculate01.py` is a stdlib-only calculator bounded to128MiB address space and
10CPU seconds. Its actual successful output is `SIZES01.json`, including every
metadata hash. It has not authenticated array payloads or a successor admission.

## Exact intended batch and selected implementation

The current37 public draft identifies seven graph hashes,16 examples and28
steps each:448references. This is the next intended pilot batch, conditional on
normal population admission, all seven complete MCMs and actual factory checks.
The public `indices` field is null because the resource-subset constructor
resolves the16rows; this investigation neither derives nor inspects labels.
The fixed model file is20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d;
training isd5276b75491e130bd03d43de28120f72dd792e42af4446382a6c127d387b8ec0.

| Graph week | Intended nodes | Edge-count interval from manifest extent | References |
|---|---:|---:|---:|
|2022-05-02|1,878,300|2,778,547–2,779,171|21|
|2022-05-09|2,265,481|3,148,950–3,149,574|70|
|2022-05-16|2,048,710|2,811,854–2,812,478|109|
|2022-05-23|1,875,043|2,641,797–2,642,421|112|
|2022-05-30|1,581,441|2,425,489–2,426,113|91|
|2022-06-06|1,581,761|2,354,613–2,355,237|42|
|2022-06-13|1,768,268|2,517,715–2,518,339|3|

N is the unchanged declared MCM32 denominator (`mcm-output-f32` exact intended
extent/128). This totals12,999,004nodes and415,968,128MCM cells. Manifest numeric
sizes are compatible with the declared four-float64 node rows, but no payload
was opened. E is deliberately an interval: the selected training contract is
int64[2,E], and the existing resident loader allows NPY headers of at most10,012
bytes including magic/length. Subtracting that maximum yields the conservative
lower endpoint. Recorded file lengths alone do not establish the exact header,
edge count, self-loop count, values or successful current graph admission.
The GAT removes existing self-loops and adds one for every node, so
E'=E-L+N and, conditional on the existing no-duplicate contract,
max(E,N)<=E'<=E+N. No old nine-graph or union80 quantity is used.

`pilot.json` explicitly selects schema2 `streamed-gat-mulsum-v1`,
block_edges65536 and graph_activation_checkpointing=true. `model.py:80–85`
uses non-reentrant checkpointing with RNG preservation. `model.py:91–102`
caches each graph's learned vector by object identity inside this single
forward. `real_pilot_training.py:173` requires every repeated hash to reference
its exact shared graph object. Thus seven unique encodings, not448complete GAT
encodings, occur in a forward. Backward recomputes checkpointed graph work;
exact peak and saved-object lifetimes remain unobserved. The cache is local to
forward and cannot preserve detached learned vectors across optimizer updates.

The caller uses `features={}` and ordinary shared tensor dictionaries. No
`compact_cold_handoff_input`, feature-residency selection or cold metadata role
is present. `FixedFeatureMap` and `compact_cold_features.py` exist, but this
caller does not select their transfer/release route. They confer no memory
saving on37. The streamed module's old introductory "not integrated" wording
is superseded for this selected route by the concrete model/caller dispatch;
this investigation does not edit that source text.

## Storage lifetime and lower-bound arithmetic

`real_pilot_import_caller.py:516–527` loads all seven `GraphSnapshot` parents
with resident=True. The `graphs` dictionary stays live through training.
`compact_mcm.Produced:205` retains the same raw graph in `_graph` and
`_graph_authority`; the caller's `targets` list retains all seven Produced
objects. Their references alias the original graphs and must not be charged as
seven further copies. The authority closure iterates and checks those targets.
Consequently a plain `del graphs` would not release the parent arrays and would
not establish a valid cold authority transfer.

`graph_store.py:76–85` loads numeric arrays then constructs Python node-ID
strings/tuples; `GraphSnapshot.__post_init__` copies numeric values into immutable
bytes-backed arrays. Constructor copies can cause earlier transient peaks;
they are not double-counted as permanent training storage. Final raw parent
numeric payload is at least1,312,489,008bytes (1.222GiB), after subtracting the
maximum header from each of28numeric members. Tuple pointer slots add at least
103,992,032bytes (0.097GiB). Actual node-ID strings, object headers and dictionary
structures are omitted, not assumed free.

The seven full MCMs require1,663,872,512logical bytes (1.550GiB).
`compact_mcm_batched.py` maps completed matrix.f32 files read-only;
`real_pilot_import_caller.py:618–620` uses torch.from_numpy for MCM and endpoints.
These are aliases, so their tensor wrappers do not add another complete payload.
Mapped MCM pages are file-backed and reclaimable: their entire logical extent
is **not** a simultaneous anonymous-RSS floor. Re-reading pages can add I/O.
Combined raw-parent payload, pointer slots and MCM logical extent are
3,080,353,552bytes (2.869GiB), before strings/runtime/temporary activations.

For largest graph N=2,265,481 and E'>=3,148,950, float32 tensors have:

| Object | Shape | Payload |
|---|---|---:|
|MCM / first GAT input x / clean copy, each|N×32|289,981,568B|
|MLP first output / GAT1 h / GAT1 aggregate out, each|N×64 or N×4×16|579,963,136B|
|GAT1 source_score or target_score, each|N×4|36,247,696B|
|GAT1 e, numer or attention, each|E'×4|at least50,383,200B|
|GAT1 maximum or denom, each|N×4|36,247,696B|
|GAT2 h or aggregate out, each|N×1×32|289,981,568B|
|GAT2 edge scalar tensor, each|E'×1|at least12,595,800B|
|One GAT1 message block|65,536×4×16|16,777,216B|
|One GAT2 message block|65,536×1×32|8,388,608B|

The first-layer aggregate call keeps Python locals x,clean,h,source_score,
target_score,e,maximum,numer,denom,attention and endpoints alive while
`_WeightedAggregate.forward` allocates out and messages. A deliberately partial
simultaneous payload sum is832N+64E'+16,777,216bytes=1.959GiB.
This excludes valid/keep/nodes masks, indexing temporaries, autograd saved
values, duplicate-edge unique/sort workspace and transient second block copy.
Checkpointing does not make those current-forward operands disappear.
The selected streaming bounds the weighted message block, **not** h/out or
E'×heads attention. The earlier eager all-edge E'×heads×width message tensor is
not selected and must not be used as the actual route's cost.

Adding this subtotal to the logical parent/MCM base yields5,183,543,760bytes
(4.828GiB) of coexisting logical payload for that graph. This is a useful scale
warning, not measured peak and not a hard resident lower bound because mapped
MCM residency is reclaimable. Excluding all mapped MCM pages gives3.278GiB of
this partial payload subtotal. Both omit Python node strings, Torch/runtime,
optimizer, dictionary/Owner objects, monitors, allocation fragmentation,
backward, graph reconstruction and kernel workspaces. Their unmeasured sizes
prevent a safe-capacity conclusion. Peak h/attention are not multiplied by seven
or448, because checkpoint/reuse changes those lifetimes.

The temporal input is only16×28×33float32=59,136bytes; its hidden output
16×28×64=114,688bytes. Those do not explain the graph-scale payload. Model/Adam
parameter sizes are likewise distinct from these millions-of-node tensors;
no actual optimizer or backward allocation was measured here.

## Smallest useful next measurement and optimization

The existing pilot phase receipt already separates graph_validation, batch,
forward, backward, optimizer and checkpoint/readback. Whole37 measurement should
retain those real timestamps and the actual enclosing cgroup memory.current,
memory.peak, memory.stat anon/file and high/max/OOM counters. Timestamp-aligned
observations before/after each unique graph and each GAT layer would distinguish
retained raw parents/file pages from current graph activations; fixed scalar
N/E'/dtype/head/block counts suffice. No tensor values, per-edge traces or broad
new profiler framework are required. Existing coarse monitor samples can miss
short peaks, so a cumulative kernel peak and phase-local samples have distinct
meanings. These instrumentation edits are proposals for a later unfrozen source
bundle, not changes to998d353 or permission to interrupt native36.

If measurement confirms Python-held forward operands dominate, the smallest
source-faithful candidate is explicit lifetime release of clean,source_score,
target_score,e,maximum,numer and denom immediately after attention is formed
and before weighted aggregation. It changes no equation, graph, head, precision
or training schedule. Any autograd-retained buffers may survive those deletes,
especially during checkpoint recomputation, so memory benefit requires direct
measurement plus frozen output/gradient/Adam/RNG/checkpoint parity. The listed
objects alone total192N+32E' (at least535,738,752bytes for the largest graph),
but that is an optimistic release opportunity, **not a promised peak reduction**.

If raw parents dominate instead, genuine post-publication cold handoff is the
relevant later join: it must retire every Produced/Owner/caller alias only after
complete verification, preserve byte/order/data lineage and currentness, then
supply identical fixed MCM/edge objects to the same factory. Simply converting
the features dict to FixedFeatureMap would neither release raw parents nor
shrink this batch's seven-graph union. Existing cold utilities require their
own reviewed interface integration; their presence is not installed behavior.
No cap increase, new allowance, financial fit, data reduction or changed method
follows from this investigation.
