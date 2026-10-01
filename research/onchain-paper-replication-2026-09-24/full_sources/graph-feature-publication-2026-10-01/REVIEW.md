# Independent corrected component review

Accepted for current-owner, per-required-graph publication of native fixed graph features. GP1 and GP2 are resolved in the reviewed source and saved evidence. No remaining material blocker was identified within the stated scope. This does not admit saved reuse, representation closure, model fitting or empirical execution.

## Exact evidence

All 292 declared final bindings match current bytes. Final manifest SHA-256: `414793f01e4313fa71e64249cc9abe003f9380816689e83cda68778a4715d693`. All 289 frozen test-source bindings also match; `check02-sources.json` SHA-256: `8c46512f07aac25a8ef62fbcb12c3eb0e147f11d9d6d3ea3ff8f09f61aa6802d`. These are declared component/dependency inventories, not an empirical execution closure.

- `publication.py`: `e0ce2673fcca7d7fdb544ac3ed113b09e3d116fd44750ab1292eaf56028284da`.
- `encoded_hashes.py`: `302922b0c403817ccbb6665942ca9d28950a6fe13a8bb41fcc9a744ee77d6f2b`.
- `test_publication.py`: `58d127ba449b5420d40ec78ef82d0c99f9f71483554be6125d43ec30a6584aab`.
- `test_encoded_hashes.py`: `b5d087d2f64a5997a2b29816a3432a4d84cbfa8293429048ab502fab8da50da4`.

Saved `check02.log` reports seven methods passing in 659.820 seconds, SHA-256 `d6648770e1e4f5e93ade5f1a8fc26785909782a4f3ec04cffd4b2380fdba8419`. Saved `hash-check01.log` reports two methods passing in 0.054 seconds, SHA-256 `78456f02072d43211eae67239b188b5eb442edf71a148c9cd1c05a1a22a887fc`. The interrupted initial suite is not counted as passing. Missing-implementation evidence, reproduced defects, original source/test snapshots and the initial withheld review remain preserved. The latter retains SHA-256 `9b555bb35a0b15b22b54a36e4c3d68847c6b9ec81e13649a7bdc716f6efc759f`.

## Findings closed

GP1: exact native NPY headers and payload hashes are now computed from the admitted tensor-backed arrays before writing. The expected canonical manifest includes the complete tree, member mapping, context and array descriptors. The actual event's component hash and strict inspected manifest must match that expected manifest. Self-consistent early storage corruption can no longer become an accepted completion merely by being incorporated into the writer's hashes. The regression alters an NPY payload before manifest construction and now requires failure without complete.json.

The hashing helper uses header-selected C/Fortran payload order and bounded contiguous chunks, releasing block/iterator references between arrays. Saved helper tests independently compare descriptors with actual serializer output for C, Fortran, reversed/strided and empty-edge layouts at chunk sizes 1, 2 and 13. Its numeric scratch fits within the existing conversion chunk allowance; this is not a measured RSS claim.

GP2: the predecessor MCM proof snapshot now receives the registered MCM output policy's metadata cap, which Metadata retains for repeated leases. The regression uses the same valid JSON object expanded to 70,000 bytes, above the old default and below the selected 262,144-byte cap, and successfully joins the resulting proof hash.

## Assessed publication and limits

Selected policy, logical reservation, numeric/event limits and current graph membership precede feature preparation. Exclusive per-graph attempts preserve partial, failed and complete identities. The actual feature route, issued dictionary ticket and saved MCM proof remain mandatory. Native views share the already counted CPU tensor storage. Full feature provenance and explicit `native_graph_feature_v1` storage bind the event and completion proof. Final receipt leases and output inventory/signatures detect late drift; a late complete-plus-failed conflict is retained rather than returned as success.

The closed suite covers strict saved roundtrip, exact artifact/event sizes, completed/failed relaunch refusal, reservation/array/event preflight, intended artifact-cap failure, early and late storage drift, and predecessor cap propagation. Fixtures are tiny registered routes with mocked guard observations. They do not establish full-fold feasibility, aggregate/physical quotas, mapped populations, historical reuse or learned representation correctness.

Native graph_complete here stores fixed model inputs; it is neither a learned embedding nor completed representation. Saved use still requires an explicit admitted tensor materializer. Existing empty-edge downstream hashing compatibility remains unresolved. No old generic loader, model fit, top-level denominator closure or empirical release is authorized by this acceptance. Repeated checks do not provide atomic protection against continuous concurrent mutation.

Only source, compact evidence and declared compact-file hashes were read during this review. No tests, historical jobs, empirical numerical arrays, raw bodies or SQLite were read or executed. No scientific setting, financial budget or historical outcome was changed.
