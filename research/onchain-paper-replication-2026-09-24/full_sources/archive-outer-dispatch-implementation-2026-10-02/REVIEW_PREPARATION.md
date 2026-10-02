# Independent archive-dispatch review preparation

This document defines bounded review coverage for the forthcoming frozen candidate. It accepts no moving implementation bytes and grants no execution or SSH authority. The basis is the accepted outer-admission assessment (`PATCH_BOUNDARY.md` SHA256 `3d25dad22b31c84a7f3f214092094d852abf1d051a8e5ce6e0f35436ddb013fd`) and its independent review, together with the existing operation-ledger and transport contracts. No tests, model, fixture, network or credential action was performed while preparing these notes.

## Admission before side effects

Trace the actual public `execute_fit_payload` entry, not only a factory called directly by tests. Establish that the supplied payload/representation is the exact registered input for the active ResearchRun and that every selected job and producer-plan selector agrees before context-directory creation or transport construction. Contradictory local/archive selections, missing inputs, malformed policy and insufficient aggregate allowance must refuse before population/graph loading, owner claims or subprocess/network use. Preflight must cover all representations before entering the first produce loop; a valid first representation cannot conceal an invalid second one. Original source, guard, run identity and output namespace must remain joined throughout the route.

## Actual operation authority

Follow the capability from the existing typed private wrapper while its captured owner transition is held. A public `Operation.lease()` call recursively takes the nonreentrant transition lock and is unsuitable inside that wrapper. A free callback, fake owner, callable with the right shape or `lock.locked()` alone is not equivalent to the original held token. Verify exact owner, ledger, claim, stage, scientific ancestry, transition lock and calling thread; revoke the capability on every exit, including fatal exceptions. Transport operations before an active claim, between claims, from another thread, after stage/owner closure or through a replaced capability must refuse.

The outer terminal phase needs its own still-valid registered run/source/guard authority and original context evidence. It cannot revive an operation lease belonging to a closed owner. Original owner terminal/content checks remain local-only and must not acquire a transport or fetch a remote object after closure.

## Original configuration and namespace

Check immutable original pins for the actual command lists, host/port/authentication paths, transport endpoint identity, rates/deadlines, diagnostic root, budget object/counters and live callback. Checking the endpoint `.identity` alone misses mutation of the maintained adapter's `.ssh`, `.scp`, `.budget`, `.live` and `.diagnostics`. Every callback boundary must preserve the original baseline rather than rereading replacement values as authority. Reject replacement/refund/reentrancy, including a callback that mutates state and returns normally.

The context must own a fresh canonical namespace with its original inode and durable claim. Root replacement, aliasing, extra unaccounted entries and changed original receipts must refuse. Its original context receipt and final/failure disposition must be anchored in actual fit output/journal evidence and registered source/configuration references. A caller-supplied updated hash cannot replace the original pin. Duplicate successful close must be nonmutating; a later refusal cannot write a contradictory failure beside accepted success.

## Independent aggregate accounting

Keep the operation ledger's decoded logical allowance distinct from transport payload reservations and observed results. The original writer reserves three times its declared payload; each reserved verifier adds one payload. The transport reserves upload length and `32768 * (floor(length / 32768) + 1)` for each download. Independent boundary examples are: download lengths 1 and 32,767 reserve 32,768 each; lengths 32,768 and 32,769 reserve 65,536 each. The extra block at an exact boundary is intentional.

Reconstruct the maximum writer, readback and verifier operation/chunk population across all selected stages and representations. Compare the derived conservative aggregate against explicit finite registered limits before any owner claim. The durable transport ledger must spend before child execution, preserve failed/ambiguous reservations, and carry them into the second representation without reset. A failed child, short/oversized response or receipt failure cannot refund bytes or reuse a command/diagnostic identity. Read the raw reservation evidence; a final mutable remaining counter alone is insufficient.

Separately reconstruct maximum diagnostic/control file counts, retained bytes and reserved failure/terminal headroom, including partial files and failed commands. A bounded stderr tail does not bound cumulative diagnostics. Transfer reservation excludes SSH framing, encryption, handshakes and stderr; do not label it a wire-byte cap. Per-command deadlines and rates do not establish whole-job bounds. Sealed upload memory and local copies coexist and require separate physical admission.

## Failure and concurrency evidence

Verify single-owner, same-thread and nonreentrant operation with checks before and after callbacks. All independently executable closure/evidence actions should be attempted without masking an original fatal. Preserve the first fatal, including MemoryError; promote a later cleanup fatal over an ordinary primary with explicit cause. Ordinary secondary publication errors must not replace fatal identity. Owned descriptors and child cleanup are one-shot; preserve partial evidence and avoid retry after uncertain close/transfer.

The maintained transport confirms its direct child after requesting process-group cleanup; that is not proof of all descendant termination. Any actual execution still requires the admitted outer guard's descendant/control evidence. No synthetic test can establish remote permissions, capacity, SSH interoperability or a physical storage quota.

## Candidate and evidence review boundary

When the author freezes the candidate, independently verify the complete manifest, exact source snapshots and raw logs, then inspect the implemented public-route joins and counterexample tests against the invariants above. Review independent arithmetic and terminal evidence rather than relying on the author's expected result. Evidence must distinguish tiny rejection/child tests from an immutable isolated actual-owner outer-dispatch fixture, and both from real SSH or empirical execution. Failed preparation/test attempts remain preserved.

An actual outer-dispatch fixture should demonstrate the dictionary-to-MCM-to-publication-to-owner-terminal route, original context anchoring and cumulative spending across multiple stages/representations, plus a retained late failure and forbidden remote use after close. The unchanged local-route regression is relevant. Full numerical or historical financial reruns are unnecessary for a narrow dispatch change. Any missing decisive evidence should be identified precisely; no current moving candidate is accepted by these notes.
