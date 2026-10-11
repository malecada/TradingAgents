# Task2 — preserve trainer/evaluator primary failures

Plan: docs/superpowers/plans/2026-10-11-onchain-pilot-efficiency.md, Task2 only.
Status: implementation and focused verification complete; uncommitted for Root integration.

Changed production files: `training.py`, `evaluation.py`, new `failure_reporting.py`.
New test: `test_training_failure_retention.py`. Existing training/evaluation tests ran unchanged.

The new helper attempts each report/cleanup action independently, attaches secondary exception types as best-effort notes, and never manufactures a terminal receipt. Guarded primary-message formatting leaves normal strings unchanged and uses `unprintable exception` when formatting fails. Existing except blocks retain bare raise, original exception identity and original traceback nodes. Existing immutable writes, complete-fit guards, continuation rules and all numerical success paths remain intact. The SVM cell and fit reports are separate actions, so failure of the first no longer prevents attempting the second.

RED01 reproduced formatting/ENOSPC replacement and missing helper; two SVM prediction fixtures initially stopped at a one-class training population. That original failure is retained. Ruling: use the existing40-row synthetic population, which contains both classes, to reach actual completed-SVM prediction failure. RED02 confirms both corrected cases fail on the intended primary-retention assertion. GREEN01:21 tests passed in15.83s, exit0. Exact commands and full logs retained in COMMANDS.json and RED01/RED02/GREEN01.log. Diff whitespace check passed.

Coverage: first-batch failure with unprintable primary and either successful or ENOSPC-failing trainer+evaluator reports; checkpoint/claim bytes retained; real synthetic optimizer checkpoint followed by failing report; SVM fit and post-completion prediction failure markers, with/without ENOSPC; cleanup/reporting continuation even when add_note raises. Same primary object and original traceback node are asserted. Existing successful predictions, metrics, continuation/replay and duplicate-fit refusals passed.

Ruling: use the parent-assigned shared checkout and owned evidence directory, without skill-created worktree/workspace, commits or extra reviewers; direct task ownership supersedes generic workflow scaffolding. Synthetic test fixtures create their own temporary Git repositories and admitted toy claims only; no actual study registrations, ledgers, sources or empirical stores are accessed by those fixtures. No scientific protocol, source pins, Main Git state, STATE or external service was mutated by this task.

Limits: disk failure can still prevent durable failure publication, and notes are best-effort. Missing terminal evidence remains uncertainty. This change does not repair unrelated outer lifecycle exception formatting, add checkpoint safe points, qualify real data/model capacity or amend60-second authority checks. The first-batch retained checkpoint stand-in is explicitly fixture bytes; a separate test exercises a real synthetic saved optimizer checkpoint. Root must include the new helper in any future admitted source roster. No broad offline suite or empirical experiment was run; Root owns coherent integration checks.
