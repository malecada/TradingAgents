# Next implementation boundary: archive-backed compact event retention

The copy/readback component and external transport are implemented. They do not
reduce peak local disk usage yet. The following existing dependencies were
inspected; they must receive an explicit new archive route without weakening the
historical local route or changing matching outputs.

1. compact_pair_log.PairLog closes a previous chunk only when opening the next
   chunk and keeps all completed chunks locally. A fresh archive-enabled writer
   needs a prebound policy, exclusive remote member naming and sealed-chunk
   receipts at that exact boundary. Never offload the still-open partial chunk.
   Persist the complete byte hash/extent, owner/scope, ordinal interval and chain
   endpoints before release. A lost acknowledgement keeps both source and failed
   attempt; it must not invent a successful replacement identity.
2. PairLog._terminal and compact_pair_log.verify read all local event members.
   The archive route must replay every event, not only trust upload receipts.
   Validate the unchanged hash chain, pair begin/progress/completion ordering,
   pair identity/purpose, terminal totals and all reserved extents. Bounded fresh
   retrieval requires deliberate scratch disposal after consumption; current
   archive.retrieve retains every attempt and is therefore only a foundation.
3. compact_stage.matching separately replays event members and joins progress
   checkpoint references plus score ordinals/purposes/values. Its archive route
   must retain these same joins and checkpoint inventory checks. Archiving only
   event chunks leaves score tails/batches and checkpoints as additional local
   requirements, which still need accounting and a compatible route.
4. compact_owner._verified_stages, compact_mcm_output._source and
   compact_terminal._original revisit the actual scientific producer objects and
   stage evidence. New archive-aware stage/owner contracts need explicit source
   and registered policy selection; do not monkeypatch io._read, silently move
   old files or permit replaced directories under an old receipt.
5. Synthetic verification must cover a full chunk and partial last chunk,
   missing/corrupt/out-of-order/misbound remote content, source revocation,
   upload ambiguity, bounded scratch cleanup and final full evidence validation.
   Original numerical fixtures and frozen production dimensions remain unchanged.

Before empirical release, measure the combined physical retained/scratch/cache
cost including this route and all remaining graph/sample/dictionary/MCM/model
objects; independently review and commit the resource/budget/hub amendments.
The conditional 249,479,184,384-byte lower bound is neither an upper bound nor a
new admitted pilot population. Existing remote capacity is not reserved.

## October2 implementation update

archive_consume.consume now accepts trusted immutable receipt bytes/hash/scope,
fetches a bounded member and disposes only its freshly owned download cache.
Metadata remains cumulative and caller-budgeted. archived_pair_log.verify now
streams these bytes while checking full event/terminal semantics and ordered
score/checkpoint-reference digests. A concrete synthetic full/partial-chunk
integration passes with disposable local originals absent. These close the
basic archive readback/cache and event-replay engineering pieces of item2 above.

Remaining: sealed-chunk writer/manifest and source disposition, actual checkpoint
and score-stream joins, explicit new stage/owner/terminal route, cumulative
metadata/transport/physical accounting and guarded pipeline admission. Neither
new helper authorizes deletion of any old source or substitution beneath a local
receipt. See their separate evidence directories for precise test/review scope.

## October2 writer and matcher continuation

The explicit ArchivePairLog now closes the fresh sealed-chunk writer/manifest
and owned-source disposition component of item1. It retains the last event
locally until the next append, preserving the existing numerical acknowledgement
contract. Its own completion fully replays the archive. Independent APW1–5
corrections and 95 focused passes are recorded in archive-pair-writer-2026-10-02.

Actual CompactMatcher integration is accepted separately: two synthetic cases
exercise exact reference scores, full and partial chunk rotation, intermediate
checkpoints and their real saved trees. Direct remote-event decoding and the
existing checkpoint validator agree with independently packed ordered digests.
See archive-matcher-integration-2026-10-02. This demonstrates composition, but
does not implement a reusable archived stage or current-owner reader.

The next concrete boundary is cold verification from a trusted archive-complete
hash, expected owner/scope/policy and ordered manifest, using fresh bounded
consumption namespaces. It must not reopen the closed writer or reuse its reads
attempts. Then integrate actual checkpoint and score-stream joins into an
explicit new stage route and bind that route through owner/publication/terminal
verification. Retained score/checkpoint storage, aggregate metadata and physical
budgets remain separate requirements. No historical-source eviction follows.

## October2 cold reader continuation

archive_pair_reader.verify now implements that cold event/manifest boundary:
trusted completion/owner/scope/policy, ordered manifests and original receipts,
fresh read attempts, every event fetched and replayed, and final checks after
the last callback/publication. Independent APR1–4 corrections are accepted;
117 focused passes and retained earlier failures are recorded in
archive-pair-reader-2026-10-02. It leaves the source read-only and cannot reopen
old attempts. Original local manifest metadata remains required.

Next: generic archived scientific-stage joins for checkpoint trees and retained
score streams, explicit owner/publication/terminal selection, and a compatible
retention/resource route for score/checkpoint payloads. Neither this cold reader
nor writer completion admits a scientific stage or supplies these missing joins.

## October2 scientific-stage continuation

The explicit archived_stage.verify content join is now implemented and reviewed.
Actual verified progress frames bind retained checkpoint intents/state trees;
a bounded disk reference index supports the final ordinal/hash/tree scan. The
maintained score-stream validator joins full ordinal/purpose/value digests to
archived matching events. Post-publication local source/read/reference/tree/score
checks and immutable policy snapshots close reviewed AS1/AS2 findings. Evidence
in archived-stage-2026-10-02 records146focused passes and every prior failure.

Next is explicit archive-backed current-owner/publication/terminal selection,
including source/policy binding, prospective finite read claims and resource
allowances. The current compact_owner stage writer/sealer/verifier and downstream
compact_mcm_output/compact_terminal still select local stage contracts. Those
contracts must remain intact. Checkpoint and score payload retention, whole-
workflow physical accounting and scientific admission are still separate gaps.

## October2 registered policy continuation

archive_owner_policy.select now supplies the prospective registered selection
prerequisite: actual fresh owner, exact job/plan/descriptor/input/source/endpoint
and conservative complete-stage logical allowances. Independent AOP1 correction
is accepted; baseline14 and corrected targeted3 passes are separately retained
in archive-owner-policy-2026-10-02. No writer or read claim is installed.

Next: durable finite operation reservations, owner transition authority and
explicit writer/seal/publication/terminal dispatch. Finite decoded member
allowances must be spent before operations, including ambiguous failures, with
no reopen or refund of terminal identities. Physical accounting, score/checkpoint
retention and empirical resource admission remain additional dependencies.

## October2 durable operation continuation

archive_owner_operations now consumes the registered selection under the actual
current owner's transition lock and reserves one writer plus finite later reads
for actual stage objects. Exclusive intents precede caller control, failures
retain their allowances, and caller-reference completion is distinguished from
scientific verification. The prospective policy explicitly budgets control
metadata; the ledger counts its fixed records and each operation's maximum.
Evidence in archive-owner-operations-2026-10-02 retains all failures, source
snapshots, nine baseline passes and five corrected targeted passes separately.

The next code must consume these claims in explicit writer/stage-seal/current-
owner publication and terminal routing. Public ledger transitions acquire the
owner lock; the producer already holding that lock needs an explicit internal
route, not recursive acquisition or bypass of claim checks. The post-owner-close
reader still needs separately bound phase authority. Actual upload byte charging
must follow immutable snapshot creation and precede dispatch; generic
put(source,member) alone cannot ensure this from an earlier stat. Receiver
diagnostic overread and protocol overhead are additional resource limits.
Checkpoint/score retention and complete physical accounting remain open.

## October2 reserved actual writer continuation

archive_owner_writer.run now runs the maintained ArchivePairLog under the actual
stage's reserved writer claim and a captured owner transition. Actual tiny
matching scores and16+2event chunk rotation are verified. It expires callback
leases, checks exact/capacity pair counts and revalidates original local writer
evidence after reservation callbacks without an extra remote replay. The
PairLog constructor's parent close now follows the fatal one-shot cleanup
contract. See archive-owner-writer-2026-10-02 for retained failures and42focused
passes. Caller values are not independently admitted scientific outputs.

Next: consume a finite read claim in the existing archived_stage.verify content
join, with a final local check after reservation callbacks. The current stage
validator's local inspect closure must remain equivalent if made reusable; do
not silently fetch a second time under one read allowance. Ledger claim
directories have an exact intent/terminal inventory, so adding read artifacts
under them requires an explicit bounded inventory contract or a separately
bound deterministic namespace. Then integrate actual producer writer selection,
scientific stage sealing, publication and post-owner terminal reads. Public
writer execution acquires its own lock; callers already holding the owner lock
need explicit control-flow integration, not a locked() ownership guess.
