# DefiLlama daily source semantics — September 15, 2026

## Decision

The requested endpoint and metric identities are supported by official sources.
The exact served chart timestamp convention and completed-day guarantee remain
unresolved. Source admission must not silently turn an integer timestamp into a
confirmed closed UTC interval or historical publication time. No financial gate
or second-vintage timing rule is changed by this documentation investigation.

## Direct support and limits

The official [free API overview](https://raw.githubusercontent.com/DefiLlama/api-docs/main/llms.txt)
identifies `https://api.llama.fi` as the unauthenticated service and lists
`/summary/fees/{protocol}` and `/overview/fees`. No paid service is needed to
express the registered recipe.

The [official OpenAPI specification](https://raw.githubusercontent.com/DefiLlama/api-docs/main/defillama-openapi-free.json)
(lines 2756–3006 as retrieved) documents a protocol slug and optional `dataType`,
defaulting to `dailyFees`; `dailyRevenue` is an allowed value. The registered
requests can therefore remain:

- `GET https://api.llama.fi/summary/fees/{encoded_slug}?dataType=dailyFees`
- `GET https://api.llama.fi/summary/fees/{encoded_slug}?dataType=dailyRevenue`

The summary schema describes `totalDataChart` as timestamp/value pairs with an
integer first item and numeric second item. It exposes identifiers, slug,
parent/child relationships, methodology and latest-fetch status. It does not
specify timestamp units, UTC interval start versus end, USD conversion, daily
finality, availability time or a partial-current-day flag for these pairs.
The summary parameter list contains no date-range or closed-day selector.
Overview documents the two chart-exclusion flags; these do not establish a
summary finality filter. A ten-digit example suggests Unix seconds but is not
an explicit timing contract. `latestFetchIsOk` is a fetch-status field, not a
per-row historical availability guarantee. These findings come from the
[summary and overview definitions](https://raw.githubusercontent.com/DefiLlama/api-docs/main/defillama-openapi-free.json).

The official [dimensions explanation](https://docs.llama.fi/list-your-project/other-dashboards/dimensions)
warns that it may be outdated. It says adapter token balances are priced to
produce results, defines fees as gross ecosystem value flows and revenue as
the retained portion distributed to treasury or holders. Token-holder revenue
is separately identified. This supports keeping the two registered metrics
distinct and does not establish that a token legally owns every reported
protocol dollar. Pricing balances is not, by itself, a precise USD valuation
or timestamp rule for the served chart.

The official [adapter guidelines](https://github.com/DefiLlama/dimension-adapters/blob/master/GUIDELINES.md),
available in the search engine's indexed text although direct open failed,
distinguish version-1 fixed UTC days from version-2 arbitrary windows and hourly
collection. They instruct adapters to use supplied range boundaries and to
return dimension balances without a timestamp. This demonstrates why generic
adapter frequency cannot establish the timestamp assigned by the API's chart
serializer. The indexed text also separates protocol and holder revenue.
Because this source was not pinned to a commit and direct retrieval failed,
its search excerpt is corroboration, not a frozen implementation proof.

## Explicitly unresolved before source clarification

| Item | Remaining evidence needed |
|---|---|
| Chart timestamp seconds and start/end meaning | Official response contract or pinned server serialization path showing the unit and day-key construction. Midnight-looking examples alone are insufficient. |
| Completed versus current partial day | Server aggregation/publication logic establishing which intervals are emitted and whether their values remain provisional. |
| USD valuation and revision semantics | Conversion/pricing rule tied to the served metric, including whether later price or adapter corrections revise old dates. |
| First-publication availability | Captured availability receipts or an admitted historical publication source. Two revision vintages cannot reconstruct this by themselves. |
| Per-protocol rule identity | Pinned methodology/adapter identity and documented parent/child aggregation; a shared ticker alone cannot resolve economic ownership or double counting. |

An explicit conservative day-selection assumption could be proposed separately,
but this review does not adopt it or call it provider documentation. The
existing P0 stability comparison remains a different question from proof of
historical point-in-time availability. A raw-source capture can retain opaque
responses while these semantics are pending; economic interpretation cannot
silently promote them to settled observations.

## Search accounting and failures

All access occurred September 15, 2026. Four focused search queries were used:
`site.docs.llama.fi fees revenue totalDataChart timestamp dailyFees dailyRevenue`;
`site:github.com/DefiLlama dimensions-adapters totalDataChart startTimestamp endTimestamp dailyRevenue`;
`site:github.com/DefiLlama/defillama-server "totalDataChart" "summary"`;
and `site:api-docs.defillama.com "summary/fees" "dataType"`.
Third-party results were not used as evidence. Six distinct page URLs were
attempted; repeated opens/finds stayed within those same pages:

1. Dimensions explanation linked above: retrieved, with outdated-page warning.
2. Adapter guidelines linked above: indexed official text available; direct open failed.
3. Free API overview linked above: retrieved.
4. `https://github.com/DefiLlama/defillama-server/tree/master/defi/src/api2/adapterData`: restricted/fetch failure, no implementation evidence.
5. `https://github.com/DefiLlama/dimension-adapters/blob/master/helpers/getStartTimestamp.ts`: 404, no implementation evidence.
6. Official free OpenAPI specification linked above: retrieved and targeted summary section inspected.

No market API was called, no raw outcome or panel was inspected, no provider
was contacted, and no paid endpoint or extra experiment was authorized. Only
this review was written. The remaining ambiguity is preserved rather than
resolved by guessed endpoint behavior.
