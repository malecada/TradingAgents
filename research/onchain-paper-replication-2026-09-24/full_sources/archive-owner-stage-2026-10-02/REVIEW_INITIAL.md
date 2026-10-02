# Initial independent review

Acceptance withheld pending AOS1/AOS2 corrections and terminal verification evidence. Source and tests were inspected read-only; no tests, transfers or empirical jobs were run. The saved check01 log was still in progress at this inspection.

## AOS1 — outer stage inventory and unsealed lifecycle are not enforced

`archive_owner_stage.py:49` and `:75–84` join the stage through `ledger._stage`, `owner._stage_bindings` and `verify_current`. These validate intent, ownership, configuration and inner evidence, but do not check the entries immediately inside `stage.root`. Generic `archived_stage.verify` deliberately leaves this outer membership obligation to its integrating owner. A foreign file or orphan directory, including one introduced by the final reservation callback, therefore remains compatible with successful acknowledgement. The source also lacks an explicit refusal of a closed/closing stage or existing stage contract/reference, although this new route has no archived stage-sealing authority.

Check exact allowed/required stage entries before source admission and after the final callback, and require the supported unsealed lifecycle explicitly. Preserve the current-only scope rather than admitting an old completion marker implicitly. A final-callback foreign-file regression should exercise the missing postcondition.

## AOS2 — inherited reader close uncertainty can escape as an ordinary error

The wrapper correctly uses fatal primary-preserving cleanup for its own two retained descriptors. Its actual call chain still includes raw closes. Most directly, `owner._stage_bindings` calls `compact_stage.read`, whose `finally: os.close(fd)` at line30 can escape as ordinary `OSError` before the generic reader starts. The wrapper then preserves the failed reservation and poisons the owner, but rethrows an ordinary exception. An ordinary unavailable-result handler could continue despite uncertain cleanup; an in-flight primary can also be obscured.

Other directly reachable boundaries are `compact_stage.inventory:45`, its stream batch-directory close at171, `compact_matcher._file:60`, `_snapshot` metadata/root closes at72/118, and the verification root closes in `score_batches:333` and `score_tail:225`. The shared `score_batches._read` file-object context can also close with an ordinary exception; failure during `os.fdopen` construction requires ownership-safe disposal of the newly opened descriptor. These are bounded reader dependencies of this route, rather than a request to redesign unrelated numerical execution.

Apply primary-aware one-shot fatal cleanup at the actual owned boundaries, preserving existing source identities and errors. Never retry an uncertain descriptor number. Targeted injections should distinguish propagation after a real close from recovery of a leaked descriptor, and cover a primary in flight where that behavior is claimed.

## Positive source assessment and evidence limits

The new optional finalizer is called after the last generic live lease and receives a frozen result. The existing callback-free source/checkpoint/score/reference/inventory and completion-byte checks follow it, avoiding another remote replay. The owner wrapper pins its source and attempt descriptors, binds the writer reference and exact canonical result hash, checks matching iterations and exact/capacity counts, and preserves spent reader claims on failure. Its MCM graph join delegates to the maintained stage-binding check.

The three actual-owner fixtures cover a dictionary read, remote corruption and late source-metadata mutation. They use mocked OS guards and filesystem transport. The eight generic hook cases include immutable finalization and six late content mutations. They do not establish actual-owner MCM/capacity branch execution, post-owner-close reuse, producer or stage sealing, a transport meter, physical-resource capacity or financial validity. Callback completion is provisional until final checks and cleanup pass.

Inspected SHA-256:

- `archive_owner_stage.py`: `6fa454cbab93ca502023c7593746b9e0b12f8e60dc2e774825c02851cf1d479f`
- `archived_stage.py`: `e8ba4dfb865039e6d84d2cea07960e6b1e5012fd51b941105153ec5a64f11de7`
- `test_archive_owner_stage.py`: `6d0ba9314cf6b73a9da1116dceb3e1d692f1b6caad74ffd83e3476161f70873b`
- `test_archived_stage_finalizer.py`: `aa66b2ebdc2c8f587c72b664f3b37618e3808cd805318e5872474c6a5e2fcc57`
