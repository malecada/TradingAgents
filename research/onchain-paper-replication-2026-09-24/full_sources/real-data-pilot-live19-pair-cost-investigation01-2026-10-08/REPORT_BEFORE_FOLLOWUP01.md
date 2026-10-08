# Pilot19 per-pair control cost: source findings

Observed counters supplied by Root: graph0114… denominator56,584,576; 26/120/169 acknowledged at302.086/422.191/489.126s; whole-caller CPU325.145s since graph begin; zero completed score batches and sampled168 durable-tail cells. These establish useful pair progress, not isolated matcher timing or the cost of any check. Seven-graph denominator415,968,128 is preserved. No extrapolated completion/capacity claim is made.

## Exact hot path

compact_mcm.produce_imported → _produce_locked:263-331 opens the stage, installs a science lease and calls the original imported_kernel.mcm through archive_owner_writer._run_locked. imported_kernel.py:51-60 extracts the original row neighborhood and processes all32 motifs in row-major order, surrounding workload.score with leases. The callback is MCMScoreStream.__call__:184-212 → CompactMatcher.__call__:254-313 → unchanged engine.create/advance/score_only. Matcher publishes begin/completion records and possible progress checkpoints; stream appends the acknowledged scalar to ScoreTail. Tail seals into a score batch only at its registered chunk boundary (:214-226), explaining why positive pair/tail counts do not imply a completed batch.

CompactMatcher._check:164-172 runs its lease and log._check; log._check itself invokes the same lease (compact_pair_log:127-130). The matcher checks before allocation, after begin, before every engine.advance, before/after score/cleanup, and after completion. Each event also receives multiple pre/post append checks and exact fixed-record rereads. ArchivePairLog._append:113-138 adds pre/post _archive_check, a JSON encode/decode snapshot of the five-field event state plus pending record, and further record/inode/signature acknowledgement. _archive_check:74-89 freshly serializes/hashes both start dictionaries, rereads their disk bodies, authenticates transport and opens child namespaces.

## Sampling does not cover the entire wrapper

compact_mcm science lease:290-298 uses target_lease, so full original authority/source/input/runtime checks occur on registered interval/call-count or forced-boundary triggers rather than every call. Fingerprint/loaded-code scans are likewise scheduled. Every invocation still checks Target pins (including canonical serialization of mapping/execution/scope), scheduler freshness and object identity. Producer start.json is reread and its expected JSON regenerated every science lease; telemetry polls cheaply return until due. MCMScoreStream._check:98-110 invokes wrapper lease and then target_lease again.

Crucial unsampled path: archive_owner_writer lease:65-71 invokes science_lease twice AND ledger._live. archive_owner_operations._live:166-175 → _current(full=False):131-154 calls Owner.lease and compact_owner.verify_current on every wrapper invocation. Owner.lease calls Binding.lease, with two live guards. verify_current:470-479 calls ledger._evidence() with default sampled=False, so history._full_evidence is forced; _current:144 subsequently calls _evidence(sampled=True) again. Thus imported-authority sampling does not remove repeated native/owner checks or full attached-ledger evidence reads on this archive wrapper. Early ledger history is small; no present or future time share is established by source inspection.

## Smallest candidates and boundaries

First bounded functional candidate: CompactMatcher._check starts with self.lease(); self.log._check(), while the genuine PairLog._check already checks terminal state and invokes that same lease before its root/durability checks. Consolidating this duplicate into one genuine log._check and retaining the matcher retention/start/root checks could remove one entire expensive archive wrapper call at every matcher check. Any implementation must explicitly retain the genuine log/lease identity join and existing pre/post event acknowledgements, ordering of failures and poisoning; arbitrary substituted log._check must not be allowed to suppress the matcher lease. This is a source-supported optimization target, not yet a reviewed patch or demonstrated speedup.

Smaller unambiguous compute-only reuse: CompactMatcher:272-273 computes cache_key(purpose) and pair.digest(identity) twice without an intervening external callback; compute each once and reuse for expected event and log.begin. MCMScoreStream:200-201 similarly hashes expected twice before a callback. Keep graph_identity validation at each actual callback boundary; do not reuse array-derived identities across numerical/authority callbacks solely because object ids match. These hash changes are bounded but unlikely by themselves to establish practical whole-study throughput.

For potentially larger gains, the unsampled archive wrapper is the concrete next attribution target. Do not silently skip Owner.lease/verify_current or change force=False merely to fit timing: those currently guarantee live guard and current evidence checks independently of the sampled imported lease. Consolidation must preserve exact current claim, owner/stage, transport, active operation, metadata, resource and revocation refusals plus full successful boundaries. Changing detection intervals requires an explicit reviewed contract, not a performance shortcut.

Keep begin/completion/progress event counts, order, exact record readback and hash chains; tail acknowledgement must remain after matcher completion. chunk_durability already batches fsync by registered record/time bounds, while retention/checkpoint/chunk/failure barriers may force earlier sync. CompactMatcher:276-278 and completion retention barriers are deliberate preservation boundaries. Zero completed batches does not mean those checks, pair events or tail writes are absent. No recommendation here changes matcher math, checkpoints, durability bounds or economic/sample criteria.

Source-only investigation; no processes, arrays, private bodies, numerical imports, benchmarks, tests, candidates, Main/Git/STATE or launch mutation. Only this report was written.

Source hashes:
- compact_mcm.py: b9b4c853b899b4ec7d053886b3ab5146d6ce081dfa045a408a2e5c34b73154bb
- compact_matcher.py: 888b1c0c302abdccbafb842d749d09034d0f3f743261f1c591bee7f58db49a1f
- compact_pair_log.py: 70691d78c0f34184db43aa93234685eb3e6100c89573af6c1bc520bafac7e756
- archive_pair_writer.py: 87464f872057a7483a7cc7a4a160541f5f56b1e0225b6dbefce6fb0bd85329f6
- archive_owner_writer.py: 7980139206c4b2a0e8b11763f44d23a73c4e9f067d9c10799a081664c42135d1
- archive_owner_operations.py: e45fd25c19f2a8f42f270cbb5c5437a823ba71a5e2e75333e928674ad1bec7bf
- compact_owner.py: 4d4d5d76aba2f3421be5b1b7c2d5f22003808b498a7fcd1f8dfb96d2079018fb
- mcm_score_stream.py: 94fd45fe16c5d833e5918f461563d9f4b63e7111c8790b0d32dc0000e2604a27
- score_tail.py: 91e1c9ba69b2922e2f77ad07ae9de4efc84f94d420ff55316e120b1df19398ca
- chunk_durability.py: da1fa8d8304a5241cdc44054901ecdf75231b8979569bcb373dec1471fb82f1e
- imported_authority_lease.py: 12d11a7a3f8b5cc07117f622978ce43ef537eab20ab80335b95eeb35cf4391bd
- imported_authority_interval.py: e61ef97f883ed9d27107f6316b774697b8949d83c313928150a0ae717b283f6f
- imported_mcm_identity.py: 9d89376185fb9632ed165a8da2f26e8fb07e2bc567611bc7fa5a83e2463e7e4d
- research/onchain-paper-replication-2026-09-24/full_sources/original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py: 8d810af1448893858504a90537a0a76b6ba70306427d3385f9571b0677a99287
