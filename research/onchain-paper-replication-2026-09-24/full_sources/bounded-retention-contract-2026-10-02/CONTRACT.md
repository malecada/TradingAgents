# Draft bounded matching restart-state retention v1

**NONEXECUTABLE; UNADOPTED.** This is a proposed prospective persistence contract,
not permission to delete anything or run a job. Independent review and a committed
pre-execution amendment are required. The existing archived-pair variant and all
historical raw data, gates, outputs, failures, spent histories and evidence remain
unchanged. No source file or current registration is amended by these documents.

## First slice and exact scope

The first slice rotates only **future matching restart-state bodies** during one
serialized current-owner dictionary or MCM stage. It preserves the current
archived matching-event representation, exact ordered completion scores, all
score tails/batches, both saved float32MCM outputs, samples/dictionary evidence,
model/optimizer checkpoints and every existing post-close scientific check.
Changing score-tail retention, pair-event encoding, output duplication or cold
feature loading is explicitly outside this first version.

The candidate version identifier is `bounded-matching-restart-v1`. A new input
`compact_restart_retention_input` must be explicitly selected identically by
execution_job.representation_jobs and plan.producers. Their descriptor extension
`compact_restart_retention` binds this version and the registered policy SHA256.
The existing compact_archive_execution selection is preserved separately. The
first release targets the currently selected archived-event route only; absence
of the new retention extension preserves the old contract exactly. Supplying the
extension with an unsupported route is rejected before any namespace claim.

The policy is additive and changes operational storage/verification semantics;
it must never be smuggled into an existing matching-policy hash or historical
stage version. Numerical matching configuration, input source identities,
Algorithm1 equations, initialization, float64 arithmetic, temperature progression,
hardening order/ties, comparison direction, RNG, sample/graph/motif populations,
checkpoint cadence and all scientific tolerances remain unchanged. No reset of
failure budgets or old run identity follows from a new retention version.

## Object classes and retention

| Class | Exact content | Rule |
|---|---|---|
| Scientific outputs | Complete declared graph/sample/dictionary provenance; ordered pair purpose/numeric identity/score/convergence/iteration records; complete stage/cell denominator; MCM/feature and final model/prediction/metric artifacts | Immutable and fully retained under existing output/archive contracts; no disposal in this slice |
| Replay evidence | Preselected independent numerical fixtures and exact raw/config/source/runtime/RNG input bindings; selected saved matching restart bodies; required neural model/optimizer/cursor/RNG checkpoints and offline inference example | Full bytes must remain recoverable and independently checked; selection frozen by a label-free rule before affected numeric outcomes; bodies exempt from restart rotation |
| Active restart scratch | Heavy M/Q/V and applicable hardening-order state for the single active pair, in fresh generation namespaces | At most current+candidate heavy generations; never treated as a permanent scientific output; all generation/verification/disposition metadata remains immutable |
| Failed evidence | Surviving current/candidate states, partial writes, manifests, progress/completion events, cleanup/guard/failure records, exact attempted scope | Freeze and retain on failure/crash uncertainty; no automatic cleanup/retry under the failed identity; already retired prior successful scratch is explicitly unavailable |
| Control evidence | Immutable claims, progress proofs, rotation intents/completions, state hashes/extent trees, live-generation transitions, final retention seal | Retain all up to a precommitted count/byte cap; metadata growth remains bounded by that cap and never silently pruned |

A body hash for retired scratch is a commitment to earlier observed bytes. It
is not recoverable backup, a reusable numerical checkpoint, or evidence that an
independent arithmetic replay was performed. The record must say
`body_available=false`, `restart_eligible=false`, and identify the verified
retirement disposition. No completion receipt may imply full historical
intermediate-state replay after those bodies are deliberately retired.

## Identity and directory contract

All new namespaces are inside the exact newly claimed stage, on its admitted
same-device canonical local root. Proposal:

- `restart/generation-<20digit ordinal>/`: mutable candidate creation, then
  immutable verified heavy body; never overwrite/reuse a generation identity.
- `retention/progress-<20digit ordinal>.json`: immutable proof of the full
  snapshot and its matched progress event.
- `retention/transition-<20digit ordinal>/{intent,complete}.json`: fresh owned
  transition; exact expected membership; failure marker retains incomplete work.
- `retention/terminal.json`: exact terminal chain/root, total counts, live and
  retired generations, replay exemptions and final scientific-score digest.

Every progress proof binds schema/version, fresh claim/owner/stage identity,
source/runtime/policy hashes, ordered pair ordinal, exact purpose and numerical
identity, matching-log start/progress-event ordinal/hash, generation ordinal and
predecessor proof hash, engine phase/cursor/iteration, complete file inventory,
file sizes/SHA256s, total logical bytes, original canonical root/device/inode
observations and immutable verification-result hash. Engine save/check remains
unchanged; independent proof admission cannot accept caller-rehashed arbitrary
metadata. Root identity and descriptor checks run through final callback-free
acknowledgement, using the existing owner transition lock without recursive lock
entry or post-close live-lease bypasses.

The new verifier's expected stage inventory explicitly includes these new roots.
Historical `checkpoints/event-*` and stage formats keep their existing parser and
full-tree checks; a v1 historical stage cannot be upgraded or reinterpreted as a
retired-body stage. A new retention proof cannot be attached to an old claim.

## State machine and ordering

Exactly one active pair is admitted; operations are serialized under existing
owner authority. The writer reserves all metadata/count/cumulative-write capacity
before creating any candidate. Active slots are structural reuse; cumulative
attempt/write/transfer counters are monotone and never refunded.

1. **EMPTY→CANDIDATE**: allocate a never-used generation and durable intent while
   retaining the previous current generation, if any. Save engine state to the
   candidate; fsync files and directory. Full existing snapshot verification must
   pass, including actual M/Q/V/order bodies and scientific identities.
2. **CANDIDATE→VERIFIED_CURRENT**: append/read back the exact matching progress
   event, then durably publish the progress proof and transition record binding
   that event and verified snapshot. Repeat source/body/inode joins after final
   live callbacks. Candidate is not acknowledged to the engine yet: all joins and, if a
   predecessor exists, its completed retirement in step3 must finish first. The
   old current remains until this point.
3. **SUPERSEDED retirement**: reserve/publish a fresh retire-intent binding old
   progress proof, expected inventory and newly verified current proof. Rejoin
   both exact generations and owner authority. Retire only old, owned scratch
   members named in that intent; never a replay exemption or declared output.
   Close owned descriptors, fsync parent, verify absence/exact remaining inventory,
   and durably publish retirement completion before acknowledging transition.
   Until the retirement completes, no third heavy generation may be created.
4. **PAIR_COMPLETE**: unchanged matcher computes exact score/convergence/iterations.
   The original ordered completion event is durable, fully read back and joined
   to exact purpose/numeric identity before the final current restart body is
   eligible for retirement. The immutable completion event is the scientific
   score commitment; subsequent MCM tail/batch publication remains unchanged.
   A downstream failure still fails the stage and preserves its completion-event
   evidence; it does not restore or rerun an already completed pair.
5. **FINAL_CURRENT retirement**: bind the exact successful completion-event hash
   instead of a newer generation; use the same retire-intent/cleanup/completion
   protocol. A selected replay generation is copied/admitted to its separately
   reserved immutable output namespace and fully verified **before** scratch
   retirement; its availability claim requires retained recoverable body bytes.
6. **STAGE_COMPLETE**: independently verify exact pair population/order/scores,
   all progress-proof and disposition chains, the set of required replay bodies,
   unchanged downstream numeric artifacts and an empty active scratch set. Publish
   one new terminal retention seal and anchor it in the original new stage seal.
   No current successful stage can finish with pending rotation or cleanup doubt.

No filesystem deletion/receipt publication is magically atomic. The logical
transaction is monotone: acknowledgement occurs only after durable operations
and final checks; every crash gap produces detectable incomplete evidence.
Physical capacity must allow current+candidate coexistence plus separately
retained replay/failure/metadata/staging obligations. The two-generation bound covers saved logical payload only. Concurrent live
engine arrays, serialization/copy buffers and filesystem allocation blocks are
separate obligations; this is not a filesystem quota or physical upper bound.

## Failure and interruption semantics

Any callback revocation, source/path/descriptor replacement, size/hash mismatch,
short write/read, fsync/close/unlink error, unexpected member, resource exhaustion,
process death or pending transition poisons the owner and stops the enclosing job.
No successful checkpoint/pair/stage acknowledgement follows uncertain cleanup.
Surviving source/candidate bodies and all partial claim evidence are preserved.

A crash after physical retirement but before a durable retirement completion is
an incomplete disposition, never silently accepted as success. Read-only
reconciliation records which body is actually available and the last fully
verified progress. It cannot invent a missing body, finalize evidence as though
unobserved work succeeded, or repeat numerical work. A separately admitted
successor may consume a verified surviving checkpoint only under a new explicit
identity/source/policy/budget; nothing here grants that successor automatically.

Earlier scratch intentionally retired by a fully completed transition is not
retroactively advertised as failed-state recovery evidence. Failed stage claims
retain all surviving failure material; no later housekeeping pass reclaims that
claim or refunds its attempt. Remote archived scientific bytes and old evidence
are never targeted by this local restart-retirement protocol.

## Independent scientific and replay obligations

C11 all-cell preservation includes failed/unavailable identities and full ordinal
coverage, not only successful scores. C13/C14 saved-model replay and independent
metrics remain unchanged, including complete required neural checkpoint bytes.
C16 requires actual recovery of declared outputs/replay members; retired scratch
is explicitly excluded from recoverability claims by the prospective contract.
C01/C02/C05–C07 numerical/source/sampling fidelity and C18 independent review must
remain satisfied. Exact source locators are pinned in the preceding retention
readiness audit; assumptions amendment here acknowledges changed restart semantics.

Required release checks are enumerated in `REVIEW_ACCEPTANCE.json`, with exact
observable outcomes. New synthetic comparison fixtures must force multiple
rotations and preserve exact scalar scores, iterations, convergence, ordering,
RNG states, semantic scientific identities and final numerical array hashes
against the unchanged retention variant. Each version must validate its own
source/policy/workload/receipt metadata; those provenance hashes may legitimately
differ and are not numerical output equivalence criteria.
Independent scalar arithmetic, assignment feasibility and saved-model/metric
checks remain frozen; equality of self-produced manifests alone is insufficient.
The proposed outcome-independent first/last rule is exact in REPLAY_RULE.draft.md.
For the original512sample single-block dictionary it selects comparisons0and261631;
MCM selects0andN×K−1. Adaptive dictionary fallback uses frozen initial eligible
ordered-pair identifiers rather than an unknowable completed-call count. Retain the
first scheduled safe checkpoint if any and explicit early-completion disposition;
never force extra cadence or choose replacement successes. Independent adoption,
stage-specific frozen selectors and physical containment remain unresolved.
Synthetic phase/shape coverage is separate; empirical endpoints do not prove it.

## Accounting and limits

Existing selected nine-graph payload arithmetic remains unchanged in this slice:
249,479,184,384bytes total conditional selected payload; archived pair events leave
55,439,818,752local score/matrix bytes. Checkpoint bodies were excluded from those
figures. This change caps their simultaneous active heavy generations at two,
plus separately retained replay/failure bodies, but does not supply a physical
upper bound or make the remaining55.44GB locally feasible.

Required prospective positive limits include maximum single-generation logical
bytes, total generation count, cumulative bytes written, retained metadata bytes,
replay-body bytes/count, failed-evidence allowance, peak live local growth, outer
RSS and wall limits. Their draft values are null with reasons until measured or
conservatively justified and independently reviewed. Current sampler/parentgraph/
dictionary/index/model/page-cache/I/O overhead stays in outer accounting.
User10GiB free-space floor remains; no existing sampler/guard check is weakened.

## Integration ownership and unresolved decisions

`SOURCE_OWNERSHIP.json` proposes a single coherent retention integration owner;
it is not an assignment while current sourcefreeze/worker ownership is active.
The source set includes the matcher writer and local/archived stage readers that
currently demand every checkpoint tree, explicit selection/policy and anchored
owner seals. Transport/dispatcher work remains separate. No score/algorithm
redesign is included.

Coordinator decisions still required before independent adoption:

1. Approve this narrow first slice with existing complete score/event retention;
   any later tail/output compaction is a separate version.
2. Independently accept the concrete first/last rule in REPLAY_RULE.draft.md and
   freeze its stage-specific selector/recoverable evidence manifests; resolve
   adaptive dictionary fallback explicitly, including checkpoint exemptions.
3. Supply complete resource/population/reuse and policy hashes/limits; the original
   resource MCM dictionary2022-01-03 vs future native reuse decision remains open.
4. Resolve how the new retention contract is bound in the still-unadopted exact
   resource registration. The cumulative61proposal remains33spent+12body+
   15financial+1resource, with no new allowance requested by this document.

Independent review and committed prospective amendments are the next authority
steps under existing authorization; no repetitive user permission request is
created. No implementation or execution is authorized by this draft.
