# Neural-only resource admission readiness — October 2, 2026

**Read-only; no execution admitted.** The nine pending neural resource cells are
independent of numerical MCM completion. A maintained finite runner could measure
that exact synthetic population separately, but no such execution-job route is
currently admitted. The existing unadopted cumulative61proposal contains only one
resource claim; a neural-only claim and a later separate MCM resource claim cannot
both be charged to that single slot without prospective reconciliation.

## Exact population and preserved history

Use the nine saved ETH graph weeks2022-01-03,2022-06-13,2022-07-25,2022-11-07,
2023-06-05,2024-01-01,2024-03-11,2024-08-05,2024-12-23. Their exact original
`neural_checkpoint-<week>` records/reasons, graph manifest hashes, graph identities
and declared counts are retained in observations.json. The first two historical
neural cells failed the conservative capacity precheck; the later cells retain
the workload-termination/unavailable reasons. None is rewritten by this review.

Each original check seeds11, creates random float32MCM with shape(N,32), repeats
the **same graph item object** over16batches×28positions, uses synthetic linspace
prices and alternating class labels, runs one classification cross-entropy/
backward/Adam(lr0.001)step and saves actual model/optimizer/RNG checkpoint state.
This is one-graph repeated-input capacity/checkpoint stress. It is not chronological
multiweek training, actual-MCM inference, a financial fit or validation of an
empirical predictive edge. Retained real graph arrays still make its execution a
registered retained-data resource run, not a synthetic-only engineering test.

All32pending requirements remain pending, coverage77/109unchanged. A future fully
verified exact nine-cell success could support only those nine requirements,
subject to independent qualification; it would leave23other resource requirements
and all1,420financial fits pending. No credit is granted here.

## Historical heuristic versus current path

Historical pilot_successor_02/phase.py:89–100 computes

`H = directed_edges * 4 * 64 * 8 + nodes * 32 * 4 * 16`.

It explicitly refuses H greater than1,073,741,824bytes from its pinned
resource-contract-v4.json under a3GiB whole-process cap and2GiB graph/model/runtime
allowance. H is10,713,395,200bytes for2022-01-03and8,778,956,800for2022-06-13,
matching the preserved unavailable records. This was an **enforced conservative
heuristic in that historical frozen phase**. That phase must not be rerun or
edited to manufacture a pass.

No neural_intermediate_allowance_bytes or this H formula exists in the maintained
model.py/gat.py/job.py path inspected here. Removing or bypassing the historical
check is not proposed. A fresh maintained runner would need a separately frozen
resource/preflight policy and explicit comparability qualification, while the
original capacity outcomes remain valid for their actual historical contract.

Current config/model.json has GAT heads[4,1], per-head widths[16,32] and float32
inputs/parameters. It does not enable graph_activation_checkpointing; the default
is false. The historical expression hardcodes64with4heads and8bytes and a16×node
term. It is not an allocation trace of current4×16float32first-layer intermediates.
Do not divide H by a convenient factor and infer that the current job fits.

Current ReplicationModel.forward caches the learned graph encoding by object id
within one forward call. Repeating the same item448times therefore encodes it
once in forward while accumulating all temporal-use gradients. The cache is
fresh for each forward, so it does not detach or reuse embeddings across updates.
Optional graph_activation_checkpointing uses non-reentrant whole-encoder
checkpointing with RNG preservation. It reduces saved activations but recomputes
the same full encoder in backward; it does not chunk the largest single graph.
Enabling it would need an explicit model/resource policy hash and prospective
parity/replay qualification, not an inferred default or altered historical cell.

GAT.forward still builds full filtered-edge/source/target tensors, deduplicates
with torch.unique, constructs h[source]/h[target], full attention arrays and full
edge-head messages. There is no edge chunking. With valid nodes, let L be the
unread existing self-edge count and T=E−L+N be effective edges after self loops.
A single first-layer float32gather/message hasT×4×16×4bytes; projected nodes have
N×4×16×4bytes. These are individual tensor payloads, **not peak bounds**. Multiple
copies, sorting/deduplication, autograd/scatter buffers, gradients, model, Python,
parent graphs and page cache coexist. Checkpointing does not bound that peak.

## Metadata arithmetic only

| Week | Historical H bytes | One first-layer gather/message at T=E+N bytes |
|---|---:|---:|
| 2022-01-03 |10,713,395,200|1,339,174,400|
| 2022-06-13 |8,778,956,800|1,097,369,600|
| 2022-07-25 |12,837,642,240|1,604,705,280|
| 2022-11-07 |7,665,418,240|958,177,280|
| 2023-06-05 |8,901,756,928|1,112,719,616|
| 2024-01-01 |8,993,994,752|1,124,249,344|
| 2024-03-11 |10,847,854,592|1,355,981,824|
| 2024-08-05 |8,029,466,624|1,003,683,328|
| 2024-12-23 |10,125,109,248|1,265,638,656|

The right column uses the effective-edge upper caseE+N for one tensor only;
no array was read to count L. Unique synthetic MCM is128Nbytes; the copied int64
edge index is16Ebytes. Those per-week terms and saved graph file sizes are in
observations.json. They must not be added mechanically and called measured peak
memory. load_graph additionally converts node_ids to a Python tuple via tolist;
memory mapping the other arrays does not make graph admission zero-resident-cost.
Full array hashing/loading/page cache and checkpoint serialization need accounting.

## Guard and physical blockers

The maintained job.resource_policy allows memory_high≤memory_max≤6GiB, requires
at least3GiB additional host reserve and startup_available≥memory_max+reserve,
requires covered disk volumes with floor≥10GiB and wall≤28,800seconds. Worker
resources.assert_guarded_worker independently enforces≤6GiB, live cgroup/readback,
zero swap, CPU-tree/affinity, owner/command/source identity and freshness. The
lower-level generic launcher can express a larger cap, but the maintained worker
cannot accept it; that is not an escape hatch.

At the retained observation, MemAvailable=7,844,708,352bytes (about7.30GiB), below
9,663,676,416bytes required to start a6GiB job with3GiB reserve. Free local disk was
19,753,005,056bytes. These are nonreserved point-in-time observations, not a cgroup
release or durable capacity guarantee. A fresh check is mandatory before any
future job; concurrent current tests/other work cannot be ignored.

Unresolved physical limits include full one-graph forward/backward peak, graph
validation/node-ID residency, temporary edge copies/torch.unique, checkpoint
BytesIO+serialization copies, model/optimizer state, output/partial checkpoint
bytes, guard logs and cleanup. Whole-encoder checkpointing needs measured bounded
synthetic parity and conservative peak accounting; it is not proof of6GiB full-
graph feasibility. No current measured upper bound was found or invented here.
All original graphs and previous results remain; no space is reclaimed by this
proposal. Current neural-only scope does not require archived pair events, score
tails or the proposed matching-restart retention implementation.

## Smallest maintained route proposed, not implemented

Propose a dedicated job kind `neural_resource` with payload exactly
`{"plan_input": "<registered input identity>"}` and one maintained
`neural_resource.py:produce_registered_neural_resource` entry. It must be explicit
in job_schema and worker dispatch; unknown jobs cannot silently fall through to
fit execution. Extend environment admission so this kind uses include_torch=True
and frozen deterministic/thread/device settings. Do not call historical phase.py.

Its plan must pin all nine original requirement IDs, graph manifests/array-member
hashes and saved independent verification evidence, exact model config and
checkpointing choice, synthetic population/seed/prices/labels/optimizer/step,
model/environment/source closure, output schemas, per-cell/whole-job resource
limits, guarded verification/loading route and failure dispositions. Graph files
need fresh unchanged-byte admission under the registered runner; this report's
compact pins do not replace it. No numerical MCM/dictionary output is an input.

Process the frozen nine cells sequentially with one graph/model/optimizer set at
a time; repeat the exact same graph object within each16×28forward. Account
readback/copy/serialization coexistence and ensure prior graph/tensor objects are
released before the next cell. If isolated per-cell subprocesses are needed to
bound allocator retention, the finite one-job supervisor must contain every child
under the same guard, maintain one immutable job claim and complete ledger, and
meter child startup/runtime; subprocesses must not manufacture nine free attempts.
This process-isolation choice remains prospective, not a promised memory bound.

Record source/model/input identity, guard readback, allocator/process/cgroup peak
measurements, elapsed forward/backward/step/checkpoint timings, checkpoint extent/
hash and exact model/optimizer/RNG state. Validate saved-checkpoint load/replay
without adding a second undocumented scientific update. Report successful,
capacity-unavailable, measured-failed and unattempted-dependent cells separately.
On OOM, guard expiry or cleanup uncertainty, stop and mark remaining cells
unavailable with the same failed-claim reason; no automatic retry/resume. Prior
completed results and partial bytes stay immutable. A later separately justified
successor requires fresh budget/identity and does not reclassify historical cells.

Use reviewed lifecycle output names such as cell-ledger.json, resource-summary.json
and artifact-index.json; no financial result or source-ingestion-success label
should be emitted for this distinct kind. Changes to job.py/environment inventory,
new runner and synthetic tests are one future bounded ownership slice; model/GAT
optimizations are a separate proposal, not part of wiring this runner.

## Admission, budget and verification requirements

A fresh committed registration/charter/gate must name this exact nine-cell scope,
original lineage, source/runtime/input hashes, graph union, model/cache/checkpointing
qualifications, failure/partial rules and all resource bounds. Independent review
must assess whether it meets each original neural requirement under a new guard,
without claiming historical3GiB/1GiB-heuristic success. One-graph repeated-input
stress does not establish general chronological multiweek capacity.

The existing draft61ceiling is33spent+12body+15financial+1resource. A neural-only
claim can only use that proposedresource slot if the exact amendment is explicitly
reconciled and adopted before execution. It leaves no additional resource slot for
a later separate MCM job. Alternatives are a single prospectively registered
resource claim containing separately scheduled dependent and independent phases,
or a separately reviewed cumulative amendment/reallocation preserving all counts;
neither is selected or adopted here. No financial-fit allowance is silently spent
on resource work, and no existing terminal identity is relaunched.

Before real retained-graph execution, required synthetic verification includes:
exact9cell plan/ledger coverage, refusal of implicit MCM dependencies or model
shrinking, guarded environment/claim/source pinning, same-object forward-cache
semantics, checkpointing parity/gradients/RNG replay, real checkpoint save/load,
per-cell object cleanup, bounded complete failure ledger, and guard/child crash
preservation. Existing test_activation_checkpointing.py is a relevant retained
engineering test source, not evidence newly run here or a full-size memory proof.
Full neural raw-graph capacity remains unknown until an admitted measurement.

## Check receipt and remaining decisions

`inspect_metadata.py` ran once with the checkout-local locked Python interpreter,
without model imports or array reads. check01.log reports PASS:15source/compact
pins, nine exact original neural records and metadata formula checks; all original
Hvalues exceed the old1GiB allowance. Source snapshots and observations.json retain
exact bytes/identities. No tests or historical entrypoints executed; no failures
occurred. No empirical claim, external transfer, production edit or gate change.

Root decisions: whether to allocate the sole proposed resource claim to neural
only or a unified resource job; checkpointing flag for the fresh route; contained
single-process vs finite-child lifecycle; exact guard/physical bounds and graph
input availability; independent comparability acceptance. These are prospective
admission decisions under existing authority, not new user permission requests.
