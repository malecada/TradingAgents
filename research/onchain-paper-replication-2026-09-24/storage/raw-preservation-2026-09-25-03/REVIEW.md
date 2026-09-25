# Independent continuation03 prelaunch review

Disposition: no blocking correctness finding in the reviewed source or exact
prepared release. One new finite `all-bulk` continuation is cleared after the
root owner freezes a released object binding the reviewed contract, candidate,
this report and supporting receipts, and commits the preparation before launch.
Neither this report nor the prepared candidate is an execution receipt.

Reviewed identities:

- Contract SHA256: `9541dbc4e3dadd203cbd17aaad12c4b8f9e6612383583cabf07f680e3b767464`.
- Transfer script SHA256: `217671b9199c3d8f0abbe956c8cccfacfafbe3e09a569d8a4a993940db08860f`.
- Candidate SHA256: `cf0809e87c0ad8a03a04d1bdc7ae3143f83770fff1fe14394da8543eb3114c91`.
- Reconciliation SHA256: `6c90d818e5d7d7faba373aac0a51c0db443f07adf77bea808337829c92148a7b`.

The operative AGENTS instructions, current study state and root review brief were
read. Review compared actual03 source with immutable02 and inspected the shared
preservation and resource-guard implementations. All contract-bound source/input
hashes matched current files. No financial registration, ledger, raw file or
previous attempt was modified.

Independent reconstruction from the frozen compressed metadata inventory found
59,083 unique resolved paths /103,524,489,043 raw bytes. All195 batches form an
exact contiguous partition; their sizes/member limits and byte totals agree with
the inventory. The03 plan equals02's preserved plan. Thirteen phase ranges cover
indices1 through194 exactly once, with no gaps, overlap or index0. The remaining
58,934 files /103,007,197,692 bytes therefore exclude the149-file pilot correctly.

The reused pilot complete receipt, guard, per-batch receipt and manifest hashes
were checked directly. All149 manifest rows, numeric member names and byte counts
match the first149 inventory rows; recovered manifest and completion marker bytes
match their originals. The recorded archive identity is
`a7f3cacdb3f4f3cdb55262dd97b1b9b9da4f1ab57d5c6ce3f28825b53d718568`.
The root's fresh read-only remote digest receipt has this same identity and
returncode0. The earlier independently downloaded/member-verified archive review
is reused; this review did not repeat a large archive read or remote download.

Both failed predecessor identities remain terminal. The current boot identity
was independently read and differs from each preserved guard's boot; all three
old cgroup paths are absent and their cleanup receipts agree. Bulk02 has no
release, worker intent or batch directory, and its retained child receipt states
exit125 before workload release. Zero prior bulk transfer is supported by the
actual wrapper/guard control flow, not merely an author's completion summary.
The prelaunch host receipt reports11,194,249,216 available bytes and no matching
backup process. These are point observations; each new phase rechecks resources.

The new controller uses a nonblocking process lock and exclusive controller,
phase and batch directories. Its CLI rejects a pilot mode, and every worker
requires the guard and exact source/input/release checks. Failed uploads are not
retried. Remote directories are exclusive; previously completed or partial
objects cannot be silently reused. Originals remain read-only; only generated
local tar copies are removed after archive, every member and completion-marker
verification. Failure and cleanup evidence remain under the attempted identity.

The256/192MiB cgroup caps, zero swap,4GiB startup and3GiB runtime reserves,
20GiB disk floor and2-CPU affinity remain in the executed guard path. One
512MiB-raw bundle is processed at a time; fixed batch/member limits keep its two
generated archive copies below2GiB. The guard uses the smaller of8h and remaining
48h controller time, with its wall checks and child-death cleanup intact. Stop
and cleanup can extend measured elapsed time slightly past a trigger deadline;
48h is the enforced execution boundary, not a real-time scheduling guarantee.

Per-phase payload reservations sum243GiB, below the245GiB03 ceiling. Every upload
reserves its exact file size before invocation; bounded downloads reserve their
entire remote dd upper bound and refuse excess local bytes. SSH protocol overhead
is explicitly excluded. The two prior pilot allocations were each2GiB, so the
249GiB conservative all-attempt ceiling is arithmetically consistent. The sum of
prior actual guard time is776.077722102 seconds; adding172,800 prospective seconds
matches173,576.077722 to the recorded precision. The inherited pilot throughput
reconstruction gives28.690961350 hours,43.036442026 with1.5 margin; the largest
phase projection remains below8h. This is feasibility planning, not a guarantee.

The XML and every source/test binding in verification.json matched:23tests,
zero failures/errors/skips,0.290s XML duration. Test execution was not duplicated.
The eight new tests check valid reuse and corrupt hash/contract/status/cleanup/
exit/batch/file-count refusal. The15 preserved helper tests cover byte identity,
corruption, interrupted transfer, no-relaunch behavior and bounded reception.

Not tested or claimed: completion of any03 transfer; prospective long-duration
throughput or stable host availability; current contents of the remaining raw
files (fresh hashing occurs during admitted packing); present remote recovery of
all59,083 files; graph/MCM/scratch preservation; financial computation, predictive
accuracy, paper-scope coverage or economic validity. Full success requires an
independent combined pilot02/new03 denominator and recovered-byte review after
terminal completion. No higher-effort correctness escalation is indicated.
