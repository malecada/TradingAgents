# Independent options metadata source review — PASS

September 11, 2026. The saved four-request capture passes independent source
reconstruction. No collector module was imported; no network request, additional
API call, archive member or financial result was opened or computed. The
independent stdlib checker is [check_options_metadata.py](check_options_metadata.py),
with machine-readable evidence in [options-metadata-review.json](options-metadata-review.json).

The run source is `828884688b944b5cd2c33537fe4fcabc28325e66`. All gate-pinned
collector, launcher, transport, guard, source-marker, request-spec, charter and
runtime hashes match local bytes; pinned source-file bytes also match that Git
commit. Claim, registration and all six output digests reconcile with the
terminal receipt. Four exact spec URLs yield four complete HTTP 200 receipts,
zero unavailable source cells, 1,069,263 raw bytes and 9,018,605 output bytes.
This review checks saved source identity; prior remote equality is separately
recorded by the coordinator and is not independently re-fetched here.

Each standalone receipt equals its aggregate counterpart. Base64 decoding,
body byte counts and SHA256 match. Request/retrieval clocks are ordered from
08:40:11.517399 to 08:40:16.763026 UTC. Local receipt modification times fall
between retrieval and the next request for all four files, corroborating the
reviewed immediate publication path. Filesystem timestamps are not independent
publication attestations. The request-definition input's earlier 08:38:02 window
is not treated as live metadata availability, and HTTP Date is not a guaranteed
market-event clock. The guard reports 7.429 seconds and peak sampled aggregate
RSS 97,591,296 bytes under the 256 MiB/120-second/one-CPU launch contract.

## Reconstructed metadata

All 1,678 returned symbol rows and their raw fields are preserved. Exact
underlying metadata identifies 1,230 BTC/ETH target rows: 654 BTCUSDT and 576
ETHUSDT. Every returned row's identity, availability flags, expiry status,
quantity fields, LOT_SIZE, margin fields and ambiguity state agrees with the
independent reconstruction. No target or non-target row was silently omitted.

For all 1,230 targets, actual returned unit is 1, minimum quantity is 0.01,
and LOT_SIZE step is 0.01. Top-level and lot min/max values agree; quantities
are positive finite numbers with ordered min/max; no duplicate symbol or lot
identity was found. These are current metadata observations, not historical
rule coverage or proof that 1,000 or 10,000 USDT can fund a position and hedge.

The literal values `underlyingType=CRYPTO` and `contractType=CRYPTO_OPTIONS`
are retained where returned, but the frozen parser's crypto classification
remains **ambiguous**. No enum reinterpretation is silently introduced after
capture. A separately documented mapping could resolve that semantic question;
the current admission report is not rewritten to pretend it already did.

`nakedSell` is absent from every per-symbol row, and that absence is correctly
marked unavailable. The separate `optionContracts` rows contain `nakedSell=true`
for BTCUSDT and ETHUSDT. Both levels are retained; the contract-level flag does
not fill the absent per-symbol field or establish the user's seller permission.
The ten optionContracts rows and their metadata-availability records reconcile.
Applicable commission/fee assets, legal entity, seller access, hedge financing,
capital reserves and historical margin execution remain unverified.

## Catalogue findings and next dependency

Independent namespaced XML parsing verifies query prefix, delimiter, max-key
limits, explicit truncation flags, contents, sizes, continuation metadata and
absence of DTD/entity declarations. The delimiter listing is nontruncated and
contains exactly two immediate child prefixes:

- `data/option/daily/BVOLIndex/`
- `data/option/daily/EOHSummary/`

The undelimited listing is truncated at 20 objects: the initial lexical slice
contains BTCBVOLUSDT ZIP/checksum names dated June 20–29, 2023. It does not sample
the other child prefix and is not a temporal or product-coverage estimate.
LastModified concerns the currently served object version; ETag is not SHA256.
Four structurally complete request cells therefore coexist with a deliberately
partial catalogue view and unknown archive-body schemas.

`EOHSummary` is a real observed source lead. Its name does not establish whether
it contains bid/ask prices, sizes, option lifecycle fields, marks or only summary
statistics. The cheapest justified next investigation is an official schema/
documentation and narrowly bounded catalogue admission for that observed prefix,
followed by at most a separately frozen representative body/checksum inspection
if needed to resolve exact columns and clocks. No unobserved filename or date
should be guessed, and no price-based selection should choose the sample.

This can determine whether a useful historical route exists, but even a body
with end-of-hour bid/ask columns would not automatically establish executable
size, simultaneous hedge fills, queue access, continuous margin marks or a
complete chain. Bid/ask-size fields, event/publication timing, contract coverage,
underlying hedge inputs and costs must be admitted before any financial test.
If only index/mark fields are present, preserve that precise limitation and
compare prospective source collection with the next distinct mechanism; do not
infer that every public historical options source is impossible.

The immediate lot-rule gap has narrowed and the archive search has identified
an observed branch worth inspecting. This is an informative **source-admission
result only**. No option premiums, Greeks, payoffs, affordability, net returns,
seller eligibility or strategy viability were established.
