# Candidate02 bounded review corrections

Candidate02 supersedes candidate01 for prospective implementation. Candidate01, its manifest, previous source versions, all raw checks and independent REVIEW_CANDIDATE01 remain unchanged. This correction addresses only ODI1–ODI3 in the independently frozen review, SHA256 c792ef24735ab460c0230c92b2eee18a6ca2adcf86515463f94988bbabe6b3fa. No shared production source, runtime, gate, original data or claim was changed.

ODI1: the original current-Binding configuration pin now includes `run.directory` and all original `Binding._snapshots`, matching the relevant compact_owner binding invariants. Pin comparison occurs before and after Binding.lease. Snapshot rebasing or redirecting the current run directory cannot be hidden by valid historical dictionary bytes.

ODI2: availability uses stdlib datetime parsing, requires explicit zero-offset UTC, and compares datetimes rather than lexical strings. Training start must precede end, original graph start must equal that start, and availability must lie at or after graph start and strictly before cutoff. If original graph end is present, start<graph end<=availability is required. Z and explicit +00:00 are equivalent; nonzero offsets, naive/malformed timestamps, reversed/empty intervals and unavailable-at-cutoff cases reject. Existing original timestamps/config bytes and semantic hashes remain unchanged.

ODI3: the adapter no longer delegates raw reads into score_batches._read's nested cleanup. It retains the actual `_open`, `_root` and signature interfaces, but uses a bounded descriptor-relative read loop with no stream wrapper/ownership transfer. Each acquired child and parent descriptor receives one independent close in reverse acquisition order, including after a prior close fails. First MemoryError/SystemExit or other true fatal object identity is retained; a later first fatal supersedes an ordinary primary with that primary as cause. Ordinary uncertain close becomes a fatal CleanupFailure and cannot be silently ignored. No shared helper was modified. This is a read-only helper, not a new publication writer or relaxation of owner/source checks.

## Evidence and test scope

- `candidate02-red-source.py` equals frozen candidate01 and is retained as the actual failure baseline.
- `red03.log`: changed run-directory and snapshot-rebaseline sentinels failed; nonzero-offset, naive and malformed availability also failed before correction. Inherited duplicate test execution is visible.
- `red04.log`: first body fatal identity, first parent-close fatal identity and ordinary-primary→later-first-fatal identity all failed through the actual old reader/helper path. Timestamp failures also repeated through imported common tests.
- `green04.log`/`green05.log`: the corrected binding and raw-reader suites passed.
- `green06.log`:29 test executions passed in0.044seconds, consisting of12 common metadata cases run twice plus5 binding cases.
- `green07.log`:17 executions passed in0.041seconds, consisting of12 common cases plus5 reader/cleanup cases. Overall these are22 distinct test methods, not46 independent methods. Timestamp and fatal methods additionally contain explicit subcases.

The raw-reader test compiles the exact relevant functions/classes from the current score_batches.py AST, deliberately excluding imports and unrelated numerical code. It calls the actual candidate `_read_registered` function on a tiny temporary `{}` file with controlled read/close injections and verifies every acquired descriptor is closed once. These temporary synthetic files are removed by the test fixture; all test source, failure source snapshots and logs are retained. Descriptor-cleanup tests are not empirical work or actual original-owner proof.

Only the pure validator, fake Binding integration and compiled-helper test profile are stdlib-only. The real public `admit` transitively imports NumPy via matching_owner/score_batches, and real Binding.check inventories Torch. That public path was not imported or executed against a real owner. No empirical arrays, original dictionary bodies, claims, OS resource scopes, model fits or provider connections were used in this correction.

All REPORT01 remaining requirements still apply: independent review, exact original admission/source blob joins, actual original-Binding/resource proof, typed numerical materialization and matching identities, explicit durable imported-owner stage, and nine-cell resource-only MCM dispatch with guarded row-major accounting/storage/closure. Neither candidate is a compact numerical dictionary capability accepted by the production MCM route; no current dictionary stage was fabricated and no empirical grant follows from these tests.
