# Independent initial archived-stage review

Acceptance withheld for two material joins. Source, contract, tests and saved logs were inspected; no checks or remote operations were rerun. Existing source files were not changed.

## AS1 — actual progress identity is not joined to checkpoint intent

`archived_stage.py:43–50` verifies the retained event number and artifact hash, then reconstructs the progress frame's pair ordinal, purpose and numerical identity from the checkpoint intent itself. The visitor at lines97–105 retains only the event number and artifact hash. Unlike the maintained local matching join, no check supplies the actual archived progress frame's pair/purpose/identity to `local.checkpoint`.

An otherwise valid archived event chain for pending pair A can therefore reference a valid checkpoint wrapper for pair B at the same event number. The forty-byte reference digest matches the event's chosen artifact, and the fabricated frame merely repeats B's own intent fields. Checkpoint-file hash verification does not establish that B belongs to A.

Validate `local.checkpoint` against each actual verified visitor frame before retaining its reference, then retain the final hash-pinned tree scan; alternatively retain the additional actual frame fields needed for the final join. Add an internally valid foreign-purpose/identity checkpoint counterexample with recomputed event/archive bindings. Ordinary byte corruption does not exercise this missing relationship.

## AS2 — mutable policy can diverge from its validated hash

`archived_stage.py:69` validates the caller's mutable policy and caches its hash in `capacity`. External leases occur before the same policy is serialized into intent at lines82–86, and later checks continue using that mutable object without an exact pinned-policy check.

A first lease can change only `policy['max_retained_logical_bytes']` to1. This field is not joined again by the log/pair/schedule/stream checks, so the intent can contain an invalid policy while the result at line156 still reports the hash of the previously validated policy. Freeze a deep plain-data policy snapshot before validation and any callbacks, or refuse canonical policy drift at every relevant boundary. Apply consistent snapshot semantics to the archive policy. Test mutation at the first lease, requiring refusal or demonstrable use of the original immutable snapshot throughout.

## Evidence and remaining scope

Raw check01 reports **15 passed in13.26s**; the expanded check02 is now terminal and reports **142 passed in57.46s**. These results do not cover AS1 or AS2. The tests use actual dictionary/MCM/checkpoint engine execution through the fixture's explicit archive-writer substitution and a synthetic filesystem transport. The forced first one-operation advance establishes genuine checkpoint creation; it is a synthetic scheduling device. The wrong-score case creates a separately valid score stream and exercises the purpose/value digest mismatch rather than simple corruption. Final-callback checks cover checkpoint, score, reference, source-mapping and new-read receipt mutation.

The optional visitor receives an immutable frame after that record's chain and transition checks. Its observations remain provisional until complete replay and final verification return successfully; an earlier visitor invocation is not independently a stage admission. Existing callers omit the visitor and preserve their result schema. The reference file gives bounded fixed-size per-checkpoint persistence, not an in-memory population list. Caller/visitor retention, transport staging, concurrent calls, physical quota and RSS remain external.

No current-owner/scientific-source selector, real network, OS guard, checkpoint resume, whole-workflow resource admission or empirical source eviction is established. Checkpoint and score payloads remain local. This review does not broaden the old local stage contract.

Inspected SHA-256:

- archived_stage.py: `041716bd06c46d948b1f5b50fc049ff7bd13985a748fc61e13524ae9b810fe7e`
- archived_pair_log.py: `e01d267c54be8bc786478d5647c90505f75f66dd96e1d57349ba3f76e6259b3f`
- archive_pair_reader.py: `11aedf0b9e5e8698831854952033f36db185c0cb4948f226912731ffc68d16df`
- test_archived_stage.py: `3304edeb5b6f4b9a47b9847bffb27c5348e9424528329c0faa7328d312df1e1a`
- test_archive_event_visitor.py: `442f3c9182c9a864711d375f4eedda721739faed64500df82d249a3ba581f6ef`
- check01.log: `b3af7c4e9ed4db3f7252f6ca1e2ecc772620e403e27dd20c5823e8fba7caa653`
- check02.log: `eff43947a8e88b6c92fba42600010c8ebf29c1f78ba15e0506eca181d53d97b7`
