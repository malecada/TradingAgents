# Driver and first-batch boundary counts

Frozen-source inspection only: exactly batched_driver.py, batched_journal.py and batched_pair_executor.py. No live state, arrays, scientific imports, tests, execution of inspected code or source edits. Reuses preceding pilot34 numeric-authority report (ef343dd428d29c50030d57874dc2b7a826c2d05b3532b447cc6153a6267b623f). Root supplied pending batch0 range0:4096/no checkpoints/no numeric summary; this report does not independently observe it.

## Full producer boundaries

Journal construction stores the callback but does not invoke it (batched_journal.py:15–37). run_batch_stream invokes it exactly twice on successful completion: entry :127 and exit :157. There are NO journal producer-boundary calls per cell, origin or row. The exit boundary follows all executor calls. Since NumericExecution publishes its summary inside the last executor call, the first numeric summary precedes that exit boundary.

Consequently the previously unresolved J is exactly1 through the first numeric summary, or2 through first journal completion before post_batch. The driver's post_batch hook occurs only after completed journal readback, consumer delivery and token rejoin (batched_driver.py:140–163); its producer boundaries cannot explain a delay before the first numeric summary. Checkpoints remain a separate source of two producer boundaries each.

With K completed checkpoints before first summary, B=2+2K counts the explicit pre-_compute boundary plus journal entry and checkpoint boundaries. Reusing the prior successful sampled-path expansion, known sites from compact_mcm_batched.produce entry through first summary produce:

- Target.check calls: 8+2K.
- Forced full scheduler-boundary requests: 21+6K.
- Whole-target graph AND node-order hash checks inside these Target calls: 10+4K.
- Driver additionally checks graph_hash and node_order_hash once at entry (:122), giving 11+4K known explicit checks of each through this prefix.

These counts exclude Target construction, internal owner/stage validation, and full callbacks triggered by ordinary scheduler polls. They are symbolic successful-path counts, not measured runtime counts. With K=0 there is no per-cell forced producer boundary in these three files.

## Ordinary authority polls

Let N=min(batch_cells,total_cells), R=ceil(N/32) rows entered from center0, C computed cells, N-C reused cells, and A the sum of session.advance calls across the C successfully computed pairs.

- driver.drive :100: one entry poll.
- driver._tasks :19,22: two polls bracketing ArrayNeighborhoodIndex construction.
- driver._tasks :24,27: two polls per entered row, bracketing neighborhood extraction. No extra per-motif driver poll.
- Prior memo source: two polls per occurrence, computed or reused: 2N.
- PairExecutor :39,54,58,61: one entry, one per advance, two on successful completion around score_only: 3C+A. Reused cells never enter PairExecutor.

Total direct ordinary polls across driver+memo+PairExecutor through first numeric summary: 3+2R+2N+3C+A. For N=4096 and R=128: 8451+3C+A; if every cell computes, 20739+A. A cannot be inferred from iterations or pending metadata. Poll wrappers do not add another original callback. Each ordinary poll may trigger policy-scheduled full scientific validation, so these are NOT counts of full hashing callbacks. Under unchanged scheduling, repeated ordinary polls still perform the fresh lightweight Target/lease currentness work described in prior reports.

## What pending establishes

batched_journal.py:129–133 publishes pending BEFORE creating/advancing the task iterator. Driver graph/order validation and the journal entry boundary precede pending. ArrayNeighborhoodIndex construction, first neighborhood extraction and first numerical computation follow pending. Therefore durable pending with no numeric summary is consistent with unfinished index construction, row extraction, pair computations, ordinary validation or their interactions. It cannot localize the stall to the first pair, establish completed cells, or attribute the supplied CPU/I/O counters.

Driver :128 computes graph_identity for all32 motif representatives once before tasks. Pair computations perform their separate local pair validation; exact dictionary-body I/O and index construction complexity require callees outside this three-file scope. No data were read to resolve them.

No removable duplicate currentness check is proved here. Per-row polls bracket extraction; per-pair polls bracket computation/scoring; journal boundaries bracket all batch work. Removing any changes the observed mutation/deadline schedule. No patch, throughput claim or active-run intervention is proposed.

## Exact inspected source hashes
047a0762cc0eee53e0ad440339238baeb527158c3a2f33293164e0b91b7a395b  tradingagents/research/onchain_replication/batched_driver.py
0d96f0f3fbe7a320161d8bd16ee7d0d0b0de0384cfbce22459dcf9a8aa9e92a4  tradingagents/research/onchain_replication/batched_journal.py
2e4c5b51f991e1c02eed00d1044a423222eebe77d0f540057f1108df562e34ff  tradingagents/research/onchain_replication/batched_pair_executor.py
