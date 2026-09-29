# Independent mapped-sampler implementation review

September 29, 2026. Scope: `sampling_weights.py`, the optional workspace arguments in `neighborhoods.py`, `test_mapped_sampling.py`, and saved focused verification logs. Review used source, diffs and compact receipts only; no tests, raw arrays, financial runs or network requests were executed by the reviewer. Production changes remain parent-owned.

**Disposition: accepted for frozen-source named offline verification, with the two initial findings corrected. This is not empirical release or registered feature-pipeline admission.** No further blocking issue was found in the inspected bounded implementation.

## Preserved initial findings and corrections

1. **P2 — failed flush skipped mapping closure.** Initial `MappedWeights.__exit__` placed `flush`, mapping close and `fsync` in one `try`. A storage flush error left that mapping open while other cleanup continued and a failed receipt was written. A retained caller reference kept the map alive after the context exited. Current `sampling_weights.py:93` independently attempts all three operations for every mapping, records the first cleanup error, retains the primary exception, and never writes success when cleanup fails. The injected flush test directly demonstrates the original open-map assertion failure in `red02.log`; current passing tests assert every map is closed and only failure evidence exists.

2. **P2 — fixed metadata reserve undercounted large allocation blocks.** Initial accounting rounded three data files but added a flat 64 KiB for separate intent, terminal and directory allocations. With 64 KiB allocation blocks these require three additional blocks even for small metadata. Current `sampling_weights.py:26` rejects unknown granularity, separately rounds two 32,769-byte content limits and reserves a directory block. `_write` enforces the 32,768-byte serialized ceiling before opening a receipt. For count 9 and 64 KiB blocks the modeled reservation is 393,216 bytes, correctly refusing a 300,000-byte budget.

The second `red02.log` failure needs qualification: it is an `AttributeError` from the incomplete mocked `statvfs` object when the old code reaches `shutil.disk_usage`, not a clean assertion that an undersized budget was accepted. It establishes that the old path missed the required earlier budget rejection; independent arithmetic supplies the actual counterexample. The corrected test succeeds by rejecting before disk inspection. The original log is retained unchanged.

## Numerical and lifecycle assessment

The mapped branch retains the same training filter, graph ordering, graph hashes, cross-graph offsets, neighborhood construction, zero-then-halve updates, recorded probabilities and manifest identity inputs as the default. Scratch paths and allocation limits do not enter scientific identity. The default retains the original `Generator.choice` call and array arithmetic; unsupported NumPy versions are rejected only when mapped storage is requested.

Mapped draws validate finite nonnegative weights in bounded blocks before consuming RNG state. The full float64 sum, division, cumulative sum, final-CDF division, scalar PCG64 draw and right-side search preserve the operation ordering examined by the earlier feasibility probe. The recorded probability comes from normalized weights, not the second normalization of the CDF. Direct tests compare against actual eager NumPy choice, including exact probability bytes and RNG state, rather than another copy of the mapped algorithm. Five seeds on two weekly graphs compare all records, sample identity, parent identity and sample arrays; additional skewed arrays of 257, 4,097 and 131,071 elements exercise repeated zeroing and overlapping weight updates.

Admission to scratch requires explicit positive integer limits, supported NumPy, an absent destination and sufficient modeled disk capacity above the 20 GiB floor. Exclusive directory/file creation prevents ordinary concurrent reuse. Existing workspaces are refused without changing their bytes. The intent binds ordered training hashes, configuration and seed; files are retained on partial allocation, neighborhood failure and caught interruption. Completion is written only after the manifest has been constructed and normal mapping cleanup succeeds. No reopening or continuation API is introduced.

The reservation is an allocation model for the three weight files, two bounded receipts and one directory block, not a strict bound on filesystem journals, inode/extent metadata, concurrent writers or total process memory. `f_frsize` alone cannot prove arbitrary filesystem overhead. The outer finite guard remains required. A hard kill, parent-directory sync failure, or failure to persist the terminal receipt can leave an unsealed workspace; that is retained failed evidence, not a resumable or successful sample. The tests cover caught interruption, not kernel/OOM termination durability.

## Evidence and remaining scope

Saved `green03.log` reports 38 passed in 29.56 seconds; `green04.log` reports 23 passed in 12.19 seconds. These focused checks are not the named broad offline suite. Log SHA-256 values:

- `red02.log`: `023b4903eb1c75ccb380aaf51a6d4676e83d2c545328a272b2fa2b5c1eff9bf9`
- `green03.log`: `70975dc422906f1197777ec036bd4a66f1327614aae9df6bc69eea60d9cb7445`
- `green04.log`: `666be3ec1261d3e1677e3d909a75cbfa38b93b859d5858f5400f27608d07ff8a`

Current reviewed source SHA-256 values:

- `sampling_weights.py`: `5f1837f93fe0523d7c851654390584fc6c04fb803f2025fd027e74a5da8318d1`
- `neighborhoods.py`: `06d80e3eed2cd49550795cf44e2bdf22c905c82067c473e9e720c5c1e055214a`
- `test_mapped_sampling.py`: `f52303d95c5a5dd83c57c0bfa4bf7d469d8d6c506f35fbd3d1acf0894ce9e1a4`

No large real graph, cold-cache resource requirement, portable total-memory bound, financial outcome or registered pipeline integration was tested. The graph-level parity fixture uses two eligible graphs; future/out-of-training exclusion is supported here by unchanged shared filtering, not a new mapped-specific exclusion fixture. Full graph residency, retained neighborhood objects, oversized neighborhoods and matching/model capacity remain unresolved. Prospective pinned scratch policy and any needed budget allocation amendment remain prerequisites to empirical use; the current 25/52 accounting and all 1,420 pending fits are unchanged by this engineering review.

## Final fixture addendum

The large-allocation-block fixture now mocks `disk_usage.free` independently, so an implementation that incorrectly proceeds beyond the budget check cannot fail merely because the `statvfs` mock lacks unrelated fields. Saved `green05.log` reports 1 passed and 22 deselected in 0.32 seconds, SHA-256 `4ccf5124d4ff475ac789d6720cc5f039b026f37eb78a1eed74c6882fe525c095`. The final reviewed test hash is `c34fafc9869b7344085c597ae5564ca2be04c8f430619b1756e85cd3ee3dcade`; both production source hashes above remain unchanged. The historical red02 qualification remains applicable. Acceptance for named offline verification is unchanged.

## Terminal offline verification and engineering release

Independent compact closure review inspected the saved command, runner, final/live/child-exit receipts, test log and frozen source bindings. The recorded command is the pinned `.venv/bin/python -B scripts/verify_offline.py` in the active checkout. The log identifies the reviewed 248-module profile: 185 standard modules produced **2,768 passed and 97 subtests passed** in 1,102.18 seconds; 63 isolated neural modules produced **548 passed and 2 skipped** in 390.99 seconds. Total: **3,316 passed plus 97 subtests, with 2 CUDA-dependent skips**. This is the named reviewed profile, not every legacy test or GPU verification.

The guard closed `complete`, child exit 0 and verified cleanup after **1,496.888658 seconds**, with a sampled cgroup-memory peak of **2,678,321,152 bytes** and zero reported memory events. The runner and receipt agree on 3 GiB memory maximum, 2.75 GiB high threshold, zero worker swap allowance, 3 GiB ongoing/6 GiB startup host reserve, 20 GiB disk floor and 3,600-second wall limit. The final disk observation was 28,532,379,648 bytes free. `live.json` is byte-identical to `final.json`; the recorded cgroup is absent at review. Cleanup's stop return code 5 is accompanied by inactive/dead unit properties, empty control group and independently observed cgroup absence. Worker zero swap must not be generalized to the host: ancestor telemetry records existing swap use.

All **eight** source-binding hashes were freshly reconstructed and match, including the two production modules and final test source reviewed above. The runner checks those same bindings before invoking the named suite. No test or workload was rerun during this review.

- `source-bindings.json` SHA-256: `0c200fc47b1db120c565bf86793d797321929d35544bea178c3de5c0d1abf15c`
- `offline01/final.json` SHA-256: `5ba7ead78e0c84855a6ed06918bb72a39747172bbaceae52a5cf3f4c028b3fab`
- `offline01/child.log` SHA-256: `b97452270ad755f7493221148044fda6d472030358f2fb4fc0978fbc63a7e8a7`

**Engineering release accepted for this optional component at the pinned source identities.** Both initial findings remain closed and broad verification is now terminal. The measured peak is a sampled suite observation, not a cold-cache requirement or a full-size sampler bound. Registered feature-pipeline policy remains disabled; no empirical claim or allocation is admitted by this result. Raw graph residency, oversized-neighborhood/matching capacity, GPU behavior and full-model resource feasibility remain open. Scientific fits and completion criteria are not closed by this engineering acceptance.
