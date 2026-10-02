# Independent candidate02 continuation review

Candidate02 remains unaccepted pending the narrow fatal-priority corrections below. Read-only hashing verified 47 candidate01/candidate02 snapshot, raw-log and freeze02 references without mismatch. Candidate02 manifest SHA256 is `bbb0accea6ca7fe1ee5883f234f1727a035959d224fa4f4245c1be48d44ffe79`. An initial reviewer hash command used the wrong base for already repository-relative log paths and stopped at FileNotFoundError; the corrected read-only command checked all 47 entries. Neither command imported research modules or wrote evidence.

The candidate01-to-candidate02 source diff addresses the reported in-flight shutdown failure, construction cleanup promotion, selected guard cleanup attempts and nonzero monitor exit. Raw check15/check16/check17 results support their stated separate scopes (3, 11 and 39 passed). No model or OS test was rerun by this review.

## NPH7 remainder — ordinary body cause is lost

At frozen candidate02 `resources.py:403`, only a fatal body error is retained as an object. A later physical cleanup fatal therefore cannot chain the actual ordinary guard primary, although the text survives in `limit_reason`. Retain that original ordinary object for possible promotion, while keeping the expected failed-state return when the body failure is ordinary and finalization succeeds. A sentinel ordinary primary followed by actual one-shot close uncertainty is sufficient verification.

## NPH8 — first-fatal priority is inconsistent

Frozen candidate02 `neural_physical.py:197`, `neural_authority.py:112` and `job.py:217` treat every `Exception` as an ordinary primary. `MemoryError` is an `Exception` but this route explicitly classifies it as fatal; a later cleanup fatal can incorrectly replace its identity. Apply the same first-fatal rule used by the low-level descriptor/socket cleanup. The smoke controller's corresponding shutdown code requires the same correction.

The authority error reductions also require that rule. At `neural_authority.py:98–100`, an ordinary handler failure already stored in `self.failure` causes a later client-socket `PhysicalCleanupFailure` to become a note. Shutdown then raises ordinary RuntimeError, downgrading the owned-cleanup uncertainty. At lines105–107 a fatal join exception can similarly become a note on an ordinary captured primary. At lines85–87 an unexpected accept error unconditionally replaces a previous failure, including a fatal. Use a consistent small priority reduction for these owned authority transitions: promote the first fatal over an ordinary original with explicit cause; preserve an existing fatal object; retain secondary evidence as notes. Bounded event/socket/sentinel tests can close these findings without running a model.

## Preparation and limits

The original smoke preparation is unexecuted. Its terminal-publication accumulator originally raised the first failure even when a later failure was fatal, and its claim observation sat outside the independent best-effort actions. A preserved corrected candidate must apply the same priority rule and attempt observer/finish after a failed claim observation. Final preparation acceptance still requires the corrected source review, exact driver/spec pins and an isolated committed source closure.

This review does not test real systemd/cgroup availability, original nine-graph capacity, empirical admission, numerical agreement, financial outcomes, timing/leakage or economic accounting. Existing tiny-model evidence does not establish those claims. No network or credential access occurred.
