---
name: crypto-market-data-provenance
description: Capture, transform, join or validate crypto market, derivatives, on-chain, news and universe data for this repository's research or paper measurement.
---

# Crypto market-data provenance

Identify the consuming charter or measurement, its permitted source/venue,
interval, instrument identity and availability rule. Start with the
[data catalogue](../../../docs/research/DATA_CATALOG.md) and nearest manifest.
A new source, field, mapping or alignment affecting an experiment needs a
declared pre-result amendment or new registration; never silently change a
frozen result's inputs.

## Retain evidence at capture

Preserve raw bytes and a versioned manifest with provider/endpoint, parameters,
UTC request/retrieval times, source/version, request status and failed/rate-limit
gaps. Record instrument/contract identity, venue, market type, schema and units,
bar convention, coverage, content hashes, transformation source commit, parent
hashes and exact join rule. For revised/non-price fields, record publication,
availability and vintage separately from observation time.

Keep old snapshots immutable. A correction is a new path plus explicit lineage;
no overwrite, replacement fetch or success-only request denominator. Follow
the registered attempt limits and endpoint denial policy. Do not open
credentials or account endpoints as a substitute for public evidence.

## Admission checks

| Subject | Required distinction |
|---|---|
| Clock | UTC and monotonic/unique timestamps; decision, opening, closing, publication and settlement times remain distinct. |
| Coverage | Measure missing ranges, truncation, identity changes, delisting and join loss; no silent fill or dropped denominator. |
| Point-in-time fields | Use only values available by the decision. Unverified historical publication/vintage stays excluded from a point-in-time claim. |
| Cross-venue join | Specify matching keys and lag; same-bar values require actual prior availability. |
| Funding | Preserve raw event times, sign, units and price basis; estimated/announced/final/revised values differ. An observed series does not prove the historical expected-event calendar. |
| Settlement | Require original-contract lifetime, applicable price/fee rule and terminal cashflow. Last close, successor ticker and generic modern rules are not recovered settlement. |
| Execution | Public depth is a snapshot, not a realized fill; state age, latency, fees, lot limits and margin assumptions remain explicit. |

Run source-appropriate integrity checks before use: schema/nulls, cadence,
duplicates, coverage, hash stability and available independent overlap evidence.
Keep failed checks in receipts. The research [governance skill](../crypto-research-governance/SKILL.md)
governs any empirical claim; a validated dataset alone does not create one.

The [artifact catalogue](../../../docs/research/artifact_catalog.json) indexes
retained anchors, not every possible dataset. A local hash or Git-tracked
manifest is not proof that raw bodies or external sibling inputs are remotely
recoverable. Reconcile referenced members and actual retained bytes using the
current retention checker; do not label an unchecked backup verified.
