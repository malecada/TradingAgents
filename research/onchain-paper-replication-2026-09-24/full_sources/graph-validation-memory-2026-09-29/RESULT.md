# Duplicate-validation memory reduction

Implemented and independently reviewed. Exact duplicate rejection uses sorted
node IDs and lexsorted endpoint pairs instead of full Python sets. Endpoint
comparisons use blocks of65536 adjacent pairs with one-pair overlap. Graph
contents, dtypes, order, hashes and conservation checks are unchanged.

81 focused tests pass, including independent pair-set oracles, signed/unsigned
endpoints, Unicode IDs, block-boundary duplicates, canonical hash parity and
registered ETH/BTC graph production. The separate200,000-edge synthetic diagnostic
reduced peak traced duplicate-check allocations from29.18MB to3.70MB; node-ID
checks changed from12.58MB to2.40MB. This excludes input construction and other
validation work, and does not measure full-pipeline RAM or real-data speed.

Sorting remains linear in memory and GraphSnapshot copies/full-population
loading remain unresolved. Source bindings, all red/green attempts and the
synthetic measurement are retained. Guards ended with verified cleanup. No
financial fit or empirical resource claim was started.
