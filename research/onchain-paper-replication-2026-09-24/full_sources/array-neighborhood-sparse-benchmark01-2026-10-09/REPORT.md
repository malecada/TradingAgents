# Bounded synthetic neighborhood benchmark

Unchanged installed baseline514ef899 versus accepted source-only candidatee3b4bf6. PASS: all warmup and repeated outputs have matching exact typed-array/provenance SHA256. Actual public API input is GraphSnapshot; outputs are genuine immutable AttributedGraph. No mock numerical graphs, original input arrays, sampling, training or empirical claims.

Fixed before execution: chain10000nodes19998edges/four sorted centers; hub4000nodes7998edges/four sorted centers including hub and leaves; dense160nodes25600edges/two sorted centers. Ten distinct centers, one warmup per implementation/center, four repetitions with alternating implementation order, no size or case adjustment. Raw per-center timing and hashes in RAW01. Fixture and both index initializations separately timed. Digest verification excluded from extraction timing.

| Case/center | Baseline median ms | Candidate median ms | Baseline/candidate |
|---|---:|---:|---:|
| bidirectional_chain/0 | 0.0613 | 0.0779 | 0.787 |
| bidirectional_chain/100 | 0.0659 | 0.0860 | 0.766 |
| bidirectional_chain/5000 | 0.0690 | 0.0861 | 0.802 |
| bidirectional_chain/9999 | 0.0703 | 0.0790 | 0.890 |
| hub_and_leaves/0 | 20.2531 | 49.4363 | 0.410 |
| hub_and_leaves/1 | 0.1644 | 0.2727 | 0.603 |
| hub_and_leaves/2000 | 0.1353 | 0.2658 | 0.509 |
| hub_and_leaves/3999 | 0.1328 | 0.2571 | 0.516 |
| dense_center/0 | 3.0685 | 4.8461 | 0.633 |
| dense_center/79 | 2.9385 | 4.9491 | 0.594 |

Candidate regressed at every measured center: chain1.12–1.31x slower; hub center2.44x slower; hub leaves1.66–1.97x slower; dense centers1.58–1.68x slower. No measured speedup in this fixed run. Ratios below1 are regressions. These tiny fixed examples do not establish actual pilot speedup or workload-weighted benefit. In particular candidate scans/merges and search overhead can dominate small neighborhoods; hub and dense behavior must be considered rather than extrapolating removed dense-N masks. No implementation changed during benchmark. No repetitions discarded.

Pinned Python3.13/NumPy2.3.0; threads1; affinity[0,1] means two logical CPUs, not isolated from active pilot.30s outer wall bound,256MiB AS,4MiB file-size bound. Actual elapsed 0.820s; peak RSS42552KiB. RSS is process observation, not native full-pilot capacity proof. Limits enforced before runtime import. No live source/Git/registration/Run/Owner/network changes.
