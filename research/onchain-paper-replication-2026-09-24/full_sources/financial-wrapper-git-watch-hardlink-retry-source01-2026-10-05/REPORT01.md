# Scoped owned-fetch hardlink observation classification

This source-only candidate changes the original watch01.py and the narrow receiver
call site. The original failed receiver, Git store and outcome are untouched.
No Git command, network operation, new receiver, recovery claim or research claim
was executed. The recover01.py copy retains the old selection/fresh-directory
literals and is not a fresh released receiver; Root owns its future exact binding.

The original combined per-file predicate made both oversize files and hardlinks
immediate ValueError failures. The candidate keeps the same fatal file-size
predicate and separates link classification at initial observation and rejoin:

- default owned_fetch_objects=None remains strict: every non-single link is fatal;
- size over4MiB and link count0 remain fatal even during a fetch;
- only a path inside an explicitly provided canonical owned `objects` directory
  may classify nlink>1 as ChangingTree, discarding that whole observation;
- every accepted complete observation still requires every regular file nlink1.

The scope must be an absolute canonical Path named objects, inside the watched
root, a directory on the same device. No selected-body/helper/refname path outside
that subtree gains retry treatment. The receiver passes that scope at exactly one
call site: inside its pipe loop, only when args[0] is fetch, cwd is its exact fresh
owned bare repository, and the actual child poll returns None. This occurs after
the genuine child PID and soft/hard4MiB RLIMIT_FSIZE readback. Pre-call, body-write,
post-drain, cleanup and all other Git operations keep strict default behavior.

The existing three attempts, at most two100ms waits and shared five-second census
deadline are unchanged. No retry, wait, time budget, capacity or exception bypass
was added. Full census/rejoin, path/type/device checks, physical/logical accounting,
member/depth/file bounds, disk floors, response limits and cleanup/fatal selection
remain intact. Retry diagnostics name only the owned relative path and observed
link count; no credential or file content is read for those diagnostics.

## Focused source-bound evidence

Six metadata-only unittest methods pass under Main .venv/bin/python -B:

1. Exact .ndiff inverses reconstruct every byte of the original watcher and
   receiver. AST comparison confirms the census retry body is identical after
   removing only argument forwarding. Caller AST proves the sole explicit scope
   is inside the live-fetch loop after actual PID/file-limit readback; default
   calls remain unqualified. Invalid scope types/locations refuse.
2. Actual temporary hardlinks demonstrate the original initial and rejoin
   predicates fail immediately. The candidate discards the first active-fetch
   observation, then succeeds only after alias removal using its existing retry.
   The accepted second observation counts the full tree and single remaining
   four-byte body, with nlink1. Rejoin aliases are created outside the owned tree
   so a changed directory fingerprint cannot mask the file-level predicate.
3. Persistent internal and external aliases refuse after exactly three attempts
   and two100ms retry requests in scoped active context. Strict pre-call/post-drain
   link observations refuse immediately without any retry request.
4. Real initial/rejoin oversize files refuse immediately, including an oversized
   hardlinked file. An injected zero-link metadata observation also refuses
   immediately; zero links do not become a retry class.
5. A hardlinked selected file outside objects remains immediately fatal even
   while an owned-fetch objects scope is supplied.
6. The exact original receiver's source-defined child limits function runs in a
   disposable Python child. Actual PID/readback reports soft/hard4MiB; attempted
   overflow fails with EFBIG at exactly4MiB. No Git, network or numerical package
   is invoked. The original limits-function source is retained unchanged.

The retry wait function is intercepted only in metadata regressions to retire the
alias deterministically and count the existing100ms requests. The production wait
and deadline code is unchanged. No statistical concurrency or universal liveness
claim follows. All six final tests passed; no final-test failures occurred.

The same pinned owned_io body is copied solely for loading the candidate watcher.
Its implementation is unchanged. The named offline inventory is not modified
outside assignment ownership. No old test matrices were replayed.

## Limits and release dependency

The failed historical fetch's exact triggering path and whether it was oversize
or a hardlink remain unknown. Settled nlink1/sub4MiB observations cannot identify
the transient cause. This candidate is a bounded observation-classification
correction, not proof of the failed fetch's cause or of successful recovery.

A link count cannot reveal the other alias's location. An external alias to an
in-objects inode therefore causes a discarded scoped observation and persistent
refusal after the unchanged bounded retries; it is never accepted as a complete
sample. No externally located path gains an allowance. Sampled child liveness is
checked at the caller; no continuous writer-exclusion guarantee is claimed.

Root must independently review the exact candidate, retain original refusal,
create a genuinely fresh receiver02 namespace/bindings and perform any authorized
actual network fetch/recovery. Source preparation supplies no recovery authority,
claim, budget change, numerical execution or launch release.
