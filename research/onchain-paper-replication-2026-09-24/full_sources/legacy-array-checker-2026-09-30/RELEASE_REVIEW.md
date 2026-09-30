# Independent legacy saved-array release review

Decision: release withheld pending LR1. This review does not authorize an array
read or a guard launch. Only this review file was written; no tests, jobs or
verifiers were run and no empirical arrays, raw bodies or SQLite were read.

## LR1 — incomplete actual guard/launcher admission

Location: `release.py:75–88`, `run_verification.py:22`, and
`test_wrapper.py:20–23`.

`live_guard` accepts a running-looking receipt with the expected owner strings,
fresh timestamp, same boot/cgroup and four requested limits, provided its
`monitor_pid` names any existing process. It never reads the exclusive launcher
reservation or compares its PID with that monitor, and neither record binds
the launcher's start ticks. A fresh receipt naming another process therefore
passes this boundary; PID existence alone also cannot distinguish PID reuse.

The check additionally omits the exact worker command, kernel-release receipt,
actual kernel controls, two-CPU affinity, wall limit, runtime/startup reserves
and guarded disk paths. Changing any of those omitted receipt fields does not
affect its decision. Thus a receipt with the same checked identity/limits but a
different command or inadequate reserve/wall/disk contract is accepted by the
array-opening boundary. The normal launcher supplies the correct parameters,
but the child does not independently establish that it is the payload of that
exclusive reserved invocation under the complete promised controls.

Action: bind PID, start ticks and boot in the exclusive reservation and join
them to the live monitor/source/manifest identity before array reads and result
publication. Check the exact worker command, receipt directory/cwd and release
state. Reuse the maintained `assert_guarded_worker` for command, live kernel,
CPU and resource checks where appropriate, then enforce this release's exact
two-CPU and 3/2/0 GiB memory, 3 GiB host reserve, 6 GiB startup reserve,
10 GiB disk and 1800-second contract. Add direct tiny boundary tests for a
foreign monitor, reused monitor PID/start ticks, command mismatch and changed
resource/CPU/kernel admission. The seven saved callback tests patch out both
`source_check` and `live_guard`; their passing results do not cover this defect.
No empirical execution is required to demonstrate or repair it.

## Other reviewed evidence

The concrete sequential payload preserves exclusive started/partial/failure/
complete receipts. It verifies metadata before arrays, checks guard and compact
file signatures around each graph, requires mapping cleanup before publishing
each graph receipt, and rechecks source before overall completion. Launcher
reservation precedes guard startup and survives startup refusal. This is a
one-off existing-output verification, not a producer rerun or future graph-use
admission. The FAILED pilot and complete 109-cell historical denominator remain
qualified as 7 complete/102 unavailable.

All 1,856 current manifest hashes were independently checked, with zero
mismatches. All 1,798 inherited closed bindings remain exact, and all 31 compact
legacy receipts are included. `verification01` was absent at review. Manifest
SHA256 is `d0de0e22b27a2798bc7cf5b531c9932645af5c83b842976571d713537a50f002`.
Source/current-vs-committed enforcement and the separately committed acceptance
record avoid a review/manifest hash cycle; actual future committed-byte checks
remain launch prerequisites.

The earlier metadata test limitation is corrected: ledger mutations propagate
closure/observer hashes and coverage mutations refresh the graph reference;
both tests now assert their intended diagnostics. The saved metadata-green02
report records ten passes and wrapper-green02 records seven passes. The array
and metadata implementation hashes remain the previously reviewed values.

Reviewed source identities:

- `release.py`: `569da72e8bb3b24cee3f0b81fb14d8d3ccf7609160b89a9e85cc546a00acdff1`
- `run_verification.py`: `26b38f5541499d7c84cbc9376c7744ef787507d030b7a6669d7a49be5dfcf7f3`
- `verify_saved.py`: `b023af41f1ae2c5483f1b4173dc1cc29a19693e8a89a3ddd475dfcc3ec2b9453`
- `test_wrapper.py`: `5eae8d5f06a786b78a082d704fb18be02e0cb6669263d520fb09225ff02b88a1`
- `metadata-green02.log`: `7083e17d08802a2a29e73d5c54d913aa29d96779eb48540f5ade93ed6bb578d3`
- `wrapper-green02.log`: `c33aa728dad4639bd3085f4c5424aea68866f9f0f3199050082ec4c03c53f71f`

Not established: empirical saved-array correctness, actual future kernel
controls/resource adequacy, runtime library byte identity beyond the declared
versions/project locks, source-body semantics, financial performance or future
reuse admission. LR1 is a bounded engineering question; no broader empirical
rerun or registration change is needed.
