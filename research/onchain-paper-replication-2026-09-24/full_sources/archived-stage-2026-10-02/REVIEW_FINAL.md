# Independent final archived-stage disposition

Accepted for the explicit archived-event/local-checkpoint-and-score content join. AS1 and AS2 from REVIEW_INITIAL.md are resolved. The prior findings, source/test snapshots and failed regressions remain preserved. No tests, network transfers or empirical jobs were rerun by the reviewer.

**AS1:** Each actual chain- and transition-checked progress frame now reaches `local.checkpoint` before its forty-byte reference is written. The checkpoint intent must therefore match the event's actual pair ordinal, purpose and numerical identity, rather than fields reconstructed from that intent. The final reference digest and complete hash-pinned tree scan preserve the previously verified relationship after subsequent callbacks. The new purpose and identity counterexamples build fresh internally valid archived logs referencing original checkpoint bodies, demonstrate successful cold archive verification first, then require the precise checkpoint-intent binding refusal. These reach the missing semantic join rather than merely failing malformed-byte or checksum validation.

**AS2:** Scientific and archive policies are canonicalized into private deep copies before policy validation or any external lease. Both mutation regressions change the original caller-owned dictionaries from the lease; saved intent must retain the original values. The scientific-policy case additionally compares the result's policy hash with the original canonical policy. This establishes snapshot semantics rather than silently adopting changed policy inputs.

The saved review-red01 log reports **4 failed, 13 deselected in8.04s** against preserved stage-check02.py. Corrected check03 reports **146 passed in64.53s**:17 archived-stage cases,2 visitor cases,117 prior archive checks,2 actual matcher/archive integration cases and8 maintained local-stage cases. Source delta, regression construction, exact error assertions and terminal raw log were inspected independently. These timings are fixture evidence, not workload performance measurements.

The accepted verifier joins caller-supplied owner/scope and terminal identities to cold archive replay; enforces checkpoint occurrence counts; validates actual checkpoint intents and state-file trees; retains bounded fixed-size reference records; and, for MCM, replays retained local tails/batches and compares the ordered ordinal/purpose/float64-score digest. After completion publication and the last external lease, it repeats source/new-read metadata, reference, checkpoint and score checks. Duplicate attempts refuse, failures retain the fresh attempt's evidence, and original source artifacts remain read-only. Repeated checkpoint reads and retained references have explicit logical bounds; there is no population-sized in-memory reference list claim.

The event visitor remains optional and existing callers retain their result schema. Frames are immutable, but visitor observations are provisional until the whole replay returns successfully. The visitor/error tests cover order, tuple frames and failure retention; caller callback retention or other side effects are not resource-bounded by this interface.

This is not registered current-owner admission, a scientific-source/calendar proof, automatic old-reader selection, checkpoint resume, real network/OS-guard execution or whole-workflow admission. Source manifest metadata, checkpoint trees and score tails/batches remain local. Expected hashes/policies and source eligibility remain caller authority. The tests use tiny synthetic fixtures, filesystem transport and injected/no-op leases. They do not establish physical quota, process RSS, concurrency safety, remote availability after observation, bulk throughput or authorization to evict empirical source data. Final checks are sampled content observations, not an atomic filesystem snapshot.

Inspected SHA-256:

- archived_stage.py: `9a63d02b6a906dad252b62de3e6ec36a9c3ce3fa06ab703a89508f1775763b9b`
- archived_pair_log.py: `e01d267c54be8bc786478d5647c90505f75f66dd96e1d57349ba3f76e6259b3f`
- archive_pair_reader.py: `11aedf0b9e5e8698831854952033f36db185c0cb4948f226912731ffc68d16df`
- test_archived_stage.py: `99e5d6430907e4b1ad0cbfde95fc142321a1a1117c88055f478a3a8aa71463a6`
- test_archive_event_visitor.py: `442f3c9182c9a864711d375f4eedda721739faed64500df82d249a3ba581f6ef`
- stage-check02.py: `041716bd06c46d948b1f5b50fc049ff7bd13985a748fc61e13524ae9b810fe7e`
- test-check02.py: `3304edeb5b6f4b9a47b9847bffb27c5348e9424528329c0faa7328d312df1e1a`
- review-red01.log: `d437b62fc4dce09a2ced5f3eb146263656e8b24c81a732cbb4bac669dd4b8217`
- check03.log: `148c164f128bfe681150f27a598741315c2e29cf4e8373e1254b9515f50671ed`
- CONTRACT.md: `665ed3d876ec67b97678025ca5e75d96e059eee0cb7db8b438bf11211ebbb414`
