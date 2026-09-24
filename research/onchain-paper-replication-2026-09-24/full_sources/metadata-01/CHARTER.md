# Bounded full-history public metadata inventory

This stage accounts for BTC and ETH2016–2024 source availability and storage,
without decoding transaction pages, acquiring prices or fitting any model.
It is one new source claim under the unchanged cumulative51 ceiling/prior17
history. The source allowance is explicitly reallocated before outcomes: one
cross-asset metadata inventory, at most15 missing asset/year body batches
(BTC2016–2024, ETH2016–2021), and two asset price batches. Existing ETH2022–2024
raw inputs remain immutable and are reused through their prior manifests.
This allocation still totals18 source claims; no retry, extra fit, second lane,
paid capacity, provider contact or fresh-confirmation assertion is introduced.

For each asset/year, list at most8 unsigned S3 pages/32MiB with1000keys per page.
Retain all request intents, returned bytes, HTTP failures, pagination failures
and missing dates. Use only the frozen public us-east-2 AWS dataset endpoint.
No redirects, credentials, retry or mirror substitution. Every2016–2024 calendar
date and required field remains in the source denominator, including unavailable
price and transaction values. A listing is not source admission.

For each complete listing, inspect current Parquet metadata for first object by
key, largest object by size (key tie-break), and last object by key. Deduplicate
identical selected objects. Each distinct object receives at most two conditional
Range requests: its8-byte trailer, then its declared footer capped at2MiB.
Require exact206 Content-Range and unchanged ETag. Retain byte hashes and UTC
request/retrieval times. Missing distinct sample slots remain explicit. No data
pages are read. Footer bytes may contain incidental per-column min/max value
statistics; this exposure is retained and cannot be used for fitting. Selected footer schemas and compressed
column sizes are resource evidence for these objects, not proof of full-year
schema, canonical-chain completeness, availability at historical decisions,
Bitcoin source precision, previous-output fidelity or exact paper data agreement.

Finite maxima:18 asset/year listings,144 listing requests,54 distinct footer
objects/108 range requests,32MiB listing plus6MiB+24bytes footer data per asset/year
(a bounded one-byte over-limit prefix may be retained per response). Base64
receipts expand stored response bytes by approximately4/3. Failed or oversized
responses stop that catalogue/object and remain evidence; independent cells
continue. Global wall limit30minutes; resource cap1GiB, high watermark768MiB,
no swap, two CPUs,3GiB host reserve and20GiB free-disk floor. This lower cap is
specific to metadata; the6GiB neural pilot and its startup reserve are unchanged.
Guarded execution and external post-death reconciliation precede terminal closure.

Outputs retain72 catalogue/footer slots, factored85,488 asset/date/field source
denominator, artifact hash index and total listed/sample compressed sizes.
All transaction-value and price cells remain unavailable at this metadata stage.
No sampled source size is extrapolated as a demonstrated full-training bound.
Further source and financial releases require their own reviewed committed gates.
