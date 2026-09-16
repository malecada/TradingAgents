# Ethereum graph source feasibility — September 16, 2026

**Public access and the required schema are feasible for a bounded prototype. A usable historical feature panel, graph-computation benchmark and predictive advantage have not yet been established.** This result supports continuing the reduced graph-information study; it does not support implementing the original entity-classification platform.

The source-only claim `eth-graph-source-20260916` ran once in the detached `TradingAgents-onchain-source` checkout at `5f318f545d230babdfee995b720a548b9e940052`. That commit was pushed and the remote ref verified before acquisition. The corrected `CHARTER-v2.md` and `gates-source-v2.json` governed the run; original v1 documents remain preserved and were never claimed. No prices, targets, models, correlations or strategy returns were opened.

## Measured result

Six fixed listings were accessible: blocks and transactions for January 1, 2024; January 1, 2025; and September 1, 2026. Each returned one Parquet object and a nontruncated listing. Both primary-date schema checks passed. Thus all eight **metadata** cells completed. This does not mean every data sample was available: the block sample was downloaded, while the transaction sample was explicitly unavailable under the frozen size/row limits.

| January 1, 2024 object | Blocks | Transactions |
|---|---:|---:|
| Rows reported by footer | 7,107 | 1,101,465 |
| Compressed object bytes | 6,168,273 | 1,572,869,635 |
| Encoded uncompressed bytes | 6,641,103 | 2,330,183,535 |
| Row groups | 1 | 13 |
| Required columns missing | 0 | 0 |
| Complete object downloaded | Yes | No: exceeds frozen bounds |

The downloaded block sample has no nulls in its five required fields. Independent closure review also found consecutive heights 18908895–18916001, continuous parent links and a transaction-count total matching the transaction footer. This establishes provider-internal consistency only. Transaction row validity, duplicates, canonical block linkage, complete-day coverage and timestamp ordering have **not** been checked. Nontruncated object listing is not chain completeness.

The capture made 11 HTTPS requests and retained 6,216,363 raw response bytes. All actual responses were HTTP 200/206, with matching ETags/range lengths for footer acquisition; slot 12 remains explicitly not attempted. All 25 lifecycle outputs and eight cells were preserved. Sampled peak process-tree RSS was 305,504,256 bytes, with elapsed time 60.88 seconds and no resource kill. These measurements describe metadata plus the block sample, not graph construction or motif counting.

## What changes the implementation decision

**Column selection makes the next prototype plausible.** The retained transaction footer identifies 118,730,958 compressed bytes across the nine required columns, versus 1,572,869,635 bytes for the complete file. The largest selected row group is 11,176,553 compressed bytes. Contract `input` accounts for 1,421,172,126 compressed bytes and is unnecessary for the proposed unlabeled top-level transfer graph. `projection-plan.json` retains this post-capture planning calculation and exact parent hashes. These are encoded-column sizes, not measured HTTP transfer, decoded application memory, graph memory or computational cost. No transaction column extraction was performed, and one day cannot establish full-history resource costs.

**Amounts are floating point.** Actual `value` type is `double`, matching the documented concern. This source is not admitted for exact wei, reconstructed balances or exact cashflow accounting. An explicitly registered count/topology prototype may be useful; approximate volume would require its own accuracy justification. No silent replacement of a volume-feature experiment is permitted.

**Historical availability is unresolved.** The 2024 and 2025 objects have September 30, 2025 modification timestamps. September 1, 2026 objects have September 3 modification timestamps. These facts demonstrate the retrieved object's vintage, not the original availability of the underlying on-chain events. They neither prove look-ahead contamination nor establish when an historical strategy could have consumed this dataset. A replay must distinguish finalized-chain event time, indexer publication and retrieval time. A declared conservative lag can support a conditional retrospective study; it is not evidence of historical feed availability.

**The graph remains an explicit abstraction.** Successful positive-value top-level transactions can represent an address graph, but not all native-ETH movement or inferred buying/selling. Internal transfers, gas and token events are absent; contract calls and address identity require explicit treatment. Current labels and entity clustering are not needed for the first test.

## Next concrete stage

Freeze a child engineering/source contract for projected columns from the already identified January 1, 2024 object, using the preserved ETag and footer rather than rediscovering a favorable day. Verify block/transaction counts and hashes, event uniqueness and deterministic ordering, receipt status, missing recipients, self-transfers, invalid amounts and day boundaries. Construct the declared count/topology graph, compare its aggregates with direct table calculations, and measure actual extraction and graph-computation resources. Temporal motifs require a compatible pinned component and hand-countable independent synthetic checks before empirical counting. Missing or invalid records must remain in the denominator.

The completed source claim consumed its single named allowance. A follow-up must preserve this terminal parent, related history and exposure, and commit its own finite request/byte budget and exact feature/semantic contract before opening transaction rows. It must not repeat this capture or treat the inspected day as fresh confirmation. The next stage is still engineering feasibility, not a financial test.

Only after a source-admitted feature panel exists should the intended matched comparison run: M0 market features; M1 the same model plus ordinary on-chain activity; M2 M1 plus fixed graph features. Dates, timing, model choices, folds, uncertainty, minimum useful improvement and later net economics must be frozen beforehand. No accuracy or profitability inference follows from this source result.

## Verification and preservation

The named offline profile passed 2,036 tests and 81 subtests. It was collected before the final launcher amendment; the latest source/launcher tests separately passed all 14 checks in the detached execution checkout. Runtime checks, all 37 inherited local claim hashes and 78 pinned metadata files passed before capture. The initial shared-environment shortcut failed the runtime check; that failure was retained and a checkout-local locked environment installed offline before execution.

Both execution-root and imported-root lifecycle verification pass, covering hashes, 25 outputs and the eight-cell denominator. `source-import-manifest.json` pins all 27 run members and six resource/preflight files copied byte-for-byte from the preserved execution checkout. Independent scientific/source closure review is recorded separately in `SOURCE_CLOSURE_REVIEW.md`. These checks do not establish canonicality, full history, historical publication or financial admission.
