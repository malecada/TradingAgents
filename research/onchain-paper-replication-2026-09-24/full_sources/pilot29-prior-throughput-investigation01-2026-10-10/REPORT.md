# FAILED28 prefix timing evidence

All 16 original 4,096-cell numeric summaries authenticate against both accepted outcome reviews and outcome13 selection. Total: **65,536 cells; 63,904 computed; 1,632 reused (2.490234%)**. Numeric calls sum **6569.758010832 s**; median **119.296494517 s**, range **115.586407495–3360.272647873 s**. FAILED28 remains failed: 65,536 journal/attempted sink cells, **61,440 confirmed post-sink cells**, zero whole MCMs and no training.

| Batch | Computed | Reused | Numeric s | Δ callback calls | Δ callback s | Callback % |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4000 | 96 | 3360.272648 | 28795 | 1602.536835 | 47.691 |
| 1 | 3936 | 160 | 116.915547 | 27872 | 68.422223 | 58.523 |
| 2 | 3904 | 192 | 151.417369 | 27714 | 86.863369 | 57.367 |
| 3 | 3936 | 160 | 120.361588 | 27872 | 69.908355 | 58.082 |
| 4 | 4000 | 96 | 116.469545 | 28192 | 68.661629 | 58.952 |
| 5 | 4000 | 96 | 118.231401 | 28192 | 69.558900 | 58.833 |
| 6 | 3968 | 128 | 310.983056 | 28057 | 162.510780 | 52.257 |
| 7 | 4064 | 32 | 135.587044 | 28512 | 78.675368 | 58.026 |
| 8 | 3936 | 160 | 194.627590 | 27880 | 106.586029 | 54.764 |
| 9 | 4000 | 96 | 1200.988975 | 28396 | 582.029708 | 48.463 |
| 10 | 4064 | 32 | 117.582931 | 28512 | 69.313350 | 58.948 |
| 11 | 3936 | 160 | 115.586407 | 27872 | 68.336528 | 59.122 |
| 12 | 4000 | 96 | 116.903566 | 28192 | 68.979107 | 59.005 |
| 13 | 4064 | 32 | 118.058065 | 28512 | 69.200466 | 58.616 |
| 14 | 4064 | 32 | 158.886899 | 28515 | 88.990855 | 56.009 |
| 15 | 4032 | 64 | 116.885380 | 28352 | 68.639009 | 58.723 |

Adjacent cumulative-counter differences total **451,437 callbacks / 3329.212511672 s / zero recorded callback failures**, 50.675% of numeric-call time. Residual 3240.545499160 s includes noncallback work and waits; it is not pure solver CPU. First-batch zero baseline and batches 1–2 deltas agree with existing accepted timing reviews. No cumulative counter was summed across batches.

Batch 0 accounts for 51.148% of numeric time; batches 0 and 9 together account for 69.428%. Inclusive-quartile Tukey upper fence 244.186352 s flags batches [0, 6, 9] descriptively. Cold start is a possible contributor, not an established explanation; batch 9 shows the tail is not confined to startup. No graph geometry is recorded in these summaries.

| Conditional repeated-prefix arithmetic | Numeric-only days for 415,968,128 cells |
|---|---:|
| all16 | 482.631602 |
| later15_excluding_batch0 | 251.495666 |
| last8 | 314.349440 |
| Repeat fastest observed batch | 135.860476 |
| Repeat median observed batch | 140.221319 |

These values are conditional prefix arithmetic, **not ETA, durable whole throughput, population bounds or capacity**. Later15 total 3,209.485362959 s, median118.231401199 s; later batches substantially improve the first-batch-only picture, but do not establish practical full-feature feasibility. Even repeating the fastest observed batch remains over 135 numeric-only days; reaching 30 days would conditionally require another 4.529× at that fastest-prefix rate. This is a comparison threshold, not a requested change to the goal or limits.

Native elapsed 12784.106644162 s exceeds summed numeric calls by 6214.348633330 s. That aggregate gap cannot be called offload cost alone. The accepted 3,532,800-byte original group archive/recovery/retirement is real, while final authority refresh failed; journal, admission, transfer/recovery, spool publication and training costs are absent from numeric-only scaling. Node degree, reuse and cold-start skew remain unknown outside this tiny prefix. Pilot29 uses a changed frozen source; no performance transfer is claimed.

Authentication uses the existing OUTCOME_REVIEW01 (2f1654a6…) and RETURNED_GROUP_REVIEW01 (40a43b52…) in `real-data-pilot-full28-outcome-review01-2026-10-09`. Each original summary hash and each archived closure member name/size/hash/range is retained in MEASUREMENTS01.json. Original matching bodies were retired by the recorded protocol; closure proof is reused from the accepted returned archive review, with no archive/arrays/binary payload reopened. These reviews and all16 summaries match outcome13 SELECTION13 rows. Capture time: 2026-10-09T15:04:25.977298+00:00; actual fresh return metadata: 2026-10-09T15:05:48.888555+00:00. Exact batch publication times are not recorded. First-batch review was 2026-10-09T12:41:37.342710+00:00; batches1–2 review was 2026-10-09T12:53:55.694953+00:00.

Unverified here: outcome13 independent acceptance ade5b90a is supplied by Root, not independently reopened; archive/body reencoding and binary source-token/origin/score joins reuse accepted reviews. Provisional receipt streams, graph-purpose reconstruction, solver correctness and cache equivalence were not recomputed. No current remote-availability or external backup of these newly written files is claimed. Exact evidence paths, hashes, scope and qualifications are in MEASUREMENTS01.json.
