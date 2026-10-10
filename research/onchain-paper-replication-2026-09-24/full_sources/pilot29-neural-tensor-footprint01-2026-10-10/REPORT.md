# Pilot29 neural tensor footprint: bounded source and metadata evidence

The selected CPU float32 path is `streamed-gat-mulsum-v1`, not PyG. No proven mandatory allocation or conservative simultaneous storage bound derived here exceeds native 6 GiB (6,442,450,944 bytes) or nominal physical 16 GB (16,000,000,000 bytes). This does not establish that the neural stage fits either limit. No neural execution or peak-memory measurement was performed.

## Authentication and availability

The actual29 gate04 pins the source/config bytes recorded in INPUTS01.json; every listed source and input hash matched. Root supplied frozen commit 21f6ca992f98d817f3eddcc3c3867674d0b3c942; Git and live Main were not changed or independently reopened. Actual resource-population metadata selects seven unique graphs in 448 references (16 rows × 28 lookback steps). Each selected graph manifest hash agrees with the population and binding metadata. The population binding authenticates canonical sorted compact JSON without a newline, not raw file bytes (real_pilot_population.py:106). Both hashes are retained. A preliminary raw-file-versus-canonical assertion was corrected to that source-defined join; no population content was changed.

GRAPH_HEADERS01.json records capture time, exact bounded NPY header bytes/hex/hash, fstat signatures and registered body hashes for four numeric members of each exact selected graph. No node-ID or numeric payload bytes were read; header schema/size arithmetic passed. Registered full-body hashes are not newly verified here. Ordinary header reads do not establish payload integrity, currentness or exclusion of writers. Metadata and source timestamps are evidence-capture times, not claims of market availability.

## Selected model and execution

Original model20f451 / trainingd527: MCM32 → MLP64/ReLU → MLP32/ReLU → GAT with four heads of width16 (concatenated64, ELU) → GAT with one head of width32 (head mean32, identity) → mean graph pool32. GAT dropout0 and negative slope0.2. Graph32 plus price1 gives LSTM input33, one layer hidden64, additive attention32 and classification logits2 (model.py:35–57,72; temporal.py). All selected model parameters and graph inputs are CPU float32 except int64 edges; fixed MCM and edges require no gradients (real_pilot_training.py:141–176). Raw graph numeric arrays are separately float64/int64.

Execution schema2 specifies 65,536-edge blocks and graph activation checkpointing. Training checkpoints the whole graph encoder non-reentrantly, preserving RNG state (model.py:80–85). Exact backward recomputation/early-stop lifetimes are not established by this source inspection. The actual helper performs one Adam joint update, seed11, lr0.001, betas0.9/0.999, epsilon1e-8, weight decay0, clip norm1; nominal training configuration epochs100 does not turn this resource update into a financial fit (real_pilot_training.py:179–210).

The 16×28 batch repeatedly references seven graph dict objects. Model.forward caches seven graph vectors by object identity within that forward only; it does not replicate graph features448 times or retain embeddings across updates (model.py:88–105; real_pilot_training.py:166–174). real_pilot_import_caller.py:473–481 loads all seven graphs with resident=True and retains graphs; :569–577 builds a plain features dict from original graph edges and completed MCM maps. The selected route therefore has no FixedFeatureMap cold eviction. torch.from_numpy shares existing ndarray backing (installed torch/_torch_docs.py:4361–4382); it does not allocate a second MCM/edge body. compact_mcm_batched.py:474–479 maps complete float32 MCM files read-only. Mapped logical bytes are not equivalent to simultaneously resident physical pages.

Checkpoint save/readback is capped at4,194,304 file bytes, restores the same model/optimizer/RNG after CPU weights-only load, and does not create a second model (real_pilot_training.py:205–225). Loaded checkpoint storage may coexist with original state. The file cap is not a RAM cap.

## Exact graph arithmetic

| Week | Nodes N | Stored edges E | MCM N×32×4 bytes | Original edges 2×E×8 bytes | First projection N×4×16×4 bytes |
|---|---:|---:|---:|---:|---:|
| 2022-05-02 | 1,878,300 | 2,779,164 | 240,422,400 | 44,466,624 | 480,844,800 |
| 2022-05-09 | 2,265,481 | 3,149,567 | 289,981,568 | 50,393,072 | 579,963,136 |
| 2022-05-16 | 2,048,710 | 2,812,471 | 262,234,880 | 44,999,536 | 524,469,760 |
| 2022-05-23 | 1,875,043 | 2,642,414 | 240,005,504 | 42,278,624 | 480,011,008 |
| 2022-05-30 | 1,581,441 | 2,426,106 | 202,424,448 | 38,817,696 | 404,848,896 |
| 2022-06-06 | 1,581,761 | 2,355,230 | 202,465,408 | 37,683,680 | 404,930,816 |
| 2022-06-13 | 1,768,268 | 2,518,332 | 226,338,304 | 40,293,312 | 452,676,608 |

Totals: N=12,999,004; E=18,683,284; MCM logical mapped payload1,663,872,512 bytes; original edge backing298,932,544 bytes. The four retained raw numeric arrays require32N+48E=1,312,765,760 bytes in aggregate, including original edge backing. Node-ID Python strings/tuples and graph containers are additional and unmeasured; the original Unicode file extent must not be counted as retained array storage after conversion to a tuple (graph_store.py:71–84).

GAT removes original self loops and adds exactly one loop per node (streamed_gat.py:124–130). If S is the uninspected original self-loop count, effective U=E−S+N. For graphs passing the duplicate-free contract, 0≤S≤N, hence E≤U≤E+N for these seven graphs. U is not known exactly. No original geometry or loop counts were inferred from headers.

For each layer with heads H and width D, source requires h[N,H,D] and aggregate out[N,H,D], each4NHD bytes; source_score, target_score, maximum and denom[N,H], each4NH; and e, numer and attention[U,H], each4UH (streamed_gat.py:131–142). These scalar edge tensors span the whole graph despite blockwise messages. Each int64 source/target vector costs8U after loop normalization. Original endpoint rows are initially views; normalized vectors are new allocations. Expanded target index[U,H] is a view, not another8UH backing. First concat reshape may alias or copy depending strides; second head mean allocates[N,32]. The report does not assume every named shape exists simultaneously or sum them into a peak.

Within weighted aggregation, h, zeros_like(h) output and one materialized messages[B,H,D] are source-proven distinct live tensors at line43 (streamed_gat.py:33–45). B≤65,536; all graphs reach a full block. First-layer full block=16,777,216 bytes; second=8,388,608 bytes. Largest first-layer h is579,963,136 bytes (2022-05-09). Consequently that local proven coexistence requires1,176,703,488 bytes. Adding retained numeric raw graph backing gives a conservative simultaneous storage lower bound2,489,469,248 bytes. This is conditional on reaching the selected neural stage and excludes MCM physical-page residency; it is not a measured cgroup/RSS lower bound or estimated peak.

Backward needs grad_h and grad_attention when their inputs require gradients, with incoming/gather/message block temporaries (streamed_gat.py:49–67). Checkpoint saves/recomputations, unique/stack preprocessing and sort workspace, einsum layout/copies, activation/MLP gradients, finite-validation masks and hashing, temporal autograd/LSTM workspace, Adam state, checkpoint loading, Python node IDs, allocator retention and other live native buffers are not bounded as a complete peak here. Individual mandatory shapes are detailed in ARITHMETIC01.json; their sum would overstate some aliases and miss other temporary storage. No full-capacity, memory-saving, GPU speed, whole-MCM completion or scientific authority conclusion follows.

## Checks and remaining measurement

estimate.py is a finite stdlib-only metadata estimator. Its executed checks verify seven graph rows, exact header dtypes/shapes, positive N/E, totals and dimension arithmetic; output is ARITHMETIC01.json. No empirical strategy, native tensor or neural test ran. A future authorized actual neural phase must measure forward/backward/checkpoint memory and confirm effective edge counts and runtime lifetimes. The current pilot and original evidence were left unchanged.
