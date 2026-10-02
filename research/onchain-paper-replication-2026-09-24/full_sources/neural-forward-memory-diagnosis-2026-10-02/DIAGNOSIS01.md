# Neural03 forward-memory diagnosis

The unchanged-model neural03 probe failed under its3.75GiB kernel memory ceiling after entering forward. The retained phase journal establishes that graph validation, graph load, model construction and tensor adapter returned successfully. Its ninth/final event is `forward_before`; there is no `forward_after`, loss, backward, optimizer or checkpoint marker. The specific operator and GAT layer at death remain unknown. The evidence does not prove that temporal processing began or that a particular allocation was attempted.

Closed identity: `eth-paper-neural-resource-20261002-03`, source8a295e2391d371193085d00c342f84e06c06fa94. The guard records270.830520813 seconds, Result=oom-kill, memory.max/high=4,026,531,840, swap.max=0, max2058/oom2/oom_kill3/oom_group_kill1/high0, sampled peak4,026,396,672 bytes and verified cgroup cleanup. The postmortem retains all nine cells unavailable. Three kernel oom_kill events are not three model attempts. This is a kernel-cap failure, distinct from neural02's ancestor-pressure termination. Probe03 is permanently closed;35 attempts are spent under adopted63 and this follow-up allocation is consumed. No financial fit was run. Any new empirical probe requires prospective cumulative64 review, a new identity and explicit resource/implementation variant.

## Observed memory boundary

| Returned marker | Elapsed seconds | Cgroup current bytes | Anonymous bytes | File bytes |
|---|---:|---:|---:|---:|
| graph_validation_after |63.414|934,809,600|364,986,368|566,579,200|
| graph_load_after |110.137|1,349,783,552|779,411,456|566,579,200|
| model_after |112.786|1,391,931,392|821,121,024|566,583,296|
| tensor_adapter_after |113.007|1,705,848,832|1,134,456,832|566,587,392|
| forward_before |113.031|1,705,840,640|1,134,456,832|566,587,392|

These are unit-wide instantaneous observations, not per-operator allocations or process peaks. They include process/runtime overhead and potentially file cache charged during earlier validation. File cache is reclaimable in principle; neither its full retention nor complete reclamation can be assumed at each forward allocation. The final sample after termination is not a pre-kill heap measurement. No pressure-control change or additional RAM advice follows from these observations alone.

The graph loader maps files, then converts node IDs into Python strings and constructs GraphSnapshot, whose numeric fields are copied into immutable byte-backed arrays. The full GraphSnapshot remains referenced by the caller throughout run_cell. Its features/aggregates are not inputs to this synthetic-MCM encoder, but remain resident. The tensor adapter allocates float32 synthetic MCM and an int64 edge tensor via graph.edge_index.copy then torch.tensor. The temporary NumPy edge copy has returned by tensor_adapter_after, although allocator retention can remain. This background footprint is relevant, but reducing it alone does not bound GAT activation work.

## Tensor extent and lifetime accounting

First cell has N=2,049,095 and E=3,182,055. GAT removes original self edges then appends exactly one self edge per valid node. With all nodes valid, E'=E−L+N, where original self-loop count L is uninspected and0<=L<=min(E,N). Thus3,182,055<=E'<=5,231,150. No array body was scanned to infer L. The complete nine-cell extent ledger is in evidence01.json.

| Float32/int64 object | First-cell logical bytes |
|---|---:|
| synthetic MCM[N,32], float32 |262,284,160|
| input edges[2,E], int64 |50,912,880|
| first MLP activation[N,64] |524,568,320|
| second MLP activation[N,32] |262,284,160|
| first GAT projection h[N,4,16] |524,568,320|
| one first-GAT gather/message[E',4,16] |814,606,080–1,339,174,400|
| one first-GAT edge scalar[E',4] |50,912,880–83,698,400|
| one first-GAT node scalar[N,4] |32,785,520|
| second GAT projection[N,1,32] |262,284,160|
| one second-GAT gather/message[E',1,32] |407,303,040–669,587,200|

These are tensor extents, not an additive measured peak. Views/expanded indices may share storage; allocator workspaces, alignment, framework metadata, gradients and temporary masks/sort storage add costs. Lifetime conclusions below derive from the eager source; the exact installed-autograd saved-tensor set has not been measured here.

MLP32→64→32 retains activations for joint backward. ReLU/linear backward typically needs the earlier activation and input; ephemeral preactivations and allocator reuse can raise transient memory. First GAT additionally creates cleaned node features, projected h, masks, filtered endpoints, duplicate-edge validation storage and appended-self endpoints. `torch.unique(torch.stack([source,target]),dim=1)` has additional unmeasured sorting/storage cost and currently repeats per layer; it cannot be silently removed.

The attention expression `(h[source]*a_source).sum(-1) + (h[target]*a_target).sum(-1)` gathers full edge×head×width tensors before reducing to scalar logits. Multiplication creates further full-size temporaries. Learned attention-vector gradients require operands, so a graph-valued source/target gather may remain saved for backward. Later `messages=h[source]*attention[:,:,None]` introduces another edge-wide gather and product. `zeros_like(h).index_add` also creates an output tensor; ELU and downstream layers retain further autograd state. It is unsafe to count a Python temporary as freed numerical storage when autograd needs it.

For illustration only, two first-GAT gather-sized extents occupy1,629,212,160–2,678,348,800 bytes, before projection, MLP saved states, graph/MCM/runtime background, softmax arrays or output. Their exact co-lifetime and the point reached by the killed process are not observed. Nonetheless, these source-level extents identify a material, architecture-preserving memory target; increasing only scheduling headroom does not change them.

ReplicationModel already caches each graph object once within a forward invocation. The16×28 resource input reuses one object, so one graph encoding supplies448 temporal positions and receives their combined gradient. There is no448-copy graph-encoder fix to make. The temporal input[16,28,33] and hidden states[16,28,64] are small compared with graph-wide tensors, but their exact backend workspaces remain unmeasured. Graph embeddings must never be reused across optimizer updates.

## Concrete next implementation route

Prepare a separately selected **streamed GAT execution variant** that preserves32→64→32 MLP, two GAT layers with heads4/1 and widths16/32, concatenation/mean policy, incoming-neighbor+self semantics, ELU/identity, arithmetic mean pooling, attention LSTM, seed11, float32 model arithmetic, every node/edge and gradient path. No sampling, truncation, dtype reduction, detached embeddings or different architecture is proposed.

1. Compute node attention scores before edge gathers: `s=(h*a_source).sum(-1)` and `t=(h*a_target).sum(-1)`, followed by `leaky_relu(s[source]+t[target])`. This removes two edge×head×width attention gathers in favor of node×head×width work and edge×head scalars. The algebra is unchanged, but backward accumulation order may differ; neither bitwise nor tolerance agreement is assumed before a numerical oracle.
2. Implement a narrow custom-autograd weighted message aggregation over fixed, declared contiguous edge blocks. Forward creates a private node output and adds each block in the original edge order. Save h, attention and endpoint identities once, not every gathered block. Backward recomputes bounded gathers: d_h accumulates attention×d_out[target] at source; d_attention is the feature dot product of d_out[target] and h[source]. Gradient contributions from the attention-score branch still flow through the ordinary autograd graph. This is explicit recomputation, not graph or edge sampling. Preserve repeated targets and self-edge order. A plain chunked Python loop without a saved-tensor audit can retain all chunks for backward and is not an adequate proof of lower memory.
3. Start the prospective synthetic prototype with a fixed block ceiling65,536 edges. A first-layer block tensor[65536,4,16] is16,777,216 bytes; this bounds that single tensor, not whole-process memory. Full h, scalar attention, projection/MLP states, outputs, gradients and indices remain. This number is a proposed engineering parameter requiring review, not an admitted empirical limit or predicted peak.
4. Evaluate the existing non-reentrant whole-graph checkpoint option as an explicitly separate checkpoint=true variant only if the streamed implementation's measured saved tensors still require it. Neural03 ran checkpoint=false. Checkpointing can reduce retained activations but does not eliminate a forward local gather/product peak. Recomputed backward can hit a different peak or exceed time limits. Do not silently enable it, infer3.75GiB capacity, or cycle identities with successively changed caps.

This route targets the dominant known allocations without requiring new hardware. Capacity at3.75GiB is unproved. If the remaining node-wide/softmax saved states still exceed the cap, the next source design must explicitly propose more bounded recomputation or source-preserving lifetime management and measure it under a reviewed synthetic profile; it cannot claim that initial block streaming was sufficient.

A secondary, separately reviewed optimization could release irrelevant validated GraphSnapshot fields before neural forward while retaining required input hashes and provenance, or introduce an immutable verified edge/count adapter. That would alter the loader/ownership boundary and needs exact validation and lifetime proof. It should not be bundled invisibly with the first GAT variant. Eliminating one transient edge copy is lower priority and cannot address the edge-wide GAT tensor extents by itself.

## Required oracle before any successor registration

Use tiny original-versus-variant synthetic directed graphs with identical parameter state, model construction/RNG order and input tensors. Check outputs, loss, gradients for all GAT projection/source/target parameters, MLP, recurrent, attention and output parameters, input MCM gradients, one Adam update and optimizer states, checkpoint/reload and RNG state. Include block boundaries, repeated targets, existing self loops, isolated nodes, zero-edge graphs, masks, multiple distinct graphs and the repeated-object16×28 route. Duplicate edges must still reject. Check float32 against the unchanged model with preregistered engineering tolerances and float64 derivative/finite-difference checks for the custom aggregation. Do not tune tolerances using empirical outcomes. Bitwise identity is desirable to measure where order is unchanged; explicitly retain any nonzero numerical difference where accumulation order changes.

Audit saved tensors by distinct storage identity as well as reference count, and instrument block maxima plus bounded process/cgroup memory on an admitted synthetic fixture. A lower sum of saved-tensor references is not a kernel-peak guarantee. Existing activation-checkpointing test source provides joint-gradient/RNG/replay examples but was only read, not executed, and does not prove this new streamed variant. Any derivative/custom-autograd limitations (for example higher-order gradients) must be declared even if the current first-order Adam route does not need them.

Only after the source/gradient/resource oracle and independent review should a new budget64 proposal select the variant, source closure, stage receipts, block limit, checkpoint policy, exact same nine-cell denominator and unchanged science. Probe03 remains closed. No code implementation, numerical import/test, empirical claim or new probe was performed for this diagnosis.
