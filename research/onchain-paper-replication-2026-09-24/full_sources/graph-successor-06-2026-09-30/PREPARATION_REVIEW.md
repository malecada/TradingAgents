# Independent metadata preparation review

Reviewed September 30, 2026. Accepted as metadata preparation only; no blocking discrepancy found. This is not budget-extension acceptance, source ingestion, admission or permission to launch.

The seven wrapper members equal the original source-index week `2024-01-01` member objects. That immutable index hashes to `18f2548bdec2602995935d951075162537b6369b8bf18647cdc7a96962cffc1a`. The seven January 1–7 daily row counts are 1,101,465; 1,128,657; 1,092,220; 1,116,573; 1,069,252; 994,947; and 1,049,831: exactly 7,552,945. The complete weekly interval is January 1–8, 2024. Original membership, graph configuration and the one-week/seven-source-plus-one-graph requirement are preserved.

All seven compact mapping hashes were independently recomputed. Their 118/118/109/109/109/118/109 span counts total 790. Stat-only checks found the recorded regular nonsymlink files and matching extents; stored-byte and 4,096-byte page-union sums reconcile, including maximum daily projected page coverage 123,625,472 bytes. These checks do not hash or decode raw bodies, establish transaction semantics, or produce new ingestion receipts. Wrapper `complete` describes retained source availability, as PREPARATION.md explicitly states.

Projection arithmetic independently reconciles: ceiling(244,158,464 × 7,552,945 / 250,000) = 7,376,461,800; the declared 30% allowance is 2,212,938,540; adding 123,625,472 page bytes and 268,435,456 metadata/reserve bytes gives 9,981,461,268 incremental bytes. Adding the 10 GiB floor gives 20,718,879,508 required free bytes. The pinned synthetic result hash matches. This is an assumption-based estimate, not an upper bound on sorting, topology, physical allocation or runtime. Fresh actual capacity remains necessary.

The proposed resource fields retain 6 GiB maximum, 5 GiB high, zero swap, 3 GiB host reserve, 9 GiB startup, 10 GiB disk floor, two CPUs and 28,800 seconds. Environment/workspace copies retain their prior bytes and require fresh validation. No extension, gate or adoption receipt exists here. Graph05's active claim is already spent: 29/56, with 12 body and 15 fit allocations retained. Only after its actual terminal, cleanup, independent review and bounded verification of any completed arrays can a complete 29-spent snapshot support prospective 57 = 29 + 12 + 15 + 1. A failed graph05 remains an unresolved original requirement. All 109 original requirements and 1,420 fits remain in scope.

At this review, active graph05's 87 source and 42 compact input hashes still match and HEAD remains `9f7401158b3544deefbc4c1b9e995d565880ce50`. No active bindings, source, state, ledger or HEAD were modified. No raw/SQLite/array bodies, network, tests or empirical jobs were accessed.

Reviewed SHA-256 identities:

| File | SHA-256 |
| --- | --- |
| PREPARATION.md | 0e8a59f1a2ce4423a934972ff15e0474c6247b274b757495ae9a0a28d826ad70 |
| metadata-preparation.json | 8ed89723e72805baa58352e6b66892fe937233235d0ef7dd0f16ef3e6eb1fefa |
| graph-plan.json | eea776c1987716ed84958b1fe7140ad70a1f8fc52893400b928d8d5c80823eb6 |
| storage-projection.json | 40f95d7554dfc4d1dadf3f0aeaa11db34a6012dc845b7f07f7cbdf3c71057dca |
| execution-job.json | 3ba3e966d2a1aae6686c3d677932f0924f189cceeb0aacb6402e10791845f1c4 |
| environment.json | f4f0ba42f05f9fda82345a4c5158a53f82225d7d224ce1b8b0fc39e1d9c99c2a |
| workspace.json | a3769663a0be2ab64fceb88d60986bd25c463717b70487e103090f5b9ec5be70 |
