# Existing acceleration status and next responsible seam

Source-only: four source bodies inspected (listed below), immediate candidate-directory names and selected reports. No live receipts, actual arrays, scientific imports/runs, installation or patch. Root-supplied first-batch timing/geometry is contextual evidence, not independently reproduced here. Static eligibility2268/4096 is not a count of actual compiled calls, completed accelerated pairs or saved seconds.

## Current connected compiled normalization

compiled_small_lse.py:125–138 selects per REDUCTION BLOCK, not per whole pair: exact ndarray/float64/2D; each dimension1–4; positive8-byte-aligned strides bounded by2^31-1; axis0/1; keepdims=True; finite entries with absolute value<=256; exact original fallback function/code; pinned NumPy primitives; default error modes; original native function signature and live sealed descriptor. Any failed eligibility test uses original SciPy fallback; nonzero native return also falls back. Loader unsupported conditions use clean fallback; source/runtime reference mismatches and fatal/ambiguous cleanup do not silently gain fallback authority.

matching_annealing.py:263–273 forwards row blocks and column blocks through this helper. Rows are chunked by cap//m; columns by cap//n. A tall matrix necessarily fails the compiled column-block dimension check when n>4; eligible short row blocks are possible only if their actual two dimensions fit. Single-column chunks with original m>1 are duplicated into two columns before reduction, preserving the existing normalization arithmetic. No node limit or matrix-product threshold alone completely describes dynamic dispatch; magnitude/error/runtime guards still apply.

Existing connected backend is already owned once per numeric executor lifetime with sequential session borrows; changing ownership again is not the larger-matrix implementation seam. Fresh reference/currentness checks remain required (compiled_normalization_policy.py:79–98 and BackendOwner).

## What already exists

1. `matching-batched-small-pair-prototype02-2026-10-09/full_advance.py` is executable uninstalled grouped annealing, accepted only as finite uninstalled evidence by `matching-acceleration-candidates-combined-review02-2026-10-09/SOURCE_EVIDENCE_REVIEW01.json`. Domain: fresh states, same group shape/edge counts,1–16 nodes per side,1–1024 edge products, full-axis chunks, supported immutable numeric inputs/runtime and sufficient complete-advance budget; bounded262144B explicit scratch. Unsupported/partial/single-item groups use original advance. This is larger than compiled4x4 reduction support but remains a SMALL-pair candidate, not a solution for59825-node neighborhoods or1,435,800 matrix products.

   Missing real seam: NumericReuseExecutor/PairExecutor currently computes one occurrence at a time; the prototype needs multiple exclusive states/graphs, genuine between-pair authority ordering, reservations, checkpoint and attempted/unknown failure attribution. Accepted review explicitly retains changed cross-pair exception prefixes and absent authority integration. It cannot be dropped into the caller or treated as universally bitwise equivalent. No old numerical evidence was rerun.

2. `annealing-hotpath-next01-2026-10-09` warm agreement-copy candidate is already visibly present in current matching_annealing.py:220–223. Current same-pair lazy reuse supports<=4096 edge products; selected adaptive extension supports4097–16384 with max_operations>edge products, immutable/runtime guards,256-entry chunks and unchanged262144B scratch. Cache is local to one advance call. Above16384 there is no cached-weight reuse in this body; the bounded ordered chunk/scalar path remains. This is not an uninstalled larger accelerator waiting to be enabled.

3. `matching-large-domain-dot-reuse01-2026-10-09/REPORT.md` is a source-grounded REFUSAL, not a candidate: original agreement uses scalar subtraction/square/math.fsum/exp, not dot. Node agreements already reside in V, and independent edge features cannot be derived from node agreements.

4. `matching-full-workload-acceleration01-2026-10-09/REPORT.md` identifies a concrete compiled uncached-edge-chunk seam but supplies no implemented/reviewed large-domain kernel. Its old publication/caller estimates predate later batching; reuse its arithmetic constraints, not those historical throughput forecasts.

## Most concrete remaining method-preserving implementation

For truly large pairs, the responsible new implementation is a bounded optional compiled equivalent of the UNCACHED edge-chunk body in matching_annealing._advance_checked:205–246, returning at the same phase/cursor/operation boundary. Preserve per-feature subtraction/square, exact fsum and exp behavior, .5 multiplication then M multiplication, ordered destination additions, lazy exception-prefix replay, budget/scratch accounting and unchanged SciPy normalization/ranking/checkpoints. No fast-math/FMA/reassociation, eager whole-pair agreements, new caps or skipped authority checks. Begin by invoking original fsum/exp in the same order; native replacements require additional platform-specific equality/refusal evidence. This is an implementation assignment still needed, not ready code or promised speedup.

Merely broadening compiled_small_lse's4x4 predicate is not justified: its pinned native source/ABI and finite qualification do not establish large-axis SciPy reduction equality. A separate large-reduction implementation would require exact numerical/near-tie/error-mode and original-state/checkpoint qualification. The current source review identifies no accepted large-matrix implementation ready for installation.

The measured56% authority share supplied by Root overlaps numerical elapsed, so accelerating a reduction or edge kernel alone cannot be called a whole-pilot remedy. No acceleration benefit, overall ETA, actual cache eligibility or resource capacity is established here. Future engineering stays separate from frozen active34.

## Exact source bodies and reused review
7f98ca93c5100e475c1a6de0280e4ce546c0adc26c3865820068b868014c496e  tradingagents/research/onchain_replication/compiled_small_lse.py
f60237416454998bbe41a969400775b134a9f285c4b64c1a5507453515b25c01  tradingagents/research/onchain_replication/compiled_normalization_policy.py
eb509ecf5c9ed7d28783b1a4230013ddcba8036a0fb5174d3aaa60307fc63b43  tradingagents/research/onchain_replication/matching_annealing.py
2787e94802566cbad0907f8edfd1b258a668b7f51b762f6fe79680c68b25afe3  research/onchain-paper-replication-2026-09-24/full_sources/matching-batched-small-pair-prototype02-2026-10-09/full_advance.py
6a812b8111d6441d5a78febae04779677b04788d0d981f2abbe98106dcfc4415  research/onchain-paper-replication-2026-09-24/full_sources/matching-acceleration-candidates-combined-review02-2026-10-09/SOURCE_EVIDENCE_REVIEW01.json
