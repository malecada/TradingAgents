# Independent pre-execution review: offline seven-day continuation

Decision: approve the single registered offline engineering attempt
`eth-seven-day-offline-pilot-20260922`, after the normal committed-source,
final hash-binding, named offline verification, actual committed admission and
remote-source checks.
This review does not report empirical numerical success. No real graph rows
were decoded, no motif experiment was executed and no ledger was written during
review. The repository research-governance contract governs this distinction.

The reviewed question remains January 2–8, 2024, with January 1 context and
January 9 blocks only. The draft registration preserves 12 exact ancestor
claims and grants one additional claim, cumulative cap 13. The failed original
pilot remains present; the original pilot family retains prior 5 / cap 6 and
the source-resume3 family prior 11 / cap 12. The 24 ancestor claim/terminal
references, eight retained-capture descriptors, exploratory reuse designation,
17 cells and 20 outputs were inspected. No date substitution, fresh holdout,
new acquisition, price target or model evaluation is admitted.

The adapter reconstructs from retained projected columns, block objects and
footer metadata, with frozen member hashes and original request identities.
The source runner requires all eight source days before counting, exact
cross-day transaction uniqueness, and both boundary links. The original
completion-window numerical code and Local40 definitions remain unchanged.
Network audit hooks apply in the coordinator and every phase subprocess.
Exclusive resource/result publication and the existing lifecycle claim guard
prevent same-identity replay; no automatic restart is supplied.

The resource path uses the reviewed 8 GiB sampled aggregate process-tree RSS
guard and two-CPU affinity, without an elapsed-time kill. Counting subprocesses
release memory on exit. The 8 GiB derived allocation ceiling and 20 GiB free
space floor are phase-boundary checks, as expressly disclosed in the charter;
they are not a hard per-write quota. Separate scratch is recomputable. Selected
raw members remain read-only; pre-existing unselected derived files are retained.

Review found an integration defect before admission: the coordinator passed
absolute plan/current-result/previous-result paths to an adapter requiring
repository-relative paths. That would have prevented source/count phases from
executing. The coordinator now passes relative arguments. Resource-stop results
were also brought into the same phase schema, and the independent review command
now carries the expected source identity. The checked final source includes
these corrections; no real retry was needed.

The first committed read-only admission subsequently rejected the gate before
claim creation with `ValueError: invalid parent ancestry`. The standard lifecycle
requires `parent` to resolve inside the same gate and family; the old pilot is a
separate imported family. The corrected registration uses `parent: null` and
`continuation_of: eth-seven-day-pilot-20260916`. The custom policy requires both
exactly, while still requiring all twelve ancestors and the unchanged cumulative
and original family caps. This fixes the lifecycle interface without resetting
exposure or granting another attempt. The rejected commit and diagnosis remain
in `admission-rejection.json`; no empirical inputs were decoded and no claim was
created. A synthetic committed-Git integration test reproduces the rejected
ancestry and verifies standard admission accepts the corrected representation.
Actual admission against the corrected committed source is required before claim.

The new independent checker imports prior reviewer algorithms, not production
numeric/storage implementations. It reconstructs transaction rows, event order,
categories, activity and eight-day exact hash identities from retained bytes;
reconciles every event/prefix/local shard and new artifact; verifies both block
links; independently recounts complete completion-day dyads and the fixed
bounded Local40 subsets; and checks exact lifecycle/output denominators.
`numerical_pilot_success` requires all seven motif days and independent closure.
A failed run receives preservation-only review, not fabricated numerical results.

Synthetic validation initially passed 35 focused tests across the new adapter,
admission policy and independent checker. After the bounded ancestry correction,
all 38 focused tests passed, including two policy rejection cases and the
committed-Git standard-admission regression. Eighteen reviewer tests cover hand-counted
projected decoding, omitted projection columns, cross-midnight dyads/oracles,
altered count/summary data, missing nodes, invalid prefix timing, boundary
height/hash/time faults, changed or omitted retained members, path escapes,
new-tree extras, unbound blobs and corrupt raw hashes. These synthetic checks
do not establish real-data numerical validity or feasibility within 8 GiB.
The named offline target passed 2,311 tests and 97 subtests before this bounded
admission correction. The later focused suite passed 38 tests in 3.53 seconds;
both logs and their SHA-256 bindings are retained in `verification.json`.
The full target was not repeated after the correction. The final verification
receipt must be frozen with the gate before execution.

Not tested here: full real source/stored/raw hash roundtrips or numerical
decoding; seven-day numerical results; live peak memory or elapsed time;
independent full-day star/triangle recount; canonical-chain correctness;
historical source publication times; full-panel representativeness; prices,
returns, cashflows, execution costs, funding, prediction accuracy or economic
value; and off-device recoverability of the complete raw dataset. The checker
retains the same exclusions at closure. No specific unresolved correctness
question presently calls for a higher-effort review.

Reviewed source SHA-256 bindings (the final gate additionally binds all
dependencies, tests, runtime files and input metadata):

| File | SHA-256 |
|---|---|
| CHARTER.md | `a841d512b3cbc075c9145b2d7956a06cf149aaebb1193d3b5c4693acbb4d99bd` |
| plan.json | `2ecea1bcbee3da1eab047c93f72ef7a02e746246fa999c81823662aee7a1d8ab` |
| history.json | `29c7261dd21d40b6270d9d4938f3046ac697166db8504b04b5c20bf349985b1b` |
| admission.py | `919725ed6500e05f0f51c675f63e8b49ba4f1a48f19aa98f3e8c6d1fd5d5b9c4` |
| run.py | `4e40ad5b59dbdfead2947a07dd5c3ebcac823b8d07a93e050650241235b4c640` |
| day.py | `523c6e1b115bebda7028997cdd5825139479620b893e0ee83d06f3b9a845d356` |
| launch.py | `f66d6d0fe26858b64189c5dd8e0b4feaa3425bb3d87e82f5b1e9c7be1e1567b6` |
| check_independent.py | `3809fbe4b0b7605c265076b7b41466b9b164df79f233eeec0d2d0c1a465735ac` |
