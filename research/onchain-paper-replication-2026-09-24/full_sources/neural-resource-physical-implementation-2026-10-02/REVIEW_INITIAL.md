# Initial independent physical-route findings

Acceptance withheld pending correction and frozen evidence. This is an early source review, not a verdict on a final candidate. Inspected `neural_physical.py` SHA256 `d7b7ca3a3b308e0be6850bc207fa3cdf4082ea00c449c985f7e00fbe6c600844`; other implementation work remained in progress. No tests or empirical work were run by the reviewer. Root and author were notified before this note.

## NPH1 — Mutable state can erase original root and claim authority

`neural_physical.py:153–186` rereads `physical-state.json` as authoritative identities and original claim hash. Removing a previously admitted role from `identities`, or clearing `claim_sha256`, lets `_scan` adopt the current replacement as a first birth. The state has neither a caller-held original anchor nor a checked immutable birth/claim history. A coherent same-experiment/source replacement therefore defeats the original-root/claim guarantee, even though subsequent current-state comparisons succeed.

Require independently anchored original birth/claim authority across processes, with rollback/reset refusal. Targeted cases should replace a previously admitted lifecycle/producer directory or claim, reset its mutable state entry, and require refusal before a further publication or acknowledgement. Ordinary cross-process state updates must remain possible without accepting an arbitrary new baseline.

Also refuse disappearance of an already bound claim: the current `if claim.exists()` branch skips a missing claim and returns the old hash. A dangling planned-root entry must not count as absent merely because `.exists()` is false.

## NPH2 — Process reopen establishes a fresh baseline from mutable files

`Scope.open`, lines131–139, derives `anchor_hash`, control inode and lock identity from the current namespace. A control-directory replacement with correspondingly edited anchor can satisfy its self-consistency checks. `job._physical_scope` compares launcher fields to current `launch.json`; external `reconcile` also obtains policy from the current anchor. These are not independent original authority across reopen.

Carry the original anchor/control/lock and selected registered policy authority from creation through monitor/child/worker and later reconciliation, with explicit trusted recovery binding. Reopening must refuse coherent replacement, not merely malformed fields. Preserve original in-memory authority against coherent public-attribute rebinding as part of the same join. Tests should distinguish normal fresh-process reopen from rebaselining a replaced root or policy.

## NPH3 — Pathname scan lacks original descriptor and final identity joins

`_scan`, lines157–175, checks each root once, then uses pathname `rglob`/`lstat`. It holds no root/child directory descriptors and does not rejoin the original root after traversal. Replacing a checked root or directory during traversal can redirect the scan or leave a current root unaccounted while returning success. The existing `StorageWatch` uses descriptor-relative traversal and final path identity checks; the new route should preserve that sampled-boundary guarantee rather than weaken it.

Use bounded descriptor-relative traversal with original path/inode joins at final acknowledgement, and retain fatal one-shot cleanup semantics. Add a replacement counterexample at a controlled scan boundary. Sampled/non-atomic qualification still applies after correction; this request does not demand a filesystem-atomic snapshot.

## NPH4 — Control reads allocate or block before size/type admission

`Scope.open` reads the whole anchor at line133; `_state` reads the whole mutable state at line153; `_scan` reads and hashes claim bytes at lines178–180. These paths do not first establish a bounded regular-file extent through a nonblocking, nofollow descriptor. A substituted FIFO can block, and oversized control metadata can allocate before the selected policy is enforced. The supervisor/reconciler does not inherit the worker's per-file write limit, and original bounded creation does not make later reads safe.

Require strict bounded control reads before JSON decoding with original file/path joins, including reopen. Add oversized and actual FIFO replacement refusals at the pre-read boundary. This is a metadata-reader requirement, not a request to read or recompute historical numerical bodies.

The review has not accepted complete resource bounds, kernel sink behavior, final observer-tail accounting, source admission or empirical feasibility. These findings concern authority and evidence preservation within the proposed bounded physical route. Final source and closed synthetic evidence must be reviewed separately.
