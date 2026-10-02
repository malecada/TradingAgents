# Same-run compact cold handoff — corrected source candidate 02

**Disposition: four reviewed source findings corrected; independent review and genuine guarded integration remain required.** No live source was installed and no numerical import, real scientific authority mint, guard, job, claim, registration, network operation or commit occurred. Candidate01, its withheld review and all source/log bodies remain unchanged.

The selected installation map is `install-map02.json`, containing four complete source snapshots. `install-map01.json`, the earlier patch files and early final logs describe the intermediate version before the additional caller-output fail-stop check. Its exact payload body is retained as `job_payload.py.before-caller-output`. Final patch files use `.final.patch`. `source-ancestry01.json` pins the original candidate manifest, review, installation map and conservative baseline source inventory. That inventory is a source superset, not an execution registration.

## CH1: preserve authenticated originals across publication

The second inventory no longer becomes an unconditional new baseline. `cold_files.extend` captures the combined roots and compares the complete old-root directory and file subsets against the original authenticated snapshot: exact membership, directory identity, file signatures and hashes. The newly added directory must have the original birth inode and exactly the expected filenames. Their hashes must match the exact encoded start and completion bodies supplied by the factory. The original snapshot and expanded snapshot are then checked again. A changed original body or late failed marker is rejected rather than adopted.

`Authority.check` also joins its saved original-root subset to `record['directory_pins']` and `record['file_pins']`; those pins remain active authority, not merely descriptive fields. Existing full versus metadata-only verification qualifications are unchanged. These sampled comparisons do not claim an atomic external filesystem snapshot.

## CH2: retain enclosing fail-stop behavior

An ordinary exception after entry into the selected handoff now raises the actual `CompactProducerError`, chained to its original cause. Selected detached finalization uses the same error route. Fatal identities remain unchanged: `MemoryError`, `RecursionError`, non-Exception interruptions and cleanup uncertainty are not indiscriminately wrapped.

The actual payload generic representation-error handler now fails stopped for the selected cold policy, including ordinary caller/output errors after a successful producer handoff. It cannot publish the selected representation as unavailable and continue to `execute_batch`. Its selected `RecursionError` is re-raised unchanged; otherwise that RuntimeError subclass would still enter the old generic unavailable path despite correct producer handling. The resident/default handler is unchanged when the cold policy is absent. This selected route conservatively fails the enclosing job even if an ordinary selected representation failure occurs before the handoff; it does not silently recover or fall back.

Actual factory failed-marker and transition-release exception fragments were composed with the actual producer/payload exception branches. The first fatal object survives later marker/cleanup failures; ordinary cleanup errors reach the explicit enclosing stop class. Existing partial evidence is retained. This is extracted caller composition with synthetic boundary inputs, not a real lifecycle run or real unavailable-cell ledger.

## CH3: preserve the original monitor PID join

The detached guard now requires `type(live['monitor_pid']) is int` and exact equality to the captured owner monitor PID, in addition to the existing owner identity, resource/watch policy and PID/start-tick liveness joins. Boolean or conflicting live PID values fail. This matches the original Binding guard check.

## CH4: synchronize exclusive directory birth before outputs

`cold_files.durable_birth` opens and validates the parent through a held no-follow directory descriptor, exclusively creates the child relative to that descriptor, captures its inode, fsyncs the parent, and verifies parent/path/child identities before closing and returning. The factory writes no handoff file or registered output before this step succeeds. A parent-open/fsync/readback/close failure stops the selected handoff and preserves any partial exclusive directory; there is no delete/recreate operation. The first actual fatal survives a later close fatal. Ancestor creation still uses the unchanged durable mkdir helper. This guarantees the selected synchronization ordering, not immunity to hardware or filesystem failures beyond fsync semantics.

## Evidence and failures

Final checkout-local `.venv/bin/python -B` verification completed with **36 successful methods** across six scripts. The authoritative logs are `verification03-test_*.log`; `verification03.json` records counts and scope.

- Eleven reviewed-boundary methods execute actual AST fragments with explicit synthetic caller/guard controls and tiny real files. Counterexamples inject a late original failed marker, changed original body, changed new completion body, wrong/boolean monitor PID, ordinary claimed handoff and immediate finalization errors, post-handoff caller output error, and fatal exceptions. The extracted caller includes its real exception branches and `execute_batch` call; successful corrected tests prove that the batch call is not reached. Parent-sync injection uses the actual factory birth/file ordering and proves that no start file exists when the first parent fsync fails.
- Eight cleanup/parity methods compose actual failed-marker and lock-release paths, preserve the first fatal through a parent-sync/close failure, exercise a valid exact snapshot extension and duplicate birth refusal, and compare unchanged archive/stage verifier calls, numeric feature methods and default payload behavior.
- Seventeen inherited file/AST/private-state methods remain passing. The old exact-count static cold-policy test is not rerun because the new selected fail-stop branch deliberately adds another cold-policy conditional. The whole payload AST matches candidate01 after removing exactly the new selected error branch, preserving both original unselected-policy refusals and both finalizations.

The final corrected caller harness run against candidate01, `red04-corrected-caller-harness.log`, has ten expected assertion failures across eleven methods, with no harness exception. `red01.log` retains the first concrete boundary failures. While making the extracted caller fixture more realistic, `red02-final-caller-fixture.log` and `red03-caller-output.log` exposed a missing `json` name in the injected harness globals; those raw failures remain and are not counted as valid production counterexamples. That harness issue was corrected before red04 and final verification. All intermediate logs, baseline source copies, old patches and the superseded payload body remain preserved.

The source and tests establish these narrow file/caller boundaries. They do not execute a genuine published scientific representation, actual guard or native unit, a full archive/stage content check, financial fitting or a genuine detached authority mint. Private-state inherited tests remain explicitly synthetic.

## Preserved method and remaining requirements

The full motif dictionary → MCM → GAT → attention LSTM method and schema-3 scientific binding remain unchanged. Existing resident/default behavior, legacy `native_reuse`, archive-stage verifier, local stage verifier and `_NativeMap` numerical implementation are preserved. No model, optimizer, RNG, dropout, sequence eligibility, batching, checkpoint mathematics, learned-embedding cache, gradient detach or larger resource cap is introduced.

Independent source review must precede integration and exact prospective release. The eventual genuine proof still needs a complete scientific representation/denominator, full source/runtime/input/output and guard joins, weak-reference/ownership release with a deliberately retained external alias, repeated-hash object reuse, gapped and short-final synthetic 16×28 batches, second-batch/live-alias refusal, full forward/backward/optimizer/RNG agreement and bounded retained physical observations. The separate two-target original-import resource fixture is not upgraded to a scientific representation. The earlier 3,823 neural comparisons did not exercise this authority.

No memory saving, allocator/RSS release, real batch membership, capacity recovery from neural04, numerical agreement with the paper or financial accuracy result is claimed. Snapshot/receipt bounds and verification cost still need measured evidence. The paper attempt accounting, adopted budget and pending model fits are unchanged.
