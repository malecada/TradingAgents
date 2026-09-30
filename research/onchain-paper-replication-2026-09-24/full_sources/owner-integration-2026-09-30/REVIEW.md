# Independent maintained matching-owner integration review

Initial acceptance withheld for OI1 below. This review concerns maintained ownership/ancestry/death integration and exclusive successor-journal publication. Pair allocation, event payload integrity, numerical consumers, orphan reconciliation and workflow quotas remain outside the implemented scope. No tests, jobs, arrays, raw bodies or SQLite were executed/read; only this review was written.

## OI1 — current guard can expire during ancestry validation before publication

In the inspected `matching_owner.py:163–175`, the lifecycle lock is taken and the current guard is checked before `ancestry.verify`. That call traverses every historical claim/producer route and checks predecessor death twice, including source admission and metadata hashing. The code then reads the parent and publishes a new FeatureJournal without refreshing the current guard immediately before publication.

If the current guard expires or monitor dies during that ancestry check, owner/start/claim metadata are still created. The recursive bind at lines178–179 eventually detects the invalid guard, but only after publication, leaving a partial successor attempt for a prepublication condition that could have been refused. A concrete fixture can wrap otherwise successful `ancestry.verify`, make the current guard assertion fail after its return, then assert that no successor directory was created. The existing expired-guard test only exercises an already-open binding.

Recheck the current active run and guard after ancestry and final parent checks, immediately before FeatureJournal creation. This does not promise an atomic OS lease; it closes the avoidable full-ancestry interval before the first mutation. Preserve the existing rule that failures after actual publication retain partial evidence and prohibit retry/deletion.

## Inspected sound behavior

The initial promotion is exactly the accepted owner/death/ancestry candidates with repository-root/import adaptations only. Preserved promotion hashes match `promotion.json`; the death module is byte-identical. `green01.log` records72 passes in90.675seconds, SHA-256 `532466bfe3b125dcd04ae812804c50fbaa1439e77addf6eb00dd7e5655b0d198`. These are promotion checks, not proof of the later successor extension.

The extension joins current actual ResearchRun, selected schema2 producer, registered policy/backend, exact source closure/numerical anchor and runtime before mutation. The lifecycle lock serializes cooperating journal creation; the recursive postpublication bind occurs after leaving that lock. No nested lifecycle-lock acquisition was identified inside the locked ancestry path. FeatureJournal's exclusive directory creation preserves previous owners and parent hash/owner identity. Claim-publication failures retain the partial journal; duplicate open is refused rather than recreating it.

The new current-journal ancestry mode requires the exact current path, owner, start, registered continuation/death claim and immediate parent/hash, includes only that directory alongside the exact historical chain, and checks inherited owner/workflow identity. Binding lease checks the current guard before and after predecessor ancestry/death verification, then rechecks immutable current metadata and terminal state. Full check additionally rehashes source/input/runtime. Existing first-owner behavior remains separate.

The initially inspected successor fixture uses real temporary Git/ResearchRun/FeatureJournal data, with current kernel guard assertion and predecessor OS death boundaries mocked. Registered policy/resource fault mutations occur before the child claim. Parent-byte preservation, duplicate creation, wrong current/parent ownership, terminal/drift checks and partial-publication failure are covered. The initial15-test successor run was still executing when this review section was written; no passing outcome is assumed for an unfinished log.

Initial successor-extension source SHA-256: `e9cd69ded67b8aa450c235f9c544ccd1101b7be15bbcd9d44e4bf45a0e67af4c` (`matching_owner.py`), `51221522256e3f1babb03512a8dad4d293d12638c4579d4bddcf92945db5e4bc` (`matching_ancestry.py`); successor test SHA-256 `d93d3cb97b05bc2e331c2c67fcbfc750db1677ee4fbf1005b7e20a37b4a6044b`. HEAD at inspection is `f68a9866d4e8b4d5db41d23e4556be25937f8ea0`.

No actual guarded successor, numerical continuation, event/checkpoint replay, orphan reconciliation, pair membership/quota enforcement, financial fit or economic claim is admitted by this inspection. A fresh named broad verification against the final source freeze remains necessary because maintained package source has changed; a historical closed profile cannot substitute for it.
