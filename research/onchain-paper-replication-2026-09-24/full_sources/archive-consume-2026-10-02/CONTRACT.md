# Bounded retrieval with disposable owned scratch

Implement a new explicit consumer of trusted archive-chunk-v1 receipt bytes,
receipt hash and expected scientific scope. The old retained-copy reader and all
existing compact owner/stage/terminal readers remain unchanged.

The consumer creates one fresh exclusive local attempt, downloads at most8MiB
through a caller-supplied bounded/guarded transport, verifies full extent/hash,
then returns immutable bytes. Only its own newly downloaded cache file is
removed, after verification. Source files and preserved archive copies are never
arguments to disposal. Immutable intent, verified and complete receipts remain.
At most one payload exists per synchronous call; cumulative metadata, parallel
calls, retained returned byte objects, transport scratch and whole-workflow
physical allocation remain caller-budgeted, not bounded by this helper.

Every failure poisons that attempt. Pre-cleanup failures retain downloaded bytes;
a late failure after successful cache disposal retains the receipts/failure and
remote evidence, not a promise to restore the deliberately disposable cache.
Interrupted attempts never retry under the same identity. Source eligibility,
remote persistence and real guard/finite transfer budgets remain the caller's
obligations. This is neither original-source eviction nor empirical admission.

Tests use only fresh synthetic files. A valid preserved receipt may be supplied
without retaining its original local copy directory; its trusted hash, exact
scope, endpoint and full downloaded content are still required. Subsequent
archive-aware event/stage/owner contracts must authorize this use explicitly.

Final descriptor-close uncertainty is fatal CleanupFailure. The original
ambiguous descriptor is never retried. Failure/cleanup evidence is attempted
through a freshly opened descriptor only after checking the original device/
inode. If that namespace or filesystem is inaccessible, durable markers cannot
be guaranteed and the fatal exception retains the evidence error. Regressions
inject an error after a real close; they do not claim to simulate an actual
kernel descriptor leak or audit every older I/O helper.
