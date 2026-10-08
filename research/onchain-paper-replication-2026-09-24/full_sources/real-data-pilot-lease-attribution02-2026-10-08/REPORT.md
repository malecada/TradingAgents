# Lease attribution02 — unconditional work versus sampled checks

**Finding:** the timed callback performs fresh producer metadata I/O on every invocation, even when no interval check is due. It also serializes three target metadata values. No unconditional whole-graph ID/feature hash was found on the actual imported sampled callback path. The supplied2926.76s/88532calls implies33.06ms average inclusive time, but source alone cannot attribute that average to the unconditional work or to infrequent expensive checks. No speedup claim or new candidate follows.

All paths below are relative to `tradingagents/research/onchain_replication/`. Source bodies are pinned in MANIFEST.json. Hotpath01 remains unchanged and uninstalled.

## Actual timer boundary and unconditional work

`compact_mcm.py:324–334` defines `_lease_body` and wraps precisely that body with `diagnostic.measure('lease', _lease_body)`. The body performs, in order:

1. Imported-type and active-stage identity checks, then `imported_authority_lease.target_lease(dictionary)`.
2. `score_batches._root(root,fd)` **on every callback**. This performs lstat, fstat and `root.resolve()` followed by exact directory/device/inode identity checks (`score_batches.py:133`). Resolve entails ancestor-path work; its syscall cost depends on path depth/filesystem/cache.
3. `score_batches._read(fd,'start.json',8192)` **on every callback**, compared against freshly generated `io._json(start)`. `_read` opens the leaf with NOFOLLOW/NONBLOCK, fstats before and after, reads through EOF, stats the current pathname, compares full metadata signatures and closes the descriptor (`score_batches.py:105`). A normal nonempty<=8192B file takes one payload read and one EOF read. `_json` sorts/encodes the current in-memory start dictionary each time (`score_batches.py:75`). This is live exact-byte mutation refusal, not a graph-body read or graph digest.
4. Optional `progress.poll(log,stream)` on every callback. Its normal not-yet-due path checks scalar state and monotonic clock and returns; only due polls produce bounded JSON/stdout (`real_pilot_partial_progress.py:74–137`). It does not scan numerical graphs or pair history.

`ScoringDiagnostic.measure` performs its own policy check before starting the timer; its `_record` and optional60s file refresh occur after computing the callback elapsed time (`real_pilot_partial_progress.py:224–241`). Thus the reported lease seconds include the body above and its nested checks; they exclude these outer diagnostic bookkeeping/write costs.

The imported producer start dictionary does **not** contain the whole source map. `_source_evidence` has already reduced it to kind/source_count/source_sha256 (`compact_mcm.py:61–68`), and complete start metadata has an8192B cap (`score_batches.py:21`). Repeated serialization is O(B_start) plus key sorting, bounded by this metadata extent; it does not grow with graph node count. Replacing it with a cached serialization would omit the current mutable start check unless another exact mutation check were proved. No removal is proposed.

## Target and lease work before sampling

`target_lease` (`imported_authority_lease.py:181`) checks genuine Target/Lease types, exact execution and registered target identity, assigns the current target, and calls `Lease.check`. Only first entry for a target requires `target.final(full_graph=False)` and explicit boundary; ordinary calls find the already registered target.

`Lease.check` (`:132`) performs `_identity`, then `target._pins`, then `Interval.validate`, then another `_identity`. It does not call `Target.check` on every invocation. `_identity` compares a fixed eight-object chain, scheduler/policy/clock pins and closed/poisoned flags; it imports but does not use canonical_bytes/thaw. This is O(1) metadata identity work.

`Target._pins` (`imported_mcm_identity.py:64`) performs:

- Four object identities and five graph-member identities via `_arrays`; these are Python id() operations on node_ids/node_features/edge_index/edge_features/edge_aggregates. Neither node IDs nor numerical array elements are traversed here.
- Owner/materialized dictionary/receipt chain equality.
- `canonical_bytes(resource_graph_inputs)` and selected-key lookup. Complexity depends on the seven-graph mapping metadata, not the represented graph sizes.
- `canonical_bytes(self._execution)` and `canonical_bytes(self.scope)`, comparing immutable byte pins. Execution metadata contains original/current identity records,32 ordered motif hash strings and32 representative sample indices; it does not contain motif arrays, full graph node IDs or graph features. Scope contains six identity strings. Canonicalization thaws nested mappings/lists before sorted JSON (`provenance.py:10,65`). Thus work scales with metadata bytes/keys and motif count, not the graph population.

No method named `Target.live` exists. The live method is **Lease._live**; conflating it with Target._pins would incorrectly attribute periodic authority I/O to every callback.

## Sampled paths and actual numeric/source scans

`Interval.validate` is unchanged (`imported_authority_interval.py:33`). A no-due invocation uses three monotonic reads plus scalar timestamp/call-count checks. Fixed100ms/1000ms/10000ms intervals,60000ms stale ceiling and65536 maximum calls remain. Boundary/first-entry/call-cap conditions can additionally force full validation. A long full/fingerprint callback can make the final live check due in the same invocation; therefore some callbacks contain two live validations. Expensive due callbacks can dominate a33ms average despite most callbacks being cheap. Actual counts/durations of these subpaths were not recorded by the supplied aggregate.

- **Lease._live** (`imported_authority_lease.py:125`) runs active Stage.lease or Owner.lease, then compact_owner.verify_current. Stage.lease adds intent/root/inventory checks. Owner.lease enters Binding.lease. Binding.lease (`matching_owner.py:97`) verifies claim, brackets metadata snapshots with two native/resource `_guard` calls, and checks owner/terminal inventory. The final compact rejoin repeats genuine claim/binding/owner evidence after the callback boundary. These are sampled live authority checks; no direct graph-array hash appears in this path.
- **Lease._finger** (`:110`) reserializes prepared configuration, source/input/runtime mappings; fingerprints every declared path; scans loaded modules/functions. Prepared configuration includes binding/selection metadata and source maps, so this path can traverse substantially more metadata than Target._pins. It is fingerprint-interval work, not unconditional per-call work.
- **Lease._full** (`:118`) invokes genuine ImportedExecution.check, rereads/hashes/recompiles authenticated loaded sources, and calls target.final(full_graph=False). ImportedExecution.check (`original_import_stage.py:163`) reaches Prepared checks, binding source/input/runtime validation and materialized numerical integrity. `MaterializedOriginal._integrity` (`original_import_preparation.py:190`) hashes dictionary content and each motif graph. `Target.final(full_graph=False)` additionally checks original stage content/materialized integrity and derives scope, which hashes32 motifs again. These motif-body hashes belong to full validation. The weekly graph hash is omitted by full_graph=False.
- **Target.check** (`imported_mcm_identity.py:101`) forces a full target boundary, leases again, rereads target manifest, calls execution.check, and calls final(). It is used at construction/preparation/kernel entry/final producer boundaries, not by ordinary target_lease. `Target.final(full_graph=True)` additionally hashes the weekly graph and node order. Imported kernel entry explicitly calls check; it does not call check for each scalar pair.
- **Target._prepare_sources** (`:117`) hashes the required source closure after preparation checks. `_sources`/Target.sources are preparation boundaries, not ordinary lease callbacks.

`CompactMatcher._check` (`compact_matcher.py:188`) calls the timed lease and subsequently checks pair-log metadata, policy/config digests and checkpoint directory. That subsequent matcher work lies outside the lease timer. Per-pair graph_identity work and engine create/advance validation occur elsewhere; they must not be attributed to the lease aggregate. The kernel calls lease around each score and several center/setup boundaries; CompactMatcher invokes it before each engine.advance and around publication/retention. Consequently88532 lease calls are not88532 graph hashes or independent full validations.

## Decision

The strongest new directly observed per-call I/O target is the exact producer start reread plus canonical-root rejoin. It is not currently removable without changing immediate mutation-detection behavior. The target serializations also protect mutable metadata and have no demonstrated redundant identical call within a callback-free segment. Full-check motif/source repetitions cross genuine authority boundaries. No safe directly removable duplicate was established in this narrower read-only follow-up, so no additional candidate is produced.

A future authorized subphase diagnostic could separate unconditional target pins/start I/O/progress from actual live/fingerprint/full invocations using the existing outer guards. This report does not install instrumentation or change timing policies, start a job, read graph bodies or propose admission. It provides source attribution and an explicit remaining measurement gap rather than assigning the33ms mean to a guessed cause.
