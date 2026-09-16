# Independent capture closure review

Execution source: `4ea20258a72286721157736b12c7147423b26214` in
`/home/malecada/Data/onchain-research/TradingAgents-onchain-comparison`.

At 17:38:53 UTC on September 16, 2026, independent spot verification passed
all 38 month cells, 76 request/intent pairs, 1,158 daily rows and 268 retained
files. Original response bodies total 81,893 bytes. The checker independently
verified stored/raw hashes, lossless decompression, ZIP/checksum agreement,
single CSV member identity, the twelve-field schema, exact calendar coverage,
and the milliseconds-to-microseconds timestamp convention. The complete spot
artifact manifest and every source cell were reconciled with the actual files.
Price and volume fields were not interpreted; no labels or models were run.

Graph acquisition remained active at that initial stage. Its original spot-only
review is preserved under `spot_stage` in `CAPTURE_REVIEW.json`; the following
terminal review supersedes the earlier pending status.

## Terminal verification

Independent closure passed at 17:50:18 UTC. All 46 registered cells are complete:
seven graph days, 38 spot months and the complete-manifest cell. The structural
lifecycle verifier independently reports 47 outputs, zero unavailable cells and
a complete terminal receipt. The execution checkout HEAD, claim source, design
source and terminal source all equal the fixed source above. The distinct raw
capture allowance is consumed at prior 6/cap 7; no replay is authorized by closure.

All 940 retained capture files match the declared manifest. Received original
bodies total 1,032,495,329 bytes; retained compressed bodies and metadata total
754,265,130 bytes. Request receipts were independently counted, not only read
from the summary: 219 graph requests plus 76 spot requests equals 295. Every
receipt is successful and binds an immutable intent and verified raw/stored
blob. Each graph date's request count also matches its actual receipt count.
The raw-manifest SHA256 is
`212be94570af8e53f2ebae38a46bb5092373d7b7fa5452e845fb0eb40383458c`.

The checker reconstructed the graph column ranges directly from retained
Parquet footers and matched every requested range, size, conditional ETag,
object identity and source-cell row/byte denominator. Blocks and transaction
columns were inspected as schema/footer metadata only. The independent checker
imports no production capture or lifecycle modules; structural lifecycle
verification was separately invoked in the same guarded process.

The unchanged 8 GiB aggregate sampled-RSS/two-CPU guard protected verification:
3.6649 seconds, 281,169,920 bytes sampled peak RSS, exit zero and no limit event.
The original capture receipt reports 703.1634 seconds, 287,535,104 bytes sampled
peak RSS, exit zero and no limit event. Both are sampled observations, not
proof of an exact peak or minimum memory need. `CAPTURE_CHECK_RESOURCE.json`
preserves the independent check's resource receipt.

No unresolved material capture-integrity finding remains. The first tranche is
ready for exact-hash import and backup verification. Remote recovery was not
checked here and remains false in the machine-readable review until separately
verified. Full-history retention plans are future preparation, not an admitted
extension of this capture.

Historical publication/vintage, canonicality and numerical graph integrity,
completion-day motif features, unfinished 2024 pilot continuation, price-field
admission, fitted predictions, inference, fees/funding and profitability remain
untested. No price fields, transaction rows, labels or model outcomes were opened
by this review. Capture integrity does not establish predictive value or a
validated strategy.

## Imported-copy verification

At 17:53:04 UTC, an independent streaming SHA256 comparison verified every one
of the 990 imported files against both the retained Data source and the
consolidated destination. Total imported size is 754,630,488 bytes. Exact
membership comprises 940 capture files, 49 lifecycle files and the original
capture resource receipt; neither tree has omitted or extra members within
those directories. No duplicate manifest entries or symlinks were found.
The import-manifest SHA256 is
`efab7eff5b4226888925617980299ab44266d37cea39cc4d2b7c248f65660e40`.
The original execution files remain unchanged. This verifies the local import;
remote recovery still requires the separate push/readback check.
