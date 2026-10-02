# Independent frozen candidate01 review

Acceptance is withheld for the material corrections below. Candidate manifest SHA256 is `a71f0ed0c7f82c2e893ec9349850038e3eb95ad707bf2bb5091720421baf89d1`; freeze01 SHA256 is `f5c56e52e27782b44a7ebca06feb7011eba171a88787ea842d3ffd6eb6ebc4e3`. Independent read-only hashing verified all 24 source snapshot/current, raw-log and freeze references without mismatch. Source and test bodies were inspected independently; no reviewer tests, local-child fixture, model, financial, SSH or credential actions were performed.

## AD1 — Honor the public job input before creating a context

`job_payload.py:39–46` calls the new preflight before the existing implementation validates the requested `job_input`. `archive_dispatch.py:78` and `:172` hardcode `execution_job`. Consequently an otherwise valid local call using `execute_fit_payload(..., job_input='another_registered_job')` now requires an unrelated execution_job input, and a selected archive call can create its context/output receipt against execution_job before the inner function rejects the actual requested job input. The existing wrapper test mocks the preflight and covers only the default name, so it cannot detect this regression.

Validate the actual requested registered payload before route selection/context side effects. Carry that original input identity consistently through preflight and Context, or preserve explicit supported-route restrictions without changing the local/reuse public contract. Add bounded cases for a valid nondefault local input, absent unrelated execution_job and differing selected input; invalid input must create no context or output receipt.

## AD2 — Rejoin original terminal and output evidence after final publication

`archive_dispatch.py:337–350` checks the original context once, writes terminal.json, calls `run.write_json` for the registered terminal output and immediately sets `_closed`. There is no post-callback recheck of the original context inode/intent/diagnostics or the new terminal/output identities. A terminal-output callback that first publishes and then replaces context terminal/intent evidence can return normally and yield a successful close. The normal start-output path already performs a post-publication `_outer` check; the terminal path needs the corresponding original-evidence join.

Capture original terminal bytes and the original registered terminal-output identity/hash, then perform callback-free local comparisons and necessary original run/guard checks before acknowledging closure. Retain the first failure/fatal and preserve partial evidence; duplicate close must remain nonmutating. A tiny terminal-publication mutation counterexample is sufficient before the larger actual-owner proof.

## AD3 — New descriptor cleanup can replace the first fatal

The new module uses `low.archive.io._release` in owned descriptor finalizers at `archive_dispatch.py:231`, `:252`, `:277` and `:279`. The underlying `score_batches._release` delegates to `_close_after_failure`, which raises a new CleanupFailure from the existing primary on any close exception. Thus an original MemoryError/SystemExit from a read/write plus uncertain directory/file close emerges as a different fatal object before `_retain` can protect it. This contradicts candidate01's first-fatal identity claim. Nested file/directory finalizers can replace it repeatedly.

Use a narrow adapter-owned one-shot primary-aware close boundary: preserve an already fatal primary and record the later close uncertainty; promote cleanup fatality over an ordinary primary with explicit cause. Do not change the globally shared helper or historical behavior without separate ownership. Cover original fatal plus actual-close-then-error, ordinary primary plus cleanup uncertainty, and nested independent descriptors; no model test is required.

## AD4 — Durably publish the fresh context directory

`archive_dispatch.py:182–190` creates the new context with `mkdir`, then fsyncs files/context through `_publish`, but never fsyncs the parent research_artifacts directory for that new entry. The later registered output receipt lives in a different directory. A crash can therefore retain that output while losing the context's parent directory entry and its reservation evidence. The existing operation Ledger explicitly synchronizes its parent after creating its root, so the new outer context should retain that durability contract.

Synchronize and rejoin the original canonical parent immediately after exclusive context creation, using the same one-shot primary-aware owned descriptor handling. Preserve failed construction evidence where possible and never retry the namespace after uncertainty. A bounded filesystem-call ordering/failure check can verify this delta.

## AD5 — Enforce diagnostic count while enumerating

`archive_dispatch.py:262` materializes `os.listdir(fd)` before line264 enforces the declared cumulative file count. A replaced or overpopulated owned directory can force an unbounded name-list allocation before refusal, undermining the bounded diagnostic/read contract. Use descriptor-relative streaming enumeration and check each count/name before accumulating metadata or opening bodies. A small over-limit enumeration test with an iterator that forbids consuming the remainder is sufficient; no large allocation is needed.

## Supported scope and remaining proof

The inspected arithmetic keeps decoded logical reservations separate from rounded transport payload and sums capacities across selected representations. The extra download block at exact block boundaries is correctly represented. Existing writer/read changes obtain the original typed held-transition token and private lease; they do not recursively call public Operation.lease. Counter/refund checks and completed diagnostic pins are present, and post-close transport refusal is explicitly nonmutating in the tiny tests. These observations do not establish real typed-ledger integration.

Raw check08 records 30 passing tiny synthetic/local-child cases in 3.83 seconds. The fixture deliberately mocks ResearchRun source/claim/guard authority and directly installs a synthetic capability; wrapper tests also mock preflight/inner execution. It therefore does not test the actual complete execute_fit_payload route, typed original operation/owner joins, full dictionary/MCM/owner-terminal closure, real admission, remote SSH or whole-route physical feasibility. After the corrections, the previously specified frozen isolated actual-owner fixture and unchanged actual local-route regression remain necessary. No numerical or financial outcome claim was assessed.
