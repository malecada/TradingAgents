# Independent graph resource pilot closure review

September 29, 2026. **The single registered graph resource attempt is closed complete at the receipt/metadata level. Independent graph-content verification remains required before downstream admission.** This review read latest STATE.md, compact lifecycle/observer/guard/source metadata and filesystem stat information only. No raw, array or SQLite body was opened, no test or new job was run, and no source, registration or earlier evidence was edited.

## Lifecycle, ownership and lineage

The claim is `eth-paper-graph-resource-20260929-03`, SHA-256 `75c6e406624a24ab575fdf5fc9702054e8113726ff98e9747fc1f4de52cab3d4`. The unique complete terminal ended at **2026-09-29T12:26:31.881232+00:00**, binds that claim, source `ebe900afda7bb7d06cb2c890ca0c7ff607d0d870` and gate-v2 hash `0be5bcccea82d5ee05d718bd38f997c4a677bf79ef2caafb8154d20c9e7dcdfa`. The original two failed pilots and corrected `03 → 02 → original` ancestry remain preserved. The earlier metadata/pre-dispatch refusals did not create additional claims.

Observer.json's terminal, owner, launch, guard-final and guard-live hash bindings all match current compact bytes. It records complete, all_cells_complete true, cgroup_empty true and financial_completion false. The guard records successful child exit and cleanup. At independent inspection the recorded cgroup is absent and recorded supervisor/monitor/wrapper/worker PIDs 1526230, 1527853, 1529491 and 1529494 no longer exist. No active same-mechanism claim remains. These observations support closure of the recorded owner; they do not authorize restarting this terminal identity.

There are eight current same-mechanism claims plus 17 historical attempts: **25 consumed of effective ceiling 52**. Closing successfully does not refund the new attempt or either prior failure. The original family object still has baseline 51/prior 17; the separately adopted extension supplies 52. Remaining 27 allocations preserve 12 body batches and 15 fit batches; all **1,420 financial fits** remain pending.

## Complete denominator and source accounting

The terminal's eight unique cell IDs exactly equal the registered denominator and the lifecycle cell-ledger output: **seven source cells plus one graph cell**, all complete, unavailable_count zero. All three expected lifecycle output hashes match, with no missing or additional output filename. The daily counts are:

| UTC day | Recorded rows |
| --- | ---: |
| July 25, 2022 | 1,275,861 |
| July 26 | 1,679,068 |
| July 27 | 1,197,448 |
| July 28 | 1,158,611 |
| July 29 | 1,192,330 |
| July 30 | 1,179,749 |
| July 31 | 1,158,621 |
| Total | **8,841,688** |

Each source cell and each of the seven sealed aggregation-boundary receipts agrees with its registered source-wrapper/mapping hash and row count. Boundary sequence numbers and cumulative row totals reconstruct correctly. Coverage metadata spans the contiguous July 25–August 1 UTC week, binds the exact claim, plan/config and graph-manifest hash, and lists exactly the graph metadata's seven source mapping hashes. Manifest availability is August 2, the declared end-plus-one-day availability boundary.

The recorded aggregate accounting reconstructs exactly:

**4,685,413 admitted + 265,309 failed + 6,598 null-recipient + 3,884,368 zero-value = 8,841,688 raw rows.**

This verifies producer-receipt arithmetic and metadata agreement. It does not independently establish that every raw transaction was classified correctly or prove raw transaction-identity uniqueness without reading the stream/database. The producer's whole-stream validation remains the source of those runtime assertions.

## Retained artifacts and resources

The artifact index contains **28 files** and exactly matches the retained source-directory file denominator. All 28 stat sizes match; all **22 JSON artifact hashes** were independently rehashed. The remaining five array bodies and SQLite database were not read. Each array's indexed size/hash matches its graph-manifest entry. Indexed logical bytes total **4,476,281,037**, including **721,044,472 array bytes** and a **3,755,220,992-byte** retained aggregation database. The database's claimed hash agrees between aggregation completion and artifact index, but was not independently recomputed. These are final retained logical sizes, not transient peak disk use or proof of external backup.

The final guard reports **1,845.388127043001 seconds** (about 30.76 minutes), child 0, verified cleanup, no limit reason, sampled peak **5,368,791,040 bytes**, **3,312 memory.high events**, and zero max/OOM/OOM-kill events. It used 6 GiB memory.max, 5 GiB memory.high, zero worker swap and two-CPU affinity. This was a successful run with memory throttling, not a zero-pressure execution. The sampled peak exceeds the soft high threshold slightly, as that threshold throttles rather than acting as a hard maximum. Last unit telemetry is predominantly file cache; it must not be interpreted as a graph-only resident-memory measure. Ancestor telemetry records nonzero swap while the worker's swap remains zero, so a whole-host zero-swap claim would be false.

Final recorded workspace free space is **30,706,520,064 bytes**, above the 20 GiB runtime floor. The larger startup floor-plus-projection requirement was a prelaunch planning condition; its being exceeded by subsequent allocated output is not itself a runtime violation. Neither final free-space difference nor retained file total reconstructs every transient SQLite sort/index allocation. This result establishes feasibility for this exact full source week and graph configuration in this run, not a general storage bound, later graph population feasibility or MCM/neural fit capacity.

## Required independent content checks

Before downstream reuse, a separately bounded verifier should:

1. Rehash all five array files against the manifest, reject missing/extra graph members, inspect safe non-object headers, shapes and dtypes, and reconstruct the exact canonical graph hash `dfdaebb2566f10f1f705b8b5ef76f0aa7440e24444b7e8b054cb313613fc2c5b` from loaded content and metadata.
2. Check node-string uniqueness, directed endpoint-pair uniqueness, index bounds, finite/nonnegative numeric fields, positive integral edge counts and all declared graph structural invariants without an unbounded Python-set allocation.
3. Reconcile edge count aggregates to 4,685,413 admitted transactions; independently test edge_features against log1p(edge_aggregates) and reconstruct node in/out count/value aggregates against node_features, using declared numerical tolerances and accumulation conventions rather than assuming bitwise equivalence of different summation orders.
4. Reconfirm claim/plan/config/manifest/coverage bindings, exact seven-day source membership, availability boundary and exclusion conservation. Keep graph-array verification distinct from a fresh raw-stream or database classification/uniqueness audit; do not claim the latter from summary metadata alone.

The read-only content check must retain its own resource guard, exact script/source identity and result, without republishing the graph or consuming a financial fit. An independent review must assess what it actually verifies. New graph/database artifacts also still need a reviewed external preservation route; local retention and this report are not remote recovery proof.

No material closure-metadata inconsistency was identified. Latest STATE's completed source-only checkpoint matches these receipts and correctly keeps independent content verification, full original **nine-week/109-cell** resource requirements, motif/MCM/neural feasibility, broad history/comparators and all fits outstanding. This closure does not complete Task 8, the full replication or C01–C18.

## Receipt identities

| Receipt | SHA-256 |
| --- | --- |
| complete.json | `4d607d48a8bedce9ab8b8fdb5f88c45c4fc1b2f7826be3dda78beac4528d137b` |
| observer.json | `4710feae8a67bb371d81c1381eb2370678938bed5886e98b684d80eab42048bd` |
| guard/final.json | `bd22359070c134aa6304e7617e4d0cc1d7e303a6ef69f72213853d968ec1412d` |
| graph manifest | `9db059698fa84a9a3b460c58cdcd0ab35e97db0f4f2f8246504c7241c13b1a49` |
| graph coverage | `66e8c6fe28a4a9bfd02a1da95395b3e1bbfaf31341b14d9601c02e76215474a4` |
