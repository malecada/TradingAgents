# Independent saved-metadata budget recount

Accepted for the narrow cumulative claim count. Independent read-only reconstruction agrees with recount01.json: 17 unique prior-lineage claims plus 16 disjoint replication-mechanism claims give 33 consumed claims, with 27 complete and six failed terminal dispositions. This closes the earlier copied-count uncertainty at the saved claim/terminal metadata level; it does not adopt a budget amendment.

The reviewer independently read history.json and rehashed all 34 listed metadata files. The lineage list contains exactly 17 unique identities. Separately scanning only `research_runs/*/claim.json` metadata for mechanism `celik-sefer-transaction-graph-full-neural-replication` produced exactly 16 identities, disjoint from the prior lineage. Every member of the 33-claim union has exactly one of complete.json or failed.json, whose status and experiment identity agree and whose claim_sha256 matches the actual claim bytes. All recorded claim paths, hashes, terminal paths/hashes, family values and group assignments match recount01.json. No duplicate or conflicting terminal was found in this population.

The pending allocation is still a proposal: 12 missing-body batches, 15 financial batches and one new resource slot. `33 + 12 + 15 + 1 = 61` is correct. Failures remain consumed; no claim is refunded, no identity is reserved and no execution is admitted by this review.

Graph09 is a distinct reserved launch-only identity. Its saved observer reports not_admitted, its owner hash matches, launch.json exists, guard release is absent and no corresponding research claim directory exists. Graph10's preserved allocation explicitly rebinds the unused proposed allowance rather than refunding a consumed claim. The absence of a Graph09 claim in this count is not permission to relaunch it; its existing launch namespace remains unavailable for reuse.

SHA256 bindings:

| Artifact | SHA256 |
|---|---|
| recount01.json | `7e81f78d0feaf366686f41ac86e8960ebf028fcf65d8cce2f2c01cf53c055094` |
| history.json | `68e4ea2f328996cef6966f2ec9f35c494b38f38182e33ae0fb7697383750aae0` |
| Retained budget-allocation.draft.json | `63fb322378f074bfef4bf4c0fd6cc61f97dd5d3987a8cd444bcd20d63f0b58ab` |
| Graph09 observer.json | `f458c07a097090e40beeb1d1087c2c127631c0478f16fd022b491353b8635361` |
| Graph09 launch.json | `ecf79f8301ee1cbb6e0b40030c9f2ae4647d1dab7d1981f56e3d5b4a059c8c7f` |

The scan covers the current checkout's saved research claim population and the explicitly pinned prior lineage. It is not an exhaustive search of every other checkout, archive or synthetic attempt, and does not independently infer broader statistical trial multiplicity. Complete means the saved lifecycle disposition, not financial success or validated replication. Historical source, output contents, financial accounting, original gate decisions and current process/guard liveness were not replayed. No output or array bodies, credentials, historical entrypoints, financial experiment or network operation were accessed or executed, and no registration or ledger was changed.
