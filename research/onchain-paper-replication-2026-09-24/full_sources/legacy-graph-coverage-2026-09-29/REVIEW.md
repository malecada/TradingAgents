# Independent review — legacy graph coverage

Reviewed September 29, 2026. Scope: `RESULT.md`, `evidence.json`, both coverage wrappers and their original compact lineage evidence. Independent metadata reconstruction used hashes, declared intervals/counts, original source code and retained closure copies. No transaction body, graph array, new test suite, empirical job or network resource was read or run. Only this review file was written.

**No material error or overclaim was found within the stated metadata-only scope.** The wrappers preserve two original completed graph identities and provide auditable coverage metadata for a later reviewed registration. They neither admit a new empirical run nor establish current array integrity.

## Independent reconstruction

All 24 inputs indexed by `evidence.json` match their recorded SHA-256 and byte size. Both coverage wrappers match their indexed hashes. Additional compact inspection checked the original gate, graph configuration, retained closure copies and historical source.

The original claim's `source_index` input is exactly `pilot_successor_02/source-index.json`, SHA-256 `18f2548bdec2602995935d951075162537b6369b8bf18647cdc7a96962cffc1a`. The gate hash matches the claim's registration hash. The gate's index and daily-map input records equal the claim records. Both phase intents bind this same source index and the corresponding seven daily maps. Every daily map's current hash equals its source-index member, original admitted input and phase-intent binding; each map's object key names the matching calendar date.

`plan_sha256` in these wrappers deliberately means the hash of that original source-index execution specification. It is not a modern graph-production plan or the separate `index_sha256` value inside the source-index JSON. `source_input` correctly retains the historical admitted name `source_index`; `source_manifest_sha256` is its file hash. This interpretation is explicitly disclosed in the result and evidence metadata.

Each week has exactly seven contiguous one-day intervals, from its Monday start to the following Monday. Wrapper members equal the source-index members in start, end, expected rows and mapping hash. Their seven hashes equal the graph manifest's complete source-hash set, not merely a subset.

| Week | Declared/decoded/raw rows | Admitted | Exclusions | Original graph identity |
| --- | ---: | ---: | ---: | --- |
| 2022-01-03 | 8,373,297 | 4,415,050 | 3,958,247 | `67ffff78a83d67b77d3fefce1bc7f6dc3a7cab0c80ac68d8c72e0c99a30022b8` |
| 2022-06-13 | 7,581,093 | 3,601,893 | 3,979,200 | `0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba` |

For both weeks, member rows sum to source-index expected rows, completed phase rows and graph raw count. Raw count equals admitted count plus all recorded exclusion categories; phase and graph exclusion dictionaries match. Wrapper/manifest configuration hashes equal the canonical hash of the originally admitted graph configuration. Recorded graph availability remains one day after the full seven-day interval ends.

Both phase results are complete and identify the original manifest hashes. The manifest, result and intent hashes also match their independent closure-index entries and the corresponding retained compact copies. The failed run terminal binds the original claim hash; closure binds that terminal hash, the original source commit and failed identity, records verified cleanup and prohibits retry. Original 109 cell dispositions remain 7 complete and 102 unavailable. This reconstruction does not retrospectively mark the 63 unfinalized source-day dispositions complete.

## What original execution establishes

The phase source at original commit `c6b568d4b1c177ab94ac37fbad462c2decc721c0` matches the preserved phase file (SHA-256 `0bc95f7e33d97485cd9e2fba6802dde168c26aa162b987ef762f9e28ee3a1522`). Historical `eth_source.py` checks mapping/member hashes, projected-range hashes, declared schema, each member's timestamp interval and row count, and the total decoded count. Historical `weekly.py` consumes the entire input iterator into SQLite before yielding a graph. Thus `next(build_weekly(...))` in the original phase does not bypass the decoder's trailing completeness checks. SQLite rejects duplicate transaction identity within that phase's full weekly stream. Separate weekly phases do not prove cross-week/global uniqueness.

Static inspection of the current `_verify_graph_coverage` schema and predicates is consistent with the wrappers. No validator or GraphSnapshot was executed by this reviewer. More importantly, this reconstruction supplies original provenance that the current metadata validator itself does not independently resolve merely from a syntactically valid `claim_sha256` or `plan_sha256`.

## Admission boundary and untested claims

Prospective reuse should bind the original graph manifest, wrapper, source index and compact lineage evidence in a reviewed registration. Actual use still requires bounded fresh graph-store verification under its admitted resource contract. Adding these metadata wrappers alone does not require rebuilding the graphs or reopening the terminal pilot.

No fresh array hash/content verification, raw-body recovery, archive-vintage correctness, historical point-in-time availability truth, wider-cohort global identity validation, full-size resource feasibility, downstream MCM/neural completion or financial result was established. The remaining seven pilot weeks and all full-study requirements remain pending. The result's qualifications correctly preserve these distinctions.

## Reviewed artifact identities

| Artifact | SHA-256 |
| --- | --- |
| RESULT.md | `5d7a2935c24aca63b4ff5d31732601af10d70379b045e30570f645521f72d241` |
| evidence.json | `c846e58f6cff5ab6363cec45d7782a92101fe8ee18e2230d016975227332e6f4` |
| 2022-01-03-coverage.json | `9d00af9ddfca34dae4431b0e25cdea676106e74074f865f3ed5f177321409f0b` |
| 2022-06-13-coverage.json | `764d3bae2fa292f12c52288242d668a413022d766ba6e34ab2efa1b4e55c5424` |
