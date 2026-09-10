# Independent review and resolution record

The integration was reviewed in separate bounded passes. Reviewers did not deploy, query accounts or run empirical trials.

## Backup and packaging

Two source reviews found no unresolved blocking defect in append-only backup, failed-push retry and partial rollout behavior. Fourteen tests use temporary local repositories and bare remotes. Deployment must install the shell and Python helper together; the Git checkout, external data root and backup worktree remain separate from the source archive. Unrelated dirty files block rather than being cleaned. The backup covers four paper journals only; executor state requires separate preservation. Git transport has no explicit timeout.

A packaging review rejected the generic deploy helper, which enables stopped trading timers, and Docker's broad source copy, which admits research artifacts. Base dependencies include large research packages, while wheel package data does not explicitly include monitor frontend assets. A positive source allowlist and preserved runtime/data roots are documented. Manual rollback refuses to overwrite an existing operator drop-in and restores only monitor code.

## Frontend

Initial RED tests showed null chart points becoming zero and unknown range anchors becoming NaN/infinity; missing accounting metadata also exposed legacy references. Corrections preserve nulls and reject the old API performance shape. Actual rendered tabs initially showed the old gate countdown and an OK badge based only on freshness; those claims are withdrawn/separated.

Independent rendering reproduced an incomplete non-null book labelled warming up (20/20), a reconciled-vs-reconciled_v2 badge mismatch, row counts labelled as intervals, and crashes from partial measurement descriptors. All were fixed with regression checks. The final reread accepted the changes; the production build and browser fixture confirm unavailable cards, suspended gate and separate freshness/measurement status.

## Backend

Review required exact paper accounting convention admission, safe malformed metadata, timestamp validation, daily null tails, twenty base observations for warmup and actual synthetic paper-writer integration. Valid observed flat warmup is distinguished from a broken chain; account equity is an unadjusted diagnostic. Existing tests that required null-row omission, legacy gross performance or the withdrawn threshold were replaced with assertions of the corrected contract; parsing, composition, auth and degradation coverage remain.

The final independent pass found that a non-flat initial overlay state could disappear into flat warmup without a measured close. Regression coverage and initial-state admission were tightened for both base and overlay before final verification. No existing financial artifact, gate or writer was changed.

Final independent recheck repeated the original startup probe: the stream is now incomplete with null cumulative return and all three values null. The prior unmeasured 100→100→103 promotion is blocked. Final integrated suite: 489 passed, five dependency warnings; frontend: 25 passed.
