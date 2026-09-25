# Static review of full-fold graph memory

September 25, 2026. Source HEAD observed:
`3a92e59c12caa0f4eedc29453270f914273f1496`.

This is independent source inspection during the active raw-backup continuation.
No tests, Torch imports, transaction decoding, array-artifact reads, network calls,
financial experiments or registration changes were performed. The report is the
only file written by this reviewer. Source hashes below bind the inspected bytes;
the active backup's bound source/input files were not edited.

The implementation contains the full trainable motif MCM, MLP, GAT, pooling and
attention-LSTM path. Full-fold resource feasibility is not established. Adding a
GPU alone does not address the current eager host-memory loading. The following
findings are concrete implementation limits, not measured hardware requirements.

## Prioritized findings

### G1 — High: all graph snapshots are resident before representation work

`job_payload.py:112–129` sums file payload sizes, then eagerly calls `load_graph`
for every graph in the representation population and retains the resulting tuple.
`feature_pipeline.py:40–47,93` retains the same graphs through the feature pass.
The aggregate file-byte check expressly excludes Python/temporary overhead; it
does not establish that this allocation fits the registered process cap.

Although `graph_store.py:32` requests memory mapping, this does **not** make the
returned graph an out-of-core snapshot: `contracts.py:27–32` copies every numeric
array and converts it into an immutable bytes-backed array. During construction,
an independent numeric copy and its `tobytes()` payload overlap. Node IDs are
materialized as Python strings at `graph_store.py:33`. Thus every week's arrays
and IDs remain in host memory together. `del graphs` at `job_payload.py:130` only
occurs after preparation succeeds; the exception path does not explicitly release
this local variable before continuing to the next representation.

There are additional large per-graph temporary allocations:

- `contracts.py:91,104` builds Python sets of all node IDs and all edge tuples.
- `neighborhoods.py:10–31` hashes arrays by first-axis row. For a `2 × E` edge
  array, each row becomes an E-element Python list and canonical JSON byte string.
  Node IDs similarly reach `canonical_bytes` as a complete tuple. The identity
  routine avoids a full graph JSON object, but is not uniformly bounded by a
  small chunk size.

**Implementation seam:** admit immutable graph handles containing exact metadata,
array manifests and identities, validate/hash their members with bounded readers,
and materialize one current graph only where necessary. Introduce an explicit
read-only backed-graph type or constructor path; changing `np.load` alone cannot
remove `GraphSnapshot`'s copies. Preserve the current canonical identity bytes,
source clocks, node order, duplicate-edge rejection and source membership. A
streaming validator must reject duplicates exactly, rather than sample them.
Failure cleanup should release process references while retaining disk evidence.

### G2 — High: the training sampler separately scales with every node-week

`neighborhoods.py:96–120` retains the training graph collection and allocates
`weights` over the total number of node positions across all training snapshots.
Each sample additionally allocates `probability = weights / weights.sum()` over
that entire population. The two float64 arrays alone require approximately
`16 × total_training_node_positions` bytes, excluding RNG choice temporaries,
graphs, indexes and retained local samples. Full-fold input streaming therefore
does not by itself solve dictionary sampling memory.

**Implementation seam:** preserve the precise global center order, overlap-weight
update, PCG64 draw schedule and frozen sample manifest while using disk-backed
weights and a bounded exact weighted-selection implementation. A replacement
selection algorithm must first demonstrate the required equivalence; chunked
summation or a different random draw mechanism can change selected centers even
if the abstract probability distribution is equivalent. Any changed numerical
sampling semantics require an explicit implementation deviation and new source
binding before empirical use. The existing sampled dictionary must never be
silently refitted under a different selector.

### G3 — High: fixed MCM tensors and journal replay accumulate across the fold

`feature_pipeline.py:114–124` constructs a full MCM array and copies it into a
Torch tensor, alongside copied edges. `:143–150` retains every required graph's
feature object in one dictionary. `job_payload.py:95–148` retains every prepared
representation until all representation jobs finish and only then starts fitting.
Multiple seed/fold representations can therefore accumulate simultaneously.

Persistence does not currently eliminate this residency. After preparation,
`registered_features.py:84–88` reconstructs the complete numerical journal while
the original `result` remains live. `feature_journal.py:105–116` loads completed
features into retained state; `component_store.py:56–63` makes writable copies
from mapped arrays. The producer therefore temporarily holds an additional full
representation during its integrity reread. Exact reuse follows the same eager
reader at `registered_features.py:119–122`.

The journal's aggregate check is made **after** the next component is loaded
(`feature_journal.py:105–110`). Its per-component allocation bound is not a peak
bound for already retained state plus the incoming payload. The outer guard can
still terminate the job; this is not evidence that the guard is bypassed.

`feature_pipeline.py:120–123` also copies a growing completed MCM prefix during
checkpointing and allocates a full result when resuming a prefix. Immutable prefix
files remain useful recovery evidence, but their peak memory must be included.

**Implementation seam:** let `PreparedFeatures` contain immutable feature handles
and a manifest binding, provide verified bounded access to a batch's unique graph
hashes, and release handles' loaded tensors after the batch. Keep fixed MCM/edge
artifacts reusable by the same identity across cells; process representation
dependencies incrementally rather than accumulating every seed/fold in RAM.
Split journal validation from full numerical reconstruction so integrity rereads
can stream hashes and closure membership without a second full resident copy.
Maintain exact attempted/unavailable cell coverage, immutable checkpoint chains,
and no recomputation of completed numerical work. `evaluate_cell`'s present
all-tensor hash check (`evaluation.py:66–68`) must gain an equally strict handle
verification path; it must not simply be removed.

### G4 — High: one batch retains several full GAT autograd graphs

`model.py:45–57` correctly shares one encoded graph object inside a forward call.
Repeated daily references therefore do not repeat a weekly GAT evaluation within
that call. However, every distinct graph's autograd graph remains live through
the temporal output and `training.py:75–81` backward pass.

`gat.py:35–44` materializes node/head projections, gathered source and target
projections, attention intermediates and an edge/head/width message tensor. With
the frozen first layer's four heads of width 16, that message tensor alone has
`(nonself_edges + valid_nodes) × 64 × 4` float32 bytes. Using the retained first
pilot graph's reported 2,049,095 nodes and 3,182,055 edges only as an illustration,
the upper expression treating every recorded edge as nonself is 1,339,174,400
bytes (about 1.25 GiB). It excludes all other tensors, backward state, other GAT
layers and other unique graphs in a batch. This arithmetic is not an RSS/VRAM
measurement or a minimum-capacity recommendation.

The batch's relevant multiplier is the exact unique graph hashes in its 16
chronological 28-day windows, not 16 × 28 independent GAT evaluations and not
necessarily one graph. It must be calculated from admitted examples. Removing
GAT, averaging fixed MCM into a scalar summary, detaching graph embeddings, or
caching learned embeddings across optimizer updates would change the method or
gradient path and is not a permitted memory fix.

**Implementation seam:** checkpoint each unique graph encoder during a batch so
backward recomputes its activations; retain differentiable shared embeddings
within that optimizer step. Non-reentrant checkpoint behavior must be verified
with fixed MCM inputs that do not require gradients, including gradients to all
MLP/GAT parameters. If one graph still exceeds capacity, implement exact
chunked incoming-neighbor softmax/message accumulation with the original full
neighbor denominator and graph output. Naive edge minibatching changes the
attention denominator. Checkpointing/chunking needs synthetic output, loss,
parameter-gradient, optimizer-step and checkpoint/recovery equivalence evidence
before resource pilots. Floating-point reduction differences must be recorded.

### G5 — Medium: GPU execution is not wired into the admitted fit path

`training.py:57–58` constructs a default CPU model and optimizer;
`evaluation.py:24–35` constructs CPU price, target and feature tensors.
`feature_pipeline.py:124–126` likewise creates CPU graph tensors. No explicit
device transfer appears in the inspected execution path. CUDA availability in
`checkpoints.py:14–17` seeds devices; it does not move the model to a GPU.
Checkpoint loading explicitly maps serialized state to CPU at `:46`, and checks
the saved CUDA RNG device count at `:49`.

**Implementation seam:** add an explicit registered execution-device contract
covering model, active graph tensors, prices/targets and optimizer/checkpoint
state. Preserve deterministic policy and prove the exact admitted topology's
resume behavior. Accelerator availability, compatible deterministic operations,
and CPU/GPU numerical tolerances must be tested on that host. A GPU purchase is
neither required nor justified by this static review alone.

## Meaning of existing estimates and next evidence

The inspected historical pilot's `phase.py:88–100` computes
`E × 4 × 64 × 8 + N × 32 × 4 × 16` and refuses the neural phase if it exceeds a
1 GiB registered intermediate allowance. That phase would use synthetic MCM
and labels and repeat **one** graph across its 16 × 28 positions. The previously
reported 8.779/10.713 GB values therefore describe this preallocation screen,
not an executed forward/backward peak, not full-fold residency and not a tested
GPU requirement. Source inspection confirms the refusal precedes the forward.
The source hash of this historical pilot is retained below; this review did not
re-hash its large raw arrays or re-execute its closed claim.

Before selecting an empirical compute contract, the unresolved measurements are:

1. Exact required graph sizes and batch unique-graph sets for each admitted fold,
   including the largest weeks; static summed payload and temporary-memory bounds
   under the revised loader, sampler, journal reader and feature handles.
2. Full-neighborhood matching feasibility, independently of neural memory. The
   previously reported 10,000-node refusal is not repaired by a GPU or by the
   memory seams above; no truncation is proposed here.
3. A separately registered guarded largest-graph forward/backward/checkpoint pilot
   on the selected implementation/device, followed by a representative complete
   batch with its actual distinct graph count and verified cleanup.
4. Measured host peak, accelerator peak if used, checkpoint/recovery cost, local
   scratch and finite-job runtime. Remote archival capacity is separate from each.

No timing-leakage, accounting/returns, fees/funding, predictive agreement or
economic-performance conclusion follows from this narrow memory review. No new
runtime test or current full-suite claim is made. The raw-to-weekly producer,
durable aggregation scratch and empirical admission integration are reviewed
separately by the parent task.

## Inspected byte identities

Paths below the package prefix are relative to
`tradingagents/research/onchain_replication/`. The final three entries are relative
to `research/onchain-paper-replication-2026-09-24/`.

| File | SHA-256 |
| --- | --- |
| job_payload.py | 14ef759c3da0d4cb807fedf6709b6d24ad7115128e5276a40ba78da4b6c05a84 |
| registered_features.py | 46c4c1326320efc7885a83e8853c071e07a357b277f5fc71a29da416cec28d8f |
| feature_pipeline.py | 8f3b28d35f15c3b67139582d626ffa1d5265d557ba8d1f470a709e46bc1fcf2f |
| graph_store.py | bf10aae3b1532e7b687b5febc5803cbf3e9f695c8b086294bcc92fcd811be379 |
| contracts.py | 7c92029d8eb1bdb50f6eea3d02423dd9265d6ba6606bcb7ea3255e11c9447e0a |
| neighborhoods.py | cffeac41c84f2e94059a3c8a3833dfb96168f6279c88c34c1b0d3d0d96875e70 |
| feature_journal.py | d95ead5e805d6f238d6f8ab44da75c2b5ab66fb465b7273ce4d34566fbc37dfd |
| component_store.py | 33d20291369aca936245062b0771f34ad7e5bde403da9d267e23f91fff2cd99a |
| evaluation.py | 1740222b10d9dc1399daff8255af7b56dcb04f4df47f1a5d5eacf8a0dd7bb3ab |
| run.py | d44fa28991f05bedf228de22975399847dd97404b1f3dba8390be7bd720f73de |
| model.py | 199ce63ee56a76deae60495598a4ca4ac6306d7d7f24cf6483a7d1f89feb4944 |
| gat.py | c2292bb164869bb4202a2af028a453f547d8e2930cd9d58ee4a59ffcb72913d6 |
| training.py | a178c226a4eb05d144798204be60a0a9c3b3640f4702f5c89d24d988a08784af |
| model_registry.py | fb22c17ea6b5780fcc639e2f21372be650f85870f67399f1092c51c0983300e6 |
| checkpoints.py | 74e7bd16d4331cbac45143884e1f35a52687b19280c214457834b0cf19a457bc |
| mcm.py | 3825d424496927dcb9f27935a12e00502f19d04b864017a7419954c2d5b4aeae |
| config/model.json | 20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d |
| config/training.json | d5276b75491e130bd03d43de28120f72dd792e42af4446382a6c127d387b8ec0 |
| pilot_successor_02/phase.py | 0bc95f7e33d97485cd9e2fba6802dde168c26aa162b987ef762f9e28ee3a1522 |
