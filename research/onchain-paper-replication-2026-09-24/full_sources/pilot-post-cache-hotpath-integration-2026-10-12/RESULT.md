# Edge-index layout improvement

The selected C05 v2 path now gathers the four edge-index rows separately for ordinary read-only NumPy arrays. This produces contiguous row buffers instead of row views of combined column gathers. The original gather remains the fallback for other array types or writable edge indices. Multiplication, ordered `np.add.at`, scalar fallback, failure-prefix repair, operation accounting and checkpoint state are unchanged. No geometry is retained across chunks or pairs; the numeric payload remains four int64 vectors per chunk. Numeric reservations and native limits are unchanged.

The post-cache attribution completed once under Root control, session89142 exit0/chunk8e9714. The instrumented larger cases attributed about 19.7–19.8% of advance/hardening time to geometry construction and 8.0% to ordered scatter. Geometry includes position creation, division, edge gathers and the current-M gather; only the edge gathers changed. Timers add overhead, so these shares do not predict production savings. All three soft-matrix digests and operation totals matched the previously accepted selected route. Cache snapshots were taken before cleanup and are not leak measurements.

The uninstrumented paired comparison completed once, session5764 exit0/chunkbeca2f. Both routes used C05 v2, the original 48 temperatures and 1,000,000-operation advance budget. The interval includes cold state/session creation, advances, hardening, production sparse scoring, diagnostic copies and cleanup. It excludes graph generation, genuine backend authority, transport and the complete real-data pilot.

| Edge products | Existing v2 seconds | Row-layout seconds | Wall reduction |
| --- | ---: | ---: | ---: |
| 1,024 | 0.018151 | 0.017354 | 4.39% |
| 16,384 | 0.225626 | 0.214281 | 5.03% |
| 131,072 | 1.040807 | 0.985647 | 5.30% |
| 1,048,576 | 8.381787 | 7.479989 | 10.76% |

All soft matrices, assignments and packed float64 scores matched bitwise; complete operation/cursor histories matched exactly. The separate 16,900-product case retained exact results under a 1,024-operation budget and genuine checkpoint save/load recomputation. Its timing is not a paired performance comparison because only the candidate route reloaded a checkpoint.

Each performance value is one fixed-order paired fixture observation. No statistical significance, whole-pilot throughput or combined speedup with earlier changes is established. Process peak RSS was 66,532 KiB, not kernel/cgroup peak or whole-model capacity. Actual outer controls reported CPUs 0 and 1, a 120-second CPU limit and 4 MiB file limit; the timeout was 120 seconds. No empirical claim, financial sample, training update or native pilot was launched.

The exact annealing source and its one required source-digest update in `batched_numeric_reuse.py` were installed by `SOURCE_INTEGRATION01.json`. The independent source and numerical-return reviews accept the literal/AST inverse, guarded fallback, duplicate-target ordering and failure boundaries. Installed focused checks completed once, session82532 exit0/chunk8ae577: **42 passed in 4.69 seconds**, covering numeric policy, pair checkpoints and the actual default/v1/v2 numerical constructor. The installed-return review authenticates those raw results and exact copies. No unrelated cleanup or full legacy matrix was repeated.

The investigation also identified duplicated feature-header checks in the cached-weight path. An unconditional deletion is unsafe: a direct helper call with the same array object and reshaped header can reuse stale row semantics. That finding is retained in the adjacent investigation directory. Fresh validation remains intact in this change.

The next real-data entry still requires rebasing the exact source/runtime/input and registration closure, incremental recovery, final release and fresh eligibility. Its results must measure actual feature throughput, storage, peak memory and training. Component benchmarks do not establish that this machine can complete the full paper scope.
