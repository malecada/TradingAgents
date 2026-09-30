# Independent conditional preservation preparation review

September 30, 2026. **Accepted as prospective fallback preparation only. No operation is released by this review.** HEAD remained `f07509f6303f5449912673b0f433335b610f8eb6`; all 62 active storage05 bindings independently match. Storage05 owns the graph07 ledger and must finish without overlap or interruption.

The sole candidate is the closed graph08 aggregation ledger, exactly **3,237,568,512 bytes**, with original artifact-index SHA-256 `be331be3ea8ee90357dd29ab67d29521d0afa1fc6c737e1a32a52c4440d3d11f`. Its unchanged compact index, claim, terminal, owner and successful guard join correctly. The original monitor and cgroup are absent. Current stat identity matches the manifest; the source is an untracked nonsymlink with one link and no SQLite journal, WAL, shared-memory file or remote sidecar. This review did not open or rehash its body.

All 30 preparation bindings match. Exact comparison with storage05 finds only the graph07-to-graph08 source path and completion description changes in the worker, and the corresponding path change in its fixture. Transport is byte-identical. The saved eligibility log reports four passing synthetic checks in 0.015 seconds. These are inherited eligibility checks, not a new transfer/recovery test or proof of future network completion.

The reused preservation helper checks the original full SHA, uploads to an exclusive remote identity, downloads and verifies the complete recovered body, and roundtrips restoration metadata. Fsynced verified evidence and an original-path restoration sidecar precede final source/path/descriptor revalidation and unlink. Successful scratch is removed only after eviction evidence; failures retain evidence and remaining scratch. Aggregate completion is published only after its own metadata roundtrip. A failure after unlink requires receipt-based reconciliation and restoration when needed, not an automatic retry or a claim that the source necessarily remains local.

Limits remain 256 MiB maximum, 192 MiB high, zero swap, 3 GiB host reserve, 3.5 GiB startup, 10 GiB disk floor, 14,400 seconds and the existing two-CPU guard. Full local recovery scratch requires **13,991,763,968 free bytes** (floor plus this ledger plus 16 MiB). The 4 GiB file ceiling, 8 GiB payload allowance and 5,400-second transport deadlines are unchanged. They are limits, not promised throughput or successful recovery.

The added prospective preflight differs from storage05 only by requiring accepted storage05 rather than storage04 closure. Its previous-graph helper is byte-identical and requires accepted graph08 producer/verifier evidence with absent owners. The preflight also requires pushed committed dependencies, the sole exact local connection hash exception, an exclusive unused execution identity, no active replication unit, a fresh December capacity deficit, adequate scratch and startup RAM. These helpers are not yet covered by the initial 30-file manifest; their exact bytes and all actual predecessor evidence must enter the future reviewed release bindings. No release/context manifest, guard or intent exists at review. The preflight was inspected, not run.

Indirect dependency review finds no current replication claim consuming this ledger body. Storage05 targets graph07, and prepared graph09 consumes compact graph08 closure evidence and original December sources; its prior-graph check does not reopen the ledger. Original graph08 artifact-index paths and hashes remain immutable and will refer to a cold body if preservation eventually occurs. Any later body verification must restore and hash-check the exact bytes first. The worker's direct active-input scan is not a universal dependency resolver; the contextual check must be repeated at final release.

Before any launch, actual storage05 completion must receive independent acceptance. Then recheck free space: **skip storage06 if December's 22,103,159,134-byte requirement is met**. Otherwise assemble and independently review the concrete release with actual accepted storage05 evidence, commit/push outside the active freeze, verify all bound bytes/owners/resources and launch at most once. If storage06 is needed, graph09's unreleased preservation prerequisites must be revised and reviewed, and actual accepted storage06 closure bound before gate generation. No present arithmetic shortfall substitutes for those steps.

Reviewed hashes:

- `bindings.json`: `a3e52364d6d22162279c2ab2488a9213fc841b3414f52cb7fc10dde7939fd93b`
- `manifest.json`: `d72b40660286e2782e9b2967bb97c9666b52f161b5695fc1ea7fa8a2c36e0237`
- `offload.py`: `eecb96752e184aee8b6e60371ffa14a1ed25bed035a1aee1ee99542871f55e59`
- `transport.py`: `ee551abbb81bec2b42355ce073c2a570d6ed0b37bd763b047b539f8c1148de16`
- `README.md`: `39294c05e21e5973d8e145be0a76220108a40ada203967dcc39d6d06c32b3ece`
- `preflight.py`: `55e6287a8f2912bc710f9c92b123adc4d3a79f74aed190cc9b2b27df8d851ab1`
- `previous_graph_requirement.py`: `9ee7f1c516c05c2b60f34aeeaf214c02ec904e947a0a7fee1d471829ceac34e7`

Only this review was written. No tests, helper execution, body reads, remote requests, launch, source edits or commits were performed. Connection metadata was hash-checked without inspecting or printing its contents. No reclaimed capacity, future recovery, graph09 admission or financial result is claimed.
