# Independent isolated score-only finalization review

September 30, 2026. **Accepted for further isolated synthetic engineering; no blocking defect found in this adapter.** This is not a production matcher substitution or empirical release. Source and saved logs were inspected independently; no tests, jobs, empirical bodies or network requests were run. Only this review was written.

`score_only` checks strict positive integer policy values and the 65,536-edge chunk maximum before allocating pairs. A completed hardening state has exactly min(n,m) injective pairs under the unchanged composite check. Its new int64 pair array uses 16 bytes per pair. Reserving that array alongside the existing sparse scorer's 64 bytes per pair plus 32 bytes per bounded right-edge chunk gives the declared 80×min(n,m) + 32×min(chunk_edges,right_edges) admission. Passing the remaining allowance to the scorer preserves both component budgets. Incomplete states and original pair-capacity violations remain refusals.

The implementation does not construct a dense hard assignment, call the composite dense result method, copy M or return either assignment diagnostic. It sorts/traverses selected pairs through the unchanged sparse reference objective and returns only score, convergence and iteration count. The original scalar reduction order and math.fsum objective remain distinct from the accelerated Torch reduction and its score conversion. Importing/reusing MatchScore is container compatibility, not proof of accelerated numerical parity. It also imports the production matching module and its runtime dependencies; no lightweight or neural-free import claim is made.

The sparse objective's conservative representable-agreement envelope is preserved. Removing zero-weight terms is accepted only within that component's reviewed domain; finite graph attributes alone are insufficient, and correlated extrema may be conservatively refused. The adapter propagates a domain failure rather than falling back, relaxing capacity or silently using another numerical backend. Finalization does not mutate the issued state, so a scoring refusal leaves the completed checkpoint available. Caller-exclusive ownership and unmodified graph/state assumptions remain necessary; M is not independently rehashed on every score call.

The allowance excludes retained V/M/Q, graph inputs, component validation/hash scans and their temporary masks, Python pair/JSON metadata, import/runtime memory and other native temporaries. Thus eliminating dense result construction is a concrete implementation property, not a measured total-memory reduction. Scoring, validation, identity checks and summation remain atomic. No scoring checkpoints, wall-time bound or full-hub feasibility is established.

The retained red log contains three missing-interface assertion failures. The saved green log reports **three tests passed in 0.026 seconds**. Three tiny pair fixtures cover reciprocal/self-loop edges, tied zero-edge graphs and a single column; the final score, iterations and convergence equal the scalar oracle. Dense result/scoring methods and np.zeros are patched to fail during finalization. The returned object lacks assignment fields, and M bytes and read-only state remain unchanged. Static inspection supplies the additional evidence that no alternative dense H allocation or M copy is present; patching np.zeros alone would not prove that generally.

The insufficient-budget case patches np.asarray and verifies refusal before pair conversion. The incomplete-state test and source check establish that pairs are not allocated before completion validation. The domain test stubs score_indices to raise: it proves propagation only, not an actual new extreme-value/domain-boundary execution. Original sparse-domain tests remain the evidence for the unchanged scorer. No exact minimum-allowance boundary grid, large pair-list case, arbitrary state corruption, concurrent alias mutation, native allocation peak, Torch equivalence or failure at every scoring instruction is tested here.

All 24 candidate bindings and all 163 prior full-suite bound files independently rehashed unchanged. The old full-suite result does not include this new isolated adapter. All 88 active graph07 source pins and 87 input references also match; HEAD remains `de91c9e084ad167e26b32effb4788d6f80130ef8`. No active frozen file or underlying component was changed by this review.

Reviewed SHA-256 identities:

- result_only.py: `a1f0b02084c2a8ba435a9a88e527e0917df3dae16c3df524d4c92fb412920dd2`
- test_result_only.py: `df11f6e88383f00520a160591ef63c46be9a1bb416c8451576af76ac85cd8556`
- IMPLEMENTATION.md: `3190af5fbcf32efc3eb0c9b741377e84c554fb0ec551779c13fa2e682121959c`
- green01.log: `d0d49642599f39bbb0c0c401f5e2b1d09e26b31d5621224b6333f4acbb52c8af`
- source-bindings.json: `f24f9d23f5ea70fb600ba924d689e864112b782aaef035745193f23e159ec53e`

Any production use still requires explicit backend/precision, policy/cache identity, capacity and checkpoint-ownership integration, focused verification and separately reviewed resource admission. No sampling, financial-fit or other empirical claim follows from this acceptance.
