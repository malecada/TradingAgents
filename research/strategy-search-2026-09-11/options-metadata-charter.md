# Options contract and archive metadata admission

Experiment `options-metadata-20260911`; source admission only. Prepared September
11, 2026 from the [eight-source review](reviews/options-feasibility-20260911.md),
without additional retrieval. No option quotes, premiums, Greeks, payoffs,
affordability calculations or financial returns belong to this investigation.

Question: can one public metadata capture establish actual BTC/ETH crypto-option
quantity rules and identify the types of objects in the already observed official
daily options archive? Competing explanations are missing/ambiguous contract
rules, inaccessible sources, or archive objects whose names do not establish an
executable historical chain. Neither source success nor failure tests profitability.

## Inherited evidence and budget

`data/predlab/gates.json:predlab_rviv_p0` is one known administrative gate bundle,
registered August 25, 2026. Its canonical sorted compact JSON SHA256 is
`442316e9a15e36839a11a7136bdf4f1af82ec9e92422994bde3250fe8f1fc55c`.
Exactly 12 rows have `experiment == "predlab_rviv_p0"` in
`data/predlab/trial_ledger.jsonl`, SHA256
`4459ddc70d41d9a99db06ab53d9ad4c8f42b6f4d282abd93b4857b4474041927`.
The broader substring search also finds eight unrelated order-flow records;
those are not additional RVIV rows. The original HAR-30 versus debiased DVOL
claim failed in the exposed June 2022–March 2025 development window. Its
forensics and inspected descriptive data remain inherited, not fresh samples.

For program scheduling, preserve `prior_attempts=1`, representing that known
gate bundle, and allow at most three new options investigations: total cap four,
with this capture the first new investigation. These administrative counts are
not independent hypothesis counts, DSR denominators, or claims of exhaustive
historical multiplicity. Preserve all 12 historical cells, the original failed
gate and broader search ancestry. This metadata task is not a financial ledger
row and does not reopen the rejected HAR configuration.

## Fixed requests and resource limits

The sole request input is [options-request-spec.json](options-request-spec.json).
In its order: public options exchange information, public options server time,
the observed `data/option/daily/` S3 prefix with delimiter `/` and max-keys 1000,
and the same prefix without delimiter and max-keys 20. No guessed descendant,
pagination, ZIP/CHECKSUM member, underlying quote or alternate host is requested.

The API URL base is frozen as `https://eapi.binance.com`, with documented
`/eapi/v1/exchangeInfo` and `/eapi/v1/time` paths. The saved source review did not
retain explicit base-URL text. The coordinator resolved that gap on September
11, 2026 from the official
[market-data documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-options/api/rest-api/market-data),
which supplies exact `https://eapi.binance.com` URLs, and the correct
[options general-information page](https://developers.binance.com/en/docs/products/derivatives-trading-options/general-info).
The older `https://developers.binance.com/docs/derivatives/option/general-info`
route redirected incorrectly to USD-M futures documentation; that conflict is
retained and cannot authorize a host substitution. This separate coordinator
check used three document URL fetches and one empty-result site search, not
metadata API calls. The original review's eight-source denominator is unchanged.
Exact coordinator retrieval clocks were not supplied. This drafting task made
no fetch; no switch to another production or demo system is admitted.

Four request/admission cells remain the denominator regardless of denial,
timeout, schema error, host suppression or resource interruption. Use frozen
`carry_capture.public_get`, whose exact file hash is pinned by the execution
gate. One attempt per URL; 20 seconds and 5 MiB each; no retries, authentication,
proxies, redirects or fallback. Same-host HTTP 403/418/429/451 suppresses later
requests to that host with explicit unavailable receipts. Global bounds:
120 seconds, 256 MiB sampled aggregate resident memory, one allowed CPU,
20 MiB received body bytes and 80 MiB
retained output allowance. No subprocess network escape or parallel requests.

Publish each receipt, including exact received prefix bytes, completeness,
SHA256, URL, local request/response UTC clocks, status/error and available HTTP
Date/Content-Type before the next request. Publish explicit unattempted receipts
for cooperatively resource-stopped cells. Recoverable parser failures become
unavailable cells and the remaining denominator is completed. An abrupt kill,
process crash or uncatchable allocation failure may leave only partial outputs;
the immutable failed/pending claim still preserves all four intended identities
and cannot be silently retried. This limitation follows the lifecycle contract.
Preserve four receipts plus capture and admission
JSON reports; never modify original stores. Metadata raw bodies retain all
symbols even though normalized interpretation is restricted below.

The separately reviewed options_resource_launcher.py restricts its own CPU
affinity before launching, invokes resource_guard_v2.run_guard with the fixed
256 MiB/120-second limits, and exclusively retains its resource report. The
monitor samples nominally every 20 milliseconds with one 20-millisecond retry
for an exiting subprocess. Brief overshoot and shared-page double counting are
possible; no background, detached or secondary-thread subprocesses are admitted.
The full disposable ResearchRun preflight includes all four invented 5 MiB bodies
and actual six-output pretty serialization under this exact guard. The output
allowance is measured using the lifecycle serialization, not compact JSON.

## Frozen admission rules

Only complete HTTP 200 bodies are structurally admissible. JSON must be UTF-8,
contain no duplicate object keys or nonfinite constants, and have an object
root. API error objects remain unavailable, never an empty successful universe.
Exchange information requires `optionSymbols` to be a list of objects; retain
all raw keys. A missing or changed schema is unavailable rather than guessed.
The separate time response requires integer `serverTime` in Unix milliseconds
(not boolean). Preserve clocks without inferring synchronization, simultaneity,
latency-adjusted quotes or historical publication time.

For each symbol retain literal `symbol`, `underlying`, `underlyingType`,
`contractType`, `expiryDate`, `side`, `unit`, `minQty`, `maxQty`, `status`,
`initialMargin`, `maintenanceMargin`, `minInitialMargin`, `minMaintenanceMargin`,
`nakedSell`, and `filters` where returned. A field absent in the actual response
is unavailable, not copied from a documentation example. Recognize BTC/ETH
identity only from explicit underlying metadata `BTCUSDT` or `ETHUSDT`; symbol
name alone is insufficient. Preserve returned type values literally. An absent
or uninterpreted crypto/TradFi type discriminator leaves crypto classification
ambiguous and prevents unconditional crypto-rule admission; no guessed enum.

Interpret positive finite decimal `unit`, `minQty`, `maxQty`, and LOT_SIZE
`minQty`, `maxQty`, `stepSize` from actual values only; booleans are invalid.
Require minQty <= maxQty when both exist. Quantity rules are partially admitted
only to the extent supplied; conflicting top-level and filter values, duplicate
symbol identities/LOT_SIZE filters, invalid quantities, and missing fields are
retained as ambiguities, not resolved by choosing a convenient field. Positive
integer expiry timestamps and literal status/side are metadata only. Margin
fields require finite nonnegative decimal values if interpreted; absent or
invalid values remain unknown. Symbol `nakedSell` never establishes account
permission. Do not multiply quantities by prices or compute capital needs.

S3 bodies must be UTF-8 XML ListBucketResult in the S3 namespace, without DTD
or entity declarations. Require exact requested Prefix, MaxKeys and Delimiter
semantics, and explicit boolean IsTruncated. Retain returned CommonPrefixes and
Contents Key, LastModified, Size, ETag, plus continuation metadata if present;
do not follow it. Contents keys must remain within the frozen prefix; sizes must
be nonnegative integers. LastModified is current object-version metadata, not
guaranteed first publication or market observation time; ETag is not SHA256.
Names can suggest a data type only: no filename proves its body schema.

Any truncated listing is partial, including the 1000-key delimiter listing;
absence from a partial listing is never global absence. The 20-key listing is
an initial lexical slice, not a representative sample or coverage estimate.
Even nontruncated empty results establish only that exact prefix/query response.
No executable bid/ask-size chain, historical contract completeness or matching
underlying hedge observations are admitted from catalogue names alone.

## Interpretation, review and next action

Capture date is the actual recorded UTC date, intended September 11, 2026;
do not fabricate a planned clock as an observation. All information is designated
current source-only exposure, never fresh financial confirmation. No costs,
beta, uncertainty test, p-value, convention-swap PnL or adoption metric applies.
Applicable fees, seller access, funded hedge/reserves, historical rule changes
and a complete executable chain remain unavailable after this task unless
separately admitted. Older/newer options systems cannot be silently combined.

Before acquisition, synthetic malformed JSON/XML, schema ambiguity, truncation,
denial suppression and resource/prefix-retention tests must pass; commit and
independently review the collector, exact request spec and execution gate.
After capture, an independent reader checks raw receipts and the four-cell
denominator without importing collector parsing logic.

An observed archive type can justify one narrowly registered body-schema
admission, only if it addresses the bid/ask-size and hedge-data dependency.
Observed quantity rules can resolve a lot-rule gap but not affordability without
a separately authorized price/capital design. If neither dependency advances,
defer this historical options execution route with exact missing inputs and rank
same-venue public spot triangular conversion as the next distinct mechanism.
No parameter refresh, familywide failure claim or authenticated Convert request
follows from this capture.

## Input window bookkeeping

The registered existing dataset is the saved request-definition document only.
Its local observation interval and SHA256 are retained in
options-source-definition-observation.json and pinned at source freeze. That
interval is documentary registration bookkeeping, not a market sample or a claim
that later metadata existed then. The local clock record is not independent
external timestamp attestation. Every live exchangeInfo/time/S3 response is first
observed at its actual request/retrieval timestamps and becomes exposed then.
The source-definition input window never backdates those outputs. No financial
prediction, portfolio selection or fresh-market evidence follows from this job.
