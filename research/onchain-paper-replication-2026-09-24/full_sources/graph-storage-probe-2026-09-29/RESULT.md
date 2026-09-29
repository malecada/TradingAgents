# Synthetic graph storage measurement

The unmodified production weekly aggregator and graph store completed a fixed
250,000-row synthetic week with500,000distinct addresses,250,000distinct edges
and7sealed source boundaries. Random-looking SHA-256 identities exercise
nonsequential B-tree insertion; every transfer is admitted and has distinct
endpoints. No real transaction, price, label or historical SQLite body was read.

The workload took55.51seconds. The guard completed with child0 and verified
cleanup, recording617,586,688sampled peak memory bytes under1GiB maximum and
768MiB high, zero swap,3GiB host reserve,20GiB disk floor and600second wall limit.
The full offline suite was running concurrently, so timing is not an isolated
throughput estimate.

Disk sampling every20milliseconds deduplicated files by device/inode across the
exclusive output tree and the process's own open SQLite descriptors, including
unlinked `etilqs_` temporary files. Observed allocated peaks were144,723,968bytes
during ingestion,132,132,864during index/sort/construction, and244,158,464during
graph saving while the database remained open. Final retained allocation was
217,870,336bytes, including105,811,968bytes for the main SQLite file. The five
graph arrays contain112,000,640logical bytes, consistent with448bytes per row
plus NumPy headers in this all-distinct scenario. Synthetic SQLite and arrays
remain local evidence; compact manifests/receipts are versioned.

## Projection and limitations

The frozen target has8,841,688raw rows:35.366752times the synthetic row count.
Linear extrapolation of the measured overlapping peak gives8,635,091,845bytes.
Adding the largest original projected-Parquet page footprint215,748,608bytes,
an explicit30% scaling allowance2,590,527,554bytes, and256MiB for additional
metadata/monitoring gives an11,709,803,463byte incremental planning estimate.

The30% and256MiB allowances are engineering assumptions, not paper parameters or
measured bounds. A September29 observation left12,050,755,584bytes above the
20GiB guard floor, only340,952,121bytes above that planning estimate. Existing
raws, old partial databases and retained diagnostic files are already subtracted
from free space. The20GiB floor remains in addition to these estimates.

This is not a mathematical upper bound, a guarantee of fit, a released empirical
job or a completed Task8. Sampling may miss brief peaks. Full-size B-tree/sort
behavior, real decoding, actual graph cardinality and concurrent filesystem use
remain unmeasured. Linear RAM scaling is especially unsuitable: this synthetic
case deliberately maximizes distinct endpoints. The outer6GiB memory ceiling
must terminate a full-size pilot that cannot fit; scientific data must not be
truncated to force completion. A release review must explicitly decide whether
the controlled uncertain-feasibility measurement is justified. Fresh resource
and ownership checks remain mandatory before launch.
