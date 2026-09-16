# Independent forensic closure review

September 16, 2026. **No material discrepancy was found in the retained-byte reconstruction or its diagnostic graph arithmetic.** The result supports the computational feasibility of this reduced static address graph on the measured day. It does not admit a source feature panel or financial evaluation. The original prototype remains COMPLETE with 117 complete acquisition cells and two unavailable integrity/graph cells; its consumed 2/2 allowance and the source allowance of 1/1 remain unchanged.

The reviewed execution source is `5bb14064e9609133616a6e3e4254585a9dd99fe0`. Review covered the frozen forensic contract and implementation, terminal result, start/resource/preflight receipts, imported evidence, and the final result/checkpoint wording. The independently authored [verification script](check_independent.py) reconstructs the retained Parquet column ranges with PyArrow and computes its own integrity checks, pair counts, adjacency sets, degree distributions, reciprocity and concentration arithmetic. It imports neither the subject graph-math module nor its reconstruction implementation. The [independent receipt](independent-review.json) retains complete computed degree histograms and metric comparisons.

## Evidence and denominator reconciliation

All 124 contract input hashes and 15 source/runtime hashes matched the execution checkout; source bytes also matched its fixed Git commit. Inputs were hashed again after reconstruction. Every one of the 117 retained range bodies passed strict base64 decoding, byte-length and SHA-256 checks. HTTP 206 status, request number, conditional/response ETag and exact Content-Range matched the frozen projection. The bodies total 118,730,958 bytes. The retained footer supplied the Parquet metadata; no source object was refetched.

Independent decoding recovered all 1,101,465 transactions. Transaction hashes were unique, every retained block position was filled exactly once, and block hash/timestamp/count checks reconciled against the 7,107 retained blocks. Sender syntax, recipient syntax after the exact declared conversion, status domain and finite nonnegative values passed. Three source-order inversions were reproduced. This is internal consistency against the same provider's retained block data, not independent chain canonicality or proof of complete UTC-day boundaries.

Exactly 777 recipient values were the case-sensitive string `"None"`. They were all excluded from graph edges. The original raw integrity report is preserved verbatim in the forensic result. Normalized mutually exclusive categories are:

| Category | Transactions |
|---|---:|
| Eligible graph event | 547,332 |
| Zero value | 530,351 |
| Reverted | 20,524 |
| Self-transfer | 2,496 |
| Successful missing recipient | 762 |
| Invalid after declared normalization | 0 |
| Total | 1,101,465 |

The other 15 missing-recipient rows are counted under reverted because that category takes precedence. Independent nonexclusive flags also match: 777 missing recipients, 20,524 failed receipts, 545,979 zero-value rows and 27,642 self-transfers. These flags overlap and must not be summed as exclusions. The cited producer string conversion is a plausible explanation; its deployment on these objects and individual contract-creation attribution were not independently established by this review.

## Independently reproduced graph

| Diagnostic | Verified result |
|---|---:|
| Eligible events | 547,332 |
| Distinct directed address pairs | 443,937 |
| Addresses incident to eligible edges | 381,191 |
| Repeated events beyond the first per pair | 103,395 (18.8907281%) |
| Reciprocal directed pairs | 10,160 (2.2886130%) |
| Reciprocal dyads | 5,080 |
| In-degree / out-degree sums | 443,937 / 443,937 |
| Maximum distinct-neighbor in-degree / out-degree | 17,270 / 4,240 |
| Sender event-count squared sum | 198,381,908 |
| Recipient event-count squared sum | 1,632,681,074 |
| Sender event-count HHI | 0.0006622170872665991 |
| Recipient event-count HHI | 0.005450039855749259 |

Both complete degree histograms matched, including zero-degree endpoints. HHI denominators are `547332²`, not transaction counts, address counts or monetary totals. The independently recomputed sorted `(sender, recipient, event count)` fingerprint is `ff0f034a037b373f11191b5c19a4c0fe20fec33ac524dd31bdc1a1551dd4492e`.

## Execution and preservation

The original forensic execution completed with exit 0 in 14.359787944 seconds, sampled peak process-tree RSS 541,306,880 bytes and no guard trigger. Independent reconstruction completed with exit 0 in 13.437310558 seconds and sampled peak 666,427,392 bytes. Both used the reviewed two-logical-CPU, 2 GiB memory-only guard; neither imposed an elapsed-time kill. The independent [resource receipt](independent-review-resource.json) preserves the measurement. Sampling can miss brief peaks; these are observed implementation costs on one day, not worst-case bounds or full-history estimates.

All six files in [import-manifest.json](import-manifest.json) matched the detached execution checkout and coordinator byte for byte, including recorded sizes and SHA-256 hashes. The source checkout remained at the recorded execution commit. Both roots contain 39 local lifecycle claims; the forensic artifact created no additional claim. Counts are local metadata inventory, not a global count or independent-hypothesis count. Review introduced no network requests, financial evaluation, registration change or ledger mutation. Final closure backup remains subject to the coordinator's subsequent commit/push verification.

| Reviewed artifact | SHA-256 |
|---|---|
| Forensic contract | `ea1fa75b843bb8df88ba1313c47e4b5cf036587617c5a41823134acc90925b28` |
| Terminal result | `a061e1439ab5d6abf8fb10df2432559b24e6ea41b0caa85c5110049f8515fa3e` |
| Six-file import manifest | `ea23e78b6c991942c0da7843ed8a76af07c531a4818fc77cf0a895a3920c9def` |
| Independent verification script | `b91dc21a95de27a80f8fc0932ff850e79d6e93943236efcdad82486162b443ff` |
| Independent comparison receipt | `43efea1c4a199098baa7a1344461bfcbffb0ea74804dcd344683d6113dc226c0` |
| Independent resource receipt | `deb9ac0347c37e482c87c69584750321630945f75b03f9c636c420c044d0cbf1` |

## Limits and next dependency

The graph describes successful positive-value non-self top-level transactions between addresses. It omits missing recipients, internal transfers, token events and entity attribution. Counts are not exact-wei amounts or economic flows. Neither historical publication timing, independent canonicality, complete day boundaries, multi-year coverage, exact temporal motifs, incremental prediction nor trading value was tested. Fees, funding, returns and cashflows were outside this diagnostic; no financial conclusion follows.

The RESULT and study STATE accurately preserve these boundaries. The next concrete engineering dependency is a separately admitted, fixed temporal-motif benchmark with explicit source semantics, `(block number, transaction index)` ordering, time units and boundary treatment. The observed hubs make static aggregation timings insufficient to infer motif costs. The post-hoc normalization cannot silently become a passing original gate, a new trial allowance or fresh confirmation data. No unresolved arithmetic question requires higher-effort review for this diagnostic closure.
