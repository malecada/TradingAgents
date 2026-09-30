# Initial independent workload-route review

Acceptance withheld pending WR1 and WR2. These findings refer to the initial
source retained as `route.py.original`; later corrections require a separate
review. The original check01 report of ten passes in 55.556 seconds is retained
and does not establish the missing refusal cases. Only this review was written;
no tests/jobs, empirical arrays or raw bodies were run/read and no source,
registration, ledger or other evidence was edited.

## WR1 — test population is self-consistent but not registered

Location: `route.py.original:117–124`, with
`registered_features.py:24–30` defining the descriptor.

The route recomputes `examples.test_mask_hash` from the supplied test rows, but
does not compare it with a registered identity. The representation descriptor
binds the training hash and union of required graph hashes, not the full test
rows, test mask, exclusions or complete ExampleManifest. Dropping or reordering
a test row and recomputing its test-mask hash can therefore leave the registered
descriptor unchanged when the required graph set stays the same. The remaining
rows can satisfy all clock checks. Changes to test-row values or exclusions
likewise need not change that descriptor.

Impact: the purported actual example admission can accept a different test
denominator or test population than the registration. Self-consistent hashes
are insufficient when the caller also supplies the object being hashed.

Correction: bind the canonical complete ExampleManifest identity through an
explicit registered input/control that is itself included in the selected
descriptor. Require exact equality before graph iteration. Retain a regression
that removes/reorders test rows while preserving required graph membership and
recomputes all self-supplied hashes, so refusal must come from the registered
anchor rather than stale internal metadata. This is a component admission fix;
no financial rerun or historical registration change is required.

## WR2 — lease drops the metadata filesystem contract

Location: `route.py.original:43–49`.

Initial admission uses the existing bounded, regular, same-device, single-link
metadata reader. Subsequent leases instead call unrestricted `file_hash` after
only a resolved-path check. Adding a hard link leaves the content hash unchanged
and passes the lease despite violating the admitted single-link contract. An
oversized replacement is read in full before a hash mismatch can reject it;
the initial compact read cap and before/after stability checks are not retained.

Impact: the repeated admission boundary no longer enforces the file ownership,
extent and stable-read guarantees established at admission. The implementation
author independently identified this issue during review.

Correction: reuse the existing bounded same-device/single-link metadata reader
with each expected hash in Route.lease. Add hard-link and oversized replacement
refusals that exercise the real lease path, preserving the initial failure
evidence. Imported-source verification remains a separately bounded source
contract rather than a reason to weaken compact metadata checks.

Other initial observations remain qualified: resident graph identities are
joined to registered graph references; sample_scope reconstructs induced
neighborhood identity and derives the accepted workload scope. It explicitly
does not replay weighted RNG selection/probabilities or provide production
journal creation, mapped population ownership, orphan reconciliation or
whole-workflow physical accounting. A byte-tampered induced neighborhood is a
useful additional regression before corrected acceptance.

Initial evidence SHA256:

- `route.py.original`: `e1e6cd8dbdc29596dcfec25ba7132acb7efae0bb08c52bb68fd7c5b070521f83`
- `test_route.py.original`: `cf6ede32e631b9992217b48f106cd3061356e36764b3da912ec0a07465cfbd68`
- `check01.log`: `1f47cce5e59ee851140cb21ef964bf4cfdca6d99f44a885da7eeb38483290ff7`

No empirical release, budget adoption, timing-safe financial dataset or
validated strategy is established by this initial review.
