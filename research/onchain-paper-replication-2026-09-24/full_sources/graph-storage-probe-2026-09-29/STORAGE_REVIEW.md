# Independent storage feasibility review

September 29, 2026. Source, compact result/projection and guard receipts were reviewed; no synthetic rerun, empirical input, array or database body was read. The observation supports preparation of a bounded resource feasibility pilot. It does **not** establish that the full week will fit or release execution.

The probe exercises production `build_weekly` and `save_graph`, with an explicit retained aggregation workspace. Its 250,000 transactions have distinct synthetic identities and random-looking address suffixes, seven source boundaries, one full declared coverage interval and 500,000 distinct nodes. It asserts admitted/raw counts, node count and edge shape before saving, and exhausts the iterator afterward. This stresses high node/edge cardinality and unsorted B-tree insertion. All event timestamps are the same day; the source boundaries partition the synthetic stream rather than test seven-day Parquet ingestion. It is an aggregation/storage workload, not a decoder or real-data completeness test.

The monitor samples allocated blocks at 20 ms intervals across retained output files and the process's matching open descriptors, including SQLite `etilqs_` temporary files. Device/inode deduplication prevents double counting an open file also found in the directory. This captures sampled unlinked SQLite storage while open, but can miss a transient allocation between samples; it does not constitute a maximum bound. Final retained files are separately enumerated. The peak occurs while graph files coexist with the live database: **244,158,464 bytes**, versus **217,870,336 bytes** final retained storage. The code and saved result support these descriptions; the reviewer did not independently inspect the binary output contents.

The saved guard closes complete with child 0, verified cleanup and zero memory-limit events. Workload elapsed time is 55.5108 seconds; guard elapsed time is 56.3192 seconds. The sampled guard memory peak is **617,586,688 bytes**. Neither that memory observation nor elapsed time establishes full-week capacity. The weekly builder still materializes node IDs, a Python node map, edge/attribute lists and graph arrays; a six-GiB full-week outcome remains an empirical feasibility question.

Independent arithmetic reconstruction confirms:

| Quantity | Bytes or factor |
| --- | ---: |
| 8,841,688 / 250,000 | 35.366752 |
| Rounded-up scaled sampled peak | 8,635,091,845 |
| Rounded-up 30% planning allowance | 2,590,527,554 |
| Projected Parquet allocated pages | 215,748,608 |
| Additional metadata allowance | 268,435,456 |
| Total projected incremental demand | 11,709,803,463 |
| Recorded free capacity above 20 GiB floor | 12,050,755,584 |
| Residual after this projection | 340,952,121 |

The 30% and 256 MiB allowances are assumptions, not measured bounds. Scaling by approximately 35 times has not measured full-size B-tree/index/sort behavior, real parsing, value/address distributions, actual admitted graph cardinality or concurrent filesystem use. The small residual does not independently validate those allowances. Existing raw, old partial databases and synthetic artifacts are already reflected in the free-space reading and must remain retained; they are not reclaimable projected capacity.

## Conditions before a bounded pilot

The uncertainty itself is compatible with a registered feasibility attempt whose failed/unavailable outcome is retained. It is not compatible with claiming the draft's promised quantitative upper bound has been obtained. The final charter must explicitly replace that preparation-only prerequisite with this reviewed projection-and-stop policy, retain the original draft, disclose both allowances and the small residual, and keep all original nine-week/109-cell and 1,420-fit requirements.

A concrete storage-location check remains: `weekly.py:43` sets `PRAGMA temp_store=FILE`, but `aggregation.py:87` only locates the main database. Neither sets SQLite's temporary directory. Before launch, establish that SQLite's effective temporary-file location is on the guarded filesystem, or route it to a declared scratch location and include every distinct affected filesystem in the guard's disk paths. The probe counts temporary descriptors irrespective of location; that does not prove a later guard watches their filesystem.

After corrected-source offline closure and final committed gate/source review, fresh preflight must confirm owner exclusivity/parent cleanup, exact source mappings, output ownership, at least the declared projected headroom above the floor, and the registered host-memory reserve. The runtime floor in `resources.py:223–224` is sampled: it detects a breach and stops, rather than guaranteeing free space can never cross the threshold. The final contract must preserve failed scratch/receipts, prohibit silent data truncation or deletion of old evidence, and never restart a terminal identity. No additional proof of successful full-size fit is required merely to ask this bounded feasibility question; no current unconditional launch approval is given by this review.

## Reviewed identities

All seven source-bindings.json entries rehash to the saved values. Probe: `a585459f56de9839bead6ebba784edce35745de4b2b8ff793d17a2da358d8f17`; result: `c6ff4ac9a2703a1722869a975478e1b0255ed2c1ebc8803063accb9485b15373`; projection: `fd30b64a61040c1c42436187cd3c0f0c9334d6f1a11b392c9af149ef17ddaf15`; guard01/final.json: `d2c2207a7eef452825e3809411be10747b297666873a6ce0396f22fb3e458d77`.

## Temporary-filesystem and final-contract follow-up

The separately guarded `check_temp_volume.py` addresses the concrete storage-location concern for the saved service environment. The script examines SQLite's temporary-directory pragma, SQLITE_TMPDIR and TMPDIR, and the built-in Unix candidate paths `/var/tmp`, `/usr/tmp`, `/tmp` and current directory. The saved output records SQLite 3.50.4, no environment or pragma override, `/usr/tmp` absent, and every writable candidate on device 66310, matching the guarded workspace. The check closes with child 0, complete phase, verified cleanup and zero memory-limit events. No empirical database was opened by this check. The reviewer inspected the script/output and final receipt, without executing it or independently browsing the cited SQLite documentation.

This closes the observed filesystem-location gap; it is a point-in-time observation, not a guarantee about a future service environment or mounts. The final prospective charter explicitly requires the check again before launch. It also replaces the preparation draft's upper-bound wording with the reviewed uncertain projection, retains both explicit allowances and all original scope, and requires fresh free space to exceed the floor plus the entire 11,709,803,463-byte estimate. Storage preparation is conditionally adequate for the bounded feasibility question. Broad verification, final committed source/gate binding, fresh admission/capacity/owner checks and retained failure handling remain release conditions.

Follow-up identities: check_temp_volume.py `6e3d82b74c37d0a11614fb363257a384fc68e298e188ca4155fc62810780506a`; temp-volume01/child.log `0d2f6512f771befb819630bbc4bbae22ec4343669e05b50ee3197abc26dd827f`; temp-volume01/final.json `cebc5410ae749330dc949552db00a6abaccfd44effe7f9b9d47674a3e0fabfce`.
