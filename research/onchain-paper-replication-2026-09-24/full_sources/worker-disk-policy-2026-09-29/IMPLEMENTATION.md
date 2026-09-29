# Explicit worker disk-reserve contract

The user-authorized 10 GiB outer guard was accepted by guarded_run, but the cold
offload worker independently required a hardcoded 20 GiB minimum. Continuation
02 therefore stopped before any network or eviction work. Its failed identity
and diagnostics remain immutable; the earlier broad graph-residency suite passed
because it does not use this worker-admission call.

`assert_guarded_worker` now accepts an explicit `disk_floor_bytes` argument.
The default remains 20 GiB, retaining existing callers' contract. Values below
the authorized 10 GiB floor, booleans and non-integers are rejected before receipt
I/O. A worker with an explicit 10 GiB contract accepts a live guard at or above
that bound. All existing memory reserve, startup, kernel controls, CPU containment,
lease, volume coverage, command identity and wall-time checks remain unchanged.
An empirical caller must still obtain a prospective reviewed registration; this
API does not itself enable any existing empirical gate.

Eleven added synthetic cases establish default refusal, explicit admission,
below-contract refusal, stricter live guard acceptance and invalid arguments.
red01.log records ten expected missing-argument failures and one already-passing
default check. All 39 resource tests pass in green01.log. A tiny, finite real
user-unit probe is prepared to exercise outer guard plus inner worker admission
under the actual 10 GiB policy before another storage transfer is attempted.
The probe completed with child exit 0 and verified cleanup, explicitly reporting
10 GiB disk admission and the unchanged 3 GiB RAM reserve. It had a 60-second
ceiling, 256/192 MiB memory and 3.5 GiB startup requirement; it read no research
data and performed no network I/O. Independent review accepted this narrow
correction based on focused regressions, source delta and actual worker admission.

No broad-suite result is claimed for this subsequent guard edit. The prior
3,390-test graph-residency result remains bound to its original source snapshot.
