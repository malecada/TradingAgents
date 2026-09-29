# Independent mapped-sampler design review

September 29, 2026. Reviewed the proposed opt-in workspace API, current sample_neighborhoods implementation and retained 6,400-choice feasibility probe. No source edit, test, empirical job, raw body or network request was made. The design is suitable for bounded synthetic implementation, subject to the following contracts and subsequent source/result review; it is not empirical release.

## Numerical identity

Keep the eager default behavior unchanged. The mapped path must retain training filtering, sorted graph ordering and hashes, offsets, center selection, neighborhood construction, recorded probability, weight updates, sample records and final RNG state. Workspace policy/path must not alter scientific configuration or SampleManifest identity.

Mapped selection must use the same full float64 NumPy sum, divide, cumsum and final-CDF normalization as the successful probe, followed by one PCG64 scalar draw and right-side search. Do not substitute block reductions or a different cumulative summation order. Validation can be blockwise; numerical reductions cannot be reordered while claiming byte parity. Record the selected probability from the initial normalized weights, not the subsequently normalized CDF. Set the chosen weight to zero before halving the same selected-neighborhood indices, preserving overlap and cross-graph offsets.

The probe is explicitly bound to NumPy 2.3.0 and finite nonnegative generated weights with positive remaining mass. The implementation should record/enforce the supported mapped-mode version or otherwise establish an equally explicit compatibility contract. Invalid, negative, nonfinite, exhausted or nonfinite-total mass must fail before consuming RNG state; invalid totals must never produce an arbitrary last index. Eager/mapped graph-level parity must exercise actual graph neighborhood membership and sample manifests, not only the isolated helper compared against itself.

## Workspace accounting and lifecycle

The proposed three float64 mappings use **24 × candidate_count** logical array bytes. `max_weight_bytes` must be described as an explicitly limited weight-workspace allocation, not whole-process/whole-sampler memory. NumPy temporaries, graph copies, selected neighborhoods, Python records and filesystem cache remain outside that narrow payload and under the outer resource guard. Validation must avoid accidental full-length temporary boolean arrays if a bounded validation claim is made.

The additional **64 KiB** allowance needs an enforceable definition. Serialized intent metadata grows with the number of training graphs; arbitrary many small graphs can exceed that allowance even when each graph has few nodes. Bound/check the encoded receipt metadata before allocation or account its exact size, including any claimed filesystem-allocation overhead. Do not call 24N+64 KiB a strict disk upper bound without accounting for page rounding and the actual receipt scheme. A fresh 20 GiB free-space-floor check should reserve the planned allocation above the floor; creating a permitted workspace must not itself predictably cross the floor.

Require an explicit positive integer budget with mapped mode (reject bool and invalid combinations consistently). Insufficient budget, unsupported runtime or an existing/symlink workspace should refuse before vector allocation. Exclusively create the new workspace; never overwrite, truncate or silently attach to completed, failed or unsealed mapped files. Bind training graph hashes in order, configuration, seed, candidate count, implementation/runtime identity and declared allocation in an immutable intent.

Flush and close mappings on ordinary success and exception paths. Write success only after the SampleManifest is complete and any promised durable data flush has succeeded. Preserve exception details and available progress under a failed receipt. A hard kill may leave intent/unsealed files without a terminal receipt; the enclosing guard must preserve that outcome. No partial weight state is implicitly resumable, and no automatic cleanup/retry may erase attempted evidence. Raw weight files must not be mistaken for an admitted sample manifest or independent empirical result.

## Meaningful bounded verification

Use the actual unchanged NumPy eager path as oracle. Compare selected centers, every recorded probability exactly, complete PCG64 state, graph/subgraph identities, record order and final SampleManifest identity across multiple seeds and graph orders. Include cross-graph center offsets, overlapping neighborhoods, excluded future/out-of-training graphs and repeated weight halving/zeroing. The tests should catch any altered RNG consumption, CDF boundary handling or probability serialization.

Exercise invalid/nonfinite/negative/all-zero weights, insufficient capacity, existing workspace refusal and failure during neighborhood construction after at least one draw. Assert retained intent/failed evidence, no false completion, closed mappings and no implicit reopen. Default-call compatibility must be demonstrated alongside mapped behavior. If a temporary-size claim is made, a targeted allocation/serialization contract check is more informative than a test merely observing the number of .bin files.

These synthetic checks are ordinary engineering. They do not authorize real graph sampling or registered feature-pipeline integration. Opt-in use in an empirical resource claim requires a prospective pinned workspace policy and allocation review, while retaining completed dictionary/sample identities for exact reuse. Full-fold graph eager residency, oversized neighborhoods, matching capacity and full-model feasibility remain unresolved by this weight-only change.
