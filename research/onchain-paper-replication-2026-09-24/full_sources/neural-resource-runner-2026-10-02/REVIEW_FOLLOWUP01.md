# Independent candidate02 follow-up

Candidate02 materially addresses NR1–3, with one remaining NR1 preservation gap.
All three live source/test files matched candidate02.json and snapshots/check05
when inspected. No tests were rerun. Raw red05/check04/red06/check05 terminal
summaries were read:5failed11passed13.15s;21passed81.06s;1failed23deselected1.69s;
36passed1CUDA-skipped9.55s. The synthetic493424-byte checkpoint observation is
qualified correctly as serialization evidence, not full-graph physical capacity.

NR2 is addressed by `_bound_worker`: exact selected execution_job kind and plan,
registered resource policy, dependency-source closure and import root, original
worker owner, live guard command/policy, claim/source flow and Torch environment
are checked before output allocation and rejoined at cell/finalization boundaries.
NR3 is addressed by canonical output ancestry/device checks plus the original
output inode and immutable intent anchor. Wrong-plan/kind, missing guard,
redirected/foreign-device ancestor and copied-directory finalizer negatives are
present. The worker route still preserves its original outer guard checks.

NR1 checkpoint-stream closure is now one-shot and primary-aware. Fatal originals
retain identity and close diagnostics; close uncertainty after ordinary failure
is promoted to CleanupFailure. The producer stops further science and preserves
the denominator; fatal originals are rethrown, while ordinary failed jobs now
exit exceptionally after run.fail. Tests cover SystemExit, MemoryError, Torch OOM,
original fatal plus close failure, ordinary plus close failure and cell-record
publication faults.

Remaining correction: in candidate02 producer's final preservation block,
`failure-ledger.json` and `result.json` are published in the same try. If the
failure-ledger publication raises, the independent summary publication is never
attempted. This contradicts the stated best-effort attempt of both records and
the earlier NR1 requirement. Existing publication-failure test injects failures
only for individual cell filenames and does not exercise this path. Separate the
two owned publication attempts, preserve the original fatal primary/notes, and
add targeted tests which fault each record independently and observe both attempts.
No additional numerical/source/architecture change is requested. Candidate01 and
candidate02 evidence must remain intact.

Final acceptance remains pending that narrow correction and frozen source/evidence
review. All earlier no-empirical/no-physical-admission qualifications remain.
