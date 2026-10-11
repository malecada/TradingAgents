# Frozen-source resource overhead investigation

Scope: exactly six source files listed below; no live receipts/processes, empirical arrays, scientific imports, tests, or source changes. Root supplied active pilot34/source1b72fe04f and cumulative worker rchar81GB/wchar58GB plus monitor CPU about13min versus worker15min. These observations are not independently reproduced here and do not identify causes, unique bytes, or a throughput rate.

## Monitor work

- `resources.py:386–407,479–546,614–646`: default sample_seconds=0.25 (actual selected value not inspected). Each running iteration performs storage checks, disk free checks, systemctl properties, cgroup/CPU-tree checks, memory observations and live-state publication, then sleeps. Effective period includes all this work plus sleep; default does not prove four completed scans per second.
- `real_pilot_storage.py:87–101,134–178`: the schema2 writable union requires the entire checkout `research_artifacts` root, current `research_runs/<experiment>` root and shared lock. Each observation FIRST calls residual_check, then walks the aggregate roots. Residual roots (`:26–82`) include runtime cache, current lifecycle run, current worker run and pilot parent. These lie inside aggregate roots and are therefore inspected again. Aggregate accounting does not double-charge them; physical metadata traversal is repeated. Historical directories under research_artifacts remain inside this scan even if they are not writable experiment outputs.
- `workflow_storage.py:117–178`: each pass recursively enumerates directories and obtains fresh stat/fstat metadata, checks device/type/link count, counts allocated/logical bytes and entries, opens directories without following links and rechecks identities. It does not read/hash regular file bodies. Cost is O(entries + directories), including overlapping residual walks. `:77–115` retries narrowly observed publication races with the original deadline; no successful-sample cache. The five-second scan ceiling is a check between operations, not syscall preemption. Birth retry in WritableUnion can repeat a whole observation.
- `resources.py:132–144`: CPU verification traverses cgroup.procs and each observed process task directory, checking affinity per thread. `:379–383,530–535`: native live-state publication writes a temporary body, replaces the path and fsyncs its directory; `_native_write` also flushes/fsyncs. These source operations can contribute work without identifying the supplied worker byte counters.

## Authority work before a first published numeric batch

- `imported_mcm_identity.py:103–110`: Target.check forces an entry target_lease boundary, invokes ordinary lease, revalidates the registered manifest and execution metadata, then calls final(). `:84–95` final forces another boundary on the sampled route, rejoins owner/import/motif/workload identities and checks graph and node-order hashes. Thus successful sampled Target.check has two explicit full-boundary requests, plus direct validation work. The called implementations outside these six files were not re-inspected; their byte cost is unknown.
- `imported_authority_lease.py:118–162`: each scheduler full callback runs execution.check and authenticates loaded source. `:51–73` reads and SHA256-checks every registered loaded module body, compiles it anew, traverses expected code objects and compares actual loaded functions. This is repeated source I/O, compilation and comparison, not cached success. Its cost scales with loaded source bytes/code objects/functions, rather than graph cells directly.
- `:9–49,111–117` repeatedly enumerates loaded module/functions, fingerprints registered paths and serializes current metadata. Target._pins (`imported_mcm_identity.py:64–70`) serializes descriptor/execution/scope on fresh checks. Exact module/source sizes and current invocation counts were not measured.
- `imported_authority_interval.py:29–73`: explicit boundaries force full callbacks independently of ordinary call-count/time intervals; live/fingerprint and stale-deadline checks remain. No source-only conclusion permits dropping either boundary or refreshing an expired interval.

The previously frozen `pilot34-measurement-locators01-2026-10-11/LOCATORS01.json` (SHA256 ec3b6ed57a6e2d61171affa8280f75dd0174b1bc33e822438be3e03c6a188698) supplies batch/stage locator semantics. No new inspection of numeric callsites or live progress occurred. A first published batch is a completion receipt, so absence does not isolate which preceding work is consuming time. Exact counts between stage start and first batch remain unmeasured.

## Future candidate and limits

The narrow candidate is allocation/traversal reduction in fresh canonical serialization at Target._pins, using the existing identity-only typed serializer successor (`authority-current-pins-serialization02-2026-10-11`) as a candidate reference, not newly verified evidence. It must reproduce exact bytes/errors for ordinary registered JSON/frozen mappings, fall back for unsupported types, and retain every fresh object/source/currentness check and callback. No serialization result or validation-success cache is justified. Actual time saving is unknown and may be small relative to complete validations.

Combining residual and aggregate walks could reduce visits, but is NOT established semantics-preserving: current code observes roots at different times, has ordered refusals, common deadlines, race retries and independent root identities. Likewise skipping recompilation can change compiler/audit-hook behavior. Neither shortcut is recommended as an admissible patch from this investigation. No source-independent promise that unchanged60s authority deadlines or monitor resource bounds will pass follows from these findings. A future fresh run would need separately reviewed source changes and bounded synthetic equivalence checks before measuring benefit.

## Exact inspected source bodies

- `tradingagents/research/onchain_replication/resources.py`: 52034 bytes, SHA256 `7bd0fad9e790be8a024b490bdd604d7aeda146e00d21b095f4b21c1391147f7a`.
- `tradingagents/research/onchain_replication/real_pilot_storage.py`: 15891 bytes, SHA256 `5c9e6a8e9c26d85065f60b52ef65581b5d2a3379be4ccfb2a2b3efd264aa941e`.
- `tradingagents/research/onchain_replication/workflow_storage.py`: 10946 bytes, SHA256 `deff02766685c1e7fb8628766acf0e0c36dc324da4672f3adc094bfac3e24a74`.
- `tradingagents/research/onchain_replication/imported_authority_lease.py`: 13673 bytes, SHA256 `edd14622f3b5948a057e38bcce937c4080b9acc985c9a419fa0ac038aa158119`.
- `tradingagents/research/onchain_replication/imported_authority_interval.py`: 4566 bytes, SHA256 `e61ef97f883ed9d27107f6316b774697b8949d83c313928150a0ae717b283f6f`.
- `tradingagents/research/onchain_replication/imported_mcm_identity.py`: 8230 bytes, SHA256 `75d4e269ad4e87a34061e8331381af417b3c850346d71711902fcd5bbf322c82`.

Outcome: source locations and repeated-work mechanisms established; monitor/worker CPU attribution, actual I/O attribution, numerical throughput, ETA and optimization saving remain unknown. No live modification or empirical claim.
