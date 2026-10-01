# Independent compact stage review

Accepted for the stated trusted-reference, frozen-stage receipt contract. No concrete blocking defect was found in the inspected joins. This acceptance does not provide a registered owner, native route selection, arbitrary-history admission or numerical recomputation.

`compact_stage.matching` requires a complete PairLog, exact externally supplied completed/started pair count, no pending pair or unacknowledged bytes, and the selected policy. It independently walks the event chain, accumulates exact ordinal/purpose/float64 completion records, verifies each progress event's deterministic checkpoint directory, intent and wrapper hashes, numerical identity digest, per-pair/global checkpoint count and cumulative reservation. The existing bounded checkpoint reader verifies nested file hashes, extents, inventories and logical cap. Directory count plus successful reads at every event-derived path rejects an extra or omitted checkpoint under the frozen-stage assumption.

For MCM, `stream` verifies the complete batch chain, exact tail destinations, no pending tail bytes, every seal link and stream inventory. Tail float64 bytes must equal batch payload bytes. `inspect` then compares a digest of the same `<Qd32s>` ordinal/score/purpose records from the stream and PairLog. This is a direct join between numerical completion and acknowledged saved score evidence; it does not compute matching again. Dictionary receipt verification has no MCM stream and relies on the caller's trusted workload/count references.

`seal` precomputes receipt bytes, checks content after the prewrite lease, publishes exclusively, then repeats callback-free content inspection after the final external lease and checks exact receipt bytes. Late failure leaves the receipt and prior evidence in place. `verify` uses the same final ordering. Existing receipts cannot be overwritten; the exclusive writer also refuses a dangling receipt symlink even though the earlier existence check alone does not detect one. The final reads are sampled checks, not an atomic snapshot against an independently mutating process.

## Saved evidence and limits

The logs preserve seven missing-module failures in `red01.log` (0.54s), seven fixture-capacity failures in `check01.log` (2.12s), and **seven passes in `check02.log` (4.09s)**. The implementation hash is identical to the preserved check01 source. The corrected fixture explicitly increases its global checkpoint count/byte budget; it does not change numerical source behavior. Positive dictionary and MCM fixtures use the actual engine and actual retained progress checkpoints. Negative cases cover corrupted checkpoint bytes, corrupted batch bytes, extra checkpoint directory, wrong denominator, and a batch mutation during the final owner callback. The latter retains the published receipt while verification refuses it.

One focused evidence gap remains: the `score` case corrupts raw payload bytes without repairing checksums. It establishes refusal by existing content validation but does not directly reach the new log-versus-stream digest comparison. A future targeted test should construct a valid, internally consistent stream with one changed finite score or purpose, retain the original matching terminal, and assert the specific comparison at `compact_stage.py:191`. The source comparison is present and correctly includes ordinal, float64 value and purpose; no such negative execution is claimed here.

The stage root itself is not inventoried by `inspect`; only the matching, checkpoint and stream subtrees are checked. The caller must impose the exclusive stage namespace, conflict markers and selected-stage membership. Owner/scope/terminal references are supplied by that caller, all fixture leases are no-ops, and no actual ResearchRun or current guard is admitted. This component must not be attached to an empty old journal and treated as an old native ownership seal. The policy is per stage; it does not establish cumulative multi-stage physical capacity, RSS, wall-time feasibility, checkpoint resumption or full required-graph coverage. Temporary test artifacts are not claimed as externally recoverable retained data. No empirical arrays, financial results or historical jobs were read or rerun for this review.

## Reviewed identities

| File | SHA-256 |
| --- | --- |
| `compact_stage.py` and preserved `stage-check01.py` | `fe96c774ec784cd2899747db8f9736ff6655a369a0113de001e3b60c782ad83f` |
| `test_compact_stage.py` | `996e6d4b1d9357773c140ccf975ca489216476c4c32208790b0441657d1922c6` |
| `test-before-capacity-fix.py` | `3cc39be71658819e737c4bd30c02b9e09c737ed29bd82c19cb2c033a1df90ddd` |
| `red01.log` | `3c374ea6c2a93bd399dca7a98e49f5239d113ff8c2803473aedff5e9d6dea81b` |
| `check01.log` | `d669db28553bad8b5040015093d1e0945a6395ed25287173fb658eb6c7528949` |
| `check02.log` | `c71f844cffcaaae8b4fbb27627dbabbc9956f0d9eb72865ef6f66f86d928e7bb` |

These identify inspected files and retained logs, not a complete execution-time dependency manifest.
