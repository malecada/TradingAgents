# Minimal future lease subphase measurement seam

Source proposal only; no executable candidate or claimed proof. Main remains frozen.

Retain the existing outer `diagnostic.measure('lease', _lease_body)` in `compact_mcm.py:332–334`. Within `_lease_body`, identify exactly three consecutive spans:

| New phase | Begin | End |
|---|---|---|
| lease_authority | before `_imported(dictionary)` branch at:325 | after original `target_lease(dictionary)` or legacy `stage.lease(); dictionary.lease()` at:328 |
| lease_start_metadata | before `io._root(root,fd)` at:329 | after the existing exact `_read == _json(start)` require at:330 |
| lease_progress | immediately before existing optional `progress.poll(log,stream)` at:331 | immediately after it; absent progress means no call/count |

The authority span includes actual active-stage require, imports and the entire unchanged sampled authority callback. It must not call target_lease again. The metadata span includes the root identity check, fresh start read and current canonical serialization exactly once. The progress span must not invoke poll when progress is None. Legacy stage/dictionary callback order remains unchanged. A failed span records its elapsed duration; subsequent spans do not execute. Preserve original return/exception identity and the existing outer error propagation.

**Do not directly nest three current measure() calls and claim equivalent diagnostic ordering.** `ScoringDiagnostic.measure` rejects names outside DIAGNOSTIC_PHASES (`real_pilot_partial_progress.py:144,224`). Each `_record` may also perform the existing automatic60s refresh (`:233–241`). Nesting it would permit a new checkpoint write/failure between authority and start checks, where the current outer-only timer writes after the complete body. That changes callback/write/failure ordering even if authority code is untouched.

The smallest safe future implementation should register the three finite keys and accumulate subphase durations without intermediate checkpoint publication, then merge them before the original outer `_record` refresh. It must leave the original outer lease counter and its elapsed definition intact and retain its existing write cadence/cap. A private deferred-record path can share current validation/aggregation logic, but requires an explicit focused review because it touches both compact_mcm.py and real_pilot_partial_progress.py. No new public caller argument or scheduler interval is needed.

Required focused metadata-only verification: imported and legacy callback traces; absent/present progress; exceptions at each span; original exception object propagation; no later span after failure; exactly one original outer refresh opportunity; no new intermediate write; fixed key/record count and8192B diagnostic-size stress. Clock time and counters remain observations, not admission or authority. No graphs, MCM execution or full suite is needed for these instrumentation checks.

This proposal supersedes the report's broader future scheduler profiling suggestion as the first concrete step: split the existing actual lease body before considering more invasive live/fingerprint/full attribution. No speculative serializer or compilation optimization should be selected from the aggregate lease mean alone.
