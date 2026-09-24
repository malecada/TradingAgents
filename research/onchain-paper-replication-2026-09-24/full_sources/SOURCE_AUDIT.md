# Extended source audit — preparation only

Public AWS documentation was retained with source URLs, retrieval timestamps and
hashes in docs/manifest.json. The registry advertises Bitcoin and Ethereum under
aws-public-blockchain/v1.0, in us-east-2. This is a candidate source, not proof of
complete2016–2024 coverage. No new object listing, footer or transaction body has
been acquired by this extended-source preparation.

The BTC schema supplies nested inputs/outputs, including spent transaction hash,
output index, address and value. It describes Bitcoin Core22.0 and daily Parquet
partitions. Amounts are DOUBLE in BTC. Existing decimal-text admission must not
silently treat those values as exact satoshis.

A proposed, tested adapter recovers a unique satoshi-grid preimage from a valid
binary64 BTC amount: calculate the nearest integer to its exact rational value
multiplied by1e8, then require that correctly rounding that integer/1e8 to binary64
reproduces the original value exactly. Reject off-grid images, ambiguous ties,
nonfinite values and amounts outside0–21million BTC. At this bound a binary64 ULP
is below one satoshi; adjacent valid amounts remain distinct. This establishes a
unique representation inverse, not independent proof of the producer's ledger
values. Bounded prevout overlap reconciliation and duplicate-spend checks remain
necessary. The adapter is not yet admitted for empirical data.

Sources: [BTC schema](https://raw.githubusercontent.com/aws-solutions-library-samples/guidance-for-digital-assets-on-aws/main/analytics/consumer/schema/btc.md),
[AWS registry](https://github.com/awslabs/open-data-registry/blob/main/datasets/aws-public-blockchain.yaml).

Next: reviewed finite asset/year registrations for public metadata and bounded
footer acquisition, explicit byte/request/disk limits and every required date/field
in the denominator; retain ETH2022–2024 sources already acquired. Actual sizes,
precision, chain coverage and feasible full-history storage remain unmeasured.
