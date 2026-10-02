# Neural checkpoint successor investigation

**Conclusion: explicit graph recomputation is a justified next tiny engineering question, but the existing whole-graph checkpoint is not yet a justified same-cap full-size successor.** It can remove retained autograd activations from the first forward pass. It does not bound that pass's simultaneous node-wide tensors, and its backward recomputation can recreate the whole graph encoder's saved activation footprint. The concrete next action is a separately released finite streamed/checkpoint comparison with first-forward and recompute/backward observations, before any additional empirical registration. If that evidence confirms whole-region backward retention remains the limiting mechanism, a separately selected segmented graph-recomputation implementation is the narrower source question; increasing caps or repeating04 is not the default response.

This investigation used source, original metadata and retained test reports only. No numerical import, array read, test, model, job, SSH, empirical claim, registration/ledger edit or production mutation occurred. The existing default and original scientific model file remain unchanged.

## Actual boundary and existing evidence

Closed04, source8631cbcce34cf827f0551dad04f6822ca8e1e1ec, reached the3.75GiB kernel memory.high=max limit with swap0 during its first forward call. The accepted REVIEW_EXECUTION04.md (`943e7fb9cf4aa823002781e1613ccf4bd1c02a98a9ac2717a4e914ddd0713c0b`) verifies the complete failure archive, nine unavailable cells and cleanup. The nine recorded phase markers end at forward_before, after graph validation/load, model construction and tensor adaptation returned. No forward_after, backward, optimizer, checkpoint or reload proof exists. Neither exact layer/operator at death nor sufficient RAM is known.

At forward_before, memory.current=1,704,366,080bytes, anon=1,137,008,640bytes, file=562,827,264bytes. These are instantaneous whole-unit counters, not a fixed process baseline or attributable tensor measurements. Some earlier validation page cache may be reclaimable; assuming either zero or complete reclamation at an allocation is unjustified. The original GraphSnapshot remains referenced throughout run_cell, with validated features, aggregates and Python node identities even though the synthetic encoder uses only counts and edges. Changing that loader/ownership lifetime would be a separate optimization, not an implicit part of checkpoint selection.

The September29 activation-checkpointing RESULT.md and REVIEW_CORRECTIONS.md retain CPU correctness, joint-gradient, optimizer/RNG/replay tests and the corrected positional tensor argument contract. The diagnostic reports1,444,104 saved-tensor-reference bytes without checkpointing versus220,890 with it. That is neither distinct storage nor kernel peak, and it used the earlier eager backend. The old stopped neural01 and CUDA skips remain preserved. The later accepted streamed numerical oracle explicitly fixed checkpoint=false throughout. Neither body proves the new combination streamed=true plus checkpoint=true.

## Why the existing option helps, and where it does not

model.py:70–76 already invokes `checkpoint(self.graph, mcm, edge_index, node_mask, batch, use_reentrant=False, preserve_rng_state=True)` only during training with gradients enabled and an explicit strict boolean option. Passing tensor inputs positionally preserves device/RNG discovery. Non-reentrant mode supports training parameters when fixed MCM inputs do not themselves require gradients. Eval/no_grad uses the ordinary encoder. No architecture change is required to ask this question directly in an isolated constructor fixture.

model.py:81–95 caches the graph embedding by graph-object identity only within one forward. Resource04 repeats one object16×28, so it already executes one graph encoding per forward, not448. Checkpointing recomputes that unique encoder in backward; caching learned embeddings across updates or detaching them would alter training and is not an acceptable substitute.

The installed checkpoint.py:1142–1153 pack hook stores a holder and tensor metadata instead of the original tensor storage during initial forward. Consequently, earlier MLP activations saved only for backward can be released while later graph layers execute. Python references and in-flight operator operands still exist. In particular, streamed_gat.py:132–145 retains cleaned features, projection h, node scores, scalar softmax arrays, endpoints and output in local variables through final activation.

Backward is a separate risk. checkpoint.py:1081–1122 stores recomputed saved tensors in the frame's recovered map;1142–1197 triggers recomputation on first unpack and returns them to subsequent backward consumers. The default early-stop boundary is after required saves have been recreated, not an assurance of one-layer-at-a-time backward. For the single whole GraphEncoder region, earlier-layer saved activations can accumulate while later layers are recomputed, alongside backward inputs and existing model/input storage. The original uncheckpointed forward peak can therefore recur or be exceeded. Existing custom weighted aggregation remains first-order-only; checkpointing does not add higher-order support.

A low outer saved_tensors_hooks count alone can be misleading: the inner checkpoint hooks hide internal saves from outer hooks. The earlier oracle's deliberate retention of storage objects also changes lifetime. A saved-storage diagnostic and an uninstrumented capacity observation must remain separate claims; neither overrides the native guard.

## Source-derived memory arithmetic, not a predicted peak

First graph N=2,049,095, original E=3,182,055. After removing original self edges and appending exactly one self edge per valid node, M=E−L+N, with uninspected0<=L<=N. Therefore3,182,055<=M<=5,231,150. No edge array was scanned to resolve L.

| Object | Logical bytes |
|---|---:|
| float32 MCM[N,32] |262,284,160|
| int64 input edges[2,E] |50,912,880|
| first MLP[N,64] |524,568,320|
| second MLP/first GAT input[N,32] |262,284,160|
| first GAT projection or output[N,4,16] |524,568,320 each|
| first GAT node scalar[N,4] |32,785,520 each|
| first GAT edge scalar[M,4] |50,912,880–83,698,400 each|
| bounded aggregation block[65536,4,16] |16,777,216 each|

A concrete illustrative simultaneous-local calculation is possible at the first GAT's `out=F.elu(out)` call. Count x and clean at128N bytes each; projection h, pre-ELU out and newly allocated ELU result at256N each; source_score, target_score, maximum and denom at16N each; e, numer and attention at16M each; two int64 endpoints at16M; int64 appended-node IDs at8N; valid mask atN and original-edge keep mask atE. This yields **1097N+64M+E=2,454,690,790–2,585,832,870bytes (2.286–2.408GiB)**. It assumes ordinary out-of-place ELU and the inspected local-variable lifetimes, and excludes allocator rounding, sort/projection workspaces, metadata and any additional saved tensors. Expanded index and reshape views are not double-counted as new backing storage. Earlier operator peaks may be larger. This is a source-based logical live-set illustration, not a measured minimum RSS or an upper bound.

Adding the observed1,704,366,080byte pre-forward sample yields3.873–3.996GiB. Subtracting all562,827,264bytes of its charged file cache first yields3.349–3.471GiB. These two scenarios show why3.75GiB is uncertain; they are not confidence bounds. Checkpointing may release earlier retained MLP/GAT state, but cannot promise enough room for current-layer locals or recomputation. A modest cap increase without an observed required peak is not a capacity result.

A potential later source optimization is shortening scalar/local lifetimes or choosing finer checkpoint segments without changing equations. A plain `del` cannot free storage still held by autograd; an in-place operation must not be substituted without alias/gradient proof. Segmenting at MLP/GAT boundaries also retains boundary tensors and input references. Any such candidate needs its own source identity and oracle, rather than being bundled invisibly with the existing whole-graph option.

## Financial batches: actual weekly membership matters

The frozen empirical builder uses weekly graph identities for each of28 daily lookback positions (dataset.py:66–105). One complete28-day lookback normally covers4–5 weekly graphs. Training config fixes batch_size16 and shuffle=false; training.py:52 refuses shuffling and:73 selects contiguous positions in the admitted example list. Prediction:99–105 similarly uses contiguous admitted indices. The label-permutation control permutes labels, not feature order. However, dataset exclusions remove days: contiguous admitted examples need not have consecutive calendar dates.

Only for16 consecutive calendar-day examples does their union span43 days, ordinarily7 weekly graph identities. Neither7 nor28 is the observed batch cardinality. Before financial capacity admission, enumerate every actual train/test batch's union of admitted graph_hashes and join each to exact N/E, dtype, MCM/edge body extent and materialization policy. No training outcome is needed for this metadata census. Gaps can increase membership. No extra batching, shuffling or dropping examples is authorized by this investigation.

FixedFeatureMap.load_batch materializes all requested unique features before returning the batch; evaluation.batch_factory retains selected graph objects through the sequence input, and checkpoint input savers retain references needed for backward. Whole-graph checkpointing does not stream those fixed inputs out of RAM. At first-week size, one graph's float32 MCM plus int64 edges alone is313,197,040bytes. Seven same-sized graphs would be2,192,379,280bytes (2.042GiB);28 would be8,769,517,120bytes (8.167GiB), before runtime, copies or activations. These are conditional same-size stress arithmetic, not observed empirical batch totals. A28-distinct tiny-graph test remains useful coverage, but passing it does not establish28-full-size capacity or the empirical weekly count. If actual admitted batch input storage alone exceeds the budget, a separately verified reload/offload/lifetime adapter or more resources is required; checkpoint flags cannot fix that floor.

## Exact selection and identity seams

Preserve original config/model.json raw SHA `20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d` and all architecture values. Its canonical core SHA is `29af65736dddfbd22b5ce94c6ff3e507041b00dc81dfcc94c6919a615a68dcb7`. Current effective resource config with explicit false hashes to `80c1377afce47e917a518918bf239e63a2f9e86204a00b824b3b7aff76ab8d6f`; deriving explicit true would instead hash to `f2a4c1361e4bc428be7d1bd04db9cb1340d3be61cf61c289bbe6070a6af9fee3`. These are different execution/configuration identities despite unchanged architecture and equations. Do not overwrite the original file or relabel a true run as the false identity.

neural_resource.validate_model:75–82 already authenticates the original core after removing an explicit matching boolean. But `_execution_identity`:92–105 and run_cell:185–197 deliberately refuse streamed checkpoint=true. The schema2 source/test contract freezes that refusal. A new candidate should introduce an explicit prospective plan version/selection for checkpoint=true while retaining schema1/2 semantics and malformed-policy refusal, rather than simply widening the old schema2 behavior. A tiny constructor-only proof does not bypass these production guards.

The streamed backend equations/source may remain exact `e8355dc4…`, with checkpoint=true separately bound by the new plan hash, effective config hash, source closure and execution amendment. Existing phase identity already includes plan/model-config hashes; its current schema2 backend fields need not be silently redefined. If an explicit checkpoint policy field is added to the nested identity, neural_phases._identity and consumers need a new exact version and legacy compatibility checks. Original checkpoint identity/phase/root authority, nine cells, all20markers per successful cell, file/tail limits and failed-cell retention remain required.

Financial candidate02 is unintegrated and expressly rejects checkpoint=true in identity selection/construct/check_model. Its newly accepted model_contract correctly captures checkpoint state, but does not authorize changing it. Later financial support needs a new explicit selection/plan contract, constructor-only pinning of the chosen boolean, persisted effective model contract and strict comparison before weights/optimizer/RNG restoration or replay. Existing candidate02/default eager behavior must remain intact. The current financial config digest includes effective model values: adding true changes that digest; architecture equivalence must be recorded separately rather than claiming the old digest is retained. This financial work need not block a tiny isolated resource-constructor proof.

## Concrete finite next proof and empirical release boundary

Prepare a new dated immutable protocol comparing the exact accepted streamed backend with checkpoint=false against the same backend with explicit whole-graph checkpoint=true. Preserve the prior eager/streamed results and tolerances. Use original architecture, seed11, CPU float32, two tiny graphs in the existing16×28 repeated-object shape plus a separately named28-distinct tiny-graph stress case. Check both fixed MCM inputs with requires_grad=false and input-gradient diagnostics; all named parameter gradients/groups, forward/loss, one Adam update/state, initialization and RNG, inference/no_grad and checkpoint/reload/continuation must agree. Preserve float32 rtol1e-5/atol1e-6 and exact nonfloating/RNG comparisons from the accepted streamed protocol; report bitwise differences without post-outcome tolerance tuning. A separate dropout0.2 case checks RNG recomputation, while the primary frozen architecture remains dropout0.

Observe initial forward, loss/backward recomputation, optimizer and durable save/reload as separate finite phases. Demonstrate checkpoint invocation and recomputation rather than relying on a flag. Keep diagnostic records bounded to scalar counts/extents, not retained graph arrays. Retain reference versus distinct-storage counts with explicit measurement-lifetime qualification. The genuine workload without storage-retaining observers must also run under its fixed native envelope; comparative phase peaks require a reviewed observation arrangement, not subtraction of two cumulative high-water counters or assuming an outer hook sees checkpoint internals. Early-stop recomputation can stop before a graph-forward post-hook; a missing post-hook alone is not a failure or proof of zero work.

A feasible preparation envelope to review is the previously used tiny-oracle controls:1GiB hard memory.high=max, swap0, two inherited CPUs,3GiB host reserve/4GiB startup,120second hard unit limit,4MiB hard per-file/log caps,64MiB sampled owned-storage stop and10GiB disk floor, exact source/runtime mapping, pre-import native readback, one-use namespace and complete descendant cleanup. This is a proposal, not permission to execute; if the exact finite fixture needs different bounds they must be declared before outcomes. Preserve unexpected numerical/resource failures rather than rerunning an identity. No real financial model fit or empirical graph belongs in that tiny proof.

Only after independent source/numerical/closure review should a separate empirical question be registered: same nine original graph cells, original model core, explicit recomputation selection, fixed finite guard and complete failure retention. Reconcile the36 spent attempts/adopted64 ceiling with all existing allocations before proposing any additional attempt; no spare slot is presumed unallocated. Commit and externally verify the exact release, then fresh admission/readiness/no-active-owner checks.04 remains closed forever. Full28-distinct or actual financial-batch capacity remains separate even if the one-graph nine-cell successor passes.

The reported latest host availability (~7.34GiB) does not establish eligibility for arbitrary higher caps. With the fixed3GiB reserve, startup minima are6.75GiB for3.75,7.0 for4.0,7.5 for4.5,8.0 for5.0 and9.0 for6.0GiB worker caps, before any extra reviewed scheduling margin. Fresh sustained eligibility and actual reserve checks remain mandatory; a RAM snapshot and a larger theoretical cap do not answer the model's unknown peak. No cap ladder, GPU purchase, swap change or scope reduction is proposed.

## Source references read

All paths are relative to the active checkout. These hashes identify the inspected source, not executed binaries.

| Path | SHA256 |
|---|---|
| tradingagents/research/onchain_replication/model.py |2f55b04d3a707e212b2a1d9e0fb591eb3ec2b4828614edcc1a5a5d8f313d3b8e|
| tradingagents/research/onchain_replication/streamed_gat.py |e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f|
| tradingagents/research/onchain_replication/neural_resource.py |ae7cd7ff76b0ddfd5e55645ea7a36a56d12089388add620a99fc70b1bc6759b9|
| tradingagents/research/onchain_replication/feature_residency.py |4ea5370958b65edf0d37950f12d358ab562291c786f28a287514c77c3838ddcd|
| tradingagents/research/onchain_replication/evaluation.py |b3af7cf6b71f8adcdd762eb471abb66d8fdd00f20087aeff377447d51a854b29|
| tests/research/onchain_replication/test_activation_checkpointing.py |0976c5dd8a464a766feec27c908886e08254b30a0e3bbd75b59386172222ed60|
| tests/research/onchain_replication/test_streamed_execution_integration.py |dbfa68e9587669e8142ab998eec1cf9fdbd1f94e185ce1a997313f866dc1f832|
| .venv/lib/python3.13/site-packages/torch/utils/checkpoint.py |b6ac0745d58fc891f0f741b433e4fdd59efb1e9fe991c6b3f2b8fc460f7d5d7a|
