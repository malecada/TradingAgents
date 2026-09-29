# Optional score-only matching

The reviewed next-matching requirements call for reducing retained diagnostics
without replacing the solver. `match_scores` now shares the exact existing
accelerated kernel with `match_batch`. Shape grouping, batch size, float64 node
and edge agreement, row/column normalization order, annealing, greedy hardening,
objective reduction and float32 score rounding remain the same. Its small
MatchScore record retains only score, convergence label and iteration count.
The legacy diagnostic API remains the default and retains its original outputs.

The score-only branch does not construct a MatchResult or copy a soft-assignment
diagnostic. It explicitly releases each hard assignment and its float64 tensor
after computing the score, before hardening the next pair. This reduces retained
results across pairs/groups. Dense per-batch soft matrices, normalization,
node-affinity broadcasts and per-pair hardening work remain; this is not a
solution to arbitrary large pairs or a proven bound on total RSS.

MCM exposes an optional `score_only=True` argument using this consumer. Default
behavior and scientific identities are unchanged. Ambiguous/non-boolean values
and reference-plus-score-only mode are rejected before graph access; the scalar
reference is never silently replaced. Feature values, dictionary order, resumed
output prefixes and checkpoint callbacks are checked against the default path.
No registered producer or empirical gate enables the option yet; an admitted
execution-policy integration remains separate work.

Red01 records eight expected missing-feature failures. Green01 reports 19 passes
and one CUDA skip across score-only, reference, accelerated and MCM checks. A
pre-edit synthetic snapshot records all diagnostic outputs for twelve pair
evaluations at two batch-capacity settings. The post-edit diagnostic outputs and
score-only scores match it exactly. Independent scalar comparisons retain the
registered tolerance. Directed, rectangular, tied, zero-edge and singleton cases,
capacity/precision refusals and iteration-cap labels are included. Weak-reference
checks prove no prior NumPy hard assignment survives to the next pair, and a
sentinel refuses diagnostic result construction in the score-only route.

The active cold-offload's eleven bindings remain unchanged. HEAD cannot move
until that job closes. Expanded green02 passed 69 tests with one CUDA skip in 39.64 seconds,
including feature pipeline, registered producer and resource guard checks. The
weak-reference test additionally verifies release of the actual float64 hard
assignment tensor before the next hardening step. Independent focused review
accepted this source for frozen offline verification; broad closure remains
pending. Existing CUDA checks cover the legacy consumer only; score-only CUDA
parity is explicitly untested. CUDA parity and full-size resource feasibility are not
established. No raw data, sample, financial fit or empirical claim was created.

## Full verification closure

The exact offline01 completed in 1,784.19 seconds with child exit zero and
verified cleanup: 2,768 standard tests plus 97 subtests, 641 neural tests,
two CUDA skips. Total 3,409 passes. All 135 bindings match. Peak sampled memory
was 2,221,502,464 bytes with zero memory.high/max/OOM events. Monitor and cgroup
are absent. Independent terminal review accepted this engineering increment;
closure-check01.json binds the raw terminal/log evidence. The cold-file offload
also subsequently closed, releasing the shared HEAD freeze. The remaining
CUDA, registered integration and full-size feasibility limitations above persist.
