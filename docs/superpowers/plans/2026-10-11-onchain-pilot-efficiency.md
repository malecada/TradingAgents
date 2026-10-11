# Reliable and efficient real-data replication pilot — implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox syntax. Reuse the already authorized bounded parallel method for independent tasks; root integrates once. Do not create a fresh implementation/reviewer framework per task.

**Goal:** Complete the unchanged representative Ethereum real-data pilot and measure whether full feature generation and joint neural training are practical on this machine.

**Architecture:** Keep the original dictionary → full MCM → trainable MLP → GAT → attention LSTM chain. Repair the genuine serial entry path, add low-cost phase measurements and authenticated progress continuation, then optimize measured costs. Parent-owned deterministic publication and real authority remain separate from optional bounded numerical workers.

**Tech stack:** Pinned Python3.13.13/.venv/lockfile, NumPy/SciPy, PyTorch, Linux systemd/cgroupv2, descriptor-relative durable files, existing typed offload/recovery tools; optional reviewed C or vectorized numeric kernels. No dependency upgrade or paid service is part of this plan.

**Spec:** [Current implementation review](../../../research/onchain-paper-replication-2026-09-24/IMPLEMENTATION_REVIEW_2026-10-11.md), [frozen replication spec](../../../research/onchain-paper-replication-2026-09-24/REPLICATION_SPEC.md), and [original13-task plan](2026-09-24-onchain-paper-replication.md). This plan improves the path to the pilot; it does not replace broader paper coverage.

## Global constraints

- Preserve original32 motifs/512 spent samples, seven WHOLE graphs/415,968,128 cells, method, iteration schedule, chronology, joint gradients and all attempted/unavailable outcomes. No resampling, reclustering, scope reduction or test-outcome tuning.
- C05: CPU float64 `atol=1e-8, rtol=1e-6`. C06: applicable accelerated float32 `atol=1e-5, rtol=1e-4`; tied assignments assessed by feasibility and score. No post-failure tolerance widening.
- Physical16GB RAM and10GiB disk floor. Last actual pilot limits:6GiB memory.max,5GiB memory.high,swap0,two CPUs/200% quota,8h native runtime,2.5GiB host reserve/startup,1GiB file cap,16GiB logical/20GiB allocated writable union. Re-read the exact successor's committed limits before launch; this plan does not amend them.
- Current imported-authority maximum interval is60s. No stale-success cache, grace reset or silent deadline increase. An indivisible over-deadline validation must refuse before empirical execution.
- Never relaunch pilot35 or any closed identity. New continuation/qualification claims retain prior spent accounting and need their own admitted source/config/allowance where applicable.
- Root alone owns live integration, registrations/accounting/STATE/Git, actual external preservation/recovery and ONE native numerical launcher. No source changes during an active numerical job.
- No credentials inspection, paid resources, provider/author contact, trading, deployment or VPS systemd SSH. No deletion before actual complete recovery of the exact declared scope.
- Ordinary reversible engineering uses focused offline checks, not a financial fit registration. Real-data/numerical resource execution follows the existing reviewed admission route. Reuse accepted immutable evidence; review changed seams once.

## Review focus

1. Source, claim or role-body mutation during compound entry must refuse; checking only cached metadata is insufficient. Task1 owns these tests.
2. Disk-full/reporting/formatting failure must preserve the original error and visible terminal uncertainty. Task2 owns these tests.
3. Crash between score/origin/summary/checkpoint commits must never credit an incomplete prefix or rerun a closed parent. Task4 owns these tests.
4. Large or uneven pairs, cache hits and out-of-order worker failures must preserve ordered scientific output and remain within shared physical limits. Task7 owns these tests.
5. Missing/late weekly graphs and repeated graph references must preserve population exclusions and joint gradients through checkpointed/streamed execution. Task8 owns these tests.

## Work order and ownership

Implement Tasks1–2 first. Task3 can proceed independently. Task4 needs the telemetry/entry interfaces from1 but can proceed independently of kernel work. Tasks5–6 select improvements from measurements. Task7 is conditional on sufficient measured memory and useful scaling; it is not required merely to increase CPU utilization. Task8 integrates one coherent bundle and executes the whole pilot. Task9 returns to full financial/paper scope.

Use at most three bounded agents with exclusive files when parallel work helps: entry/telemetry owner (Task1); error-retention or storage owner (2 or3); continuation or kernel owner (4 or6). Never assign two owners to `compact_mcm_batched.py` or the memo/driver simultaneously. Root integrates their independently checked increments. No new review of unchanged numerical bodies is necessary.

All package paths below start at `tradingagents/research/onchain_replication/`. `T` means `tests/research/onchain_replication/`. New tests stay in that named offline directory; inspect their imports/fixture/subprocess boundaries before execution. Existing native tests are reused only for changed paths, not all historical matrices.

Focused test command, with an actual task filename in place of the example:

```bash
env PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
    RUN_ONLINE_TESTS=0 PYTEST_ADDOPTS= \
    .venv/bin/python -B -m pytest -q -p no:cacheprovider --import-mode=importlib \
    tests/research/onchain_replication/test_backend_entry_bundle.py
```

Run the named `scripts/research_runtime.py --check` before numerical qualification. Use `scripts/verify_offline.py` at the coherent integration checkpoint, rather than on every doc edit. Unknown or empirical tests are not admitted by their filename.

## Task0: Close the factual baseline and preserve the failed increment

**Files:** Update study `STATE.md`, short `full_sources/parallel-execution-2026-10-02/COORDINATION.md`, current applicability index `CURRENT_IMPLEMENTATION.md` (new), and a new pilot35 outcome selection using the existing reviewed incremental capture/return tools. Preserve all old evidence bodies.

**Deliverable:** One current source/evidence/resource route; pilot35 permanently FAILED; no invented receipts or reopened claim. Financial/resource milestones remain distinct.

- [ ] Verify the original terminal operation SHA `d30e5e42…`, failed/summary/guard/Root closure joins and current unit/known-PID absence. Carry forward75closed=33COMPLETE42FAILED/highest adopted106; keep28pending+3preclaimreserved and separate paper accounting unchanged.
- [ ] Independently review the actual attempted/unavailable outcome and preserve/recover only its actual new declared increment with the existing tools. Retain postcapture review receipts for the next increment. Do not recopy old stores or claim installed-runtime/raw-store recovery from compact Git availability.
- [ ] Index current installed source, original protocol/model/training identities, applicable gate/resource limits, installed versus source-only accelerators, and F/C evidence. Update `fidelity.json` only with accepted dispositions; historical `completion-interim-*` remains immutable. Label stale protocol resource paragraphs as superseded, not silently rewritten history.

**Acceptance:** A reader can find one executable route and the exact35 terminal disposition without rereading every historical review. Actual35 recovery remains an empirical-successor gate; it need not block independent source engineering.

## Task1: Timed compound backend-input admission

**Files:** Modify `compact_mcm_batched.py` (input constructors and550–553 seam), `tradingagents/research/lifecycle.py` only for an opt-in grouped read, and `original_dictionary.py` only if factoring its reviewed bounded reader is necessary. Create `phase_timing.py`, `T/test_backend_entry_bundle.py`, `T/test_phase_timing.py`.

**Interfaces:**

```python
# phase_timing.py: fixed allowed phase names; scalar counters only.
class PhaseTotals:
    def measure(self, name: str): ...  # context manager; monotonic/process CPU
    def snapshot(self) -> dict: ...    # counts, exclusive wall/CPU, bytes, failures

# lifecycle.py: opt-in, default read_input behavior unchanged.
def read_inputs(self, names: tuple[str, ...], *, max_each_bytes: int,
                max_total_bytes: int) -> dict[str, bytes]: ...
```

`read_inputs` operates only on the genuine admitted run. Names must be unique registered roles, nonempty and at most16; maximum individual body2MiB and combined body4MiB. Under the existing lifecycle lock, check active claim and fresh source/contract at entry; read each exact role through descriptor-relative no-follow bounded bodies; check active/source/contract again before returning. Pin registration/path/hash and stable file identity around each read. Source changes during the transaction fail at exit; role mutations fail immediately at read/readback. This coalesces per-role source admission into two full checks and is an explicit detection-cadence change, not an unchanged-success cache.

The compiled constructors gather normalization source/library/runtime, edge source/adapter/library/runtime/ABI and the shared environment into one distinct roster. Parse from returned immutable bytes, keep all existing role/source/ABI/runtime/hash constraints and invoke genuine lease boundaries before and after. Do not acquire a lease callback recursively while holding a lock that it can reacquire. If an end-to-end compound validation still cannot meet60s, do not launch; profile and reduce the indivisible source-validation operation or specify legitimate smaller complete boundaries.

- [ ] Add clock-injected tests: ten old role admissions at15s each demonstrate stale entry; new grouped admission performs exactly two fresh checks and returns identical registered bytes. Test duplicate/unregistered roles, oversized combined bodies, redirects/hardlinks, source/claim mutation between checks, terminal claim, and role mutation during read. A single61s check must still refuse.
- [ ] Implement the bounded grouped transaction and adapt both input constructors. Keep `read_input` unchanged for other callers. Preserve primary errors and descriptor cleanup. Assert exact three actual outer lease boundaries and original configuration/output/refusal behavior in fixture controls.
- [ ] Add exclusive counters for entry preparation, lifecycle source admission, role-body read/hash, lease full/fingerprint/live, module authentication and backend construction. Use a stack to subtract child time; report totals once per completed batch/terminal, not every cell. Failed entry timing is retained.
- [ ] Run the two focused offline files and the existing imported-authority interval controls touched by this seam. Review the changed contract plus concrete caller together once. Require serial preparation to fit its fixed deadline under bounded engineering qualification before a new real pilot.

**Acceptance:** The known550→553 gap no longer performs ten full admissions. No stale or changed-source success is accepted. Measurements identify each long phase; they are not inferred from a pending marker. Performance is measured with genuine guards, not just stub latency.

## Task2: Preserve primary errors in trainer and evaluator

**Files:** Modify `training.py`, `evaluation.py`; create small `failure_reporting.py`, `T/test_training_failure_retention.py`. Extend existing `T/test_training.py` and `T/test_evaluation.py` only for affected paths.

**Interface:**

```python
def record_failure(primary: BaseException, actions: tuple) -> None:
    # actions are zero-argument reporting/cleanup closures; never claims success.
    for action in actions:
        try:
            action()
        except BaseException as secondary:
            try:
                primary.add_note("secondary failure: " + type(secondary).__name__)
            except BaseException:
                pass

# At the original except block, preserve its traceback and exception identity:
except BaseException as primary:
    record_failure(primary, (publish_fit_failure, publish_cell_failure))
    raise
```

Format the primary reason with a guarded helper: use class name and a fixed `unprintable exception` fallback if `str(primary)` raises. Each existing publication is a separate action. Missing failed publication remains visible uncertainty in outer receipts; never synthesize a terminal or overwrite existing completion.

- [ ] Write a fixture where the first batch raises a distinct exception, its `__str__` raises, both publications fail with ENOSPC, and a checkpoint already exists. Assert the same primary object/traceback escapes; both reporting actions were attempted; checkpoint bytes and prior claim remain unchanged. Also cover successful failure publication and SVM fit/evaluation marker combinations.
- [ ] Implement the helper and replace only affected except blocks. Retain original failed/complete immutability and continuation rules.
- [ ] Run focused error-retention/training/evaluation tests. Commit this independent reliability fix without waiting for matching optimization.

**Acceptance:** Secondary publication/cleanup failure cannot replace the actual numerical/training cause. No claim of guaranteed disk publication when the disk is unavailable.

## Task3: Single-pass storage observation

**Files:** Modify `workflow_storage.py`, `real_pilot_storage.py`; extend `T/test_workflow_storage_guard.py` and create `T/test_pilot_storage_single_pass.py`. Keep `resources.py` native/resource enforcement unchanged except bounded telemetry joins.

**Interface:** Extend `StorageWatch` traversal with an optional fixed set of descendant subdomain counters. `WritableUnion.check()` returns the existing union observation plus independently checked residual totals from that same traversal. Standalone `residual_check()` remains for other callers.

- [ ] Build synthetic union fixtures with nested residual roots, a prospective lifecycle directory, shared lock and historical siblings. Compare all bytes/entries/files/directories against the old algorithm. Test residual violation below the union cap; late birth/rebirth; symlink/hardlink/device/type refusal; directory change; retry/discard; descriptor-close failure; and the same shared5s deadline.
- [ ] Accumulate each nested residual count during one fresh walk; do not skip historical writable scopes, cache mutable stat totals, lower the scan rate or weaken disk/native guards. Explicitly document that two separate observations become one shared traversal, still non-atomic across the live tree.
- [ ] Measure monitor process CPU, walk duration/entry count and publication/fsync time with a finite synthetic tree. Review the changed scan semantics and run both focused storage files.

**Acceptance:** Same original scopes/sublimits and refusal cases, one traversal, bounded telemetry overhead. Do not infer saving from fewer function calls alone.

## Task4: Verified completed-prefix continuation

**Files:** Modify `batched_journal.py`, `batched_numeric_execution.py`, `batched_driver.py`, `compact_mcm_batched.py`, `grouped_offload.py`, `real_pilot_import_caller.py`; create `batched_continuation.py`, `T/test_batched_continuation.py`.

**Interfaces:**

```python
@dataclass(frozen=True)
class CompletedPrefix:
    parent_experiment: str
    workflow_identity: str
    graph_hash: str
    next_ordinal: int
    batches: tuple             # immutable registered summary/hash references
    origin_sha256: str
    score_sha256: str
    numerical_contract_sha256: str
    spent_counters: tuple

def verify_prefix(run, registered_input: str) -> CompletedPrefix: ...
def restore_prefix(prefix: CompletedPrefix, journal, numeric, consumer) -> None: ...
```

Only fully durable complete batches enter a prefix. The parent remains terminal/FAILED; a new reviewed claim with explicit parent/provenance consumes its own allowance and records reuse, not new computation credit. Authenticate source/config/dictionary/graph/order/typed score bodies/origins, all prior operation/checkpoint counters and actual recovery. Restore the next row/motif ordinal and original output placement. Start a fresh memo at a batch boundary; do not invent inaccessible prior cache state. Cache reset is an explicit execution-cost/provenance change and prior spent work is not refunded. Preserve both currently required offload recoveries. Partial checkpoints remain unavailable unless separately qualified for exact state restoration.

- [ ] Create tiny deterministic3-batch fixture outputs and crash before/after each score write, origin write, summary fsync, prefix commit and retirement boundary. Verify only the last fully authenticated batch is reusable. Corrupt one score/origin/summary/config/source/ordinal/hash and require refusal.
- [ ] Implement prefix verification and restoration with existing journal/recovery primitives. Reject active or COMPLETE parents, unregistered prefix input, wrong workflow and missing recovered body. Keep legacy default `resume_supported=false`; select the new route only through an explicit versioned execution policy.
- [ ] Compare uninterrupted serial output with failed-parent + fresh-successor completion: exact scores/order/scientific cell denominators and configuration; imported prefix origins remain byte-identical. A fresh memo can change later computed/reused counts and origin references, so authenticate those new origins rather than asserting uninterrupted-cache identity. Distinguish imported complete cells, newly computed cells, new cache origins and retained partial work; debit actual new work without refunding the parent. Test repeated continuation rejection and post-restore failure/cleanup.
- [ ] Run only focused continuation/affected journal/driver fixtures; combine source/entry review with the next coherent bundle. Publish actual reusable cursor and measured maximum safe-point delay. Do not claim a600s hard bound while one pair or training batch can run longer.

**Acceptance:** Interruption can preserve real completed progress without reopening a spent identity, silently dropping old budgets or crediting partial work. An eight-hour stop no longer implies restarting all completed batches. Before launch, prefix manifests and required remote bodies are genuinely registered/recovered, not inferred from filenames.

## Task5: Profile-guided exact overhead reduction

**Files:** Conditional changes to `imported_authority_lease.py`, `compiled_edge_owner.py`, `batched_numeric_reuse.py`, `matching_immutable_session.py`, `matching_annealing.py`, `compact_mcm_batched.py`; extend focused tests for each actually selected seam. Reuse source-only candidate bodies/reviews by hash where applicable.

**Measurement output:** Extend existing numeric-batch summaries with a bounded `performance` mapping: exclusive wall/CPU by phase, source reads/bytes/compiles, state scans/bytes, cache-key bytes/hits, checkpoint inventory bytes/time, and actual native accepted/refused chunks by finite reason code. Counts may be cumulative; deltas are explicitly labeled. `elapsed_seconds` retains its existing meaning.

- [ ] Record a fixed engineering corpus once, including cache hit/miss, small/large matrices, empty/directed edges, checkpoint save/readback and backend fallback. Check `sum(exclusive_phase_time) <= enclosing_time + timer_resolution`, no negative deltas and identical numerical output with telemetry disabled/enabled. Record raw failures.
- [ ] Choose the largest measured avoidable cost, then apply one of these explicit changes: (a) activation-owned expected-code table retaining every fresh source hash/live code check; (b) immutable row-key framing reused without losing exact collision-byte comparison; (c) allocation-free/chunked finite scans preserving mutable-state validation; or (d) fresh role authentication per borrow with sealed-FD/function checks per advance. Leave unhelpful options unselected.
- [ ] For(a), independently review existing cachecandidate02's compiler/audit-event cadence deviation before adoption. For(d), explicitly register the changed external-file mutation-detection timing; test mutation before/within/after borrow and lease revocation. Neither permits a last-valid authority cache. For(b)/(c), test attempted mutations and byte/finite-state errors rather than assuming public arrays are private.
- [ ] Re-measure complete guarded pairs/batches. Keep a change only if useful enclosing time improves without output/refusal/budget/cleanup regressions. Preserve existing exact path checks; no repeat of every unchanged historic test/review.

**Acceptance:** Demonstrated enclosing saving with actual hit/fallback counters and bounded added measurement cost. Inner-kernel speed or policy selection alone is insufficient.

## Task6: Genuine numerical acceleration under frozen method

**Files:** Modify `matching_annealing.py` only at the selected node/edge/reduction seam; add `matching_numeric_kernel.py` (or one source-owned C implementation) and its policy/adapter; extend `T/test_matching_accelerated.py`, `T/test_matching_reference.py`, add `T/test_numeric_kernel_contract.py`.

**Interface:** A bounded `fill_agreement(out, left, right, start, stop)` fills an existing scratch buffer from readonly contiguous numeric features. It never invokes a Python callback per element or allocates a whole edge-product matrix. The caller retains original direction, half-edge coefficient, temperature schedule, normalization, hardening, operation cursor and checkpoint ownership. GIL release, f32 selection or reduction reassociation is explicitly declared and separately qualified; no automatic GPU selection.

- [ ] Use independent scalar equation fixtures from the frozen corpus plus zero/empty/directed/tied/extreme cases; assert assignment row/column uniqueness and objective at C05. For a separately selected float32 route assert applicable C06 and tie feasibility/score. Retain strict bitwise/error-prefix tests on unchanged exact paths.
- [ ] Implement the largest measured numeric phase with bounded vectorized/C numeric operations. Keep a truthful fallback for ineligible geometry/runtime. Do not substitute approximate summaries, omit cells, change iteration counts or silently recast arithmetic. Authenticate real source/library/runtime/ABI and report actual use.
- [ ] Qualify chunk/operation cursor, boundary failure/checkpoint restore and scratch/file/resource bounds. Compare complete guarded pairs against the reference and prior backend, not just one inner function. Register numerical engineering execution separately when native/process work requires it.
- [ ] Report sustained useful cells/s across the admitted geometry strata, including all authority/extraction/offload costs. If saving is insufficient, state the exact next kernel/compute requirement; do not repeatedly launch the full pilot hoping that a tiny1.16× result scales to100×.

**Acceptance:** Method fidelity and frozen numerical criteria plus a material measured whole-pair saving. Future GPU/distributed implementation is a distinct concrete decision after this evidence, with separate paid-resource authorization if needed.

## Task7: Bounded two-worker matching, only if useful

**Files:** Modify `batched_driver.py`, `batched_numeric_execution.py`, `batched_numeric_reuse.py`, `batched_pair_executor.py`; create `pair_workers.py`, `pair_worker_protocol.py`, `T/test_pair_workers.py`, `T/test_pair_worker_failures.py`. Root owns integration; no concurrent memo/driver editor.

**Interface:** A parent-owned pool permits at most2 distinct in-flight matching tasks. Requests carry ordinal/purpose/config/source hashes, finite dtype/shape/byte framing and local immutable pair buffers; results carry matching output or a bounded checkpoint/error plus operation counters. No arbitrary pickle/unpickle, weekly graph population, credentials, Owner/Binding/ResearchRun or closure-bearing callback crosses IPC.

Workers are persistent spawn/exec processes in the same verified cgroup/CPU mask with sanitized thread/plugin/cache/bytecode environment and parent-death behavior. Parent decides memo hits, deduplicates in-flight keys, commits LRU/origin/result/checkpoint counters in original row-major order, and services genuine authority requests. Use an explicit opt-in interleaved-poll contract: genuine checks at every existing seam, bounded speculative computation, revocation cancels all work. This changes timing but not authority identity; strict globally ordered callbacks are a fallback if the new semantics cannot be admitted.

- [ ] Test a framed fake-worker corpus before numerical workers: out-of-order completions/errors, duplicate keys, invalid length/dtype/source/purpose, blocked IPC, late checkpoint, dead/stuck child, parent death, revocation, cancellation and terminate/kill/reap failures. The earliest ordered error escapes; speculative later work is retained as abandoned work, never published as completed cells.
- [ ] Implement bounded IPC buffers and ordered commitment. Checkpoint requests block with at most one bounded snapshot until their ordinal reaches the parent. Parent wait loops service polls and deadlines; a blocked large read cannot starve the60s lease. Preserve primary errors and actual cleanup uncertainty.
- [ ] Reserve/measure parent residency, two worker runtimes, simultaneous states/scratch, IPC and checkpoint copies under the existing6GiB cap. Large pairs use a predeclared serial fallback before dispatch; no excluded scientific occurrence. A host idle-RAM sample is not sufficient admission. Never replace a worker before its predecessor is reaped.
- [ ] Run one finite authorized serial-versus-two-worker qualification on the same corpus/config: exact or applicable frozen-tolerance outputs, ordered receipts/origins/cache effects, checkpoint cursor, budget and first-error prefix. Measure useful completed cells/s, startup/IPC/offload wall time, each-process CPU, cgroup peak/high/OOM and all descendants.

**Acceptance:** Repeatable enclosing throughput gain under the same shared limits, with all original cells and genuine authority. A proposed1.5× useful gain is an engineering selection threshold, not a scientific criterion; reject/regard as optional if gain is negligible. Never promise2× or infer distributed scaling from this test.

## Task8: One coherent integration and the whole real-data pilot

**Files:** Update concrete policies/roles, `real_pilot_import_caller.py`, `real_pilot_training.py`, `real_pilot_throughput.py`, reservations and ONE new fixed caller/envelope/registration bundle. Reuse existing builders, native guard, incremental capture/return and reviewers. Do not create another generic launcher framework.

- [ ] Freeze the selected changes together. Run focused affected checks, then named offline verification/runtime check once. Independently review combined source/entry/currentness/resource closure, including any continuation or worker policy. Commit/push before empirical execution; generate joins from actual files and immutable anchors rather than repetitive manual identity edits.
- [ ] Retain/review/recover35 and every prerequisite attempted outcome. Prepare/review cumulative same-family allowance if needed without refund/transfer. Bind actual recovered increments, genuine Owner/Binding/ResearchRun, exact installed source/runtime and unused namespace. Freshly verify source, claims, processes, all-descendant limits and storage/RAM eligibility. ONE launcher only.
- [ ] Execute the fresh fixed whole-pilot identity with checkpoints/verified continuation, actual native use/fallback telemetry and milestone timestamps. Require dictionary import → first complete batch → first WHOLE graph → all seven WHOLE MCMs → real batch factory → joint update/checkpoint. Keep the16-example subset/scaler and `paper_financial_fits=0` reporting. Partial cells remain partial; missing targets remain unavailable.
- [ ] For training, verify repeated graph references preserve first-order gradient accumulation and no cross-update detached cache. Test missing/late expected-week rejection, batch membership/scaler lineage, stream/eager output-gradient-Adam parity at frozen tolerance, and checkpoint RNG/model/optimizer/cursor readback. Measure actual forward/backward/update/checkpoint wall/CPU and peak memory, not a synthetic proxy.
- [ ] After actual closure, independently inspect all failed/complete/unavailable cells, original exits/nulls, logs/checkpoints and exact process/cgroup cleanup. Perform actual declared-scope external recovery before any retirement. Report feature rate distributions, maximum safe-point latency, incremental storage/transfer/recovery, training phase timings and capacity uncertainty.

**Acceptance:** The full unchanged pilot milestone is actually completed and preserved, or an exact measured blocker is recorded with reusable verified progress. No accuracy target, arbitrary positive metric or policy-selection shortcut can substitute for completion.

## Task9: Use measured feasibility to enter the original paper experiments

**Files:** Update study `STATE.md`, `CURRENT_IMPLEMENTATION.md`, current acceptance/coverage report, `TABLE_COVERAGE.md`, and original study registrations as actual scope is admitted. Preserve prior ledger/version bodies.

- [ ] Derive a planning range from measured complete-graph geometry, full-pipeline throughput, local/remote storage and real update time. State extrapolation assumptions and remaining full-fold population uncertainty; report what additional CPUs/GPU/RAM would accelerate and which path must support them.
- [ ] Prepare the full-fold initial ETH experiment and matched price/graph comparators with complete common masks, training-only full-fold scaler and all seeds/cells. The pilot's subset scaler and one update are not reused as full-fit completion. Restore100-epoch fitting only under measured capacity and reviewed registration.
- [ ] Continue original Tasks10–13: BTC/history, remaining treatments/comparators, all1,420 fits (45initial included), independent metrics/checkpoint replay and Tables1–6 accounting. Preserve original cohort/vintage blockers and independently executable work; no modern substitute or silent unavailable-cell deletion.

**Acceptance:** Implementation completeness, paper-scope coverage and numerical agreement have separate published dispositions. The pilot establishes resource feasibility; only full admitted experiments can establish paper numerical agreement. Trading/returns are outside this prediction-replication plan.

## Coverage and decision gates

| Requirement | Primary tasks | Evidence that remains separate |
|---|---|---|
| C01/C02 architecture/traceability |0,1,5,6,8 | Original source-silent choices and historical fidelity records. |
| C03/C04/C07/C10 data/dictionary/clocks |0,8,9 | Full asset/history/raw reconciliation and provider vintage. No resampling. |
| C05/C06/C09 matching/acceleration/masks |5,6,7,8 | Finite corpus acceptance is not universal numerical identity. |
| C08 joint trainability |2,8 | Synthetic pass and actual pilot update reported separately. |
| C11/C13/C14 retained outcomes/replay |0,2,4,8,9 | No financial fit completion from a resource update. |
| C12/C17 comparators/tables |9/original Tasks9–12 | All1,420fits/full table denominator and cohort blockers. |
| C15/C16 resources/recovery |0,3,4,7,8 | Each recovered scope explicit; no assumed full-store backup. |
| C18 independent closure |changed-seam review,8,9/original Task13 | This plan itself closes no empirical acceptance criterion. |

Before an expensive empirical retry, serial preparation must be reliable, telemetry useful, selected code qualified, completed progress recoverable, prior outcomes recovered and a fresh source/registration/resource release concrete. A new failure triggers a focused diagnosis/fix/changed-seam qualification, not an immediate blind relaunch.

The full feature denominator implies about688 useful cells/s for seven days or4,814/s for24h. These are illustrative capacity targets, **not promised completion dates or study criteria**. If measured performance remains near6–8cells/s, two workers will not make the whole pilot reasonable; prioritize a genuine numeric kernel and a concrete compute decision. Retain the objective and disclose the requirement rather than reducing graphs, motifs, history or model complexity.

## Self-review of this plan

- All12 review weaknesses map to tasks: W01→1; W02/W09→5; W03→6; W04/W08/W10→4 and3/8; W05→2; W06→8; W07→3; W11→0; W12→9.
- All five review-focus failure classes have named owning tests/tasks. New method names/types are defined above; legacy default routes remain unchanged until explicit selection.
- No fresh numerical run, implementation adoption, budget amendment, tolerance/resource increase or paper-completion claim is made by writing this plan.
- Original13-task/C01–C18 scope remains intact; broader data/fit requirements are routed to9 and the original plan, not silently dropped.
- Implementation should start with Task1 source engineering and Task2/3 independent work after this requested analysis/plan is reviewed. Task0 actual preservation gates the next empirical successor, not all engineering.
