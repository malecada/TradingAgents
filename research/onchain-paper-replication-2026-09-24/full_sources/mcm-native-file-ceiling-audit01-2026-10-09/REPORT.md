# Actual seven-graph native file ceiling audit

The presumed current FSIZE impossibility is disproven. All seven registered node_features NPY headers were read as bounded metadata (128 bytes each), joined to registered manifest SHA/extents and typed-policy row counts. No feature payloads were read. Largest graph is 2,265,481 nodes: score spool and published matrix each 289,981,568 bytes; origins 652,458,528 bytes. All fit the unchanged 1,073,741,824-byte ceiling. 8,402,640 is pair_policy.limits.max_pair_entries_override, not a graph row count.

| Input | Nodes | Cells | Each score/output bytes | Origins bytes |
|---|---:|---:|---:|---:|
| graph_20220502 | 1878300 | 60105600 | 240422400 | 540950400 |
| graph_20220509 | 2265481 | 72495392 | 289981568 | 652458528 |
| graph_20220516 | 2048710 | 65558720 | 262234880 | 590028480 |
| graph_20220523 | 1875043 | 60001376 | 240005504 | 540012384 |
| graph_20220530 | 1581441 | 50606112 | 202424448 | 455455008 |
| graph_20220606 | 1581761 | 50616352 | 202465408 | 455547168 |
| graph_20220613 | 1768268 | 56584576 | 226338304 | 509261184 |

Actual file lifetimes and future segmentation seams:

- compact_mcm_batched.py:129–142 verifies and streams one scores.f32; _compute:316 opens it exclusively and sink:383 appends ordered f32 scores. It persists through grouped recovery, publication and downstream checks. grouped_offload.finalize:43–59 seeks/reads the same descriptor to compare fresh recovered f32 bytes; all these joins would require a segmented read-at abstraction.
- batched_numeric_execution.py:57 creates numeric-origins.bin; _complete_batch writes ordered 9-byte records, finish:118 hashes it and verify:151–178 rechecks extent/currentness/summary ranges. It persists as scientific execution provenance. Segmentation would require ordered cross-part hashing/range reading and authenticating every part identity, while leaving numerical cache guards and receipts unchanged.
- compact_mcm_output.py:97/108/151 verifies/publishes one matrix.f32 plus manifest with exact inventory; open_verified:198–226 yields one memmap. compact_mcm_batched.produce:458–466 independently maps that same filename into a complete (rows,32) ndarray and Produced. Output manifests/inventory, identity checks, mapping lifetime and Produced consumers must change together if segmentation is ever needed.
- real_pilot_import_caller.py:542–578 retains all seven Produced objects, then torch.from_numpy(result.matrix) and full edge tensors for joint update. This actual route does not use FixedFeatureMap to evade the full-matrix requirement. feature_residency.FixedFeatureMap.load_batch:41–49 materializes and hashes component references, not an arbitrary chunk-backed matrix interface.
- streamed_gat.GraphAttention.forward:116–145 requires a complete torch Tensor: torch.where, einsum, full scores and normalization; only weighted edge aggregation is block processed. A storage-only segmented reader could reconstruct the identical complete ndarray/Tensor and preserve math/order/joint gradients, subject to separately admitted memory/copy lifetime. A lazy chunk object cannot be dropped into the current ndarray→torch interface. Reworking GAT projection into chunks is a different numerical/gradient seam requiring proof, and is unnecessary for the seven actual file extents.

Selected execution_job native_unit_limits.file_size_bytes=1GiB. resources.py:572 emits native LimitFSIZE, :837 checks worker rlimit; real_pilot_import_caller.py:191–192 sets/verifies selected worker limit. Source inspection is not an OS execution test. No cap changed, no launch performed.

Minimum failing node counts for32motifs: origins 3,728,271; f32 score/output 8,388,609. Future workloads beyond these need a new representation or compatible segmented publication; current full24 does not. Aggregate retained disk, temporary copies, whole training memory, archive recovery, remote capacity, and runtime success remain independent unresolved checks. This corrects only the claimed per-file impossibility.
