# Triangle source capture: independent post-result review

**PASS for the registered raw-source and schema claims.** All six request cells
are complete, zero unavailable, with eight matching retained outputs. The exact
exchange-information and batch-ticker inputs are structurally available for a
separately registered static conversion proxy. No conversion factor, spread,
profit or cross-source price alignment was calculated by this review.

The independent [checker](check_triangle_inputs.py) reads retained Base64 bytes
and uses strict JSON/Decimal validation without importing the collector or
financial calculation. Its [JSON evidence](triangle-inputs-review.json) records
hashes, clocks, identities, schema checks and resource results. The official
structural verifier separately passes the six-cell/eight-output denominator.

## Provenance and complete evidence

Claim, completion and committed registration match source
`270d724eaf6b9781bf099c816b7d475df50412a9`, with gate SHA256
`fcf50aa82ba0947d4858945edae0d897b3c927faa89b086a43a05c6819e8560a`.
All declared source, charter, runtime, request-spec and helper hashes match the
committed bytes. Earlier experiment/dataset/family objects are unchanged from
`gates-options-eoh.json`. Each individual raw receipt exactly matches its copy
in the aggregate capture. Actual output hashes match the completion receipt.

The capture retains **19,899 raw bytes** and **107,998 output bytes**. All six
requests are attempted, complete HTTP 200 responses with no retained error.
Strict UTF-8 JSON reconstruction finds no duplicate keys, nonfinite constants
or malformed source identity.

| Source | Raw bytes | Independently verified structure |
|---|---:|---|
| Exchange information | 15,686 | Exactly BTCUSDT, ETHUSDT and ETHBTC, correct base/quote assets |
| Server time | 28 | Positive integer Unix-millisecond `serverTime` |
| Batch best ticker | 358 | Exactly three symbol rows; positive finite bid/ask prices and quantities, uncrossed within each pair |
| BTCUSDT depth | 1,326 | 20 bids and 20 asks, strict price ordering and positive prices/quantities |
| ETHUSDT depth | 1,290 | 20 bids and 20 asks, strict price ordering and positive prices/quantities |
| ETHBTC depth | 1,211 | 20 bids and 20 asks, strict price ordering and positive prices/quantities |

All observed symbol records state TRADING and `isSpotTradingAllowed=true`.
LOT_SIZE, MARKET_LOT_SIZE and NOTIONAL filter names are present for all three;
all raw fields are preserved. The result correctly leaves their actual market-
order interpretation and personal account access unavailable. Source-level
availability is not account entitlement or an executable lot/fee calculation.

Depth identities follow the frozen request URLs; every response has a nonnegative
integer `lastUpdateId`, distinct strictly descending bid prices, ascending ask
prices and uncrossed best sides. No ticker/depth values were spliced, compared
for opportunity or used as if they described one instant.

## Time and resource limits

The first request starts September 11, 2026 at 09:10:25.404644 UTC and the last
receipt ends at 09:10:29.052054: **3.647410 seconds** across the six sequential
requests. The batch-ticker request spans 09:10:26.744354–09:10:27.051204 UTC.
Its rows have only symbol and bid/ask price/quantity keys; no event timestamps
are supplied. The later depth responses contain only `lastUpdateId`, bids and
asks. An update identifier is not a timestamp.

Every local interval is ordered within the run, agrees with its monotonic
duration within 21 microseconds and remains below the 20-second request bound.
The returned server clock, 09:10:26.257 UTC, lies inside its own local request
interval (0.167798 seconds after request, 0.126865 seconds before retrieval).
That does not timestamp the other responses or establish cross-pair simultaneity.
HTTP Date headers differ from local retrieval by approximately −0.357 to −1.052
seconds. Those coarse clock observations do not establish quote freshness.

The retained resource report records successful exit, no limit reason, 6.29028
seconds total, 59,486,208-byte sampled peak process-tree RSS and 32,336 KiB child
`ru_maxrss`. These match the declared sampled 512 MiB/120-second policy. Sampling
and transient/shared-memory qualifications remain; actual server-clock accuracy
and between-sample memory maxima are not independently attested.

## Interpretation, ancestry and next admission

This first triangle-source claim consumes one of the three allowed questions for
the exact static-conversion mechanism. Its recorded zero prior exact-triangle
attempts does not erase broader OFLOW/passive-liquidity failures or unknown
historical multiplicity. Funding, dated and options budgets remain unchanged.

The positive result is that the required **input schemas** are available. It is
not evidence of a positive triangle conversion factor. The follow-up must use
the exact retained exchange-information and single batch-ticker bodies, preserve
their asynchronous/exposed status, and freeze the two directions, capitals and
fee assumptions before calculation. The separately reviewed full-notional proxy
cannot become a wallet-wealth bound under abstention/rounding/partial sizing, nor
an inference about actual sequential execution.

Unknowns remain: simultaneous matching-engine state, quote age, deeper liquidity,
fees and fee assets, lot/dust/notional handling, actual fills, atomicity, account
access, temporary inventory risk, repeated opportunity frequency and expected
return. No numerical financial outcomes, price comparisons, API requests or
network operations were performed in this review. External recoverable backup
remains the coordinator's separate verification step.
