# Independent initial archive owner policy review

Acceptance withheld for AOP1 and terminal test evidence. Source, contract and test assertions were inspected without rerunning tests or performing transfers. The current check01 log remains nonterminal at inspection; its dots are not treated as a completed suite.

## AOP1 — selection can become retroactive during its callbacks

`archive_owner_policy.py:109–111` requires an empty actual owner's stage set before `_record`. The latter invokes external owner/guard boundaries at lines54 and87. An otherwise valid callback can start a stage while selection is running. Final `owner.boundary()` and `verify_current()` accept valid existing stages, so selection can return after a stage was created despite the contract that storage selection precedes all stages.

Require empty `owner.stages` and no active stage again, callback-free, after `_record` and immediately before issuing Selection. A regression should use the actual owner to begin a stage from a controlled late boundary and require selection refusal; retain a direct already-started refusal too. This sampled gate does not itself make future selection consumption atomic: the forthcoming mutating adapter still needs the owner's transition serialization and durable finite claims.

## Supported boundaries and arithmetic

The gate requires the actual compact Owner class, its original Binding/run authority and current source/input/runtime/guard checks through owner boundaries. The inherited numerical source closure includes every current package Python module through `job.required_sources`; this is not merely trusting the source_commit string in the returned record. Registered execution job and producer plan select the same archive input, both bound descriptors carry its registered hash, and the policy is read with exact registered-byte verification. Final rechecks join the policy/input/transport identity after the last owner callback. Frozen record values and fresh returned writer-policy dictionaries prevent ordinary result mutation from changing the selection.

The complete required-stage tuple includes dictionary plus every required graph's MCM stage. Each stage conservatively receives the same registered maximum event count. For S stages, E maximum events and V declared stage verifications, remote payload is `S*E*168`; decoded payload allowance is that amount times `3+V`, representing upload, round-trip readback, writer-final replay and declared cold reads. The writer allowance derives its exact maximum chunk count; reader allowance uses `3*chunks+8` metadata units; each stage read additionally reserves40 bytes per permitted checkpoint plus fixed metadata. Workflow accounting sums writer and finite read/reference envelopes over all required stages with control metadata margins. Stage remote prefixes are deterministic hashes of actual owner identity and stage name and fit the writer's filename bound.

These calculations are prospective logical allowances, not measurements or operation meters. The future adapter must reserve every attempted verification/transfer, including failures, before dispatch; this gate does not spend or enforce those future counts. Physical filesystem allocation, protocol framing, transport buffers, live scientific arrays, cumulative concurrent consumers and remaining checkpoint/score/graph storage are outside these archive-envelope amounts.

Current tests use actual registered ResearchRun/Binding/Owner objects with mocked OS guard. They exercise selected-input/descriptor mismatch, underreserved envelopes, changed input, terminal run and endpoint drift, immutable returned policy behavior, distinct required-stage prefixes and absence of new owner/remote entries on selection. They do not yet cover AOP1, actual OS-guard execution, archive writer installation, archived stage owner sealing, current publication/terminal selection or empirical admission. Existing local routes remain unchanged.

Inspected SHA-256:

- archive_owner_policy.py: `7b3c73746d171fb6fafec14409921fcf9d0d46a4c962a2b06520d2141571cf55`
- test_archive_owner_policy.py: `daf265a62467f29a809d9387dcd5223434c2d95140a738b07a55dd312eec73a6`
- CONTRACT.md: `3cc1a3e15c485329312b0076157ea73a014dc7c9b917590e02bb61071d0d3a25`
