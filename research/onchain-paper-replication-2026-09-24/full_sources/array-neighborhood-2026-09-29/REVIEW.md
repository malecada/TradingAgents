# Independent array-neighborhood component review

September 30, 2026. Source and saved synthetic evidence review only; no tests, jobs, raw arrays or network requests were executed. No material algorithm or buffer-accounting defect was identified. Focused component acceptance does not enable a registered consumer or alter the frozen study capacity.

The implementation preserves complete weak-hop membership by traversing the previous frontier and accumulating a separate following mask. Previously selected nodes are removed before forming the next frontier. `flatnonzero` returns ascending global indices, preserving valid unsorted source node-ID ordering. Induction visits outgoing edges of each selected source exactly once, retains edges whose destination is selected, and sorts original edge-column indices before copying. Thus directed attributes, self-loops and original edge order survive; no truncation, symmetrization or tie policy is introduced. Exact node-cap excess is refused after expansion, and an isolate/hop-zero result remains the center alone.

The index precheck precedes graph hashing and sorting. Its retained numeric arrays are two edge orders plus two offsets, `16*(E+N+1)` bytes with the intended 64-bit indices. The additive scratch allowance `16E+40(N+1)+4N+chunk*(64+2*node_width+2*edge_width)` is conservative for the inspected live arrays: sort/count work, old/new frontier indices and masks, selected indices, global/local mapping, arange, retained-edge indices and bounded endpoint/feature gathers. The operation counts induced edges before allocating output arrays and adds twice the exact node/edge numeric payload. `AttributedGraph` makes immutable byte-backed copies while source output arrays remain live, so this factor covers that constructor coexistence. In-place quicksort restores edge order without another full retained edge array. This assessment is an allocation-path audit, not a measured process peak or proof about every allocator implementation.

The stated exclusions are material: original graph arrays, Python node-ID metadata, graph validation/hash internals, caller-retained prior outputs, allocator overhead and process/library state are outside this allowance. Validation can still allocate a linear sorting index. Repeated successful calls can accumulate arbitrary caller-owned results; the allowance covers this index and its current extraction, not that population. Outer resource protection remains necessary.

The nonblocking lock protects extraction and close, refuses reentrant use, and is released in a finally block. Close drops graph/index references and refuses to invalidate a live extraction. Results copy node/edge/features into `AttributedGraph`; they do not borrow reusable index scratch. The mapped input's lifetime, if used prospectively, would remain its caller's responsibility. The new API requires Python integer center/hop/cap values; this is narrower than some NumPy-integer inputs accepted by the legacy API, whose behavior is unchanged.

Saved green01 reports 18 passes. Retained red02 cleanly demonstrates the original missing busy-close refusal; the corrected lock implementation is exercised by green02, **52 passed in 6.80 seconds**, including the new component and legacy/mapped graph checks. Tests cover all centers at hops 0–3, literal directed order, unsorted IDs, self-loops, isolate/zero-edge results, repeated calls, immutable output after close, capacity refusal and a complete **10,002-node synthetic star** under an explicitly larger local test configuration. That test does not change or qualify the frozen 10,000-node study setting.

Two evidence limitations were reported to the author. The output-admission test expects a buffer exception but does not yet instrument output allocation, despite its name; source ordering independently supports the claim. Constructor partial-index allocation failure cleanup is present in source but not injected by the current tests. These are test-strengthening opportunities rather than observed source failures. No matching, sampling, dictionary or registered-pipeline integration is present in this component.

Initial inspected hashes:

- `array_neighborhoods.py`: `458c884d046f5939acce9e02aa65ada43950e540ab98d8a37328eb0d06656f1d`
- `test_array_neighborhoods.py`: `9195a5e1f882cc283848e23eb27260bd60506e7badf57481403cc721ccd74ed8`

Broad verification, full-size source residency and matching feasibility, consumer checkpoint behavior, admitted execution-policy binding and any empirical resource claim remain separate. No new sample or financial outcome is established by this review.

## Final focused component addendum

The new public `selected()` uses the same nonblocking lock and `_select` contract, returns the independently allocated ascending index array, and releases the lock on success/failure. Returned indices remain caller-owned; no reusable mask or index-storage view escapes. It adds no numerical or neighborhood-selection change. The source explicitly treats prior caller-retained outputs outside the invocation allowance.

Added tests meaningfully address the earlier evidence gaps: an `AttributedGraph` sentinel proves over-budget results never reach immutable output construction, while injected failure at the second argsort proves retained object state is closed and clears graph/orders/offsets. Allocation of the preceding mutable output arrays remains checked by source ordering rather than a NumPy allocation sentinel. A real synthetic mapped-input test verifies output arrays after both owners close and confirms the index does not close its caller-owned map. The public selection output survives another extraction and index close. Retained red03 distinguishes the missing public selection method failure from the already-passing injected cleanup case.

Saved green03 reports **53 passed in 23.04 seconds**; final green04 reports **55 passed in 14.23 seconds**. Focused acceptance is reaffirmed for the final source and tests:

- `array_neighborhoods.py`: `514ef8993d962c29b81777791303904f79a31e695cb0b5d152b27bdd02e2cf3f`
- `test_array_neighborhoods.py`: `c8b26f347af8c9f00dc475c8ff0234565c8f467ba5dd43e33ccf3ae2508a82a7`
- Green04: `de12ddf76d11010674cc7640c2b31fddca122e2679d9d452d96584cc98ee9b46`

The inspected IMPLEMENTATION.md (`b2692067d416062cd366f91e985bd8d248af2dbb46270f79a98129220f9e1408`) accurately limits the result to an optional component, exact supported-input semantics and its explicit numeric allowance. It does not enable a current sampler/MCM producer or revise the study cap.

The prospective launcher (`8a49f90c7631379675115f3c7bc81eb8b61bb6161c5622e68eb09cb4c0b69311`) checks frozen HEAD and declared source hashes, validates the 10 GiB policy, and calls only the pinned named offline target. Its controls match the prior reviewed profile: 3 GiB maximum, 2.75 GiB high, zero swap, 3 GiB runtime reserve, 6 GiB startup reserve, 10 GiB disk floor, 3,600-second wall limit and the unchanged guard's two-CPU default. Success requires complete phase, child exit 0 and verified cleanup. It is acceptable for one fresh bounded engineering verification once source bindings are frozen and guard checks pass. The prospective 139-file binding set was not yet present for independent audit at this inspection; no run or broad result is asserted. All full-workload and empirical limitations above remain.

## Terminal named-offline closure

Independent inspection of the saved child log confirms **2,768 standard passes plus 97 subtest passes in 1,027.66 seconds**, followed by **680 neural passes and 2 CUDA skips in 517.18 seconds**. Total: **3,448 passes plus 97 subtest passes, with 2 skips**. The log explicitly retains reviewed-profile exclusions; this is the named offline target, not the unrestricted historical suite.

All **139 source bindings independently rehash correctly**, and current HEAD matches frozen `58ec1181a7bbe5d3d982401973f85acb0484f1a4`. Final/live receipts agree: complete, child exit 0, cleanup verified, **1,548.356068 seconds**, sampled cgroup peak **2,415,431,680 bytes**, zero memory.high/max/OOM events and no limit reason. The saved command uses the pinned interpreter with `-B scripts/verify_offline.py`; controls match the reviewed profile above. Monitor PID 2277975, recorded cgroup and last recorded workload threads are absent at review. The earlier pending frozen-binding and broad-verification conditions are therefore closed for these exact bytes.

Terminal evidence hashes:

- Source bindings: `993a32054d4134464717b8e6c2e02509653a09db3e243abf2e752937c16e1ee3`
- Final receipt: `785167aba7d7302f8aea7254a6b3fc992128242b9ac50704496c131a81fbb050`
- Child log: `64f00e66b7c4995c7afbfe44235ded5d1db84c6491444b170e58380c9ba76a08`

Engineering closure is accepted for the optional array-neighborhood component. No tests or other jobs were rerun, and no source/HEAD changes were made by this reviewer. The observed peak applies to this synthetic verification/cache state; it is not a production or cold-cache whole-fold memory bound. Registered sampler/MCM integration, full-size matching feasibility, checkpoint/capacity lineage and empirical resource release remain separate. Neither this result nor the separately reviewed budget-only census proposal enables a new empirical claim or changes the frozen study cap.
