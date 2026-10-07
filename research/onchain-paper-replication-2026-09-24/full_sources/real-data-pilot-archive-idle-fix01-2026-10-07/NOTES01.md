# Full archive revalidation after an idle gap

The candidate changes only archive_control_history.Interval.check's force-boundary
semantics. A forced call can follow idle time, but must run the original complete
callback and finish strictly within max_stale_ms measured from this entry. Only
then are last/observed advanced and callback count reset. The entry timestamp is
not itself a renewed authority certificate. No audit is skipped, no cache is
adopted, and an already failed scheduler cannot be revived.

Ordinary sampled calls retain both original stale-entry refusal and duration
measurement from their previous completed observation. Exactly 60 seconds still
fails the strict less-than check. Clock/policy replacement, backward/nonfinite
clock, callback exceptions and failed audit remain sticky failures. The existing
60-second archive policy is unchanged; the distinct imported-authority scheduler
and its 60-second policy are untouched.

This is a prospective explicit engineering semantic amendment. It must be bound
into the successor's committed source and registration. No historical failure is
reclassified, and actual pilot14's unrecorded age remains unknown. The 317-second
fake-clock scenario is a synthetic gap, not an asserted observed archive age.

## Actual consumers and subsequent path

archive_dispatch.Context._outer(sampled=False) calls its original _full_history
through force=True after unchanged active-claim, configuration, adapter, transport
counter, spent budget, namespace, guard and history-object checks. _full_history
retains inventory, original reservations, output anchor, both complete journals,
diagnostic pins and namespace readbacks. Its _live path uses sampled=True and
therefore cannot refresh an expired sampled observation.

archive_owner_operations reservation _evidence(sampled=False) likewise invokes
its original _full_evidence with force=True. That complete callback retains typed
ledger joins, reservation identity/accounting, directory inventory, original
metadata and per-operation claims. Stage/writer boundaries explicitly invoke
_evidence(); sampled inner checks use _evidence(sampled=not full). Both consumers
receive the same narrow scheduler correction. No transport/claim/counter code or
callback body changes.

## Checks and limitations

The focused probe loads both original and candidate source with the locked local
interpreter. It reproduces original refusal before an idle forced audit, tests
fresh complete revalidation, unchanged sampled refusal, both actual consumers'
extracted original invocation statements, strict callback duration, failure
poisoning, and clock/policy defects. Real tiny Journal controls verify intact
history and rejection of modified chained bytes, extra names and altered counters.
The mutation fixture even repins changed file metadata so chain validation itself
must detect the corrupted body. All fixture files remain under this owned scope.

The consumer invocation probes are extracted literal call statements, not fake
claims or full Context/Owner execution. Their surrounding checks are preserved by
byte-identical source, not purportedly exercised with genuine authority. No
scientific arrays, numerical fit, real provider operation or registered run is
performed. Full resource/throughput capacity and end-to-end completion remain
unproved. The watchdog's 1GiB bound is sampled RSS containment, not a native hard
memory limit; actual run took about0.10s and sampled about21MB.
