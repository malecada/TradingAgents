# Reevaluation provenance and run controls

The common wrapper requires committed source, gate and correction policy before creating a family output directory. A previous start marker refuses a second invocation, including an incomplete run. Inputs must resolve inside the two registered source roots. Every consumed file is SHA256 hashed before use and checked again at completion. Market Parquet rows are filtered before materialization, with unique ordered UTC indexes and frozen date limits. The NLST4 settlement exception is limited to the registered ETH five-minute file and existing cohort.

Completion requires exactly the registered cell IDs, without duplicates. Runtime package versions and thread settings, source commit, gate/policy hashes, input hashes and output hashes accompany each immutable result. Strict JSON serialization is checked before any ledger append. Independent families serialize ledger writes through a file lock.

Regression evidence includes rejected unregistered sources, changed inputs/source/gate, duplicate or incomplete cells, preexisting output, post-bound market reads and unserializable results. The common suite has11 passing synthetic tests. Integrated common/accounting/PRX and related accounting, inference, registry suites passed119 tests in14.12s (verification/integration-accounting-prx.log).

This is an integrity fence, not a filesystem sandbox. The numerical wrappers were also reviewed for fixed source paths, no network operations, frozen candidate counts and no promotion. An exceptional disk failure during ledger append can leave a partial completion; the preserved start marker requires identity-aware recovery rather than deleting artifacts and rerunning blindly. Original gates, raw stores and previous results remain unchanged.

Final integration of all four wrappers and related accounting, registry, inference and causal-DEX suites passed **171 tests in19.03s** (`verification/final-integration.log`). This is additional to the repaired base's prior779-test offline verification.
