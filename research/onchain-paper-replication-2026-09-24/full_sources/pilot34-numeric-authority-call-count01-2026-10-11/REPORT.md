# First numeric batch: symbolic authority counts

Source-only; exactly four additional source files. No live receipts/processes, imports of research code, arrays, tests or pinned edits. Counts below describe successful sampled schema6 control flow, not measured pilot34 invocations. Prior six-file findings are reused from pilot34-resource-overhead-investigation01-2026-10-11/REPORT.md (fcb81428429c04e02c6a84ba5e06eb0b73f6cbce46baa8cbb4a993401f8b4582).

## Critical multiplicities

| Call site | Successful source-level work |
|---|---|
| compact_mcm.py:109,111,126,154,179 | Five Target.check calls in imported _prepare. |
| compact_mcm_batched.py:501,508,510 | Three explicit sampled entry full-boundary requests after preparation. |
| compact_mcm_batched.py:511 | One more Target.check, following owner.boundary. |
| compact_mcm_batched.py:518–522 | Each producer boundary performs Target.check, owner.boundary, stage.lease, then Target.final. One boundary runs before _compute. |
| compact_mcm_batched.py:346–362 | Each successful checkpoint callback adds TWO producer boundaries, before save and after metadata publication/inventory checks. |
| batched_numeric_reuse.py:244–273 | Every cell, computed OR reused, makes TWO ordinary authority_poll calls, before work and after result validation. Computed cells also enter PairExecutor; its internal additional polls were not inspected in this four-file budget. |
| batched_numeric_execution.py:106–139 | First occurrence starts memo batch; final occurrence completes it before returning. No extra Target.check is called directly for an origin record. Origin root/file metadata is checked each occurrence. |
| batched_numeric_reuse.py:111,170–186 | Numeric source attest once at construction, once at begin_batch, once at end_batch, and twice per checkpoint. These are numerical source/runtime guards, NOT Target.check or full scientific authority callbacks. |
| compact_mcm_batched.py:369,455 | Genuine producer boundary is passed into BatchJournal; ordinary target.lease is passed into driver.drive. These uninspected callees determine additional journal/stream/origin callback multiplicities. |

From prior inspected Target source: Target.check explicitly requests two full scheduler boundaries and one Target.final(full_graph=True); Target.final(full_graph=True) explicitly requests one full scheduler boundary and hashes whole target graph plus node order. Therefore EACH producer boundary entails THREE forced full requests and TWO whole graph/node-order hash checks. These are not per-cell by definition: they occur wherever journal/stream/checkpoint calls invoke that boundary. Ordinary per-cell target.lease can trigger a policy-scheduled full callback, but its full callback uses Target.final(full_graph=False), avoiding the explicit whole-target graph/node-order checks.

## Symbolic successful prefix through first numeric summary

Let N=min(batch_cells,total_cells), K=completed checkpoints in that prefix, J=additional producer-boundary invocations from uninspected journal/driver callees before that summary, and Q=any other invocations of that same producer boundary in the prefix. Include the explicit pre-_compute boundary:

B = 1 + 2*K + J + Q.

From entry to compact_mcm_batched.produce through that prefix, explicit Target.check count is 6+B; explicit whole-target graph AND node-order hash checks are 6+2*B; forced full scheduler requests are 15+3*B. Thus checkpoints alone add six forced full requests and four graph/node-order hash checks each. These are known-site counts: Target construction/owner/stage/callee validation and ordinary scheduler-triggered full callbacks are excluded, not asserted absent.

Numeric memo source-attest calls through one completed first batch are exactly 3+2*K, absent failed/retried/close paths; each attest rehashes every SOURCE_PINS module body and checks runtime function identities (reuse.py:50–59). Numerical source byte total is that count times the fixed source-roster byte total; no source-byte total was measured here. Ordinary memo authority polls contribute exactly 2*N. Total ordinary polls additionally include PairExecutor/driver and any nested validation; their counts cannot be inferred from completed-cell or reuse counts alone.

The first numeric summary is written only after memo.end_batch (execution.py:136–159); it is not a receipt that the journal's later publication/offload boundary has completed. Both source-attest and forced Target full validations can therefore occur before the first summary, without any published progress.

## What is hashed; what remains unresolved

The prior Target source establishes whole graph/node-order hashes in final(full_graph=True), and repeated dictionary materialized integrity, imported-stage content and derive_scope checks. derive_scope enumerates representative graph_identity values. It does NOT establish, without their callees, an exact count of whole dictionary-body bytes read or hashed. Numeric reuse validates and obtains graph_identity for the current pair and builds an exact key twice when cacheable; those pair graphs must not be conflated with the whole target graph. Authority Lease._full rereads/hashes/compiles registered loaded source on every forced full callback, in addition to execution.check work. Source bytes, imported dictionary bytes, full graph traversal and source compilation are different costs.

No check removal is proved semantics-preserving. In particular, the second Target.final in producer boundary follows owner.boundary and stage.lease, so deleting it would remove a post-callback mutation/currentness observation. Reuse does not waive the two per-cell polls. Any future optimization must preserve callback ordering, fresh reads and mutation refusal, including compiler/audit-hook semantics; existing fresh canonical-serialization work is a narrower candidate than caching authority success.

Remaining precise source gap: BatchJournal/driver and PairExecutor determine J and additional per-origin/per-chunk polls; they were deliberately not opened as a fifth additional source file. Actual K/J/Q, elapsed costs, bottleneck attribution and pilot34 throughput remain unknown. No active-job modification is proposed.

## Exact four source bodies

- `tradingagents/research/onchain_replication/compact_mcm.py`: 28867B SHA256 `abd86e24681f0df4ef3ca82cfb016662d9af5a46a38a32bafc65e7c92f2dacf8`.
- `tradingagents/research/onchain_replication/compact_mcm_batched.py`: 46184B SHA256 `e93d3b7073c8de5d1c3e7f5f30b55ba613b47a014f8fe449a0fe7e8a746941dd`.
- `tradingagents/research/onchain_replication/batched_numeric_execution.py`: 23417B SHA256 `8552d9496539450e65bcb2d57404e7a783b917a24807088639e81e1dadc568af`.
- `tradingagents/research/onchain_replication/batched_numeric_reuse.py`: 20116B SHA256 `dabc42d5a83ed5ef31d1eb31985da1529acf604c6ce6354badf276e5c07a936a`.
