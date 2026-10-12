# Compact MCM cleanup expectation investigation

Conclusion: the three compact_mcm failures are stale cleanup assertions predating the weight-cache change. This is established by current source, scoped Git history and the supplied installed regression log; no unchanged-baseline test execution was performed here. The other four installed failures are outside this investigation.

## Exact evidence

- `tests/research/onchain_replication/test_compact_mcm.py:148,178,194,196`: all failing cause/type expectations originate in commit `6ee88fb497` (2026-10-01), per scoped Git blame. The injected engine.create failures are at lines 136–143, 170–172 and 191–193.
- `tradingagents/research/onchain_replication/owned_io.py:29–52`: all cleanup actions execute; primary plus cleanup failures are identity-deduplicated/flattened in order; genuine fatal exceptions retain precedence; otherwise an owned_io.CleanupFailure carries `.failures` and a matching cause group for multiple leaves. The entire file has no diff from `4566d19e56` (2026-10-05). Lines 29–52 originate in that commit.
- `tradingagents/research/onchain_replication/compact_mcm.py:435–445,447–465`: outer cleanup delegates to io._cleanup with the primary, poisons the owner, and final descriptor cleanup delegates through io._release. The equivalent tail is already in `4566d19e56`; lines 436–444 originate there. `score_batches.py:17` reexports the owned_io class and functions.
- `tradingagents/research/onchain_replication/compact_matcher.py:23,308,334–353`: engine means matching_checkpoint. The injected exception replaces its create call; state is never assigned. The ordinary injected primary propagates unless special cleanup notes exist. The separate compact_matcher.CleanupFailure is used for matcher/engine cleanup uncertainty, whereas the third fixture injects its failure later in outer producer log termination. No real engine.create body or cache session constructed by that body runs in these injected failure cases. Existing producer/matcher policies are not claimed to be absent.
- `pilot-matching-weight-cache-integration-2026-10-12/INSTALLED_OFFLINE_CHECK01.log:28–29,61–62,67–108,415–422`: first failure has ordered RuntimeError + OSError ExceptionGroup; second has ordered RuntimeError + OSError ExceptionGroup; third has ordered RuntimeError + injected bare owned_io.CleanupFailure BaseExceptionGroup, wrapped in owned_io.CleanupFailure. Overall log result is 7 failed, 100 passed, 1 skipped in 328.88 s; only these three failures are diagnosed here.

## Previously accepted semantics

`real-data-pilot-stale-cleanup-test-correction01-2026-10-06/REPORT01.md` already describes five stale score_cleanup expectations, requiring exact fatal owned_io.CleanupFailure, original primary plus actual injected cleanup objects in order, and identity agreement between `.failures` and cause-group members. Its candidate-only synthetic run reported 12 passing tests; this is retained historical evidence, not a rerun or proof that compact_mcm tests passed.

`real-data-pilot-failure-cleanup-review01-2026-10-08/REPORT01.md` independently accepts a narrow stream-close ordering change and explicitly preserves all-action cleanup, ordinary cleanup uncertainty fatality with primary evidence, and genuine fatal BaseException precedence. It says outer cleanup is byte-identical. These semantics predate the cache work.

## Smallest test-only correction

In these three fixtures, retain the primary RuntimeError instance and record each actual injected cleanup object as it is raised. Require exact `m.io.CleanupFailure` for the outer ordinary-primary/cleanup cases, `.failures` equal by identity and order to the primary followed by actual cleanup objects, and a BaseExceptionGroup cause whose `.exceptions` match that tuple by identity. The first two groups are ExceptionGroup because all their leaves are ordinary Exceptions; the third requires BaseExceptionGroup because its synthetic cleanup leaf is a bare owned_io.CleanupFailure. Preserve exact messages/types as well as object identity. For the successful-body parameter, retain fatal cleanup checking and assert the singleton cleanup cause if strengthening that branch.

Replace the third test's `m.compact_matcher.CleanupFailure` expectation with `m.io.CleanupFailure`; do not change production exception handling. Keep all poisoned-owner, failed-marker, descriptor-closure, test-owned retained-fd release and transition-lock-release assertions. Recording the actual cleanup instances prevents a correction from accepting discarded or invented cleanup evidence. No numerical-policy, cache, source authority or scientific-method change is needed for these three assertions.

Scope: source/public evidence and read-only Git history only. No numerical imports, tests, live changes or Git mutations. Only this new evidence directory is written.
