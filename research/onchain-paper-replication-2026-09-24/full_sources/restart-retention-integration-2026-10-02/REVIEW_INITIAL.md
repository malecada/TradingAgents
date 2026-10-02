# Independent candidate01 review findings

Candidate manifest SHA256 `8e3669826027aa3671f93fe7b42a2276c862406a1855ea53052beff2b1057b66`, binding13 source files and2 tests. Final acceptance remains pending closed owner evidence and the narrow corrections below. No reviewer tests or empirical work were run.

## RRI1 — Retained save path lacks original cumulative counter protection

`compact_matcher.py:201` returns through the retention branch before the old per-save `max_total_checkpoints` check. Ordinary `__call__` already reserves the worst-case per-pair count against `matcher.checkpoints`, so this is not a claim that benign public calls necessarily exceed the schedule. The residual is that mutable `matcher.checkpoints` is not included in the controller's original runtime authority, while `_save` relies only on the possibly larger retention.max_generations bound. A callback refund or direct retained-save path can therefore allocate beyond the still-declared schedule total; later archived-reader refusal comes after allocation.

Require the original controller-owned generation count to enforce the selected stage-wide schedule before pair allocation and every snapshot, and refuse inconsistent/refunded public counters. A tiny cap/refund regression and exact delta review can close this narrow issue without automatically repeating the expensive normal owner chain. Preserve owner05 as candidate01 evidence, not evidence of later bytes.

## RRI2 — Duplicate stage completion poisons historical successful evidence

`stage_retention.Controller.finish_stage` catches rejection from `_finish_stage` and calls `fail` unconditionally. After a successful first call, a second call reaches `live`, rejects the closed controller, and then marks it failed and writes `failed.json` beside the successful seal. This changes the terminal namespace merely because the already completed action was requested again, invalidating previously usable evidence.

Refuse duplicate closed completion before entering the failure-mutating body, while retaining failure evidence for errors in an active completion. Add a tiny successful-finish/duplicate-finish check that asserts unchanged control bytes, seal, original spending and terminal state. This finding does not require removing legitimate owner-level late-failure evidence.

The reviewed architecture otherwise keeps a distinct archived v3 interpretation, original stage selector/seal authority, binary-frame to JSON-progress bridges, FIRST-before-retirement and retained original manifest controls. The old local stage APIs explicitly refuse retention policy. Completed Stores retire their current bodies, and the new reader reconstructs cumulative reservation arithmetic independently. These source observations do not yet constitute final acceptance of the whole candidate or its failure paths.
