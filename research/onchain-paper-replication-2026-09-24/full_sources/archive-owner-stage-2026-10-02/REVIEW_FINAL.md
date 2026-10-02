# Final independent review

Accepted for the bounded reserved current-owner, unsealed-stage read contract. AOS1 and AOS2 are resolved on the inspected source and retained evidence. No additional material blocker was identified. Source, test assertions, terminal logs and hashes were inspected independently; no tests, transfers or financial experiments were rerun. The initial review and predecessor sources remain preserved.

## Findings disposition

**AOS1 closed.** `archive_owner_stage._unsealed_stage` now requires the actual active stage, no closed/closing state, no contract/reference, and exact required outer entries: intent, matching, checkpoints and, for MCM, stream. It runs before source admission and again after the final callback. The owner binding checks retain the registered matching iteration limit and required MCM graph join. The new final-callback foreign-file case reproduces the prior gap and now requires refusal with both completed and failed reader-claim evidence and a poisoned owner.

**AOS2 closed for the reviewed reader chain.** `score_batches._release` preserves an in-flight primary while making uncertain cleanup fatal. `_read` uses `fdopen(closefd=False)` so ownership stays with the raw descriptor even when file-object construction fails. Stream close and raw descriptor close are independently attempted once; uncertainty is never handled by retrying the descriptor integer. The reached compact-stage metadata/inventory/stream, matcher checkpoint-file/tree, batch verifier and tail verifier boundaries now use the same contract. Three focused reader cases verify successful-read and failed-read close uncertainty, original primary causality, and raw-descriptor disposal when `fdopen` fails. Six generic scientific-read injections cover metadata, checkpoint, inventory, batch and tail paths. Stack-based injection identifies a reached path; it is not proof that every close site or every simultaneous failure combination was individually tested. Injections after a real close establish propagation, not leaked-descriptor recovery.

## Accepted behavior and evidence

The wrapper consumes one finite reader reservation under the captured owner transition, derives the writer archive reference from retained claim evidence, and independently checks the actual source metadata rather than treating the reference as scientific proof. Exact or explicit capacity-mode pair counts feed the generic verifier. The finalizer receives a frozen result, pins the actual fresh attempt before completion callbacks, and completes the claim with the hash of the canonical result bytes. Final callback-free checkpoint, score, reference, source and inventory joins follow that callback. The wrapper then rejoins its pinned source/attempt, owner, ledger and stage, and closes both retained descriptors before returning. Failure after completion remains a completed-plus-failed claim; no allowance is refunded.

Saved terminal evidence:

- `check01.log`: **28 passed, 173.37 seconds**, before the two review corrections.
- `review-red01.log`: **7 failed, 11 deselected, 61.31 seconds**: outer membership and six inherited close paths.
- `review-red02.log`: **3 failed, 0.18 seconds**: shared reader close/primary/construction ownership.
- `check02.log`: **87 passed, 320.80 seconds**. This comprises four actual-owner cases, 14 finalizer cases, three focused reader-cleanup cases, and the existing archived-stage, score-batch, score-tail, matcher and local-stage checks.
- Separate `archive-regression01.log`: **121 passed, 6.55 seconds**, covering the shared-reader archive dependencies with filesystem transport. This is a separate verification population, not a single combined run.

The actual-owner positive performs one dictionary pair and observes exactly one remote `get` during its new reserved read. Its allowance assertion is the conservative four-pass total `(3 writer + 1 reader) * 200 events * 168 bytes`, not actual bytes consumed. The generic MCM fixtures separately exercise real checkpoints and score-stream joins. There is no actual-owner MCM or capacity-count integration case in this new wrapper suite. Explicit closed/closing/contract/reference refusals are implemented but not separately parameterized here.

## Limits

The actual-owner fixture mocks the OS guard and uses synthetic filesystem transport. No network, actual guarded job, empirical result or financial validity follows. The route neither publishes a stage seal nor switches a scientific producer, whole-owner closure or post-owner-close reader. It does not implement per-transfer metering, authorize source eviction, or establish total RAM, physical quota, throughput or whole-workflow capacity. Checkpoints and score tails/batches remain local. Remote content is observed during the one actual replay; final local checks do not claim continuous remote availability. Checks are sampled rather than an atomic snapshot. Timing, cashflow conventions, exposure, fees and funding were outside this engineering test scope.

## Inspected SHA-256 identities

| File | SHA-256 |
|---|---|
| `archive_owner_stage.py` | `a4d02e1464e5e99ea5491274de38dceabd50474ff86972c9672e3cf3489ba703` |
| `archived_stage.py` | `e8ba4dfb865039e6d84d2cea07960e6b1e5012fd51b941105153ec5a64f11de7` |
| `compact_stage.py` | `5f35aee853dd0198eb1d36390c2fb137e34d007b6eae24a0f16e9c09157bbfde` |
| `compact_matcher.py` | `bc9988647e4c5c68ea45c3e35c957acc487fd613ba58b40ac17928c783fd2a2d` |
| `score_batches.py` | `715125e543edd383c4bdeab59d10f7a269faec18f3b5fd16af79013e1bb37555` |
| `score_tail.py` | `b5e807e022349ca7e0d18c02512812932103865ba0779d641be6877995694870` |
| `test_archive_owner_stage.py` | `eb079f6284cfe432be57fdd13c82f894ec5ddf7009d22255ed62b8f7785e4e62` |
| `test_archived_stage_finalizer.py` | `9f222a5c552b967168f72d0803b3446b7f1ea15535e676afca0083174c7c0419` |
| `test_scientific_read_cleanup.py` | `3c4f0bd3667710a6d8694d696db50e1d483f7c8e50fdbc365ef1e4e24add8510` |
| `check01.log` | `c7af7485eaede7c514c0b7449683d0782ddae78c023c6ac12815af84d65d4d38` |
| `review-red01.log` | `9045644f1cb56e36d5fb74b07bbe6ca9f876dd1f646f6cdd3af35284e0a657c4` |
| `review-red02.log` | `83fd39e98e11b6f732b9f2ecdc013b48abe4ecf5f205d64eff95284dae3abf77` |
| `check02.log` | `eb9fbef5fd855895c93079bb52487c2ccf04c8052f8d9f05baf639e8e9a64d10` |
| `archive-regression01.log` | `bced6b6f808db5e579c0bc8be08f0aba39a3223215d03eb81aba93b4016a710a` |

Preserved initial `owner-stage-check01.py` hashes to `6fa454cbab93ca502023c7593746b9e0b12f8e60dc2e774825c02851cf1d479f`, matching the initial review. The four preserved reader predecessors were also hashed and inspected as the pre-correction source identities.
