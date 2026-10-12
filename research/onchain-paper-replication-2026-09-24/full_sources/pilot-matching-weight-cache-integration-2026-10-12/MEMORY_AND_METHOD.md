# Single-pair agreement reuse

The candidate retains the original 48 temperature iterations, ordered edge
accumulation, row/column normalization, hardening, checkpoints, operation budgets
and fixed C05 tolerances. It caches only half-agreement values produced by the
existing NumPy helper for the same immutable feature pair. These values do not
depend on the changing assignment matrix. Every contribution still multiplies
the current assignment and accumulates in original order.

The new numeric policy is explicit and default-off. Existing scalar, compiled,
NumPy-v1 and 256 KiB adaptive-cache routes remain available. No original motif,
sample, data window, outcome or spent identity is rerun or replaced.

The new policy reserves 32 MiB for retained weights, validity and bookkeeping,
plus 64 KiB of additional bounded scratch. It owns at most one pair and must
release references explicitly even if a closed session remains reachable. The
cache is not serialized; a restored session recomputes its weights. Cumulative
allocation/release counters are distinct from live bytes and measured peak RAM.

The current numeric reservation has no slack: 289,981,568 output bytes plus
461,349,748 buffer bytes equals 751,331,316 bytes. Selected v2 therefore needs
784,951,284 bytes, an explicit additional 33,619,968-byte reservation. Both
per-graph validation and whole-pilot validation must refuse insufficient funds
before allocation. This derived reservation changes; the native 6 GiB maximum,
5 GiB high watermark and all other job limits remain fixed. Physical fit has
not been established by this arithmetic.

The synthetic baseline profile preserved all 48 temperatures without enabling
a Python profiler, which would disable existing guarded fast paths. In its
131,072-product case the wrapped original agreement helper accounted for
49.98% of the measured advance/hardening interval. The wrapper adds overhead;
the interval excludes setup, scoring and production authority. This motivates
the candidate and is not a production speed estimate.

Independent source review, numerical comparison and a finite paired benchmark
are required before installation. Future empirical use also requires exact
source/configuration/registration, the new memory charge, complete entry
preservation and release. Whole-pilot throughput and memory remain unmeasured.
