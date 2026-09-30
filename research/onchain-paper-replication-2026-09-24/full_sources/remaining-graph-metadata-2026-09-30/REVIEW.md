# Independent remaining graph metadata review

September 30, 2026. **Accepted as metadata-only preparation. No material mismatch was found.** No generator or tests were rerun, and no raw, array, SQLite or remote body was opened. Independent reconstruction used compact mappings, exact integer arithmetic and file stats. Only this review was written.

All 38 source bindings match. The frozen original source-index SHA-256 remains `18f2548bdec2602995935d951075162537b6369b8bf18647cdc7a96962cffc1a`. Each of the fourteen copied wrapper members exactly equals its original indexed member, with matching mapping hash, dates and row declaration. The graph plans retain the seven source-input keys and original one-week coverage. Selection is the two remaining original dates after active March graph07, not a response to financial or prediction outcomes. March completion is not assumed.

| Original week, end exclusive | Declared rows | Retained spans | Maximum daily projected page bytes | Incremental planning bytes | Required free bytes including 10 GiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| August 5–12, 2024 | 7,621,136 | 196 | 133,038,080 | 10,077,450,807 | 20,814,869,047 |
| December 23–30, 2024 | 8,617,920 | 232 | 155,787,264 | 11,365,740,894 | 22,103,159,134 |

Independent interval-event reconstruction of the union of 4,096-byte pages matches every new daily page total and all seven prior March reference totals. It accounts for overlap rather than summing duplicate pages. All 428 span paths currently exist as nonsymlink files with their declared compressed lengths; interval endpoints and raw-length declarations are internally consistent with each mapping. Stored-byte sums and span counts match metadata. These checks do not hash compressed bodies, validate their content or establish remote recovery.

Using exact integer ceiling arithmetic, August's scaled synthetic peak is 7,443,059,439 bytes and its 30% margin is 2,232,917,832 bytes. December's corresponding values are 8,416,552,441 and 2,524,965,733 bytes. Adding the maximum daily page footprint and 268,435,456 metadata-reserve bytes gives the incremental figures above; adding 10,737,418,240 bytes gives both declared free-space requirements exactly. The projection uses the unchanged 244,158,464-byte sampled synthetic peak for 250,000 rows. This is an assumption-based scale estimate, not a measured full-graph peak, proven upper bound, current free-space measurement or guarantee of success.

The generator is exclusive-output preparation. Its completed outputs should remain preserved; the generator must not be rerun against this identity. Wrapper `status: complete` describes retained source coverage, not newly performed ingestion. No new gate, resource claim, budget adoption, completed graph or financial exposure is created by these files.

For each actual successor, require the preceding producer and saved-array verification to close and receive independent acceptance; then evaluate actual free space, review any necessary separately authorized preservation, obtain the exact cumulative budget snapshot/review, generate and review the concrete gate, commit/push outside the active freeze and perform fresh admission, source-stat, runtime, ownership, memory, disk and temp-volume checks. Neither week may run concurrently with active graph07. All original matching, MCM, neural and financial requirements remain open as applicable; these metadata files do not reduce their denominators.

Observed HEAD remains `de91c9e084ad167e26b32effb4788d6f80130ef8`. All 88 active graph07 source pins and 87 input references were also rehashed unchanged. This review does not modify those frozen objects or assert terminal progress.

Reviewed identities:

- prepare.py: `8a734db07f1b1bfe6ff011aaf8d7dbfc9cbc83af8a45bf47704c2ccd78d5aa27`
- metadata.json: `a0e02da40286e0d3d9d2af23b9844f2d952eb6e97a422bbe7e18c9a6d70beb50`
- README.md: `afd21acead6ad154d333396cdd8080d192ad5a808d8824e0da2b90b27a7849bc`
- source-bindings.json: `b58199d1eb84b5cf91b1bf2c59fa58f82a4157842d71ef4b0992c066320a7fff`
- August projection: `53f79a41c2699597f91fb9e6cfb4dde01144ce632c56bc4ecbe96419c1e0412c`
- December projection: `d28bc204e4df1df1f280c5315c065aa13b43149d1ec0dac34749c2add050fce4`
