# Independent sampling-policy implementation review

September 29, 2026. Source-only review of `sampling_policy.py`, `feature_pipeline.py`, `registered_features.py`, `job_payload.py` and the new policy tests. No tests, raw arrays, empirical jobs or network requests were executed by the reviewer. This review is separate from the preceding mapped-sampler implementation acceptance.

## Initial snapshot and required corrections

Initial inspected SHA-256 identities:

- `sampling_policy.py`: `79d1253009e6ba5e8815f82fdf3422113d5559b92e5e0e36bfec84fc2963354d`
- `feature_pipeline.py`: `f6fa95bba24ddf17472d5a982bc274a7d42e9b45139d632d3d6fb6548dbc84e1`
- `registered_features.py`: `ced324d66c9a92382c9ffbe8e3046ba0dae8e22f8a7182fafada2ddab2244361`
- `job_payload.py`: `04d6b25583e4463f54c2647807142320c32dd2a2f56cc87b84fb8cd41331785e`
- `test_sampling_policy.py`: `c504856796dc89c04cb754d9f633b8752f40fa3e0690ad971683e2f8829440bb`

**P2, root-discovered and independently confirmed — workspace containment checked after writes.** In the initial `registered_features.py`, `durable_mkdir(root)` and `FeatureJournal` construction occur before the new sampling root/filesystem check. A pre-existing `research_artifacts/onchain_representations` symlink to an external directory therefore receives workflow directories and journal files before rejection. Move containment and filesystem qualification before any representation directory creation. The announced correction and its saved regression remain to be reviewed; the initial code is not accepted for release.

Two meaningful verification gaps were sent to the implementation owner. The initial failed-parent test proves no resampling/no successor scratch, but does not compare its final full feature binding to uninterrupted computation. Existing job payload integration tests omit `sampling_input`, so they do not exercise successful forwarding of the new option through the real admitted job path. Both should be covered before release rather than inferred from direct-producer tests.

## Assessment of the other implementation paths

The policy reader uses `run.read_input`, rejects extra fields, unsupported modes, nonpositive limits and boolean numeric fields. Exact caller/producer input-name equality prevents omission from silently selecting eager behavior. The producer records the input name and admitted hash in its claim, while the descriptor, sample and feature identities retain their previous scientific inputs.

The early job loop precedes all population producers and checks policies across the entire representation-job set. A malformed later policy prevents execution of an earlier valid producer. Policy names and allowed MCM arm checks are applied before graph loading; completed reuse with a supplied policy is rejected. Default calls carry no sampler kwargs. Existing normalized proposed/diagnostic representation identity remains unchanged.

The feature pipeline branches on a retained `samples` checkpoint before calling the sampler. A newly admitted execution policy can therefore coexist with exact inherited sample bytes without scratch allocation. Existing failed-parent ancestry, active-owner and completed-representation refusal remain in place. The tests deliberately distinguish sample publication from scratch completion: an exception before the samples event leaves empty journal events and a completed scratch receipt, and same-owner reopening is refused. That scratch receipt is not a reconstructible samples checkpoint; no generalized automatic continuation guarantee follows.

The registered producer necessarily accepts graph objects already supplied by its caller, so its own policy checks do not undo prior caller-side graph loading. The job entry point provides the promised early preflight before its own population/graph/numerical work. Resource limits retain their narrow weight-workspace scope; graph residency, matching capacity and total process memory remain outer concerns.

Final corrected-source and saved-result review is pending below. No empirical gate, claim, resource allocation or financial criterion is admitted by this report.

## Corrected source review

The root check now executes inside the lifecycle lock before `durable_mkdir(root)` or `FeatureJournal` construction. It checks resolved containment and the device of the nearest existing ancestor. This closes the pre-existing external-symlink counterexample. The later check remains as defense in depth. This is a cooperative repository-owner boundary, not an atomic defense against a hostile process replacing filesystem components outside the lifecycle lock.

The saved `red03.log` directly reproduces the initial defect: after rejection, the external directory contains the newly written workflow directory instead of remaining empty. Its SHA-256 is `bd66786bd748928e517630be8137db7e855c7fb37eb9c2529be4a29131fb0531`.

The successor test now computes an uninterrupted eager oracle before injecting failure, then requires exact final feature binding and dictionary identity after source-bound continuation under a changed admitted policy. The sampler is replaced by a failing sentinel during continuation, and absence of successor scratch is asserted. The new real job test includes the policy in both admitted producer plan and job payload, runs actual graph loading, registered producer, mapped sampling, dictionary fitting and MCM, and checks the scratch sample identity against the resulting dictionary. Only final `execute_batch` is stubbed; this test does not claim additional model-training parity.

Corrected hashes are `90f43a3f6e1eeac629bab91fe779f62e87372bb35bc40e979ab7940f324dcc75` for `registered_features.py` and `8503d0cdfc860ece039f942060a2062ac87c652c164a87c705b53524390dccac` for `test_sampling_policy.py`. The other three initial hashes remain unchanged. No further blocking production issue was identified in this corrected snapshot. Saved green02 terminal evidence remains pending at this source-review checkpoint.

## Focused verification closure

Saved `green02.log` subsequently closed with **37 passed in 90.60 seconds**, SHA-256 `c932f02cbe8e656ecfa72dc0c610ba59b66405866d59ff14ab326f874ee0493d`. The corrected producer and test source hashes were rechecked and remain exactly as recorded above. The reviewer did not rerun the suite. The initial outside-write finding and two integration-test gaps are closed by the corrected source and retained focused results.

**Accepted for frozen-source named offline verification.** The focused result is not broad-suite closure, actual-data resource feasibility or empirical release. The policy is available to prospectively admitted registrations; no existing gate/configuration is enabled by this review. Full graph residency, oversized-neighborhood/matching capacity, full-model/GPU resource limits and all pending financial fits remain outside the demonstrated scope.

## Terminal named-suite closure and engineering acceptance

Independent saved-evidence review confirms `offline01` ran the pinned `.venv/bin/python -B scripts/verify_offline.py` in the active checkout. The 249-module reviewed profile comprises 185 standard modules and 64 isolated neural modules. Saved output records **2,768 passed plus 97 subtests in 1,082.10 seconds**, then **566 passed and 2 skipped in 628.49 seconds**: **3,334 passed plus 97 subtests, with 2 CUDA-dependent skips** overall. This is the named reviewed profile, not every legacy test or GPU execution.

The guard closed `complete`, child exit 0 and verified cleanup after **1,714.363942 seconds**. Sampled cgroup memory peaked at **1,934,086,144 bytes**, with zero reported memory events and no limit reason. Runner and receipt agree on 3 GiB maximum memory, 2.75 GiB high threshold, zero worker swap allowance, 3 GiB ongoing and 6 GiB startup host reserves, 20 GiB disk floor and a 3,600-second wall limit. Final recorded free disk was 23,358,967,808 bytes. Final/live receipts are byte-identical and child-exit evidence agrees. At review, the recorded cgroup, monitor PID and workload PID are absent. Cleanup stop return code 5 is accompanied by inactive/dead unit state, an empty control-group property and observed cgroup absence.

All **16 frozen source bindings** were freshly hashed and match, including the corrected five source/test identities above. The runner checks those bindings before launching the named target. No source drift, rerun or source modification occurred during this independent review.

- `source-bindings.json` SHA-256: `29c4b0c8814792471d62daf7337341142377fccb12f0e2d626309508c70c6095`
- `offline01/final.json` SHA-256: `1b9a4f92b5368998a46d2622c279d159415f6f94865d3b1f5640272b373a0a10`
- `offline01/child.log` SHA-256: `8a299e7793f4d1bff41181e60690b2a59fd811ac093d95ea4c3c28c4b9d45f12`

**Engineering acceptance is complete at these source identities.** The increment supplies optional, explicitly admitted mapped-sampling policy routing and exact checkpointed-sample continuation; it does not enable an actual empirical registration, amend an allocation, create a claim or complete a financial fit. The measured suite peak is not a cold-cache requirement or a full-size graph/model bound. Worker zero swap does not describe the host, whose ancestor telemetry records existing swap use. Full raw-graph residency, oversized neighborhoods/matching, full-model/GPU feasibility and scientific completion remain open. Initial failed evidence and the publication-gap limitation remain preserved above.
