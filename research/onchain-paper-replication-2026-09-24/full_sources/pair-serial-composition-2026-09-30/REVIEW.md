# Independent serial composition review

Accepted as the isolated serial pair/journal/workload component described in
SCOPE.md. No material blocker was found in the inspected component. This is
not acceptance of registered ownership, empirical continuation or an execution
release. Reviewed at HEAD `7d79ed9de4cb45b70074e8237eb69c4560d0fed6`.

The source checks workflow context, workload identity, ordered typed graphs and
the maintained numerical identity before reuse or reservation. It follows only
the journal's exact published reference, verifies its owner/identity/policy/
parent and complete extent, and validates completed-score schema/range before
return. The completed branch creates no solver session and spends no new
reservation. Progress starts a fresh session only after the caller has supplied
a journal owner with an unused target directory; the published parent and
cumulative journal charges remain retained.

For numerical work, the policy-derived checkpoint envelope is durably reserved
before session create/resume. Each save is extent-checked before publication;
lease callbacks bracket the relevant operations. Pending reservations refuse
before solver allocation, including a fully saved but unpublished completion.
Slice exhaustion preserves published progress and poisons this consumer.
Exceptional paths retain their journal/artifact evidence rather than discovering
or silently adopting an orphan.

The cleanup correction is effective on source inspection. Every returned
session closes in the finalizer; a close failure becomes CleanupFailure, which
inherits directly from BaseException. The adapter's explicit cleanup-error note
is also elevated when construction fails without returning a handle. Such
failures cannot be mistaken for ordinary RuntimeError/OSError unavailable-cell
results by Exception-only handlers. Consumer poisoning prevents subsequent
calls after these errors. An outer worker must still treat fatal BaseException
as termination; this component does not itself stop a process.

Saved green03 reports ten tiny tests passing in 0.628 seconds. The source of
those tests covers actual PairSession score comparison with the scalar oracle,
durable dictionary/MCM callback composition, unchanged reservations during
completed reuse with create/resume forbidden, progress continuation with fresh
engine create forbidden, ancestor-byte preservation, pending/orphan refusal,
logical quota refusal before allocation and fatal cleanup behavior. The
retained red02 report demonstrates the earlier nonfatal constructor cleanup
note; original source/tests and preceding reports are retained. No tests were
rerun during review.

Evidence qualification: the new combined dictionary fixture has three samples
and a partition threshold of four, so it does not exercise the partitioned
hierarchy through this durable adapter. The new progress fixture covers one
failed-parent journal hop; completed reuse is demonstrated on the same active
journal, not a complete registered representation inherited across actual
ResearchRun failures. These are remaining integration coverage limits, not
claims proved by the ten tests. The previously reviewed workload and numerical
components retain their separate scopes.

All 24 declared direct-file hashes independently match bindings.json, SHA256
`923e1a88781b76f017bebd5a2bc8b0cccbbd38adb5b893ce7c9b0b1424c8cca5`.
This is explicitly a direct-file inventory, not a full import/runtime or
committed execution closure.

- `serial.py`: `c23d2d709385de7a9d241ea48d993655785c7304c9e542e8e565765a698970ee`
- `test_serial.py`: `672b1bf7be3d655098dbb7d5d70d1e12ddcc1f0e981c4294d2641940c52d7a84`
- `SCOPE.md`: `fee497e73d113dabd93ca760c90cd4809b32cb2ad8cd6bda5e0cfac490d28072`
- `green03.log`: `02a3163ea547257cb086d0155748c218d3ea3700b5c934855a24232f8c81f024`
- `red02.log`: `6f2aa78380b7549eed24c0179c85d6ab3dca0374d9d4c20a0265642ee1b76379`

The lease hook is not a verified matching_owner.Binding. Caller-derived purpose
membership, actual ResearchRun/current-guard admission, failed-parent death,
representation ancestry, physical whole-workflow quota, orphan reconciliation,
scalable journal representation and full-graph MCM feasibility remain pending.
No source/body availability, empirical numerical agreement, financial return,
fit readiness or budget adoption is established. Only this review was written;
no source/tests, ledgers or other evidence were changed, no jobs were launched,
and no numerical array/raw-body/SQLite files were read.
