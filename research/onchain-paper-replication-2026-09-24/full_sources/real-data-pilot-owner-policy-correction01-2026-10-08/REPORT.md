# Resource owner policy schema correction

Candidate only. Main source, registrations, accounting, STATE, Git and scientific stores were not changed. No run, Owner, claim, graph, model or empirical job was constructed. Native20 remains the root-reported failed/spent attempt; this metadata regression provides no scientific progress or capacity proof.

The original `matching_owner.bind` line200 accepts exactly `matching_pair.POLICY_FIELDS`, although resource-only compact execution already admits `checkpoint_layout` and `max_pair_entries_override`. Both appear together in the frozen pair limits. The original exact statements reproduce `ValueError: pair limits differ` in BASELINE_TEST02.txt before any graph access.

The candidate adds `_pair_limits` and calls it at the original validation position. The resource branch calls the existing `compact_policy.pair_policy`, which requires all original fields, refuses unknown fields, enforces integer (not boolean) values in (0, 2**63), and validates exact layout fields/format and bounded integer chunk entries. The legacy branch preserves its exact original schema/type/positive checks, including its historical lack of a 2**63 ceiling. Both retain the existing 65536 edge-chunk maximum. Limits are neither stripped nor mutated at binding. No other production source candidate is required by this trace.

Routing trace:

- `resource_binding.open_first` selects genuine `matching_owner.bind(...,_resource=True)`; no ownership bypass is added.
- `Binding` freezes the complete original limits. `compact_owner.attach` validates compact stage policy and requires exact canonical equality with those bound limits; its original matching config remains unchanged.
- `imported_mcm_identity` binds the original matching configuration and current execution identity, with no duplicate pair-limit whitelist.
- `compact_matcher` already validates the full policy, calls `effective_matching` to copy config and increase only explicit capacity, rejects capacity decreases, preserves original config and policy pins, and binds checkpoint layout into scope. Before lower pair validation it removes only the capacity override using `pair_policy`; checkpoint layout remains explicit. Legacy PairSession schema remains strict and unchanged.

The requested `final20/inputs06/compact_policy.json` is absent. Gate03 experiment `eth-paper-real-data-end-to-end-resource-20261008-20` actually pins `real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json` SHA256 `636d70d7e805be856ae76a40e6e3bd0b5b34531feead8e635b4f64fd7faba786`. The regression reads that file and `final20/templates02/pair_policy01.json`, asserts exact limits equality, 8402640 explicit capacity, and sharded-npy-v1/262144 chunk entries (2MiB payload plus128-byte NPY header). Source/policy hashes are in SOURCE_PINS.json.

Verification: pinned `.venv/bin/python -B .../test_owner_policy.py` passes6 focused tests (CANDIDATE_TEST02.txt), including97 malformed resource variants and56 malformed legacy variants, both optional fields together, each individually, default route, original-limit compatibility, capacity copying/increase/decrease and strict legacy schema refusal. The candidate validator and original require function are AST-compiled directly from their real source; its sole production bind call is checked structurally. Existing compact validators are imported normally. This isolates exact validation from the full owner import and authority construction; it is deliberately not an end-to-end Binding or matching proof. Full-source syntax compilation passed without writing bytecode. The named broad offline profile was not run because this task is a bounded metadata-only candidate without neural imports.

An initial harness attempt imported `matching_owner` wholesale, which transitively imported torch through `feature_journal` and `component_store`; its failed no-neural assertion and original schema errors remain preserved in BASELINE_TEST.txt. No model construction, scientific array access or numerical job occurred. The corrected harness uses the exact AST validator and a hard neural-import blocker; BASELINE_TEST02.txt preserves the intended two schema errors with the no-neural check passing. Later candidate logs are additive. This initial harness limitation is not hidden as a passing result.

Candidate SHA256: `b7cb394c8c65a2d9688a9557c991a2e694b48fc0b3d2317f71a51c857680dfaa`.
Baseline SHA256: `b6c1e2b312eb7132a781835aeb037ffac93d378699fa07852692664235ae47c9`.

Root integration/review and any refreshed registration remain separate. Full scientific execution, complete seven-graph MCM, downstream training and resource feasibility remain unverified.
