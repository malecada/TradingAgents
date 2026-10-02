# Isolated streamed GAT candidate01 — awaiting bounded GREEN

The actual one-use RED run reached only RESOURCE_EDGE_WIDE_SAVED_TENSORS after all eleven preceding numerical checks. Its launcher terminal is expected_red; the underlying worker/guard has the expected failed exit1 rather than an execution success. Native cleanup was verified. The retained report measured four saved full edge-wide backing allocations of6,750,464 bytes each and29,714,945 total distinct saved-storage bytes for the fixed257-node reference layer. Those figures describe the instrumented tiny oracle, not the empirical graph or uninstrumented process peak.

Candidate01 is a new standalone source file; production and frozen reference/oracle/protocol/launcher files are unchanged. It preserves GraphAttention parameter names, dimensions, initialization calls and their order. A stdlib AST comparison verified exact constructor-body equivalence after removing only the new finite block-policy assignment/argument. No numerical module or candidate was imported by the implementer.

## Implemented numerical boundary

Source/target scalar attention scores use `einsum('nhd,hd->nh',h,a)` before endpoint gathers. This requests a true node dot product, avoiding an explicit node×head×width multiplication followed by sum and the original edge-wide attention-vector products. Backend-internal packing/workspace is not asserted absent. Node scores, softmax, dropout, normalization, activations and the original incoming+self ordering remain on the unchanged autograd path.

`weighted_aggregate` accepts same-device CPU float32/float64 h and scalar attention, contiguous int64 endpoint vectors, and positive integer block_edges<=65,536. It rejects invalid shape, dtype/device, endpoints or block settings before aggregate output allocation. h/attention may be strided; it does not force a complete contiguous copy. An optional fresh empty audit dictionary gets exactly four block counters; ordinary GraphAttention execution does not supply an audit. A reused/malformed audit rejects rather than silently resetting observations.

The custom function saves h, scalar attention, source and target once. Forward iterates original contiguous edge ranges, gathers at most one selected block, multiplies by scalar attention and accumulates into a private node output. No per-block autograd graph is retained. Backward recomputes target-output-gradient and source-node blocks, scatters the weighted output gradient into d_h, and forms each scalar d_attention as a feature dot product. Gradients still join the learned attention-score branch, GAT projection, MLP and temporal path. Every source edge remains represented; no sampling, detachment or dtype reduction occurs.

The first-order-only boundary uses `once_differentiable`; higher-order use is deliberately unsupported and must refuse under the frozen oracle. CPU only is an explicit current candidate limitation; no GPU equivalence or memory claim is made. The constructor remains checkpoint=false under the unchanged test model configuration; no checkpoint implementation or policy was introduced.

Node-dot and blocked scatter/reduction may change floating-point accumulation order relative to eager source. Output, gradient, Adam, RNG, reload and finite-difference agreement are unverified until the frozen GREEN oracle runs. All original frozen numerical tolerances remain unchanged. The max65,536 edge block limits individual block work, not node-wide projections, total autograd state, allocator workspace, file cache or whole-process peak. No assertion is made that this implementation fits the empirical3.75GiB cap.

## Readiness and ownership

Only stdlib AST parsing/comparison and bounded reads of closed RED metadata were executed during implementation. No Torch/NumPy import, numerical GREEN, guard, empirical array load or claim occurred. Source manifest records frozen source bytes and RED evidence references. Root owns the distinct one-use GREEN release object/runtime/source mapping, source checkpoint and actual guarded launch after review. Any failure remains retained; this source must not be silently changed under an active GREEN identity.

Passing GREEN would establish only the declared tiny engineering oracle. Independent code review, a bounded capacity assessment and explicit prospective64 registration with new empirical identity are still required before any full-graph successor.35attempts remain spent under adopted63; closed neural03 is never rerun.
