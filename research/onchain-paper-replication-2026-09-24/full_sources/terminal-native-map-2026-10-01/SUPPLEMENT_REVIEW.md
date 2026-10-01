# Independent correction review — registered integration pending

The inspected source delta addresses NM1 and NM2. No additional material blocker was identified in the corrections. Final component acceptance remains pending the actual registered preparation/seal/map integration and final bindings. No tests, jobs or empirical numerical reads were performed by the reviewer; only this supplement was written.

For NM1, `minimum_capacity` derives the largest required graph's native payload from resident node/edge dimensions and motif count. It requires that payload within the live tensor allowance and twice that payload plus `9 * chunk_entries` within the numeric allowance. `prepare` calls it before `seal.finish`. The pure test independently exercises the exact boundary and one-byte insufficiency of each limit. This establishes minimum individual-graph capacity, not feasibility of every multi-graph chronological batch or any full fold. Aggregate requested batches still require their runtime preallocation check.

The new actual registered low-cap test forbids `seal.finish` and checks that neither journal seals and no seal attempt appears. The separate success test performs actual preparation first, then forbids producer/admission reentry and the generic loader while exercising verified hashes and maintained batch_factory; it also tests repeat preparation refusal and lost guard. Their source has been reviewed, but no closed execution result is available at this review boundary.

For NM2, the public accounting query now takes the same nonblocking operation lock as loading and verification. Internal `_live_tensor_bytes` is used only from those locked paths. The controlled thread/barrier regression pauses an active batch, verifies public query refusal, then confirms the newly returned tensors remain counted and prevent excess allocation. The final accounting inequality allows previously returned wrappers to die during the operation without falsely refusing the new batch. The result dictionary retains all new tensors until return, and their weakref registrations are created while the lock is held.

Saved `check02.log` records eight passing pure methods in 1.232 seconds. The saved red02 contains one missing-capacity-helper error and one missing-query-lock failure; it is not evidence that an old actual registered preparation performed the capacity counterexample. The original source and test `.check01` files match the exact hashes recorded in INITIAL_REVIEW.md, which remains unchanged.

Weakrefs continue to account only for original returned wrappers, not detached/views/autograd storage surviving those wrappers. This is not a total resident feature-storage or RSS bound. The private helper remains a numeric adapter rather than an admission authority. No cold/historical reuse, financial fit, full-fold resource feasibility or empirical release is established by the pure checks.

Reviewed SHA256 values:

- `native_map.py`: `3dc16db234de6d44c11635d1dc66d7a040120101a1d50087c026470dfaf1ba78`.
- `test_map.py`: `702c6370f7b98a6bfd2d0a4f46afe5c2489da16f95ea559bb6be5f1ab87893c6`.
- Pending integration `test_prepare.py`: `727ba4eea55f0054de2b38ef7b9c0d4460a3c48694e1b93ac6547af4f338e191`.
- `check02.log`: `60b2d8e8d8284b08d07f4b766faf329e9ccc7f8b54fc10ebb11553bd0558d260`.
- `red02.log`: `d4e81ad9aa1f645ae04e4627bf74ad61e4f5b72531b71e28ef049d4047e1917c`.
