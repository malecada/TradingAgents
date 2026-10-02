# Candidate02 — NR1–NR3 corrections

Independent REVIEW_INITIAL.md found three material issues in candidate01. Its
sources, logs, original manifest and implementation report remain unchanged in
candidate01-original/ and snapshots/check03/. No registration or empirical claim
is adopted by these corrections.

NR1: checkpoint file ownership now uses one explicit close. A fatal primary,
including CleanupFailure, SystemExit, MemoryError or Torch OutOfMemoryError,
retains its exact exception identity; close failures are attached as notes.
Uncertain close after an ordinary primary is promoted to CleanupFailure with the
original error as cause. There is no descriptor retry. Serialization errors leave
partial bytes, and close uncertainty cannot be converted into a successful result.

The producer stops science after the first error, attempts every remaining cell
disposition, attempts a complete failure-ledger and summary, attaches publication
errors to the primary, and rethrows fatal errors. Secondary publication failure
cannot mask a fatal primary. Ordinary failed rows still return for lifecycle
publication, but the worker now raises after run.fail for neural_resource so its
process cannot return normally after an unsuccessful resource job. Uncatchable
process death still requires the existing outer observer; no automatic resume.

NR2: the public producer joins registered execution_job bytes, requires its exact
neural_resource kind/plan payload, checks the complete dependency source inventory
and imported source root, reads original owner metadata, rejoins the live worker
guard with registered command/resources, verifies owner/source identity and every
policy field, and validates the registered Torch environment before output or
allocation. The same join is repeated at cell boundaries and finalization. These
are the existing authoritative guard requirements, not a fabricated capability.
Synthetic tests mock external admission/guard boundaries explicitly; no real owner
scan or empirical graph is performed.

NR3: the canonical original output path and nearest existing ancestor must be on
the admitted root device covered by that guard. Symlink redirection and simulated
foreign devices fail before output creation. The original output inode/device and
intent hash remain anchored in the producing run and are rejoined for final
publication; a copied replacement directory with the same claim is rejected.
Per-cell publication also checks the original namespace.

## Retained verification

- red05: 5 failed, 11 passed, 13.15s. Reproduced swallowed SystemExit/MemoryError,
  publication masking fatal, close masking original CleanupFailure, and missing
  execution-job authority. Exact contemporaneous sources/tests retained.
- check04: 21 passed, 81.06s. Includes exact wrong-kind/plan, absent live guard,
  redirected ancestor and foreign-device refusal. Filesystem journal wait was
  observed during this synthetic attempt; no duplicate run was launched.
- red06: 1 failed, 23 deselected, 1.69s. Isolated finalizer accepted a copied
  replacement owned directory before the original inode/intent anchor was added.
- check05: 36 passed, 1 CUDA skip, 9.55s. Own runner plus activation-checkpointing
  suite; normal reviewed conftest; no broad/actual-owner suite. Includes Torch OOM,
  secondary-close promotion, full failure denominator, ordinary worker failure
  exit, independent numerical one-update oracle and original scientific shapes.

All current source/test snapshots are direct copies at snapshots/check05/. The
latest test prints an exact synthetic checkpoint measurement to check05.log:
493,424 bytes for the original unshrunk model/Adam/RNG after one update on an
invented three-node graph. It is not a physical memory bound or guarantee of an
identical production serialized extent: longer registered identity metadata adds
bytes. A finite prospective 1–2 MiB checkpoint allowance can be evaluated against
this measurement with explicit metadata margin and unchanged refusal semantics.
No such limit is silently adopted here.

Whole-job guard containment remains hard; per-cell elapsed checks are cooperative.
Existing graph copying, full GAT intermediates, allocator retention and checkpoint
load copies remain limitations. Full-size feasibility remains unknown. Model/GAT,
original configurations, historical phases and previous results are untouched.
