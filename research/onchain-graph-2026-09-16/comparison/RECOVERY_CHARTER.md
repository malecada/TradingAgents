# Missing graph-source recovery

The September 17 user instruction authorizes recovery of the 521 unavailable
dates in the terminal remaining-cohort capture. The explicit single additional
allowance is `SOURCE_RECOVERY_AMENDMENT.md`, hash-bound by the recovery gate and
certificate. This is raw-source engineering only, with no graph event decoding,
price interpretation, labels, model fitting or financial conclusion.

The original run closed at 08:55:58 UTC before the current boot at 13:17:25 UTC.
Its 563 complete days and 521 unavailable days remain unchanged. There were six
individual transport failures and 515 DNS failures beginning at 07:28:59 UTC.
An empty or failed network response was recorded for each unavailable date;
those failures are not successful coverage. The recovery runs in a fresh fixed
checkout on Data and never restarts the original identity.

## Frozen inputs and reuse

`recovery-cohort.json` identifies exactly the 521 unavailable dates in ascending
order, the 563 excluded complete dates, and six complete response prefixes from
the original Data store. Those prefixes contain 233 successful requests and
449,845,693 bytes of files, including metadata. Every selected file's size and
SHA256 is frozen; raw/stored hashes, ETags, byte ranges, schema and request order
are checked before any new HTTP for its date. Complete originals are never
downloaded again. Failed or truncated responses are never reused as valid bodies.

Successful prefix files are copied byte-for-byte into the new date directory,
with an explicit reuse-provenance record. Original timestamps remain original
capture timestamps. The original store, including failed responses, is untouched.
The new lifecycle output and accompanying manifest/provenance distinguish logical responses, reused responses and
actual new HTTP requests/bytes. Copies consume disk and are charged again in the
new storage budget. January 9, 2024 additionally reuses the previously retained
full blocks through the unchanged hash-bound block-reference procedure.

Only missing requests use the original anonymous AWS public-blockchain endpoint,
same fixed inventory keys/ETags, conditional headers, nine transaction columns
and block schema. No proxy, credentials, redirects, provider switch or automatic
request retry is permitted. DNS resolution alone is checked before launch and
before a new claim; no data body is fetched by that startup check.

## Bounds and outage behavior

Each date retains the inherited 291 logical requests and 272 MiB logical response
bound, inclusive of valid reused bodies. New HTTP totals therefore cannot exceed
151,611 requests and 141,712 MiB over all 521 dates; actual reuse reduces them.
Individual responses remain bounded to 32 MiB plus an overflow sentinel inside
the aggregate budget; full blocks 16 MiB, footer 4 MiB, selected columns 256 MiB,
32 row groups, 2,000,000 rows and 8 GiB logical transaction object. Timeout is
30 seconds. No numerical transaction rows are decoded.

The first transport failure—including DNS, reset, TLS/read timeout and truncated
body—latches a stop across every later date. HTTP 401/403/429 and storage stops
retain the inherited global stop. Other deterministic schema/object errors are
unavailable for their date without retries. A stopped attempt records the later
dates as unattempted/unavailable with zero new requests; it does not keep issuing
hundreds of doomed requests during an outage. No automatic resume is configured.

Shared raw ceiling remains 120 GiB, with a conservative 54 GiB prior family-body
baseline (original measured total with prior baseline: 57,348,575,704 bytes).
Metadata remains capped at 2 GiB, charging 512 MiB prior metadata and 128 MiB
reserved lifecycle/log/guard overhead up front (original measured metadata
accounting: 519,823,360 bytes). Copied prefixes receive their own worst-case
storage reservation in addition to the inherited working allowance. Available
disk must exceed the 20 GiB floor plus working reserve before every request.
Separate preserved checkout copies also consume free space; the floor is checked
against actual filesystem availability, not only logical family accounting.

The unchanged 8 GiB sampled process-tree RSS guard and two-CPU affinity apply.
There is no duration kill. Per-date lifecycle outputs are bounded to 16 KiB,
final index to 32 MiB and summary to 1 MiB, within the reserved metadata allowance.

## Verification and termination

The separate raw checker reconstructs footer-derived byte spans and reconciles
every intent/receipt/body and per-day manifest. A recovery-specific independent
check compares copied prefix bytes against the frozen manifest and separates
reused versus new network counts. A failing check preserves the original capture
fields and publishes an unavailable final source cell. No source-validation
result implies canonicality, motif correctness or historical availability.

Identity `eth-graph-source-recovery-20260917` has 522 cells (521 dates and final
index), with every failure/unattempted date retained. Immediate per-date outputs
and immutable source files survive interruption. The launch record includes PID,
process start ticks and boot ID. A crash consumes this identity; do not relaunch
it or delete evidence. The finite job has no recurring scheduler or auto-restart.

Source, gate, amendment and independent review are committed and remote-hash
verified before launch. Prior terminal/metadata evidence is copied and backed up;
the roughly 51 GiB old bulk raw corpus and new raw output remain local on Data
without a verified off-device backup. No full raw Git import is attempted.
After successful acquisition, whole-panel numerical admission and the matched
M0/M1/M2 prediction evaluation remain separate outstanding work.
