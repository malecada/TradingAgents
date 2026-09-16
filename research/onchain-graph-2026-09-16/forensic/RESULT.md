# One-day Ethereum graph feasibility result

September 16, 2026. **The reduced static address graph is computationally feasible on the measured day.** This establishes a practical extraction and reconstruction path. Temporal motifs, historical feature availability, predictive improvement and trading profitability remain untested. Zero strategies are validated.

The sample is January 1, 2024, UTC. It contains 1,101,465 transactions across 7,107 retained blocks. The graph includes successful, positive-value, non-self top-level transactions with valid sender and recipient addresses. It excludes missing recipients, reverted transactions and zero-value transactions. It does not include internal transfers, token events, entity attribution or monetary weights; it is not a complete ETH-flow graph or a reproduction of the paper.

| Measurement | Observed result |
|---|---:|
| Projected transaction columns | 9 columns, 117 successful range requests |
| Downloaded column bytes | 118,730,958 bytes (118.73 MB) |
| Full source object size, not downloaded | 1,572,869,635 bytes (1.57 GB) |
| Eligible graph events | 547,332 |
| Distinct directed address pairs | 443,937 |
| Addresses incident to eligible edges | 381,191 |
| Original guarded extraction run | 570.36 seconds; 981.69 MiB sampled peak RSS |
| Offline diagnostic reconstruction | 14.36 seconds; 516.23 MiB sampled peak RSS |
| Offline decode, integrity and pair counting | 8.78 seconds |
| Static graph summary calculation | 2.77 seconds |

Both executions used two logical CPUs and a sampled 2 GiB process-tree memory guard, with no elapsed-time kill. Neither triggered the memory guard. Timings include the particular implementation and retention overhead. They are not full-history estimates or motif benchmarks, and sampled RSS can miss brief peaks. The offline reconstruction issued zero new network requests.

## Source issue and preserved original result

The original strict gate correctly rejected 777 recipients containing the exact text `"None"`. Its lifecycle result remains **COMPLETE with 117 complete acquisition cells and two unavailable integrity/graph cells**. It has not been relabelled or rerun as a successful experiment. The retained [original result](../prototype/RESULT.md) and [closure review](../prototype/CLOSURE_REVIEW.md) explain the diagnosis.

A separately committed [forensic contract](CHARTER.md) mapped only that exact recipient sentinel to missing. All 777 affected rows remain in the transaction denominator and are excluded from graph edges. Of these, 15 are reverted and 762 successful; exclusion precedence places the former in the reverted category. No other malformed recipient was accepted. This normalization is consistent with the pinned [AWS producer's string conversion](https://github.com/aws-samples/digital-assets-examples/blob/a72285ae82da1c38fd39c5b8c7c60e209372342b/analytics/producer/copilot/ethereum-worker/worker.py#L190-L192), but neither the deployed producer revision nor individual contract creation was proven.

After this declared normalization, all original internal consistency checks pass: unique transaction hashes, complete block positions, matching block hashes and timestamps, and category reconciliation. The mutually exclusive categories sum to 1,101,465: 547,332 graph events, 530,351 zero-value transactions, 20,524 reverted transactions, 2,496 self-transfers and 762 successful missing-recipient transactions. Three file-order inversions were observed; any later temporal algorithm must explicitly order events by block number and transaction index.

The graph has 5,080 reciprocal dyads, with 10,160 directed pairs participating in reciprocity (2.29% of directed pairs). Repeated events beyond the first event per pair account for 103,395 events (18.89%). Maximum distinct-neighbor in-degree is 17,270 and out-degree is 4,240. These hubs make a separate motif-computation benchmark necessary; fast pair aggregation does not establish the cost of enumerating higher-order patterns.

The [machine-readable result](results/result.json) retains raw and normalized integrity reports, degree histograms, count-concentration statistics and the deterministic pair-count fingerprint `ff0f034a037b373f11191b5c19a4c0fe20fec33ac524dd31bdc1a1551dd4492e`. It explicitly marks source feature-panel and financial-evaluation admission false. These diagnostics cannot override the original gate or become fresh confirmation data.

## What this changes

Data volume and basic graph computation are no longer speculative blockers for this reduced one-day scope. The measured projection retrieved about 7.55% of the complete object. A full node, distributed processing and a GNN platform are not necessary for this demonstrated operation.

The next useful engineering step is a separately admitted, fixed temporal-motif benchmark, with explicit event ordering, time units and boundary overlap. Before a historical forecasting panel, source semantics and availability also need admission: later object modification dates do not establish what was available at old decision times; provider-internal consistency does not prove independent canonicality or complete day boundaries; DOUBLE amounts do not establish exact wei. One measured day cannot establish multi-year coverage or worst-window resources.

Only after those dependencies are resolved does the proposed matched comparison become meaningful: market features; market plus ordinary on-chain activity; and those same features plus a small fixed graph-feature family, using the same model and chronological folds. This diagnostic supplies no evidence of incremental prediction or economic value, and authorizes no additional experiment.

## Verification and preservation

Execution source: `5bb14064e9609133616a6e3e4254585a9dd99fe0`, committed and remotely verified before execution. The detached execution checkout is `/home/malecada/master_thesis/TradingAgents-onchain-forensic`; its HEAD is preserved. Preflight verified the checkout-local locked Python 3.13.13 environment, 124 bound inputs, 15 source/runtime hashes, 79 inherited metadata hashes, 39 local lifecycle claims and the original parent structure. No 40th claim was created; exhausted source/prototype allowances remain unchanged.

The three focused test modules passed 40 tests in 1.40 seconds. The previously passed named offline suite (2,060 tests and 81 subtests) is inherited for unchanged core code, as accepted in independent pre-execution review. Six execution/preflight/resource artifacts were imported byte-for-byte under [import-manifest.json](import-manifest.json). Final independent reconciliation is recorded in [CLOSURE_REVIEW.md](CLOSURE_REVIEW.md).
