# Explicit activation-checkpoint execution candidate

Two candidate source bodies add explicit execution-policy activation checkpointing without altering the frozen original scientific model/training JSON or their hashes. No live Main file, empirical policy, ledger, claim or native unit was changed.

The new policy is execution schema2 with exactly `backend`, `block_edges` and `graph_activation_checkpointing` in addition to `schema_version`. It retains the existing `streamed-gat-mulsum-v1` backend and existing positive integer block_edges≤65536 rule. Its checkpoint flag must be boolean true. It adds no new numerical backend. None/eager and the exact existing schema1 streamed policy remain supported with their original defaults. Existing scientific-config checkpoint behavior outside this selected route is preserved; schema2 refuses a simultaneously enabled config flag so two authorities cannot silently conflict. The selected route requires the original zero GAT dropout.

`ReplicationModel` derives its runtime checkpoint flag from the execution policy after retaining the original config unchanged. The graph encoder receives the same immutable execution metadata. The one-update helper independently validates the selected policy, both model/graph execution objects, and the actual runtime checkpoint flag. A factory cannot implicitly enable checkpointing while the helper is selected as None. Policy metadata continues into the actual saved checkpoint and completion record through the existing fields. The helper's original config pins, exact16 consecutive rows, seven complete graphs, MCM32 width/full edges, original optimizer/clip, all-parameter joint gradients, finite checkpoint/readback and resource-only qualifications remain unchanged.

## Tensors and recomputation

The existing nonreentrant `torch.utils.checkpoint` call is reused byte-for-byte with `preserve_rng_state=True`. It wraps the complete graph encoder: MLP, all original GAT layers and pooling. The encoder's internal intermediate activations needed by backward are recomputed, subject to PyTorch nonreentrant early-stop behavior. No graph nodes, edges, motifs, heads, layers or temporal steps are removed.

This does not free the seven original graph/MCM input objects or edge arrays. Tensor arguments and parameters remain available for backward. The model's identity cache still retains one pooled graph vector per distinct graph and reuses those vectors across the448 batch/lookback references. The temporal embeddings, prices, attention-LSTM activations, parameter gradients, optimizer state, original dictionary, retained MCM outputs and other caller-owned data remain. The checkpointed execution's peak and elapsed cost on real graphs are unknown; no memory saving or whole-pilot capacity is asserted.

## Fresh bounded verification

Four focused synthetic engineering methods passed in2.576 seconds, actual session85366/final tool37131d exit0. Historical numerical identities and the previously reported3823-check comparison were not rerun or modified.

One fresh paired CPU-float32 update used the unchanged original model/training configs, seed11, batch16/lookback28, seven synthetic complete3-node/3-edge MCM32 graph objects and the same existing streamed backend/block size4. Schema1 streamed execution was compared to schema2 checkpointed streamed execution. Actual logits, loss, all20 parameter-gradient tensors, updated model state, Adam state and RNG state were bitwise equal in this case. Both actual checkpoint files were read back and preserved. All GAT, LSTM and attention parameter groups had non-null finite nonzero gradients. Graph encoder entry counts7 versus14 demonstrate backward recomputation while the original448-reference object reuse remains.

Other checks cover both exact source inverses, unchanged GraphEncoder and model methods except construction, policy/config conflict and dropout refusals, preserved None/schema1 validation, and implicit factory checkpoint refusal before optimizer/checkpoint creation. The failed synthetic namespace is retained with its actual failure record. These are offline algorithm checks with synthetic prices/labels/graphs, no ResearchRun/Binding/Owner, no paper data and no financial-fit credit. Regression-task equivalence, nonzero dropout, GPU devices, real graph sizes, peak-memory savings and full-size timing were not tested.

## Integration boundary

The two source patches are candidate-only. Root must separately review, integrate and bind the exact complete source/runtime closure, then prospectively select an execution policy in the registered pilot plan if appropriate. The policy is a computational implementation assumption that must be declared before the pilot; this candidate does not adopt it. Existing full-size resource-policy, population subset/full-fold distinction, original32/512 import authority, finite storage/transport, genuine Run/Owner and native-entry requirements remain in force.
