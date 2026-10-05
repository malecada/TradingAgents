# Parent storage scheduling source candidate

The only source changes against the actual final Parent
0534945d070521c4dcfe85adcdfe6fa39e698a2a3101f95756828d3d33069375 are:

```python
 def active_checked():
  parentwatch.check();require(shutil.disk_usage(CAP).free>=10*GIB,'active disk floor')
 def checked():
  watch.check();active_checked()
```

The supervisor receives active_checked in place of checked. The original checked
call remains before spawn. The original cleanup sequence still performs owned
child/native drainage, terminal retention, then checked, on both normal and
exceptional paths. No constant, storage budget, file cap, native predicate,
cleanup/fatal precedence, retry, sleep, process ownership or registration check
changed. A literal inverse proves equality to every original Parent byte.
Candidate parent SHA256:
f57bea4491024486d3a1749a9ce896b88df76ad72067cde556a1a76793b207e3.

This candidate retains the old reserved identity/source/registration literals.
It is a non-release source delta and must not be executed as a Parent. Root owns
any genuinely fresh identity and complete source/input/Parent/recovery binding.
The existing reserved Parent and failed preclaim outcome remain unchanged.

The active Parent checks its own tree and the independent10GiB disk floor.
The source-pinned original native guard performs whole-CAP checks before native
dispatch, before release, in its running loop and at finalization. This removes
the redundant Parent whole-CAP traversal during the native guard's own startup
publication. It neither excludes filenames nor accepts incomplete censuses.
StorageWatch and its fixed three-attempt/five-second behavior are unchanged.

## Focused verification

Main .venv/bin/python -B ran five unittest methods successfully. Tests import only
stdlib and the exact actual StorageWatch/resources metadata modules. The candidate
Parent is parsed, never launched; its exact nested callbacks are compiled in
isolation. No preflight, Admission, Owner, ResearchRun, systemd command, subprocess
workload, numerical package or checkpoint decoding is executed or fabricated.

1. An exact inverse reconstructs all baseline Parent bytes. AST checks bind the
   tested callbacks to the actual supervise argument, the pre-spawn checked call
   and the original retain_cleanup/retain_terminal/checked cleanup sequence.
2. A deterministic injected duplicate-observer mutation makes the original active
   checked callback fail. The new active callback passes while the real unchanged
   StorageWatch successfully counts tiny Owner/cpu_ready publications. It continues
   counting a final receipt after drainage. This is a synthetic scheduling witness,
   not a reproduction of the unknowable original changed directory or a claim of
   universal concurrent-publication liveness.
3. Parent-tree and disk failures still refuse active supervision. CAP failure still
   refuses pre-spawn and post-drained normal/failure boundaries. A real watcher
   rejects a post-drain logical-byte excess under its unchanged finite limits.
4. Actual installed job/resources protocol bodies and StorageWatch hashes are
   checked. Source AST ordering verifies predispatch, prerelease, running and final
   native accounting boundaries. Exact extracted observe_storage/boundaries/
   final_disk functions run against a real isolated tiny tree; each publication
   enters the accepted denominator. Actual logical storage excess and active/final
   disk breaches still refuse. These tests execute the metadata bodies only; they
   do not dispatch a native unit or claim to validate kernel containment anew.
5. The genuine assert_guarded_worker rejects absent release, false release and
   command mismatch. The pinned actual worker source retains full policy comparison
   before ResearchRun.start. No synthetic object is promoted to execution authority.

All five tests passed on the first run. Test output and source pins are retained.
The broad historical suite was not rerun. The nearest retained storage/fatal
semantics are reused by exact immutable source pins; their implementations were
not edited and no new matrix was introduced. The named offline profile inventory
was not changed outside assigned ownership.

## Remaining uncertainty

The original mutation's exact changed directory and first two attempts were not
retained, as documented in the bounded investigation. The unchanged native watcher
can still fail closed when a genuine workload publishes concurrently. Accounting
remains sampled metadata, not an atomic snapshot, hard quota, continuous writer
exclusion or proof of whole-fit capacity. Root still needs fresh binding, exact
independent source/recovery/Parent review and any separately authorized one-use
release. This source candidate creates no claim, launch, budget refund or extension.
