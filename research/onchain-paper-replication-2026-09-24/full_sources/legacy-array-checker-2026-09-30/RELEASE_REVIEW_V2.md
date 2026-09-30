# Independent corrected legacy saved-array release review

Decision: conditional acceptance for exactly one fresh `verification01`
existing-output verification under the reviewed finite launcher. LR1 is closed.
No actual array correctness or completed execution is claimed by this release.
The original withheld review and original wrapper/protocol/manifest bytes remain
preserved. Only this review was written; no test, guard or verifier was run and
no empirical array, source body or SQLite database was read.

The corrected `release.py:82` calls maintained `assert_guarded_worker` to check
the exact child command, released state, boot/lease, own cgroup, live kernel
memory controls, CPU affinity/tree, disk-volume coverage and resource bounds.
It then requires the exact 3 GiB maximum/2 GiB high/zero swap, 3 GiB host
reserve/6 GiB startup reserve, 10 GiB disk floor, checkout disk path and
1800-second limit. The durable launcher reservation records PID, start ticks,
boot, source and manifest hash; these join the live monitor's actual non-zombie
process identity. The sequential payload retains the same checks before and
after each graph and before complete publication.

The direct synthetic boundary tests exercise the real boundary, with only
process/kernel surfaces substituted. The saved red02 report retains ten
missing refusals from the old implementation; green01 records seven passes
after correction. The final green02 report records eight passes in 0.017
seconds. An additional matching one-CPU receipt/actual-affinity test asserts
`exactly two CPU IDs required`. The review's interim concern that this case
could pass was retracted after inspection of `resources.py:117`: its existing
`verify_cpu_tree` already requires exactly two IDs. No production change was
needed for that regression.

All 1,870 final current file hashes were independently checked with no
mismatches. All 1,798 inherited closed bindings remain exact; the original
31 compact legacy receipts, preparation, corrected sources and retained
failure/review evidence are bound. The final manifest SHA256 is
`f5dcd478dd159f927e58a2c3798497fa669d4940636fdd7d01df0ea1e2eebd4b`.
`verification01` remained absent. Reviewed source HEAD before the prospective
commit was `697c08d533b5489d035bfc9f495d9d621dcd5c6d`.

Exact release conditions:

- Commit and push the reviewed sources, manifest, this review and an acceptance
  record binding this review hash and the final manifest hash. The launcher
  must use that exact fresh 40-character commit and pass all current/committed
  byte and declared Python 3.13.13/NumPy 2.3.0 checks.
- Immediately before the sole launch, confirm the identity is unused, no other
  replication guard is active or activating, and fresh startup memory/disk
  checks satisfy the reviewed limits. Freeze bound sources and HEAD through
  termination. Any reserved/partial/failed identity remains spent; no retry
  under `verification01` is released.
- Run the two saved graphs sequentially through the reviewed launcher, retain
  all receipts, and independently reconcile completion/failure, partial graph
  summaries, exact monitor/child death and cgroup absence before closure.

The payload and array/metadata implementations retain their previous reviewed
bytes and scope. Exclusive receipt creation preserves earlier partial results;
mapping cleanup precedes publication and the next graph. The previous metadata
denominator/day-order test masking is corrected with propagated references and
specific diagnostics. No outstanding material blocker was found in this
bounded re-review.

Reviewed corrected identities:

- `release.py`: `29c8575656c7d4e15dd08889e8d79a4ffa9e7ff558aa2333b049a1ca073ddc86`
- `run_verification.py`: `07bc2cc2899a8d0c1a14cf9955ff24b2dabe407bb6a6ef50f0da2ae44a10c04b`
- `verify_saved.py`: `b023af41f1ae2c5483f1b4173dc1cc29a19693e8a89a3ddd475dfcc3ec2b9453`
- `test_release.py`: `db85576b6c5bcca0a552bd23c7387eed385fa819f5951d91eccd26ef69a03fbb`
- `release-green02.log`: `96485832097fedaa3b4ae32cb5c1527cb164573c2a086d3250786e0cb224a9c8`
- `VERIFICATION_PROTOCOL.md`: `b87de6a4a1672eef58dfa9e9a34b8707e219d6ffccffb9f87c3c581d580bdaf4`

The original FAILED pilot remains FAILED with all 109 cells retained
(7 complete/102 unavailable). Verification does not create a financial trial,
fit, sample or rebuild, or admit future graph reuse. Source transaction
uniqueness, values, exclusions/provider semantics and financial performance
remain untested. Installed library byte identity beyond the declared versions
and project locks is not asserted. Actual resource sufficiency and saved-array
numerical correctness await the one-off execution and independent closure.
