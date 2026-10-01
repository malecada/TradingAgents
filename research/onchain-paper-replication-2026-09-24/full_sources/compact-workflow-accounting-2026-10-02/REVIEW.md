# Independent static accounting review

Accepted as conditional retained logical-payload arithmetic only. No material arithmetic error or missing term within the explicitly selected lower-bound scope was found. This is not resource or empirical admission.

The four source/input hashes recorded in lower-bound01.json match the inspected files. The pinned prior accounting input hash matches inputs02.json. All nine unique week rows were independently joined to that metadata's actual node counts: each cell count is exactly nodes × 32, and the two-copy matrix term is twice its recorded float32 MCM payload. No graph array, label or outcome body was read; no numerical experiment or test suite was rerun.

Independent reconstruction from the format declarations and source behavior gives:

| Retained payload | Bytes per completed cell | Nine-graph bytes |
| --- | ---: | ---: |
| Pair log begin and completion, 168 bytes each | 336 | 194,039,365,632 |
| Retained score tail record plus float64 batch | 80 + 8 | 50,819,833,856 |
| Raw float32 MCM output plus graph-artifact float32 matrix | 4 + 4 | 4,619,984,896 |
| Total | 432 | 249,479,184,384 |

The total denominator is 577,498,112 cells and at least 1,154,996,224 pair events. Every row and total in lower-bound01.json matches this independent calculation. The total is 232.34559631347656 GiB, correctly rounded to 232.35 GiB. The smallest selected row is 22,614,280,704 bytes. Tail and batch storage remain retained, and the output and graph artifact are distinct saved matrix copies; the calculation is not accidentally counting only transient in-memory copies.

The assessment correctly excludes progress/checkpoint state, metadata and headers, filesystem allocation, dictionary work, graph inputs and saved edges, scratch/model state, prior attempts, failures and backup staging. These omissions make the result a lower bound, not a usable whole-workflow reservation. In particular, the earlier score accounting's metadata allowance is intentionally absent here rather than silently presented as covered. Actual completed iteration-cap results still require begin and completion; additional progress only increases the event term. Dictionary pair count reuse does not reduce the explicitly assumed full MCM denominator.

The quoted free-space observation is an author-recorded transient observation, not independently reconstructed here. Taking that observation and the unchanged local retention format as stated, the smallest row already exceeds its available bytes before the 10 GiB floor or omitted costs. A remote backup does not by itself satisfy the current local same-device writer. Physical allocation, peak-live behavior, compression/offload feasibility, I/O/runtime and host capacity remain unmeasured. No population, source transition, checkpoint disposition or resource amendment is adopted by this calculation.

Direct reviewed hashes:

- lower-bound01.json: `cae2eaa2b7ae503eb0921fd0d1b95ef73bedc745a1578a8791683dcd26151255`
- ASSESSMENT.md: `c0f69ce51713ec103ed2a221d5fa8d86fd2779ac1546a3451c2aa06397b03864`
- Current score_tail.py, confirming the unchanged 80-byte format: `9e3cffff04c6e6186aa04f7da66443007b84b9174756671dcb11d9a6c95bc8ad`
- Current score_batches.py, confirming float64 payloads: `69f6551049e6220f327177f9379e0ddb1144fb66da2fac24814fbb367a0041a2`
- Current compact_mcm_output.py, confirming the separate float32 output: `d462f271dc688e16321a52ed493aa8d81ca890974ccbf2fef209b4764293d393`

The prior score accounting pins historical source versions. Their retained formats were checked against these current implementations; no assertion that those old source hashes equal the current cleanup-corrected files is made.
