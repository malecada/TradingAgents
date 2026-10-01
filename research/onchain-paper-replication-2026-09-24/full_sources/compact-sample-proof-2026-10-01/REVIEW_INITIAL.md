# Independent initial compact sample-proof review

Final acceptance remains pending terminal evidence and correction of the retained-scratch lifetime below. Source, tests and relevant sampler/index/workload contracts were inspected read-only; no tests, historical jobs or empirical arrays were run/read by the reviewer.

## CSPROOF1 — Prior selection scratch survives into the next extraction

`tradingagents/research/onchain_replication/compact_sample_proof.py:92–101` retains `selected`, an independent int64 array returned by ArrayNeighborhoodIndex.selected, and the final `positions` chunk after their downweight update. Those local references remain live through the next draw's lease, optional index replacement and neighborhood construction. The index's documented buffer allowance excludes caller-retained prior outputs; its next extraction creates its own selection scratch. This extra preceding selection has not been released or separately reserved.

Delete both references after the update loop, before the next numerical boundary. A weak-reference regression can prove the previous selection is collectible before the next neighborhood/index is entered without changing matching/sampling semantics. This concerns the claimed buffer accounting, not total RSS or a different neighborhood algorithm.

## Semantic assessment and requested evidence

The weighted audit matches the preserved sampler's arithmetic: normalized weights, cumulative probabilities normalized by their final sum, and `cdf[chosen-1] <= uniform < cdf[chosen]`, equivalent to right-sided CDF search. The chosen center is zeroed and the exact selected neighborhood indices are halved. The two global float64 vectors account for `16 * total_centers`; local index/extraction scratch remains a separate bound.

Current helper negatives reach altered probability, induced content, selected-index hash, retained-prefix and sample identity refusals. Add a distinct valid-equal-probability but wrong-center case that reaches the CDF-interval error. A probability-field mutation alone does not exercise the saved uniform's center selection. The positive kernel-parity fixture and existing state transitions are useful but do not replace this targeted negative.

The dictionary workload scope matches the accepted workload implementation's exact fields: workflow, scalar backend, ordered typed local graphs, sample identity, matching settings, fold-bound dictionary settings and seed. Public admission requires the actual publication and verifies event hashes before the semantic helper; its helper-only counterexamples intentionally bypass that outer hash gate. Final callback-free checks cover retained draw/artifact evidence and actual training-parent hashes after the last external lease.

This is current-owner sample provenance under the registered supplied population, not complete calendar/exclusion or price/label reconstruction, dictionary execution, native selection or empirical release. Full checks redo semantic verification; inner leases rely on the declared frozen-input contract. No terminal check01 outcome is claimed in this note.

Reviewed source SHA256: `65a3c3adff5c71b4c87f8c764e265e4fb29e7da28143403dabbed2b0eac31163`.
Reviewed tests SHA256: `a483a5c95f808f4ae94707a3f347aeda2d74fc69b39dc0c6bf163977d5264f9c`.
