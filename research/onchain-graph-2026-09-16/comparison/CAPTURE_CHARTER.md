# Matched-comparison input capture, first tranche

User authorization on September 16, 2026: start pulling data, followed by a new
Data partition for this purpose. The preserved execution checkout and new raw
artifacts will reside under /home/malecada/Data/onchain-research/ on the mounted
ext4 Data partition (/dev/nvme0n1p3; 176,155,725,824 bytes available when checked).
The existing workspace and stores remain in place. This fixed first acquisition tranche
captures seven Ethereum training-source days (January 1–7, 2022), and 38 monthly
Binance ETHUSDT spot 1d ZIP/checksum pairs (December 2021–January 2025). It opens
metadata/calendars only; no graph reconstruction, price-field interpretation,
labels, fitted predictions or financial result is authorized by this gate.

The forecast design is PROTOCOL.md. This acquisition is a separately bounded
engineering prerequisite. Completion does not admit the graph panel or the
forecast. It does not reopen the failed seven-day 2024 pilot, replenish that
family, or assert that the whole historical panel currently fits on disk.

## Exact sources and limits

Graph keys, object sizes and ETags are fixed by the retained 2022–2024 inventory
from eth-panel-readiness-20260916. Anonymous conditional HTTPS GET requests target
only its original AWS public-blockchain bucket. Per source day: 291 requests,
272 MiB response bodies, 32 MiB maximum individual payload plus one overflow
detection byte reserved inside the total allowance, 256 MiB selected columns,
16 MiB full block object, 4 MiB footer plus 8 trailer bytes, 32 row groups,
2,000,000 transactions and 8 GiB logical object. Selected columns and types
are inherited unchanged from pilot/plan.json. Capture nine exact transaction
columns, full block object, footer and trailer; retain every original byte in
lossless zstd blobs with raw/stored hashes and immutable request intents/receipts.
No numerical values are used for graph features in this tranche. A complete
source day certifies only bounded schema/range/object-byte capture.

Graph maximum is 2,037 requests and 1,904 MiB received bytes over seven days.
Free disk is checked before each request; acquisition stops if free space is
below 20 GiB plus 544 MiB working reserve. A denial (401/403/429) stops all
subsequent graph acquisition. Other failed dates remain unavailable without
retry; subsequent scheduled dates may still be attempted. Every failed or
unattempted cell is retained. Ordinary per-request timeout is 30 seconds.

Spot requests are exactly
https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1d/ETHUSDT-1d-YYYY-MM.zip
and its .CHECKSUM companion for each frozen month, in chronological order.
There are at most 76 requests, 1 MiB payload per response and 16 MiB aggregate
received bytes. Retain original ZIP/checksum bytes and bounded response prefixes
on errors. No proxy, credentials, redirects or retries. Denial stops subsequent
network acquisition. Check 20 GiB free-space floor before every request.
Verify checksum, safe sole CSV member, bounded expansion to 1 MiB, twelve fields
and exact UTC daily opening/closing timestamps (milliseconds through 2024,
microseconds in 2025). Price/volume fields remain uninterpreted strings.
January 2025 whole-month capture is container granularity; future analysis is
restricted to the January 1 opening endpoint and earlier registered bars.

Provider documents: [Binance archive documentation](https://github.com/binance/binance-public-data#data-information)
and [spot REST specification](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md).
Both historical archive revisions and unknown delivery times remain limitations.
A checksum proves current-byte agreement, not historical availability.

## Lifecycle and history

Use ResearchRun under identity eth-matched-input-capture-20260916 from a fixed
preserved source HEAD with committed gate, charter, source hashes and inputs.
Forty-five source cells (seven dates, 38 months) plus one complete-manifest cell
are frozen. All statuses, receipts and unavailable cases survive. Full manifest
binds all raw blobs, request receipts and per-source results, with independent
raw/stored hash and zstd checks. Unexpected crashes leave the claimed identity
consumed; no implicit replay or resume. Independent failure closure is required
if the resource receipt or terminal manifest is absent.

The downstream raw-input family has prior_attempts 6, attempt_budget 7, importing
the six exact graph predecessor claims once: initial source, strict prototype,
failed 2 GiB motif, completed 8 GiB motif, metadata readiness and interrupted
seven-day pilot. This single new allowance tests training-source coverage and
spot archive structure, a distinct prerequisite from the incomplete 2024 motif
pilot. Original family limits/amendments and failed receipts remain unchanged.
The static forensic reconstruction is inspected history, not another lifecycle
claim. Existing broader ETH forecasting exposures are spent; the source capture
cannot create fresh financial confirmation. No allowance for bulk capture,
pilot replay or model fitting follows merely from completion of this tranche.
Further authorized acquisition requires its own concrete reviewed bounds.

Resource limit is the existing 8 GiB aggregate sampled process-tree RSS guard,
two logical CPUs, no elapsed/CPU-duration kill. No paid source, provider contact,
account, order, production action or unattended schedule. The retained old
stores remain immutable. Capture artifacts are preserved/imported with exact
hashes; reviewed commits are pushed and remote hash verified. The free-space
floor is operational protection, not proof of whole-history storage feasibility.

Success requires every scheduled source available and an independently verified
raw manifest; unavailable input or transport results are reported without
substitution. Numerical graph canonicality/day-boundary checks, the interrupted
pilot continuation, true publication-time evidence, price admission and the
actual matched comparison remain separate prerequisites. No return-based
selection, multiple-testing inference, profitability or accounting verdict occurs.
