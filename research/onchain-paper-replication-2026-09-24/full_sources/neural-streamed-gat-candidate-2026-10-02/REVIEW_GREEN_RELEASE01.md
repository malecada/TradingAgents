# Independent prospective GREEN source and release review

Disposition: **accepted for one bounded synthetic GREEN invocation after the commit/backup and fresh launch prerequisites below**. This is source/release acceptance, not numerical equivalence, reduced measured storage, full-size RAM capacity, production integration or empirical admission. No numerical library, candidate, oracle or research module was imported and no test/job/admission was run by this reviewer. Only this report was written.

## Exact binding

- `green-release01.json`: `dbb77a314e351eee054bce3b4dfd4a8c8da1b7a54ba5e5e56f43eba1642ceaa9`.
- `candidate01.py`: `0cb820710876a4cb59b94b43f1aa8e3e80429d69c35c40a579067eead3ff91b2`.
- `candidate-manifest01.json`: `d4561bb2dcf371ac3207f1ec8144c20bc84cfdeaa3eec8e2961209b05067ffce`.
- `oracle02.py`: `74a21db805cb1ab8e5f7c42a8d54b5f90400b4d794eebb0fbf7d438b41d655ee`.
- `guard_launcher02.py`: `3f8f49f21274381a4a081bba021eff2d0420517399825702193e758e0c0112db`.
- Accepted closed RED review: `1172f4a6c1065eccb5677a55d433e9755227b62246cd7bb1e7cc5e217f9c0b22`.

All **234 selected files / 1,819,280 bytes** independently match exact SHA256, canonical regular single-link type and the 4 MiB/file and 16 MiB total source limits. The 227 inherited RED pins additionally match Git at `48cff10a92b715a1e15272d05cf697106ef634ff`, the current review HEAD. All 251 installed-distribution metadata versions match; package binary attestation is not implied. All 13 candidate-manifest file/reference entries match size/hash. Four baseline modules match the original `8a295e2391d371193085d00c342f84e06c06fa94` Git blobs.

Whole-object comparison against red-release02 shows only mode, identity, qualification and seven added pins differ. No old source pin, limit, runtime version, oracle/model selection or launcher hash changes. Added pins are candidate source/report/manifest and closed RED result/review/tree manifest/archive. Source/RED bytes are frozen; the qualification explicitly corrects the stronger CANDIDATE01 wording: four full-extent saved records do not independently demonstrate four distinct backing identities because raw identities were not retained.

## Mathematical and source review

`candidate01.py:129–131` computes each node/head dot product before gathering endpoints. Algebraically this is the same source/target attention logit as the baseline feature products and sums. Projection, mask handling, incoming edges, removal/reinsertion of self edges, duplicate-neighbor rejection, stable incoming softmax, dropout shape/order, ELU/identity and head concatenation/mean are preserved. Einsum reduction order/backend workspace can differ; bitwise identity or reduced backend workspace is not assumed.

The custom aggregation at lines 32–65 implements `out[t,h,d] = sum_e:t_e=t attention[e,h] * h[s_e,h,d]`. Its first derivative scatters `attention[e,h] * grad_out[t_e,h,d]` into the source-node gradient and computes each attention gradient as the feature dot product `sum_d grad_out[t_e,h,d] * h[s_e,h,d]`. Those returned gradients join the ordinary attention-logit/projection paths; no learned attention branch or MCM/MLP gradient is detached. Repeated targets and sources accumulate in original contiguous edge order. Private output mutation occurs inside custom forward; block intermediates are recomputed in backward. `save_for_backward` records only h, scalar attention and two endpoint tensors once. Conditional gradient allocation respects `needs_input_grad`; endpoint/control inputs have no gradients. Empty aggregate edges yield zeros. CPU float32/float64 and first-order-only behavior are declared rather than generalized to GPU or higher derivatives.

The positive exact-int block check excludes bool, nonintegers, zero/negative and values above 65,536. Both loops slice at most that bound; individual temporary blocks are bounded, while full node output/gradients, projections, scalar attention, index validation, allocator and library workspaces remain. No whole-process memory bound follows from block size alone. Noncontiguous h/attention can be gathered without an eager whole-tensor contiguous copy; endpoint vectors are required contiguous. Candidate code contains no random call beyond the original constructor and dropout. Independent AST comparison confirms exact constructor equivalence after removing only the new block argument/assignment: original parameter names/shapes, initialization order and RNG calls are unchanged.

The candidate has not changed production GraphAttention or the full model. The oracle injects only the selected layer into the preserved model constructor, leaving pooling/temporal/output logic and checkpoint=false unchanged. Source-level algebra does not replace actual floating-point/gradient checks.

## Frozen oracle and clean-result requirement

The accepted oracle02 remains byte-identical. GREEN must pass the eleven actual RED precursor checks plus the bounded-block/first-order and removed-edge-storage checks, in exact order. These cover directed/self/isolated/masked/zero-edge fixtures, float64, dropout and RNG, duplicate rejection, full 16×28 two-graph model with masking, all model/MCM gradients, Adam state/update and exact serialization/reload; aggregate gradients, gradcheck, two independent central differences and invalid blocks are checked. Float32 and float64 tolerances remain fixed. The finite fixtures do not prove arbitrary graph/dtype/backend equivalence.

Saved-tensor hooks span both forward and backward, retain backing storages to disambiguate allocator reuse and classify actual backing extents, including aliases. GREEN must remove all forbidden/unknown saved extents and reduce deduplicated saved bytes relative to the eager baseline. This deliberately retaining observer is not an uninstrumented process-peak measurement. The retained report omits exact alias identifiers and numerical tensors/difference magnitudes; pass marks establish only that the selected assertions passed, not a independently replayable tensor comparison from report text.

The original RED report was independently checked as failed/red with eleven checks and only the named AssertionError. The accepted raw closure review supplies complete tree/native evidence. Original known RED PIDs and cgroup are now absent; GREEN's distinct `owned/neural-streamed-gat-oracle-green-20261002-01` namespace is absent. RED is permanently closed.

The unchanged guard02 accepts GREEN only with actual worker code0, clean complete guard, successful terminal unit/cleanup states, no unexpected storage/log/cleanup diagnostic, zero initial/final kernel high/max/OOM events, exact native memory/file/time readbacks, matching CPU/child/cgroup identity, storage/disk observations and all thirteen ordered checks. It requires descendant cleanup and re-verifies source/runtime afterward. A merely successful oracle report cannot override a breached native envelope or failed cleanup.

## Sole-invocation prerequisites and limits

Root must first commit the exact selected files, release and review, establish the intended external backup, and verify current HEAD against every selected source pin. The launcher also compares every selected source to its actual launch HEAD before exclusively reserving the unused identity. Numerical imports occur only in the child after native readback. Any failed/reserved GREEN identity remains terminal; no silent source edit, relaunch or threshold adjustment is accepted.

The native envelope stays 1 GiB memory.max=memory.high, zero swap, 120-second systemd unit/guard deadline, two-CPU affinity, 3 GiB host reserve, 4 GiB startup, 10 GiB disk floor, 4 MiB per-file limit and sampled 64 MiB allocated/logical owned-storage stops. CPU quota may be unavailable; affinity is the required enforcement claim. Sampled storage stops are not an aggregate hard filesystem quota, sampled peak is not exact lifetime peak, and unit timeout does not bound all outer verification/retention work. Current admissible resources/readbacks and no duplicate/heavy conflicting invocation must be checked by the sole launcher.

After closure, preserve and independently review the exact GREEN report, guard/events/native controls, all owned files and final outer records, including failed/unavailable outcomes. Passing this tiny engineering run still requires independent production integration and a qualified capacity assessment before any separately registered neural04 experiment. Empirical accounting remains 35 closed under adopted63; budget64 acceptance is prospective only. This review does not test financial leakage, fees/returns, paper numerical agreement or complete asset/history coverage.
