# Independent archived event replay review

Accepted for bounded replay of trusted completed compact event bytes through an explicit archive-aware reader. No material semantic defect identified within this scope. Source, original local event/stage contracts, test bodies and terminal log were inspected independently; no tests, SSH or numerical jobs were rerun.

The trusted terminal hash binds canonical bounded terminal bytes and the exact start hash. The start joins explicit owner/scope, fixed event format, bounded event/chunk/pair limits and iteration cap. Complete-state validation rejects pending pairs and requires started=completed, exact event accounting (two events per completed pair plus progress), exact number of full/partial chunks and exact byte extent. Replay applies the unchanged `_advance` transition rules to every hash-chained record, then joins final state, chain head and full payload digest. Metadata and returned chunks are immutable bytes, so a final lease does not require reopening a mutable local evidence tree to protect the already-read values. Remote availability after those observations remains unclaimed.

The score digest uses ordered little-endian ordinal/float64-score/purpose records (`<Qd32s`), matching the existing stage join. The checkpoint-reference digest uses event ordinal and referenced artifact SHA (`<Q32s`), also matching that join's byte layout. These hashes bind recorded references and values; they do not inspect actual checkpoint files, recompute matching scores or prove selected scientific policy meanings.

check01.log reports **70 passed in 1.01 seconds**, including 14 new cases and 56 prior archive checks. The positive fixture writes an actual PairLog with two pairs, one progress event, both completion kinds, a full three-event chunk and partial two-event chunk. It archives both chunks, removes only disposable synthetic originals and preservation copies, reads through actual archive_consume, and compares semantic state to prior local verification. Independent struct/hash expectations verify the ordered score and checkpoint-reference digests. Negative cases cover corrupt/swapped/short/mutable/missing/revoked reads, owner/scope/terminal mismatch, failed status, malformed counts and extra terminal fields.

Coverage does not include a zero-event dictionary log, every malformed transition, large/many-chunk scaling, a specifically last-final-lease failure, real remote reads, checkpoint-tree or MCM-stream joins, or current-owner/stage/terminal admission. Shared `_advance` is deliberately reused; the positive local-reader comparison is not an independent numerical oracle. Caller-supplied trusted metadata, bounded transport, scientific source/policy authority and aggregate limits remain prerequisites.

Memory qualification: the loop retains its preceding `raw` binding while the next read_chunk call returns, so direct transient chunk retention can include both old and new chunks, up to roughly 16 MiB at the 8 MiB format cap, plus record/digest/reader scratch. It is constant with event count, but this review does not certify a single-chunk peak or full RSS budget. Reader-side staging, immutable buffers retained by the caller, repeated cache metadata, parallel reads and total I/O remain separate obligations.

The writer and old local reader are unchanged. Only explicitly disposable test files are removed. This component does not grant original-source eviction, archive-backed ownership or empirical execution.

Direct reviewed SHA-256:

- archived_pair_log.py: `707a507570f85a5f95a8a1bf5d22995aff380fae3a3c0395f0bbd0ab0f21d1a2`
- test_archived_pair_log.py: `95b7812f0dc0661ebc8a8e108b969225c4cccbd191aa16e28c6b583f308478e5`
- CONTRACT.md: `d02517328c70cd31f9b7ec4380f56c62edefb4a19111d98f8b29df227485ea98`
- check01.log: `504d4d3829dbba51301411609f05220eb16b8af90c3f7ffb99c38f88656273b2`
