# Independent corrected legacy array-checker review

Accepted for the isolated numerical/hash/extent checker component. AC1 is closed; no remaining material blocker was identified within this bounded scope. The initial REVIEW.md remains unchanged, and its numerical/extent observations and untested boundaries still apply. This is not empirical-array correctness, metadata admission or execution release. Only this review was written; no tests/jobs, empirical arrays/raw bodies, frozen source edits or commits were performed.

The sole implementation change at arrays.py:191–195 handles a rejected NpzFile explicitly. The finally block calls close() and verifies both zip and fid are cleared, while preserving the existing memmap-close path and all-resource iteration. Cleanup exceptions or retained handles become visible RuntimeError failures rather than success. The allowed NPY schema is unchanged; an archive still fails the memmap/extent check.

The new test at test_arrays.py:90–100 creates a real NPZ archive at edge_aggregates.npy, updates declared bytes and file hash, reseals the expected manifest, and records the actual np.load result. It requires rejection and closure of both returned archive/file handles. Retained red02.log demonstrates the previously open ZipFile, with one failure among12tests. Closed green02.log reports12passes in0.153seconds. Existing success and numerical-failure mapping cleanup tests also pass. No tests were rerun by this review.

The preserved arrays.py.original and test_arrays.py.original match the initial reviewed hashes exactly. The correction changes no identity serialization, numerical tolerance, dtype/shape/count rule, file/hash/byte budget or historical source. Final reviewed artifacts are:

| Artifact | SHA-256 |
|---|---|
| arrays.py | `7be012596952f10fc0795397a9da2ceb88b66135cd034bc3021b31d775242735` |
| test_arrays.py | `ed96dc612f78d193d7ee79245a95f077b36601821617d8b209170c5ec1c71ed5` |
| red02.log | `bdaf577ba3a2fc39394325dde1a3a428723c60fdd4203783c8de1441ddab6055` |
| green02.log | `0005f30f0f6adb8fb1a6484b669a6e710a902a280e393b69ae04bd1a4f3cbdf7` |
| Initial REVIEW.md | `5c0766ebb6f122d54a641bf53755049bd727164c9bd399cac1987b5d8deb3e38` |

The unchanged tiny-fixture checks do not prove empirical graph arrays, raw transaction/exclusion semantics, complete historical claim/phase/coverage/config joins or whole-process resource feasibility. Explicit stable source/input ownership and the future guarded metadata adapter remain requirements. Additional malformed-header/late-mutation/chunk-boundary and cleanup-failure fixtures may strengthen verification; no additional defect is asserted from those gaps alone.

A future release must bind this exact source, its synthetic evidence, both reviews, original failed-claim denominator and individually complete graph phases, external coverage, raw/canonical graph configuration, runtime and wrapper. It must preserve one exclusive attempt and close mappings between graphs. The current corrected offline run at source0c100035b96b6e50cf9231d8b018eb67d0bcb2c1 retains its own freeze; this isolated acceptance neither modifies its source/inventory nor authorizes concurrent empirical verification or a repeated identity.
