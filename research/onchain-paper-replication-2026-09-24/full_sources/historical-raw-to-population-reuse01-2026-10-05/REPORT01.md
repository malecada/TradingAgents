# Historical raw reuse inventory

The exact pinned historical fullpanel plan supports all 1,096 ETH source dates in
2022–2024, with 1,221,389,903 declared transaction rows and 59,083 unique retained
span physical identities. No metadata/extent failures occurred. Source JSON
hashes, object ETags, declared range membership and current regular-file extents
were checked by the existing `prepare_pilot_sources.py` functions `ordinary`,
`special` and `span`, extracted unchanged without importing a launch module.
The new bounded driver reads only declared JSON metadata and stats raw bodies.
No raw body was copied, rehashed or decoded. Original declared payload hashes
are preserved for the real decoder to verify later.

`daily-maps/` contains 1,096 concrete projected_zstd inputs referring directly to
retained Main/external raw paths. `weekly-inputs/` contains 156 seven-day Monday
partitions (2022-01-03 through 2024-12-23), comprising 1,216,561,898 declared rows.
January1–2 2022 and December30–31 2024 remain present partial-week boundary days,
not unavailable sources. No repeated object-key/ETag date identity or distinct
paths sharing a physical span identity was observed. These are file identities,
not runtime objects or original eligible row identities.

| Fixed fold | Raw-supported / required weeks |
|---|---:|
| 2018 | 0 / 161 |
| 2019 | 0 / 162 |
| 2020 | 0 / 161 |
| 2021 | 0 / 161 |
| 2022 | 51 / 161 |
| 2023 | 103 / 161 |
| 2024 | 156 / 162 |

Exact required/missing timestamps are in `INVENTORY01.json`, derived using the
actual unchanged `calendar.expected_week` and `population_assembly.required_weeks`.
The 2024 gap is six Monday weeks 2021-11-22 through 2021-12-27. Earlier missing
weeks are absent from this exact retained plan; this is not an all-source absence
claim. This inventory does not expand the previous study-artifact-only graph
inventory into a false claim of missing historical raw data.

## Concrete integration seam

`GRAPH_PLAN_DRAFT01.json` and `INPUT_BINDINGS_DRAFT01.json` bind 147 currently
unproduced weeks through the existing registered `graph_production` build route:
147 weekly source roles, graph configuration, exact original ETH schema and plan
(150 roles total). The existing decoder consumes the emitted projected_zstd
mapping, validates stored/raw hashes and expected rows, and the existing producer
provides its admitted scratch directory. No decoder/aggregation/model change is
needed. The original double-valued wei representation remains approximate; no
exact-wei assertion or previous20-feature substitution is introduced.

Nine existing graphs are excluded from the build draft. `EXISTING_GRAPH_REUSE01`
pins their manifests and seven existing coverage proofs. Two legacy pilot-02
weeks (2022-01-03, 2022-06-13) lack `graph/coverage.json`, which the current reuse
validator requires. The attempted nine-graph reuse draft stopped on that missing
file; `PREPARATION_FAILURES01.json` preserves the failure. No proof was fabricated
and no duplicate graph build authorized. Root must bind genuine retained
aggregation/coverage evidence for these two legacy graphs before current reuse.

Root must register exact source inputs/windows/output/resource bounds and obtain
the required genuine authority before any new graph transform. These drafts do
not assert feasibility of all147 weeks in one run. Original fullpanel feature
extraction remains closed. Missing earlier raw periods require a separately
bound source inventory/provenance; the existing public acquisition implementation
is `research/onchain-graph-2026-09-16/comparison/graph_capture.py`, using the
historical plan's AWS public blockchain endpoint and explicit date/object range
inventory. No acquisition or replacement fetch occurred here. BTC raw coverage
outside the prior scoped graph census was not investigated by this ETH task.

## Price metadata, checks and limits

`PRICE_METADATA01.json` pins retained Coin Metrics ETH/BTC capture manifests,
source revision, 2016-01-01–2025-01-01 requested interval, declared response
hashes and actual file sizes. Response values/date membership were not read or
verified. Historical Binance prices cannot silently substitute for the selected
source. Source publication/vintage remains unverified, dates already exposed,
and full raw off-device backup unverified as stated by REPLICATION_SPEC.

Six focused offline controls passed with Main `.venv/bin/python -B`: metadata
hash tamper, half-open range framing, changed stored extent, incomplete week,
no numerical imports, and actual fixed-plan/calendar denominator. Tests use
synthetic bytes only; no Owner/Binding/ResearchRun was constructed. Actual raw
integrity, complete eligible train/test populations, price/label joins, full
original graph representation and empirical resource capacity remain unresolved.
Only this new directory was written. Source pins and every emitted body are
listed in the seal; metadata preparation grants no launch or scientific authority.
