# Independent continuation release review

Decision: **approve one full-panel continuation, conditional on the release
conditions below**. No unresolved material correctness blocker was found in the
reviewed continuation source or preserved seed contract. This is approval of
bounded extraction and its final integrity check, not numerical admission of
the unfinished panel or any financial claim.

The review independently inspected `run.py`, `hash_union.py`, `admission.py`,
`launch.py`, `memory_guard.py`, the charter, runbook, plan, history, draft gate,
preserved outputs and interruption records. The reviewer authored the separate
final checker and its synthetic tests; its union algorithm uses an independent
Python fixture/Counter oracle and quicksort, without importing the producer's
union implementation. This is not a claim of a second independent human or
agent audit of the checker itself.

## Preserved evidence and unchanged accounting

All 54 source files bound by the original full-panel gate still match their
frozen hashes. The numerical plan remains
`19f3716454216afc172aec2939a9908ba3b57921e99249951e1860b995d1d691`.
The continuation plan passes the final checker's independent calendar and
source-reference validation. The complete denominator remains 1,096 dates,
1,221,389,903 transaction rows, 2,193 cells and 1,099 outputs. Expected graph
coverage is 1,094 dates with precisely the original two boundary exclusions.

The 1,623 seed references were independently reconstructed from the 206
published daily outputs and their references, then compared with the plan's
exact member set. Every archived seed size and SHA256 matches: 206 outputs,
593 prefixes, 206 checks, 206 cleanup records and 412 hash receipts, totaling
202,076,864 bytes. Previously completed outputs are republished byte-for-byte;
the July 25 output SHA and prefix anchor the first new day's boundary.
The partial July 26 source scratch and three unpublished prefixes are preserved
outside the execution seed. The earlier collision/admission finding is resolved
by this exact seed selection.

The history preserves all fourteen ancestor claims and terminals; all 28
metadata hashes match actual files. The old run has exactly one failed terminal,
its claim and 206 output hashes agree, and its original resource receipt remains
empty. The continuation is prior 14 / cap 15 under a distinct identity. The
full 2022–2024 interval remains exposed and exploratory. No sample freshness,
financial hypothesis reset, OOM cause or recovered resource peak is asserted.

No trading book is constructed, so fees, funding, return conventions and
capital denominators are outside this continuation. It must not be interpreted
as evidence about returns or strategy viability. Historical `available_at`
remains null; following-day block evidence establishes retrospective numerical
boundaries, not information available at an historical trading decision.

## Execution, resources and failure handling

The runner restores only declared completed-date evidence into a fresh
execution namespace. New extraction is limited to the remaining 890 dates.
Existing original hash metadata must match retained copies before new decode.
The old root owns indices 0–205; the new exclusive root owns indices 206–1095.
The new append capacity subtracts old payload bytes, and allocated-byte
preflight counts both roots. Combined bucket bounds include old bytes and every
new chunk. No global hash body is copied to disk or modified in the old root.

Daily checks precede hash append and durable output publication. Cleanup retains
the original exact-manifest contract. Unexpected daily failures stop later
dates explicitly; missing days and duplicates cannot disappear from the panel
denominator. Global duplicate admission remains all-or-nothing. The producer
uses segment verification and heapsort; independent closure additionally
reconstructs every checked sorted daily stream across both roots and detects
duplicates with a separate bounded quicksort implementation.

Compute and review each receive a distinct transient user service and exclusive
receipt directory. The worker verifies actual containment before claiming:
kernel memory.max 6 GiB, memory.high 4 GiB, swap maximum 512 MiB, boot/unit/command
identity, fresh monitor lease and at most two CPU affinity slots. Startup
requires 9 GiB available host memory; a running host reserve below 3 GiB stops
the unit. Loss of the monitor lease terminates the contained process tree.
This limits the job; it does not guarantee safety against unrelated host loads.

Initial and terminal OOM counters are required. Missing counters are not zero.
The final checker requires both snapshots, their consistency, a successful
child/unit exit, verified cleanup, exact kernel controls and the pinned command.
Unknown or failed guard evidence cannot produce full-panel admission. Disk
checks include the preservation archive, restored artifacts, new lifecycle and
resource records. Receipt-directory ownership and lifecycle claims reject replay.

## Verification and release conditions

The four continuation synthetic test modules passed **106 tests**, including
39 independent final-checker cases. They cover cross-root and within-day
duplicates, missing/altered segments, forged writer hashes against independent
daily digests, combined allocation limits, seed-byte/path changes, unpublished
prefix exclusion, full failed-cell retention, direct unguarded execution,
reserve/lease failures and missing/positive terminal OOM evidence. No real raw
capture or global hash body was decoded or scanned by this release review.

The inspected draft gate has 68 source references, all matching current bytes,
and its existing input references match their files. Final release must:

1. Bind this review, `approval.json`, the new offline verification evidence and
   exact amendment in the completed gate. Recheck complete source/runtime/input,
   ancestry, seed and budget bindings with standard admission.
2. Pass the full named offline target from the pinned runtime. The focused
   synthetic result above is not a substitute for that required check.
3. Commit the complete contract and reviewed source, remotely verify that exact
   commit, prepare the fixed exclusive execution checkout at that source, and
   pass admission there before the sole continuation claim.
4. Immediately verify that no old/new compute or review owner exists and that
   the new hash/artifact/resource namespaces are unused. Confirm actual kernel
   control readback and worker identity after launch.

These are explicit release prerequisites, not an instruction to request fresh
user permission for the already authorized continuation. Any source or criteria
change after these bindings requires an updated review before claim.

## Limits of the conclusion

The actual 890-day continuation, full-population old/new hash uniqueness,
runtime memory behavior under the real workload, exhaustive full-day
star/triangle counts, canonical-chain provenance, historical availability,
price/model performance, financial returns and off-device raw backup remain
untested. No full-panel result or resource-success verdict is granted in advance.
Higher review effort is not requested: the specific remaining correctness task
is execution of the frozen independent union and compact-evidence check after
the admitted continuation reaches a terminal state.
