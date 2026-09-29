# Independent registered graph-residency implementation review

September 29, 2026. Reviewed the new population/policy component, mapped-loader preflight/observer refactor, registered producer, job integration and synthetic test source. No tests, raw arrays, empirical jobs or external requests were executed by the reviewer. This report is the reviewer's sole write; implementation remains parent-owned.

## Initial source identities

- `graph_residency.py`: `59e1e26564eb0011580d56550f59b8cab55a8a7d12bd59d172db5c81f29d6fca`
- `mapped_graph.py`: `2f1062bc9e080e4efc270834edd9782d1538e523cfd5dc5afda9dceaf722e643`
- `registered_features.py`: `a15100e06315434d209684857753a08bd652ad2ecf1709f4823d521a43d7c071`
- `job_payload.py`: `8a75a43d5ddeadbc44250a0f06ac2f80d5a20aaf31dfc3f9aa7333fcc56a37fb`
- `test_graph_residency.py`: `642a0a0ae0199ac81670e0acdcf2a23264785ce68d0c1f8f7ba81aa95082ebdb`

Saved initial `green01.log` reports **57 passed in 56.98 seconds**. The initial code is not accepted until the following provenance finding is resolved.

## P1 — direct-producer lease can relabel foreign mappings

`graph_residency.py:57–91` exposes a constructible/replacable frozen dataclass whose `validate` method trusts its own `manifests` labels. Membership of each array handle in the same object's `_mappings` proves internal consistency, not binding to those manifests.

Concrete counterexample: copy a valid graph store to an unadmitted directory, open that foreign store through `open_graph_population`, then pass `dataclasses.replace(foreign_lease, manifests=admitted_manifests)` to the direct registered producer. Graph objects, open mappings, byte totals and canonical graph hashes are identical, while the substituted labels match the admitted references. Current `validate` accepts every check although the backing paths are foreign. Subsequent scientific hashing does not repair storage provenance: equal logical content is not the same declared input path/manifest. The existing foreign test performs the opposite substitution (valid lease labeled with invalid references), which cannot expose this bypass.

Bind the exact lease/graph/member objects to loader-issued provenance that public construction or dataclass replacement cannot relabel, or independently verify actual mapped filenames/member identities against admitted references. Preserve rejection before descriptor construction or numeric access. Add the inverse-foreign-provenance counterexample as a regression. This is a supported-call-path admission contract, not a demand for security against arbitrary Python memory modification.

## Additional meaningful test gaps

The initial byte/count refusal fixtures set the limit to 1, proving that one graph fails independently. They do not demonstrate rejection when every graph fits individually but the simultaneous population exceeds its aggregate ceiling. Add byte/count thresholds between the largest individual graph and the total population, and a separate stricter `max_graph_payload_bytes` case with a permissive mapped policy. The planned partial-open, unresolved close-failure, source-bound successor and input-drift probes also remain necessary for the associated claims.

## Other source assessment

Policy schema and admitted input-name/hash routing are explicit. The job checks all policies before population assembly, refuses unused reuse policies, and preserves eager defaults. Direct mapped calls are checked before descriptor hashing, and input-only reference resolution does not invent same-run output paths. Shared preflight preserves the mapped loader's member/hash/size/magic checks. Population inspection sums declared file bytes and actual member counts before opening a mapping; the payload ceiling is conjunctive through the smaller cap.

The private mapping observer is notified immediately after registering every map in the loader's cleanup list, including maps opened before graph construction or a failed context entry. The population closes successful graph contexts with ExitStack, marks the lease inactive and checks for any remaining open observed handle. `GraphPopulationCleanupError` is rethrown before the job's generic unavailable-representation handler, so the intended fatal-cleanup route precedes batch execution. The real synthetic job test compares full feature binding and dictionary identity to eager production and observes closed mappings at a stubbed batch boundary; it does not establish new model-training parity.

Source review of these paths found no separate numerical-identity change. Scientific descriptors exclude the policy. File-byte and handle-count ceilings remain distinct from RSS, page-cache, validation, adjacency, neighborhood, matching and model allocations. All graphs can still be mapped simultaneously. Published backing files must remain stable; context lifetime still governs borrowed raw views.

Final acceptance is pending the provenance correction and saved focused closure. No empirical gate, claim, allocation or financial criterion is enabled by this review.

## Corrected ownership and diagnostic safety review

The private live-owner registry now records the exact issued lease instance, original graph tuple, original manifest tuple, original handle tuple and totals. `validate` checks identity against that registry before numeric access; a public constructor or `dataclasses.replace` result has no issued entry and cannot relabel foreign maps. The entry is removed and the lease marked inactive before context cleanup on every exit. This closes the reported P1 under the documented cooperative in-process owner model; it does not claim security against arbitrary mutation of private Python state.

The first probe (`red02.log`) crashed while pytest formatted a failure traceback: NumPy array formatting reached closed mapped buffers through the inherited dataclass representation. It is retained as a diagnostic crash, **not** a clean provenance assertion. The revised safe probe in `red03.log` directly confirms the P1: relabeled foreign maps reached the descriptor-hash sentinel. The same log independently demonstrates the representation defect in an isolated subprocess, returning **-11** when `repr` was called after closing the graph context. The corrected `_MappedGraphSnapshot.__repr__` reads only asset/start metadata, with no array or ID iteration and no new scientific fields. Error reporters can now represent the graph without dereferencing closed mappings. This does not make arbitrary raw-array access after closure valid.

Evidence identities:

- `red02.log`: `16c6d07e64d3f02fd00e41f351b5123a67068f9791c7b76cddb56ab2becdbc1a`
- `red03.log`: `444eb2ff8b123dd71463d922fd8e8cd68fc8d80a7e92e0d529b9bc4f52526504`

The expanded aggregate tests set byte/count ceilings to the largest individual graph while asserting that population totals are larger, and a separate case makes only the legacy payload ceiling restrictive. Each asserts no first mapping. Policy byte drift is rejected before representation claim. Actual job-boundary cleanup probes cover both a completed numerical producer and a partial graph-open failure: deliberately unclosed observed handles cause the fatal cleanup exception and prevent `execute_batch`; the completed journal is preserved, and the partial-open cause is retained. Tests close their injected leaks afterward. These cases directly exercise the distinction from ordinary unavailable representation handling.

Current reviewed identities:

- `graph_residency.py`: `1ded72ad7c25135780a718455b430eafa020e8f3de6ca608b04e005b798609a6`
- `mapped_graph.py`: `c5e93b325599a82bf65e5b31074e9c76a73b25d479ddea7d3ff3687e75f7b197`
- `registered_features.py`: `a15100e06315434d209684857753a08bd652ad2ecf1709f4823d521a43d7c071` (unchanged)
- `job_payload.py`: `b4cb97519fd3435f8594f4fa44f0c0e9bd2110bf346b745ad4855faaa6715f3f`
- `test_graph_residency.py`: `f74a6723fede48998e9a4128ba92a392e7955c18c6cadf6fa49840d9f1c0f50c`

Saved `green02.log` is now terminal with **83 passed in 106.57 seconds**, SHA-256 `947764b33551b17def7142bf67ffba6635c89bbe319ee479578dbd3f7093a824`. No further blocking source issue was found in this corrected snapshot. The announced failed-parent exact no-resampling successor test remains to be reviewed, so this is provisional correction closure rather than final acceptance of the complete verification scope. No tests or jobs were rerun by the reviewer.

## Successor verification and focused acceptance

The extended failure test now creates an uninterrupted eager oracle, retains a failed parent's durable `samples_complete` event, and registers a distinct child owner with that exact failed-journal hash. Its larger mapping-count allowance is admitted through a new policy file rather than modifying the parent's input. The child opens the original graph manifests, makes any sampler invocation fail the test, and requires exact full feature-binding and dictionary identity equality with the uninterrupted oracle after the mapped context closes. The original failed-journal hash is checked unchanged. This directly establishes the claimed checkpointed-sample continuation under an explicit execution-policy change; it is not a new sample or model-training parity claim.

Saved `green03.log` reports **24 passed in 32.22 seconds**, SHA-256 `6d96cfd643fa9f98312a36afa27e4be5770111d0de6ec39613231b184061868b`. Final test SHA-256 is `9e73b6a227f0a36ac740b8cd73c4e96f813132fdae63448730057e350bab3077`. All four production source hashes remain exactly as recorded in the corrected review above. The reviewer inspected source and saved evidence only, without rerunning tests.

**Accepted for frozen-source named offline verification.** The P1 provenance finding, diagnostic representation defect and identified aggregate/continuation test gaps are closed. The red02 diagnostic-crash and red03 clean-regression distinctions remain preserved. This integration supports only admitted immutable input manifests; same-run output loading remains unsupported. Aggregate file bytes and open-array limits do not bound RSS, page cache or validator/adjacency/matching/model allocations. No actual gate/policy is enabled, no empirical resource claim is created, and no financial outcome or full-size feasibility is established by focused acceptance.

## Narrow next-work source assessment — not suite closure

While the named offline suite remains active, reviewed `NEXT_MATCHING.md` at SHA-256 `47fb92152b3277a05c902f5690669c1b1d9babdae4e3b55175a704a31fe98fcb` against the frozen reference/accelerated solvers, dictionary, neighborhood and MCM implementations, `config/dictionary.json`, both matching configurations, the protocol and precision-v2 amendment. No source edits, tests or raw/empirical work were performed. No substantive error was found in the plan's workload arithmetic or current route/capacity/checkpoint assessment.

Independent arithmetic confirms 512×511/2 = **130,816 unordered pairs**, with **261,632 directional scalar-reference solves** for a full unresumed 512-sample dictionary below the 2,048 partition threshold. The graph-size arithmetic is 2,764,221×32 = **88,455,072 scores**, multiplied by four bytes = **353,820,288 float32 output bytes** excluding headers. Neither calculation estimates elapsed time, peak memory or representative-neighborhood size.

Source inspection confirms that dictionary fitting uses the scalar solver twice per pair; accelerated MCM does not alter that route. Pair entry and neighborhood limits remain 4,000,000 and 10,000 respectively. Dictionary checkpoint opportunities follow a completed bidirectional pair, and MCM opportunities follow every motif solve for a center; elapsed-time polling therefore does not guarantee a 600-second maximum between durable checkpoints. Intermediate matching matrices, result retention and complete induced neighborhoods remain relevant costs. Capacity fields participate in the existing sample/dictionary/matching identities, so prospective overrides cannot silently reuse revised labels or old checkpoint identities.

One clarification was sent to the implementation owner before future work: interpret exact score/hardening preservation against the **same backend, device, precision and shape-batching route**. Scalar-to-accelerated fidelity remains governed by the registered tolerances and tied-feasibility policy; accelerated scores/soft outputs round to float32 and GPU index-add is not promised bit-stable. An incremental score consumer must not silently turn grouped batches into another numerical route while claiming exact parity. The active accelerated configuration is `config/matching-stable.json` under `matching-precision-v2.md`; original `config/matching.json` is retained historical evidence and lacks the accepted internal-precision field.

The proposed order—close the active suite, improve bounded consumers, design explicit capacity/checkpoint handling, integrate admitted policies, then review a new resource registration/allocation—is consistent with current boundaries. No future implementation, budget amendment, capacity increase or empirical execution is accepted by this source assessment. Terminal suite review remains pending its exact final receipts.

The owner subsequently applied both fidelity/configuration clarifications. Reinspected `NEXT_MATCHING.md` SHA-256 `9d8cdd2dd01a6140fe80400f395b9637cd23090cb7f768313ff3ef9bdb7039d1` explicitly states same backend/device/precision/shape batching for exact parity, retains scalar/accelerated tolerance and tied-objective qualifications, and links the existing active stable configuration and amendment. **The narrow documentation assessment is closed with no remaining substantive finding.** This does not close the still-active offline suite or authorize the proposed next work's empirical phase.

## Terminal failed offline01 closure — no engineering release

Independent saved-evidence inspection confirms that the pinned `.venv/bin/python -B scripts/verify_offline.py` attempt **failed** after **1,505.371987 seconds** because the guard observed **21,443,002,368 bytes** free against its **21,474,836,480-byte (20 GiB) floor**: a shortfall of **31,834,112 bytes**. `limit_reason` explicitly records `RuntimeError: disk floor breached`. The failed receipt is not a completed suite or a source-test failure verdict; the transient storage writer is not attributed by these receipts. Subsequent recovery of free space cannot retroactively turn the attempt into a pass.

The standard phase has a saved terminal summary of **2,768 passed plus 97 subtests in 1,098.56 seconds**. The 66-module neural phase shows progress beyond the printed 69% marker but **has no terminal summary**. Its dots/skip markers cannot supply a completed pass or skip count. The final guard's child exit code is **null**, not zero, and no combined successful-suite total is asserted.

The sampled cgroup-memory peak was **1,899,073,536 bytes**, with zero reported memory events (including high, max and OOM). The guard reports verified cleanup, stop return code 0, failed/inactive cleanup properties with empty control-group path; at independent review both recorded cgroup and monitor PID **3178481** are absent. The receipt's older `unit_properties` running observation precedes cleanup and does not override its terminal failed phase or current absence. Final/live receipts are byte-identical.

All **132 frozen source bindings** were freshly hashed and match. Evidence SHA-256 values:

- `source-bindings.json`: `6f9ec62bb6b26314d6e7952d2394848bd8e4ad93aa28b4444d09933ca10b1b66`
- `offline01/final.json`: `31f813bf32af7d5c4e9e755884533528811ff10fcc318ac298ba787c091bef06`
- `offline01/child.log`: `3eed2d55b271a3bada2fd89e483b6677004f83a84ffd9f9f2e46467715385313`

**Failed-attempt closure is accepted; broad verification and engineering release remain incomplete.** Prior source/focused-test acceptance and its findings are preserved, but do not substitute for a completed named suite. No rerun, source mutation, empirical admission, resource allocation or fitting was performed by the reviewer. Preserve this terminal identity and partial outputs. Any separately authorized subsequent verification needs fresh storage qualification and distinct retained attempt evidence; this report does not initiate it.

## Prospective offline02 disk-policy successor review

The user explicitly requested lowering the disk limit to 10 gb. The new policy expresses this as **10 GiB = 10,737,418,240 bytes**, consistently with the guard's existing binary units. It applies to subsequent jobs; it does not alter the already failed offline01 result or the separately active cold-offload job's frozen 20 GiB floor. Empirical successors must still bind their allowance through prospective registration. Retention, restoration and immutable-attempt requirements are unchanged.

Independently compared the proposed successor binding set: **all 132 original entries are preserved exactly**, with four additions for the disk policy, original binding manifest, failed terminal receipt and new launcher. All **136 file hashes** freshly match. The referenced disk-policy path is included in that hash-bound set. The launcher checks those bytes, requires the predecessor's failed/cleanup-verified terminal with absent cgroup, then targets a new `offline02` receipt directory. That directory does not exist at this review; no successor launch was performed. The predecessor's failed terminal/hash remains unchanged.

The command remains the pinned named offline target. Only its disk floor changes: 3 GiB memory maximum, 2.75 GiB high, zero worker swap, 3 GiB ongoing/6 GiB startup host reserve and 3,600-second wall limit remain identical. The new launcher also requires complete phase, child exit zero and verified cleanup for its own successful exit.

- Disk policy SHA-256: `fa093b7c683687e98b09533fbbd363c8fdca8f91406a80f1169c51fbdf8e44d0`
- `run_offline02.py` SHA-256: `69362cb4ad7ae1610c9d33a756b29f66e34265f07886df6bc6a5766da1e2e932`
- `offline02-bindings.json` SHA-256: `9be9df0cf555e04f12e85e3a1545f46b601fcc5d70f01b48bf181200be394f58`

**Prospective engineering successor accepted under the user's explicit revised reserve**, conditional on the separate offload reaching reviewed terminal closure and fresh launch capacity/ownership checks. The launcher itself only checks offline01 ownership; scheduling after offload closure remains an operator prerequisite, not a claimed built-in cross-job exclusion. A lower disk floor does not attribute the earlier transient writer or guarantee completion. This review launches nothing, changes no active limit, and grants no empirical claim or financial-fit allowance. Broad verification and engineering release remain incomplete until the distinct successor has actual terminal evidence.

## Terminal offline02 closure and final engineering acceptance

Independent saved-evidence review confirms **offline02 complete** on the pinned named target `.venv/bin/python -B scripts/verify_offline.py`. The 251-module reviewed profile contains 185 standard and 66 isolated neural modules. The saved log reports **2,768 passed plus 97 subtests in 1,345.68 seconds**, then **622 passed and 2 skipped in 519.14 seconds**: **3,390 passed plus 97 subtests, with 2 CUDA-dependent skips** overall. This is the reviewed named profile, not all legacy tests or CUDA execution.

The guard closed after **1,868.958187 seconds**, child exit **0**, cleanup verified, no limit reason, sampled cgroup-memory peak **2,657,550,336 bytes**, and zero reported memory events. The unchanged memory controls are 3 GiB maximum, 2.75 GiB high, zero worker swap, 3 GiB ongoing/6 GiB startup host reserve and a 3,600-second wall limit. The successor used its explicitly authorized **10 GiB disk floor**; final recorded free disk was **23,691,902,976 bytes**. Final/live receipts are byte-identical and the child-exit record agrees. Monitor PID **780052**, workload PID and recorded cgroup are absent at independent review. Cleanup stop return code 5 is accompanied by inactive/dead successful unit properties and an empty control-group property, consistent with observed absence.

All **136 frozen bindings** were freshly reconstructed and match. The successor binding manifest is unchanged from prospective review. The original offline01 terminal retains its exact failed hash, and the cold-offload guard retains its exact failed hash; neither history is rewritten by this successful successor. No test, job, raw-array read or remote action was performed by the reviewer.

- `offline02-bindings.json` SHA-256: `9be9df0cf555e04f12e85e3a1545f46b601fcc5d70f01b48bf181200be394f58`
- `offline02/final.json` SHA-256: `797ec7233e63489df1c2974d7eeb752eeaf58b04a1bd62f3686812651ff203dc`
- `offline02/child.log` SHA-256: `8568df24346241ef3e6ab6e29b88762f1602de917afaa6ee9c05f9cd2ebb8588`

**Engineering release accepted for the registered graph-residency increment at the reviewed source identities.** The provenance and diagnostic-safety findings, focused integration checks and named verification are closed. This supports optional hash-admitted, input-only mapped-population integration with aggregate file/count limits and fatal unresolved-cleanup handling. It does not enable any existing empirical policy, grant another research claim, complete a financial fit or establish full-fold RSS, cold-cache, adjacency/matching, full-model or GPU feasibility. The sampled suite peak is an observation, not a portable resource bound. Failed offline01 and failed cold-offload remain separately failed with their evidence preserved; successful offload or reclaimed space is not implied.
