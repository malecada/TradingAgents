# Native compact integration interface audit

Read-only source investigation. This records concrete outstanding interfaces; it is not implementation or execution acceptance. Dated paths below are relative to this study's `full_sources/`; maintained module names refer to `tradingagents/research/onchain_replication/`.

## Selection and policy identity

`native_producer.py:selected`, `ROUTES` and `required_sources` currently select `resident-native-current-owner-v1`, require identical plan/job input names and registered descriptor/output names, and refuse existing representation/pair namespaces before allocation. Its `prepare` creates the existing OwnedJournal through `pair-owner-route-2026-09-30/ownership.py:open_journal`.

Compact persistence needs an explicit selected route using the new `compact_policy.BACKEND`, with the policy input/hash joined in both producer plan and selected job and bound into the representation's declared execution identity. Preserve the old branch and numerical `matching_pair.BACKEND`; a storage/execution selector is not permission to silently change numerical identity. `matching_owner.bind` presently requires its exact scalar pair policy schema and descriptor `pair_execution` hash. The compact schedule must be separately and explicitly bound: `operations_per_call`, `calls_per_checkpoint`, `max_checkpoints`, `max_total_checkpoints`, `max_total_checkpoint_bytes`. It changes checkpoint cadence prospectively.

Use actual dictionary capacity or required graph node-count times ordered motif count to derive occurrence allowances. Bind the log limits, score chunk limit and retained logical allowance to the admitted stage. Per-stage reservations do not establish a whole-workflow physical quota or cumulative allowance across independently created stages.

## Ownership and leaf callbacks

The existing dictionary/MCM readers and producers use exact `type(owned) is OwnedJournal` checks. An arbitrary replacement or duck-typed owner cannot enter those paths. An explicit compact owner must join the actual ResearchRun/Binding, workload descriptor, policy, source/runtime, current guard and exclusive namespace; retain partial starts, checkpoint intents, logs and failures without retry or deletion. An empty old journal is not evidence that compact pairs completed.

The dictionary insertion point is `pair-consumer-route-2026-10-01/route.py:dictionary_consumer`, currently constructing Serial. `dictionary-proof-driver-2026-10-01/driver.py:fit` admits the sampler proof and derives sample scope before calling the workload. Preserve ordered typed sample identities, both directional purposes, partition/block/RNG context, hierarchy, memberships and matrix ordering. Preserve the producer result's dictionary/matrices/workload/sample-provenance contract and the publication driver's internal admitted-sample receipt. MCMScoreStream cannot replace the dictionary callback: it validates a different, row-major center/motif occurrence scheme.

The MCM insertion point is `mcm-publication-2026-10-01/driver.py:compute`, which constructs Serial after actual dictionary admission and selected MCM policy checks. Preserve exact graph membership/hash, node order, ordered motif identities, matching configuration, numerical backend and workload scope. Its result must retain native float32 matrix, completed rows/cells, output bytes, dictionary provenance, MCM policy and `_lease`. CompactMatcher can supply the scalar callback; MCMScoreStream adds ordered durable score acknowledgement and must complete before a successful publication claim.

## Publication and saved admission

`mcm-publication-2026-10-01/publication.py` currently binds full-matrix output to a `mcm_progress` event and proof carrying graph/order/motifs, dictionary provenance, workload and pair-workload hashes, selected policies and exact counts. It does not bind compact execution evidence. A compact publication must explicitly reference the actual pair-log start/terminal, score-stream terminal, completed/pending denominator and retained checkpoint evidence. Dictionary publication similarly needs its actual compact stage terminal. Update the corresponding exact-schema admission path rather than adding unvalidated metadata or reinterpreting old proofs.

The representation closure in `representation-closure-route-2026-10-01/closure.py:admit` checks the exact required graph/MCM event union, dictionary ticket, scientific lineage and saved graph artifacts. It relies on upstream owner/ticket leases for pair ownership. Compact stage evidence must become an explicit prerequisite while preserving this denominator and all native feature hashes.

## Terminal handoff

The active chain's `terminal-output-lifetime-2026-10-01/seal.py` is a hard interface boundary. Lines 113–247 snapshot old `j.records`/`j.state`, pin certificate/start/event references, derive session ownership and artifact inventories from reserve/publish events, construct the old JSON-event terminal and invoke `owned.seal('complete')`. PairLog has different state, chunks, terminal and checkpoint paths.

A distinct compact handoff must prove exact stage membership, no pending pair, completed counts, terminal hashes, retained score tails/batches/links and retained progress checkpoint inventories/content. It must bracket the final live-owner lease and terminal transition, then use the postseal current-run/source/guard contract; old active-owner leases must not be weakened to accept terminal state. Preserve partial/conflicting seals and the original output registry guarantees. Old cold readers cannot silently interpret a new compact seal as their existing pair-journal format.

## Lease and source obligations

`pair-owner-route-2026-09-30/ownership.py:OwnedJournal.lease` replays every old event, copies pair state and enumerates session directories on each call. `mcm-publication/.../driver.py` calls dictionary/owner/source leases and hashes the entire resident graph around pairs; the workload Route repeatedly invokes Binding. Leaving those calls in the inner loop would preserve major scaling costs even with fixed-size compact records.

A fast operation lease therefore requires its own reviewed contract for pinned source/input identities, live guard/owner and append acknowledgement, plus explicit full content/history verification boundaries. An unchecked cached success or removal of a check is not equivalent. Compact primitives' callback-free final readbacks remain necessary because an external lease can mutate evidence. File-system and source mutation guarantees remain sampled, not atomic snapshots.

`job.required_sources` includes maintained package modules, but dynamic dated `SOURCES` lists, imported route paths and the future registration must also bind the compact policy/owner/consumer/publication/seal modules and their transitive dependencies. Preserve historical source hashes and existing backend behavior. The current completed synthetic composition checks do not supply this registered source closure or authorize a retained-graph resource job.
