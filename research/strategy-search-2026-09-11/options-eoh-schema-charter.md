# EOHSummary single-object schema discovery

Experiment `options-eoh-schema-20260911`; parent `options-metadata-20260911`.
Source-schema question only: what literal first-row fields, row widths and
empty-field patterns occur in the earliest officially listed BTC EOHSummary
object, and can its integrity be verified? No option quote interpretation,
premium/strike selection, payoff, Greeks, affordability, returns or fills are
computed. Unknown schema is the registered discovery target, not a license to
change the financial hypothesis after observing prices.

## Evidence, selection and ancestry

The saved [official-source review](reviews/options-eoh-schema-source.md) identifies
147 BTC ZIPs with checksum companions in a nontruncated catalogue, dated May 18
through October 23, 2023, with twelve missing calendar-date keys. No ZIP body was
opened by that review. The lexically earliest BTC ZIP is selected solely from
that catalogue: `BTCUSDT-EOHSummary-2023-05-18.zip`, listed size 402,333 bytes,
LastModified `2023-06-06T13:24:13.000Z`; its checksum is listed as 100 bytes.
Listed size and modification date are provenance observations, not guarantees
of the bytes now served or market/publication times. The earliest object is not
a representative day, evidence of inception, or a favorable economic selection.

Exactly one known RVIV administrative gate bundle and twelve exact historical
ledger rows remain inherited, together with its failed HAR/DVOL gate and unknown
overall statistical multiplicity. The options metadata investigation used the
first of three new investigations. This source probe consumes the second,
leaving one under the unchanged options family cap of four including the known
prior bundle. A rename, parse failure or unavailable cell cannot reset that cap.
The 2023 object date lies within the previously exposed June 2022–March 2025
RVIV development window; new columns do not restore financial freshness.

Any lifecycle window for observing the static request-spec bytes is documentary
bookkeeping only, with its actual locally observed marker supplied by the gate.
It is not a market-data observation window. Preserve separately: filename date
May 18, 2023; catalogue LastModified June 6, 2023; source discovery September 11,
2026; and actual future request/retrieval clocks of this acquisition. No date
is backprojected as first public availability or untouched confirmation.

## Fixed acquisition and outputs

The sole request input is [options-eoh-request-spec.json](options-eoh-request-spec.json):
one exact ZIP URL followed by its exact `.CHECKSUM` URL. No fallback date,
underlying, filename, host, pagination, refresh or retry. If either request
fails, retain the ZIP/checksum pair and its explicit missing dependency; no
alternative object is selected. No current options API or hedge-data request.

Use the already frozen `carry_capture.public_get`: each request has a 20-second
wall timeout and 5 MiB received-body cap, without auth/proxies/redirects/retries.
HTTP 403/418/429/451 suppresses remaining same-host attempts. Both request cells
remain in the intended denominator. Publish received bytes or exact partial
prefixes, hashes, counts, status/error, completeness and actual request/retrieval
UTC clocks before starting the next request or parsing either body.

Four declared outputs: two individual raw receipts, `eoh-capture.json` and
`eoh-schema.json`. Global limits: 10 MiB acquired raw bodies, 64 MiB total actual
lifecycle-encoded outputs, 512 MiB sampled aggregate RSS, two allowed CPUs and
120 seconds through the pinned reviewed `resource_guard_v2`. Record its exclusive
resource report separately; the gate pins the launch path. No filesystem ZIP
extraction, background/nested worker, original-store mutation or network outside
the two reviewed public_get calls. Account for actual pretty serialization,
including duplicated raw receipts, rather than compact JSON size.

Cooperative resource stops and recoverable parser errors retain both receipts
and unavailable result cells. Abrupt termination/allocation failure may preserve
only partial outputs and the immutable claim's two intended identities; it
cannot become a silent retry or be represented as complete schema admission.

## Frozen integrity and schema-discovery rules

Only complete HTTP 200 bodies qualify for interpretation. A checksum response
must be strict UTF-8 containing exactly one SHA256/basename record, optionally
ending with a newline, with the frozen ZIP basename. Require 64 hexadecimal
digest characters and verify them against retained ZIP bytes. A valid checksum
record without its ZIP stays a source receipt, not verified archive integrity.
Preserve both request outcomes and the paired-integrity dependency explicitly.

The ZIP must have exactly one member named
`BTCUSDT-EOHSummary-2023-05-18.csv`. Reject extra members, directories, encryption,
absolute/traversal paths, corrupt ZIP/CRC/deflate, or mismatch between declared
and actual uncompressed bytes. Maximum uncompressed member size is 16 MiB;
maximum uncompressed/compressed member ratio is 100, with zero compressed size
handled without division or a bypass. Bound expansion before allocating or
reading beyond the limit; never extract to a path.

Decode strictly as UTF-8 without replacement; preserve the presence of any BOM
rather than silently repairing bytes. Parse using the standard CSV reader with
comma delimiter, double-quote quoting and strict mode, no dialect sniffing,
and maximum field length 1 MiB. An empty object, decode error, CSV error or
resource overflow is unavailable, with raw bytes retained. Unknown field names
are not a schema error: discovering them is this precommitted experiment.

Preserve the first CSV record verbatim as a **candidate header**, including
empty and duplicate tokens and column index. No official header specification
has been admitted, so header-versus-data semantics remain unverified. Report
total parsed records including that first record, records after it, the full
record-width frequency table, and the count/indices of rows whose widths differ
from the candidate header. Do not silently drop malformed-width or blank rows.
Record exact empty-string field counts by column index over subsequent rows,
and absent-column counts separately; whitespace-only and other tokens are not
automatically null. Unknown null encodings remain unknown. Summaries may be
bounded at 2 MiB of actual encoded output; exceedance makes normalization
unavailable rather than truncating denominators silently.

No substring heuristic may label a field a bid, ask, size, clock or executable
quote. Preserve literal header tokens, but semantic field mapping, clock units,
timezone, observation frequency, quote age and hour-start/end conventions remain
unavailable unless separately supported by exact official documentation. Do not
convert numerical-looking fields into prices or timestamps, compute spreads,
inspect extrema, choose contracts, or claim per-hour chain completeness. Actual
raw bytes are retained for a future separately registered semantic admission.

Distinguish request completeness, paired integrity, lexical CSV discovery and
economic usability. A successful lexical schema report is not admission of a
historical quote chain; a failed checksum/parse does not demonstrate economic
failure of volatility compensation. No p-value, beta, capital or convention-swap
PnL criterion applies to this source-only stage.

## Review and continuation

Before execution, test malformed checksums, multiple/path members, ZIP CRC and
deflate failures, expansion bounds, UTF-8/CSV errors, unknown/duplicate headers,
ragged/blank rows, literal empty-field counting, denominator retention and actual
output/resource limits on invented inputs. Commit and independently review the
exact source, spec, charter, launcher and gate before acquisition. An independent
post-result checker verifies retained bytes and reconstructs integrity/counts
without importing collector parsing logic.

If literal columns and a subsequent documentary mapping suggest useful quote,
size and clock information, the remaining family allowance can address the exact
semantic/lifecycle/hedge dependency under a new registration. No financial test
is admitted by this charter. If this object supplies no useful documented route,
defer the historical EOHSummary execution route with named missing inputs and
switch to the next distinct mechanism. Do not treat this one old object as a
rejection of every public options source or all options strategies.
