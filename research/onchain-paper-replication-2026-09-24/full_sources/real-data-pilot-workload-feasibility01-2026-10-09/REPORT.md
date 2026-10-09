# Seven-MCM workload feasibility — bounded metadata investigation

Measured prefix throughput does not plausibly support completing the representative seven-MCM workload within the current eight-hour envelope on this machine. This is a conditional feasibility finding, not an unbiased runtime forecast or proof that every later neighborhood has the same cost. An orders-of-magnitude throughput gap remains; a small constant-factor change alone does not close it under the observed-prefix assumption.

| Graph week | Observed nodes | Motifs | Required scalar comparisons |
|---|---:|---:|---:|
| 2022-05-02 | 1,878,300 | 32 | 60,105,600 |
| 2022-05-09 | 2,265,481 | 32 | 72,495,392 |
| 2022-05-16 | 2,048,710 | 32 | 65,558,720 |
| 2022-05-23 | 1,875,043 | 32 | 60,001,376 |
| 2022-05-30 | 1,581,441 | 32 | 50,606,112 |
| 2022-06-06 | 1,581,761 | 32 | 50,616,352 |
| 2022-06-13 | 1,768,268 | 32 | 56,584,576 |
| **Total** | **12,999,004** | **32** | **415,968,128** |

The exact pinned graph manifests match ALL_INPUT_REFS01 and draft02. Each node count was independently checked against the existing count metadata and freshly observed node_ids and node_features NPY headers. Fourteen bounded headers were read; no array payload was decoded or hashed. Full-array SHA values are inherited authenticated manifest declarations, not newly verified payload integrity. The pinned original dictionary metadata contains exactly32 representatives.

Current compact_mcm computes rows × motifs. The actual imported kernel loops over every center in range(n), then every representative; it invokes workload.score once per cell and requires completed rows=n and cells=n×k. Thus32 refers to motifs per node, not32 sampled nodes. The diagnostic1024 acknowledgement limit is an intentionally partial measurement and supplies no complete-MCM or model credit.

## Conditional throughput sensitivity

One live23 checkpoint was read once: **739 pairs / 1948.568s = 0.379253 pairs/s**. Its checkpoint is a sampled watermark, not the current process counter. The closed22 retained checkpoint is **1024 / 4218.814s = 0.242722 pairs/s**; its later final matching elapsed4224.698s is distinct and was not substituted.

| Scoring-only target | Required comparisons/s | Multiple of live23 prefix rate |
|---|---:|---:|
| 8 hours | 14,443.34 | 38,084× |
| 24 hours | 4,814.45 | 12,695× |
| 7 days | 687.78 | 1,814× |

At an unchanged live23 prefix rate, pure division gives 12,695 days (about 34.8 years); the closed22 checkpoint gives 19,835 days. These deliberately conditional figures express the scale of the denominator; they are **not completion estimates**. Startup, remaining graph loading/extraction, archival/recovery and neural training are not budgeted by this calculation. A complete seven-MCM run also needs its own full storage/retention capacity; the accepted one-stage diagnostic reservation is insufficient authority.

The prefix is ordered and censored. Neighborhood sizes, edge-product counts and optimization eligibility can vary substantially over nodes and motifs, so the observed rate cannot establish an unbiased population mean, tail bound or hardware scaling factor. Inclusive phase clocks overlap and must not be added or interpreted as exclusive CPU attribution. No causal speedup estimate is inferred from the22/23 comparison. No denominator was reduced, no new sample or experiment was run, and no registration, source, active process or budget was modified.

Exact manifest/count/source/header hashes, the single selected-field checkpoint snapshots, and unrounded arithmetic are retained in EVIDENCE01.json. Investigation used stdlib only with256MiB AS,4MiB FSIZE,30s wall cap, CPUs3/4 and nice10. Main/native23 remained untouched.
