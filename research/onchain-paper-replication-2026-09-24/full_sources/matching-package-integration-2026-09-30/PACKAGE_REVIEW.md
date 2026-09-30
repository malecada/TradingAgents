# Independent package promotion review

Accepted for the maintained, caller-owned pair component scope. No blocking promotion defect was found. This is not approval of registered pair admission, feature-journal integration, dictionary/MCM dispatch or an empirical job.

Source review was performed at HEAD `c1b4c2d35cf05bbdc7b2acd7b6f1502e3d31b873`. The six new modules and test file were untracked at inspection. The review read source, saved logs and compact metadata, reconstructed source hashes and compared source/AST definitions; it did not import or run the new code, rerun tests, open saved numerical arrays, change production files or commit anything.

## Derivation and semantics

Every original and maintained SHA-256 in `package-derivation.json` matches the corresponding bytes. `matching_hardening.py` and `matching_sparse.py` are byte-identical copies of their reviewed predecessors. The other changes replace path-based dynamic imports with maintained package imports. The removed `component` definition in `matching_checkpoint.py` was only the dynamic import helper. AST comparison shows no other function or class body changes. The typed graph hashes, checkpoint schemas 3, backend version 2, policy validation, scalar updates, normalization, rank ordering, sparse scoring and cleanup bodies remain unchanged.

`matching_identity.py:14–42` retains separate weekly/local domains, parent/center and exact node/edge order, dtype/shape/byte identity, including the empty-array branch. `matching_pair.py:61–84` retains absolute nonsymlink-contained exact references, compact manifest size/hash checks and ordered graph/config/context/backend/component identities. The numerical component fingerprint now naturally uses maintained module filenames and hashes. Consequently historical isolated adapter manifests are not directly interchangeable with maintained-package manifests, even though numerical bodies are preserved. No migration or cross-implementation checkpoint reuse is proved or authorized here. The package retains exact source-commit and policy equality on resume.

Normal imports share module objects through Python's import cache rather than privately loading dated paths. No import-time numerical or filesystem job is introduced by these modules. No default matching, registered policy, journal or dictionary/MCM caller was changed by this promotion. Source fingerprinting supplements rather than replaces admitted source/runtime verification: a caller's syntactically valid hash remains a declaration, and loaded code must stay frozen under the eventual registered guard.

## Saved verification

`red01.log` is a single test-module import error because the maintained module was absent. It is correctly a missing-module red, not 19 independently failing behavioral cases. `green01.log` records 19 tests passing in 0.302 seconds. The new test imports `tradingagents.research.onchain_replication.matching_pair` normally and incorporates the reviewed snapshot/local cases plus the zero-edge singleton case.

The inspected tests exercise directional scalar-score parity, soft-assignment byte equality and hard-assignment equality for actual tiny `NeighborhoodIndex` outputs; typed identity and old-schema refusal before numeric loading; exact completed-score reuse with solver entry forbidden; exclusive names and quotas; retained publication failures and parent reference; primary interruption preservation; and closure of an actual restored rank mapping. The singleton test saves, closes, restores and completes a one-node zero-edge pair. Mocked module attributes are scoped through context managers.

`focused01.log` records 117 passed and one skipped in 112.50 seconds. It explicitly states that 26 encountered files were withheld and that this is not the full legacy suite. This review accepts the saved focused result, not a new whole-suite or guarded resource result. The summary log alone does not enumerate every invoked module or establish current-branch broad coverage. No real-graph, Torch-equivalence, GPU, capacity-scale package or financial result was tested by this review.

## Remaining release boundary

The requirements in `REGISTERED_INTEGRATION_REVIEW.md` remain open: actual claim-derived owner and lease, verified failed-parent ancestry, exact latest journal references, publication-gap recovery, cumulative ancestor-inclusive reservations, backend-aware workflow/cache identity, and fatal unresolved cleanup before batch continuation. The current pair API remains an explicitly caller-owned component; its independent session counters and exact-reference checks do not implement those registered guarantees.

The six new package files expand `job.required_sources()` even when a graph job does not call matching. Graph10 gate-v2 therefore needs the already identified immutable gate-v3 source-closure review before dispatch. Old offline receipts can still establish unchanged historical files, but cannot be labeled new broad verification of these additions. Commit/source freeze and a named guarded offline result remain separate steps; this focused source acceptance permits preparation of them without enabling empirical matching.

## Reviewed hashes

| File | SHA-256 |
|---|---|
| `tradingagents/research/onchain_replication/matching_identity.py` | `f011658abf3b56b04a0ec33a7bdfed2c68e2e2e79791aa96c5ca7f8fd1653f89` |
| `tradingagents/research/onchain_replication/matching_annealing.py` | `c1331bf7fd6bc436c2663c626c69c6bcecffcc16a8e56992c9c6bcf520ab0b47` |
| `tradingagents/research/onchain_replication/matching_hardening.py` | `c0c4a2eb21ad62d3a966e8619d84370be388e1e4a402f7608fc91abb3f796312` |
| `tradingagents/research/onchain_replication/matching_sparse.py` | `06f2d312a1527f335decc8e0c4d1283448a28e783d5e64018d70e9bf3416883e` |
| `tradingagents/research/onchain_replication/matching_checkpoint.py` | `de8f7077e513105719fffcf6ea13e96bfb0199056acf0227ecf744df189ee35c` |
| `tradingagents/research/onchain_replication/matching_pair.py` | `3fc8a0666b2b4bf334411a85decd7dbf484b038827255714c6727ffe3846621c` |
| `tests/research/onchain_replication/test_matching_pair_checkpoints.py` | `587203f669d951d7722c9d8801d37e32b38f52518c828dc17f054c4278534427` |
| `research/onchain-paper-replication-2026-09-24/full_sources/matching-package-integration-2026-09-30/package-derivation.json` | `7d50f15cabb8296b31eef47dddb2c16bf38c2f2b6ab11dbe63e545df4d7fe1e1` |
| `research/onchain-paper-replication-2026-09-24/full_sources/matching-package-integration-2026-09-30/red01.log` | `e652ce34a44c297d42b5346bd7e45a18f36464888fb02788bd1a117e89f53eb4` |
| `research/onchain-paper-replication-2026-09-24/full_sources/matching-package-integration-2026-09-30/green01.log` | `f03ca231148d0801bc7adf4255e668c8455f6e736698f98c32aab739210240b7` |
| `research/onchain-paper-replication-2026-09-24/full_sources/matching-package-integration-2026-09-30/focused01.log` | `fcd4693acd1d73077044d273bb8dd8c4be336ef6cd1e0f68bdf807b76ba656bf` |
