# First synthetic implementation handoff — conditional on contract review

Preferred candidate selected by the coordinator: the narrow matching restart
rotation described by CONTRACT.md. No implementation is authorized by this file.
Begin only after independent contract review and release of the current
producer-integration source freeze. This is a concrete two-file initial slice,
not a parallel edit to current package owners.

## Exclusive first ownership

- New `tradingagents/research/onchain_replication/restart_retention.py`.
- New `tests/research/onchain_replication/test_restart_retention.py`.
- New separately dated synthetic evidence directory, source/test snapshots and
  complete red/green/failure logs, assigned at dispatch.

No edits to compact_matcher, policy, stage readers, owner seals, dispatcher or
existing tests in this first slice. The new module is an unselected internal
persistence component and grants no admission/old-path deletion authority.
The later single integration owner needs the explicit ten-file candidate scope
in SOURCE_OWNERSHIP.json to bind this component coherently.

## Minimal component responsibility

Implement one fresh local namespace and exact versioned store state machine:

- claim a previously absent canonical same-device root with immutable contract,
  owner/stage/source/policy bindings and positive count/byte limits;
- publish and fully verify candidate engine-generated snapshot bodies before
  immutable progress proof acknowledgement;
- rotate a verified predecessor using a fresh retirement intent/completion and
  preserved metadata; no third active generation and no borrowed foreign root;
- finish a pair only against an externally pinned exact durable completion-event
  reference, then retire its successful current state or preserve a declared
  replay exemption;
- read/verify the complete explicit available/retired disposition chain without
  claiming retired bodies recoverable;
- stop on failure, preserve surviving bodies and incomplete records, and close
  descriptors without masking primary failures.

Keep numerical engine.advance/score and all ownership/admission policy outside
this helper. It may consume the existing strict engine-save snapshot verifier;
that verifier must not be mocked into success for corruption cases. A caller
lease is only revocation/authority checking, not permission to select arbitrary
existing paths for deletion. The component records execution_admitted:false and
can only retire generated members beneath the exact fresh root it owns.

The first test component does not impersonate a closed owner or confer a trusted
stage seal. The subsequent integration must bind original live authority and
externally anchored expected claims; generic self-rehashed receipts alone never
establish source/owner trust.

## Exact initial test cases

All filesystem mutation occurs under disposable pytest temporary roots with
invented tiny graphs and real saved engine state; no actual research owner or
empirical fixture is imported. Use the checkout-local locked interpreter and
normal reviewed offline conftest, plugin autoload disabled. Tests must precede
production implementation and preserve the failing run.

1. Force three successive incomplete-state snapshots of one fixed tiny matching
   workload using the existing engine; verify only current+candidate coexist,
   old heavy body is retired after the next proof, and every original generation
   manifest/hash/ordinal/disposition remains immutable. Assert the old generation
   cannot be opened as a recoverable checkpoint.
2. Independently compute the fixture's assignment score and feasibility from
   literal input arrays; compare exact completion-event purpose/order/iterations
   and final score with the unchanged engine route. Expected numerical answers
   must not call the new persistence helper or production verifier. Existing
   C05/C06 tolerances remain unchanged.
3. A pinned successful completion reference permits final-state retirement only
   after actual durable score-event readback; wrong purpose, score, numeric
   identity, iteration/convergence or ordinal fails and retains current state.
4. A deterministically preselected generation is copied into a separately bounded
   immutable replay namespace and independently reloaded before scratch
   retirement. Its bytes stay available; unselected retired generations remain
   explicitly unavailable. Replay identities are selected before scores are read.
5. Inject failures at candidate-file fsync, proof publication, retire-intent,
   first/last member retirement, descriptor close, parent fsync and completion
   record publication. Every failure stops acknowledgement and preserves all
   surviving bodies and both primary/cleanup errors. Simulated restart performs
   read-only reconciliation and refuses automatic continuation/retry.
6. Reject extra/omitted files, short state bodies, stale hash/extent, equal-byte
   directory replacement, symlink/hardlink or cross-device substitution, and final
   callback mutation. Use real descriptor and snapshot verification.
7. Exhaust each count/logical/control/cumulative-write/replay limit before the
   corresponding allocation. Retiring a body never reduces cumulative spent
   counters or makes failed identity reusable. The two-generation bound is never
   reported as a measured physical/RSS bound.
8. Verify a successful store's terminal proof with live/network callbacks
   forbidden. Verify mutation fails. A foreign historical checkpoint namespace
   or legacy stage format cannot be claimed/upgraded/retired by this component.

Preserve exact source/test snapshots and full output. A passing initial slice
proves only the local persistence primitive. It does not satisfy BR13 full
producer-to-terminal integration, C16 remote recovery, a resource admission,
whole-workflow physical capacity or a financial claim.

## Next bounded integration acceptance

After independent component review, one owner may bind the explicit selection,
matcher, old/new reader dispatch, original archive claims and stage/owner terminal
seal. Run the full BR01–BR14 suite against an immutable isolated source snapshot.
The decisive actual-owner synthetic fixture must cover both dictionary and MCM,
retirement plus replay exemption, ordered scores and saved graph output,
owner/terminal closure, post-close local verification and late-failure retention.
Historical/current variants must continue failing if a required old checkpoint
tree is absent. No generic bypass flag or implicit fallback is acceptable.
