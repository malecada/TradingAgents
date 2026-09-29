# Independent registered sampling-policy design review

September 29, 2026. Read-only review of the proposed design against the current registered producer, job payload, feature pipeline and journal implementation. No production edits, tests, numerical jobs, raw arrays or network requests were made. This report authorizes no empirical execution or gate amendment.

**Disposition: suitable for bounded implementation and synthetic verification, subject to the following explicit contracts.** Separating an admitted execution policy from scientific representation identity is consistent with the existing exact-reuse and failed-parent ownership model. Final source and evidence review remains necessary.

## Admission and ordering

Require exactly `schema_version`, `mode` and `max_weight_bytes`, with an actual integer schema version 1, mode `mapped`, and a positive actual integer byte limit. Reject booleans as integers, extra fields, unsupported modes and malformed references. Read through `run.read_input` so current bytes must match the admitted hash; do not fall back to a path read or eager mode after a policy error.

The producer plan reference must exactly match the caller/job reference, including omission versus a supplied name. Record the admitted input name and SHA-256 in the immutable producer claim without adding either to the scientific descriptor, sample identity, dictionary identity or feature binding. Registered policy change in a fresh failed-parent successor is an execution change; it does not relax graph population, seed, configuration, required-graph, source or full-ancestry checks.

**Preflight placement matters.** Current `execute_fit_payload` performs `produce_registered_population` calls before its representation preflight loop. Putting policy checks only in that later loop would not support the promise that invalid policies fail before numerical work. Validate every representation job's policy schema, producer/job reference match, operation and allowed arm immediately after checking the admitted job payload, before any population producer, graph loader, feature computation or optimizer is invoked. Preserve the later science/population checks as well. One invalid job must prevent work on earlier valid jobs; do not discover policy errors sequentially after some producers have run.

Only proposed/MCM diagnostic representations may request sampling. Apply the existing normalization consistently: `proposed`, `training_label_permutation` and `mcm_without_gat` share the proposed representation. Reject a supplied sampling policy for non-MCM arms and for completed reuse, rather than silently reading or ignoring it. Pure defaults and existing registrations without the new field must retain behavior.

## Workspace and continuation

Derive the scratch path solely from the exclusively created current `FeatureJournal.directory`, with the fixed child name `sampling-weights`. No caller-selected path, attachment to parent scratch, overwrite or automatic retry is permitted. Creating the actual workspace must remain the sampler's exclusive operation. Keep the existing mapped component's allocation/disk checks and outer resource-guard requirements; the policy byte ceiling describes weight workspace allocation, not graph residency or total process memory.

Pass the optional sampler arguments only on the branch that actually creates samples. When the admitted failed-parent journal provides a complete verified `samples` checkpoint, deserialize and use it without invoking the sampler, probing/reserving scratch capacity, or creating a sampling directory. Recheck policy admission if a new successor declares a policy, but do not reinterpret that unused policy as measured execution. Existing parent ancestry and source/owner checks remain mandatory. Completed journals must follow exact reuse and never become new producer attempts.

**There is a publication boundary to preserve and disclose.** The mapped sampler currently writes `complete.json` on return; `prepare_features` subsequently emits `samples_complete`. A failure while persisting that event can therefore leave a completed scratch receipt but no reconstructible journal sample checkpoint. The scratch receipt contains a sample identity, not the full saved sample objects. It is not sufficient evidence to reconstruct/reuse samples or resume the weights. Preserve both the scratch and failed journal, refuse reopening that workspace, and do not claim that all numerically completed sampling is recoverable or universally avoided on future explicitly admitted work. Exact journal-checkpoint reuse is the supported continuation guarantee. A failure-boundary test should make this distinction concrete.

## Required meaningful verification

- Use an actual synthetic registered proposed/MCM producer with mapped policy, not only mocked kwargs. Compare complete sample/dictionary/feature bindings with the eager oracle under identical science, and verify the claim's policy name/hash and derived scratch location.
- Exercise working-byte hash drift, wrong input names, plan/job disagreement, malformed schema (including bool limits), unsupported arms and reuse. Assert zero calls to population production, graph loading, sampling and fitting where early admission is promised.
- With multiple representation jobs, put an invalid policy after a valid job and assert that no producer starts before the complete policy preflight finishes.
- Create a failed source-bound parent with persisted complete samples, admit the exact successor ancestry, switch execution policy explicitly, and make any sampler invocation fail the test. Verify no successor scratch is allocated and final scientific binding matches uninterrupted production.
- Preserve failed scratch/publication evidence and terminal non-restart behavior. A completed representation reused through the job must not receive a sampling policy or call the sampler.
- Check all three MCM-related arm names or their normalized descriptor path; verify default-call and job forwarding compatibility. Test inputs and expected identities should use the real admission and journal contracts.

The intended increment enables an admitted option in code only. No real gate/configuration is amended here, no empirical capacity is established, and no new resource allowance follows. The family remains 25/52 consumed with the remaining 27 allocated and all 1,420 fits pending. Raw graph residency, oversized neighborhoods, matching capacity, checkpoint/GPU feasibility and broader study completion remain unresolved.
