# Independent graph07 metadata preparation review

Accepted September 30, 2026 as preparation only; no blocking discrepancy found. No budget extension, gate, admission, empirical ingestion or launch is accepted by this review.

Seven wrapper members exactly equal the original source-index week2024-03-11 objects (index SHA-256 18f2548bdec2602995935d951075162537b6369b8bf18647cdc7a96962cffc1a). March11–17 daily rows 1,245,874;1,232,719;1,277,221;1,300,877;1,312,102;1,275,332;1,204,019 sum to8,848,144. The weekly plan retains March11–18 UTC and seven original sources; a subsequent graph claim must retain the seven-source-plus-one-graph denominator. Wrapper complete means retained source availability, not newly executed ingestion.

All seven mapping hashes match. Independent stat-only checks reconcile 91/100/100/64/55/64/64 spans (538 total), regular nonsymlink source paths and stored-byte extents. Stored-byte sums and unions of4,096-byte pages agree for every day; maximum daily projected page bytes are156,852,224. No body was hashed, decoded or opened, so declared rows and raw semantic/hash correctness remain producer obligations.

Projection independently reconciles: ceiling(244,158,464 ×8,848,144 /250,000)=8,641,396,994; ceiling(30% thereof)=2,592,419,099; adding156,852,224 page bytes and268,435,456 reserve gives11,659,103,773 incremental bytes. Add10GiB=22,396,522,013 required free bytes. The synthetic-result hash matches. This remains an assumption-based planning estimate, not an allocation/runtime upper bound or proof of feasibility.

Graph06 remains the active owner; its88source/54input hashes and HEAD02eef1c48292c8cb1fa864bb9803cab92c25d80c match. Its actual terminal, cleanup, independent closure and bounded verification of any completed arrays remain prerequisites; preserve any failure and unresolved original requirement. Current30/57 already includes that active attempt. Prospective58 must preserve30spent+12body+15fit+one resource slot using a complete actual closed snapshot and new reviewed charter/gate. All109original resource requirements and1,420fits remain in scope. No extension or gate exists in this preparation directory.

The new disk need is graph07's requirement. Conditional closed-ledger-offload02 cannot be justified by pretending graph06 failed its successful disk preflight. Any later use needs updated contextual release after graph06 closure, fresh capacity/eligibility/dependency checks and actual accepted preservation evidence before reclaimed bytes count. Prior preparation alone authorizes no transfer.

Reviewed hashes:

| Object | SHA-256 |
| --- | --- |
| PREPARATION.md | 9f6404f2b5907aeb4eee51ebdae771afe6b9d77c20101608f1c78de23456bfc6 |
| metadata-preparation.json | a5d84ee1d29d1fb3f8ae9ff2979953b871c34a879da7dd5f7bad5969566b2dc0 |
| graph-plan.json | 7e092e27beb87cf1444f96e452c64021e3341d9e02f3827f185a6dea217d758b |
| storage-projection.json | 16f74a297e1ed9364cf76c88595c2e7587f4cadebc26b3ca2b4f9891426d461a |
| execution-job.json | 3ba3e966d2a1aae6686c3d677932f0924f189cceeb0aacb6402e10791845f1c4 |

Only this review was written here. No tests, jobs, network, source/HEAD edits or raw/array/SQLite body reads occurred.
