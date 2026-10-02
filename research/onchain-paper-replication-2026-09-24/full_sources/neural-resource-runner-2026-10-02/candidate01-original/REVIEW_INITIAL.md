# Independent candidate01 neural runner review

**Changes required.** Three material source defects remain. This review ran no
models/tests, read no retained graph arrays, and made no network call or source
change. All three live source/test files match candidate01 and snapshots/check03
exactly; all36members of SHA256SUMS match. Raw check03 reports22passed1skipped9.01s.
The skip is CUDA availability, not a passing GPU check. Earlier reconstructed
snapshots are labelled correctly and are not pre-run attestations.

## NR1 — fatal causes and checkpoint cleanup can be downgraded

`neural_resource.py:122–126` owns a checkpoint stream through a raw context manager.
A serialization/fsync primary followed by an uncertain stream close can be replaced
by the close error. `neural_resource.py:179–191` catches every BaseException,
including SystemExit and cleanup-fatal sentinels, retains only type/str, discards
notes/causal diagnostics and returns ordinarily. `job.py:271–274` then calls
ResearchRun.fail, which writes failure evidence and returns; it does not rethrow.
Thus the worker marks the run failed, correctly, but fatal termination/cleanup
uncertainty becomes a normal function/process return. No false successful
ResearchRun.finish is alleged.

Required correction: attempt each owned cleanup once; preserve an original fatal
primary and attach cleanup uncertainty, or raise fatal cleanup from an ordinary
primary. Retain failed/remaining-cell evidence best effort, then propagate the
original fatal cause. Failure-record publication must not replace that cause or
skip other independent preservation actions. Add sentinel fatal+close/fsync faults,
SystemExit and allocation/OOM short-circuit cases; retain the full nine-cell
failed/unavailable denominator where storage remains writable. Existing tests
cover ordinary RuntimeError but not these fatal/cleanup boundaries.

## NR2 — public registered producer lacks actual dispatch/guard authority

`produce_registered_neural_resource`, lines144–149, accepts an active ResearchRun
and caller-selected plan_input, but neither it nor registered_plan reads the
original execution_job to require kind=neural_resource and its exact selected
payload. ResearchRun._active/_check_source validate claim/registration/source
closure, not a live owned worker guard. An actual admitted run containing the
required9cells/outputs/plan can therefore call the producer directly and allocate
without this kind/payload or guard. The producer's tests explicitly bypass guard
and source checks; the separate mocked worker test proves guarded dispatch exists,
not that direct producer entry cannot bypass it.

job.worker does check the guard at236–247 and Torch inventory at254. Preserve those
checks and additionally bind producer entry to original run/source/claim and exact
registered dispatch/plan plus live owned guard before mkdir, graph/model allocation
or checkpoint creation. This can be a narrowly validated capability passed by the
worker or an explicit existing guard rejoin. Older census/graph helpers rely on an
outer-wrapper convention, but that convention does not establish this new route's
stated hard-containment precondition. No empirical use of the direct helper is
admitted by its current signature/docstring.

## NR3 — output path containment does not bind the guarded filesystem

`neural_resource.py:148` only checks resolved lexical containment. A nested mount
inside the admitted root can pass while placing all checkpoint outputs on another
device. `job.resource_policy:61–63` only requires the admitted root's device among
guarded disk paths, so this path can escape the asserted disk-floor coverage.
The existing census producer explicitly checks the nearest existing output
ancestor's device against root before creation (`census_production.py:48–53`).

Require an original canonical output ancestor/root device covered by the live guard,
reject redirection before allocating, and rejoin the owned output namespace when
publishing/finalizing. Test a simulated device mismatch and redirected ancestor
before any graph/model allocation. A post-write allocated-byte measurement cannot
supply missing guard coverage for the target volume.

## Reviewed behavior retained

The nine dates and requirement IDs are exact and ordered. Plan checks join graph,
configuration and node-order hashes, declared extents, exact seven-day ETH windows
and experiment input windows. Real mapped validation precedes resident graph load;
count-refusal tests use a separate allocation observation. Model digest disallows
silent shrinking. Seed11, same graph object repeated16×28, PCG64 float32(N,32),
linspace prices, alternating labels, one cross-entropy/backward/Adam update and
epoch1/batch0 are preserved. The independent test spells out the unchanged update
and compares model, optimizer and RNG outputs. Roundtrip adds no optimizer step.

The bounded writer refuses checkpoint growth beyond its configured allowance and
retains partial bytes; the state is loaded with weights_only and independently
compared against pre-save state and restored live state. Output allowance reserves
nine maximum checkpoints plus metadata and final accounting includes producer and
lifecycle output directories. These are finite logical/refusal checks, not proofs
of full-size physical sufficiency. Full GAT allocations, checkpoint load copies,
allocator retention, cooperative timeout limits and process-lifetime RSS are
qualified appropriately. The source diff does not change model/GAT architecture,
original config, historical gates, outcomes or admission policy.

No acceptance of empirical execution, physical feasibility, the unadopted budget62
proposal or GPU behavior follows from this review. Corrected source and focused
synthetic evidence require follow-up independent review.
