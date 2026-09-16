# Independent memory-failure review

September 16, 2026. **The registered full-day Local40 benchmark failed its 2 GiB memory envelope.** The guard observed 2,656,620,544 bytes of process-tree RSS after 219.656934598 seconds and terminated the child with SIGTERM (exit -15). No elapsed-time kill occurred. The observed peak is about 2.47 GiB; it is not evidence that the computation would finish at that memory level. Sampling can miss brief peaks.

Only integrity, bounded-oracle and graph-build outputs were published. No full-day motif vectors, local shards, summary, concentration statistics or phase timings were retained. This result cannot be presented as successful motif feasibility. It is a failure of the pinned Raphtory0.17 Local40 operation under the declared envelope; it does not prove that every temporal-motif implementation is infeasible.

Execution source is `82b92974606cedd43f787df4d4cfb86434232792`, preserved in the dedicated detached checkout. The original source allowance1/1, prototype allowance2/2 and original prototype117-complete/2-unavailable outcome remain unchanged. The newly authorized downstream attempt is consumed: cumulative3/3. No automatic retry, additional configuration or larger resource allowance follows.

## Independent retained-byte reconciliation

The [independent failure checker](check_independent.py) verified the committed claim/source/gate, 128 input hashes, 12 source hashes, six runtime hashes, 77 inherited metadata hashes, resource receipt and exact three-output denominator. It does not import the benchmark's numerical implementation or its oracle. Its separate [result receipt](independent-failure-review.json) predates failure-only terminal recovery and correctly records the then-existing claimed-incomplete state.

Independent Parquet reconstruction from the 117 retained range bodies recovered all1,101,465 transactions. Strict base64/hash/length, ETag and range checks passed. All transaction hashes were unique; block hash/timestamp/position/count and day bounds reconciled against the 7,107 retained blocks. The exact777 recipient sentinels were excluded, with unchanged normalized categories/nonexclusive flags and static pair fingerprint. The independent reconstruction reproduced the same547,332 eligible events,443,937 directed pairs and381,191 incident addresses.

Sorting by block number and transaction index reproduced the full ordered-event fingerprint `1d9f9fd78c2a4363f508b7ecbb3fcc5fc729d7ea62f65c9a77ae337fbf7a535d`. Time was checked as integer seconds with nondecreasing block timestamps. No transaction-order or event-multiplicity discrepancy was found in the retained graph-build evidence.

The six bounded subsets were independently selected from raw events using the registered degree/tie rule and first30 incident-event rule. Every retained sample event matched, and direct enumeration of all triples reproduced all40 local slots for every address in each subset. These checks validate the retained subsets, not the absent full-day result. No full-day two-node, star or triangle outcomes were calculated by the reviewer after resource failure.

Independent failure verification completed with exit0 in14.431747351 seconds and sampled peak616,407,040 bytes under two-logical-CPU affinity and the same2GiB memory-only guard. The [review resource receipt](independent-failure-resource.json) retains that observation. This is the cost of reconstruction and bounded checks, not the cost of full-day motifs. The production219.66-second elapsed figure includes admission/input validation, decoding, subset checks, graph construction and unfinished motif work; the absent phase-timing artifact prevents a reliable split.

## Failure-only recovery review

The reviewed `close_failed.py` SHA-256 is `48b257db849f6c53283e84ac2575e6b0e7541ea6f86c5c5f0ecb2349ecc82108`; its `failure-closure-bindings.json` SHA-256 is `ca59d589a6e57f5d8eaf09d81e8d9ff93570fecfb18def23ac2459cbb9bec066`.

**The exact reviewed recovery is approved for failure-only closure after its preservation commit.** The script pins the execution root and HEAD, original claim, guard receipt and three partial-output hashes. It requires the recorded terminal memory violation and absence of an existing terminal receipt. It re-admits only the existing own claim, verifies original inputs and calls the existing append-only `ResearchRun.fail` path. It does not call start, finish, output publication or the empirical benchmark. It checks unchanged original bytes and structural validity afterward. The supervisor's completed guard receipt establishes that its child was terminated and waited for before this operation.

The original claim continues to register five cells and44 expected outputs. Three outputs remain present;41 were never published. The proposed external closure note distinguishes three cells with evidence before failure from two unavailable motif/export cells. These are progress facts, not a successful five-cell completion or fabricated output coverage. Terminal recovery and exact import were pending when this section was written; their final verification belongs below.

| Evidence | SHA-256 |
|---|---|
| Original claim | `6ba7c1697b7b9e0fa4e8928e596b78efee593eac953d924734b9df38844d8eb1` |
| Frozen gate | `c0c025c487352bf8c257f6c1d5ade3b97f8aef0a16540367d6133be74aef9a6f` |
| Production memory-guard receipt | `f35b96227e3f32c0d779b152c6fc2b4a904643d9ff79aaf35b3071121e469601` |
| Integrity output | `c0d30ef69478e8ddbecfc4a5f13b0b54fbf51d7b725685078d594ae8d7373f41` |
| Bounded oracle output | `33abe95f96ae3d166960ad5c6d92fe5b8e6f288c7ec3ae61ef6377f82ec21df3` |
| Graph-build output | `056501cbeafe6f76218c75a7bd30d463f7c57179d145131ccd8135d41a35c202` |
| Independent checker | `f80ddeae30d9cb56a2bc0ea6374fb0a570884c33ff9e4727c0fb7893f98bdd4c` |
| Independent failure-review receipt | `db43981178ba4031d5c56cdf8070242faa6dfcfb58bbfda6a2e7145e7f487058` |
| Independent resource receipt | `f21f8cc245863574c83cffe10b476d4c795e6e8c434e8c9162117844da9bf4d9` |

Independent canonicality/day-boundary completeness, historical availability, exact wei, full-day motif counts, predictive value and financial performance remain untested or unavailable. The previously demonstrated static graph operation remains a separate result. No additional empirical run, budget reset or financial conclusion is admitted by this failure review.
