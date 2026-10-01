# Independent initial compact-matcher review

Acceptance withheld pending the external-lease publication boundaries below. The findings originate from the preserved check02 source (`6edd4ba674a1af688f415d0466b20a3d118fdeec013f0a6147e0537e131b4435`). Parent-owned corrections began during review; this note distinguishes the observed accounting correction from still-open boundaries. No test or numerical job was rerun by the reviewer.

## CM1 — per-pair cumulative reservation omitted (source correction observed)

The original constructor limited checkpoint count to `max_publications`, while `_save` enforced only the global schedule count/byte allowance. `pair.policy_check` establishes capacity for one publication, not every retained snapshot of this pair. Multiple checkpoints could therefore exceed the selected `total_checkpoint_bytes` despite individually fitting `max_checkpoint_bytes`.

The concurrent correction now requires `pair.LIMIT + max_checkpoints * (max_checkpoint_bytes + pair.LIMIT) <= total_checkpoint_bytes`, preserving a conservative original per-pair allowance. It also checks the whole possible new pair's global checkpoint count and `max_checkpoint_bytes + 2*8192` wrapper/state envelope before begin or engine allocation. This addresses CM1 in source. Saved check03 reports seven passes in 0.38 seconds; final acceptance must bind the final source and all subsequent corrections separately.

## CM2 — progress publication invokes callbacks after checkpoint validation

Original `_save` calls `_snapshot` and checks the checkpoint root, then calls `self.log.progress(result)` and returns. PairLog invokes its separately supplied external lease during this call. That callback can change the just-validated checkpoint intent/wrapper or array bytes; the progress event can be acknowledged despite the now-invalid target. PairLog expressly does not validate checkpoint bodies, so it cannot close this boundary.

Required correction: after progress event publication and all external callbacks, check the exact event binding and perform callback-free revalidation of the prebound intent, wrapper, state manifest/hash tree, extents and directory identity/inventory. Preserve an already written progress event and corrupted/partial checkpoint on failure, poison the consumer, and never proceed to another numerical slice or successful callback. Add a targeted late log-lease checkpoint mutation regression.

## CM3 — completion acknowledgement can escape the independent matcher lease

Original `__call__` checks the matcher, then directly returns `self.log.complete(...)`. The latter invokes its own external lease. If that callback revokes the matcher lease, the numerical callback still returns a successful completed score. Constructor accepts distinct leases, so equivalence cannot be assumed.

Required correction: before returning the score, perform the final combined ownership checks and callback-free exact completed-event readback against the original purpose/numerical identity/result. Retain the event if a final check fails, and poison the consumer. Add a regression with a still-valid log lease that revokes the matcher lease during completion publication. Avoid introducing another callback after the final content checks that can invalidate the other side unchecked.

## Supported behavior and evidence scope

The implementation derives the same ordered-pair/numerical-component identity as PairSession, writes durable begin before engine creation, calls unchanged create/advance/score_only methods and closes actual state before completion publication. `CleanupFailure` inherits BaseException; explicit close failure cannot become an ordinary unavailable-cell error. Engine-error cleanup is attempted in finally with primary-failure context retained. A progress checkpoint uses exclusive event-derived storage and bounded metadata/64 KiB file hashing; it is not silently resumed.

The corrected-cap check02 log reports **five passes in 0.39 seconds**. Positive coverage includes exact tiny scalar-reference score parity, actual engine close/drop of dense state, absence of per-completed-pair owner/artifact files, a real progress save and read-only load, event capacity refusal before engine creation and corrupted-array refusal before progress publication. The cleanup test calls real close, then injects a failure; it proves fatal propagation after actual release, not recovery from an actual OS mapping-close failure. Original check01's invalid normalization-cap fixture and missing-module red evidence remain preserved.

Grouping advance calls before optional snapshots is a prospective checkpoint-cadence change, not an empirically admitted continuation policy. Stable ranking can still execute inside advance and is not bounded in wall time or RSS by `max_operations`. Cached numerical source identities rely on the stated source freeze and external admission. The purpose check validates workload and ordered graphs but does not itself derive full MCM/dictionary occurrence membership. Per-pair checkpoint bodies, global logical counters and compact logs do not establish a hard filesystem quota, process-memory bound, historical reuse or full-fold feasibility.

Initial check02 log SHA-256: `e20e9cabe83d8ff6ec03789b00fc2299e7d3b8eed2bf1778e2f16ec1cf733087`. No registration, ledger, numerical source or retained empirical artifact was edited by this reviewer.
