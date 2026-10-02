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
