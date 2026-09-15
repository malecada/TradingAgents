# Pinned DefiLlama serializer follow-up — September 15, 2026

## Result

The named repository could not be admitted through unauthenticated public GitHub
metadata. Two targeted requests returned HTTP 404:

1. `https://api.github.com/repos/DefiLlama/defillama-server/commits/master`
2. `https://api.github.com/repos/DefiLlama/defillama-server`

The second request was observed at `2026-09-15T09:07:47.369575+00:00`; the first
preceded it in the same task. Retained receipts are
[01-receipt.json](value-rev-source-20260915/01-receipt.json) and
[02-receipt.json](value-rev-source-20260915/02-receipt.json). They record the
requested URL and HTTP error. No success response body or commit identity was
obtained. Error-body text was not retained; the HTTP exceptions are preserved.

HTTP 404 from unauthenticated GitHub does not distinguish a missing, renamed,
private or otherwise inaccessible repository. It does not prove that no public
implementation exists elsewhere. The first request's `master` branch was the
specific previously attempted path; repository metadata was then requested to
avoid inferring a branch name. That request also failed, so no authoritative
branch or current commit was found.

## Consequences

The exact `defi/src/api2/adapterData` directory could not be enumerated under a
verified commit. No serializer or daily aggregation implementation was read.
The unresolved timestamp unit, UTC interval start/end, partial-day inclusion,
valuation and revision issues in the [prior review](value-rev-daily-source-semantics-20260915.md)
remain unresolved. No production-deployment inference is made from a public
HEAD; no public HEAD was established at all.

The concrete next dependency is an authoritative public repository/path mapping
or a commit-pinned official implementation reference for the summary serializer.
An official response contract could resolve the same semantic question. Guessing
unlisted files or broadly searching repositories after the metadata failures
would exceed this follow-up's targeted purpose. A later public-source match
would still require distinguishing its code semantics from evidence of the
actual deployed API version and historical publication availability.

## Resource and preservation record

Only two of the six permitted HTTP requests were used. Each used a 20-second
urllib timeout, no authentication header or credential lookup, and a bounded
read of at most 1 MiB plus one overflow-detection byte for a successful body.
No successful source body was downloaded; the 5 MiB retained-source total was
not approached. Both requests completed promptly with HTTP errors, with no
retry, clone, market API, price data, provider contact or raw-outcome inspection.
Only this review and the two public-source failure receipts were written.
Existing research source, gates and historical evidence were not modified.
