# Independent news provenance engineering review

Disposition: **PASS for the one bounded metadata-only source inspection** after
the required committed source/gate and verified remote freeze. No real corpus
path, CSV line, Parquet file or article record was opened in this review. Only
implementation, registration and invented fixtures were inspected.

## Concurrent-change finding resolved before outcomes

The initial `_identity` omitted ctime. An independent invented CSV test changed
the file in place after the first byte was read, preserved its size and restored
its original mtime. The initial code reported a present schema and unchanged
before/after identities even though ctime had changed. This could hide a
metadata-preserving source update during inspection.

The coordinator added `ctime_ns` at `news_provenance.py:63` and a genuine
in-place-write/mtime-restoration regression. An independent repeat now reports
`concurrent_file_change`, removes the schema, and retains region digests and
both identities. A separate same-size path replacement also rejects correctly.
The charter explicitly qualifies file metadata comparison as best-effort change
detection: same-tick changes can escape filesystem timestamp resolution, so no
atomic snapshot is promised. Neither ctime nor mtime is historical availability.
This correction does not expand any content read or target scope.

## Source and privacy boundaries

The entire serialized input specification matches `default_spec()` exactly,
including seven absolute targets, whitelist, normalization and every resource
bound. The main path checks that equality before inspection. It has no network
calls, alternate-path discovery, recursive corpus search, model, return join or
financial calculation. Imports do not perform a real inspection.

Absolute paths are walked component by component relative to held descriptors
with `O_NOFOLLOW`; symlinks at either an intermediate or final component are
rejected. Final file type is checked and nonblocking open avoids a FIFO read.
Secret path components are excluded. Directory enumeration counts all encountered
entries, including excluded names, with a single iterator-only overflow probe.
Overflow withholds both selections rather than treating a truncated list as
global lexical order. Eligible paths are restricted to four-digit directories
and literal monthly filenames. The first two lexical candidates are fixed
before metadata reads, and a failed selected file is not replaced.

Parquet reads are restricted to the leading magic, trailing length/magic, and
at most 1 MiB of the declared footer region. `read_schema` receives an isolated
in-memory buffer containing those metadata bytes, not a handle to the original
file or its data pages. The parser version is fixed. Projection emits only
whitelisted field names with safe primitive type categories, counts and hashes
of unknown names. Arbitrary key-value metadata, row-group statistics and parser
error messages are not published. Corrupt/oversized metadata is unavailable;
there is no fallback to records or another file.

CSV reads use one-byte unbuffered reads through only the first physical line,
up to 64 KiB. CRLF handling stops at CR, without reading the LF or following
record. Strict UTF-8/CSV parsing rejects embedded-newline/incomplete headers;
schema width is capped before projection. Unknown literal names are hashed;
the raw first line is never published. Plausible ID/time field presence is a
frozen heuristic for a candidate header, not proof of corpus identity or field
semantics. A date column cannot establish publication, retrieval or first-seen
time. Known-name normalization collisions remain ambiguous.

## Independent adversarial checks

`check_news_privacy_synthetic.py` ran eight independent invented checks, all
passing on the final inspector hash. A nonempty Parquet fixture planted private
article strings in row-group min/max statistics and private schema metadata.
Instrumented reads were exactly the three permitted regions; neither article
strings, private metadata nor unknown raw field names appeared in the sanitized
result. Every published region digest matched its actual bytes. Other checks
covered CRLF without read-ahead, multiline/invalid-UTF8/headerless first lines,
mtime-preserving in-place rewrite, same-length path replacement and an
intermediate symlink. No production target was opened. Results are retained in
`news-privacy-synthetic-review.json`.

The final implementation regression suite has 20 passing synthetic checks,
including the corrected concurrent-change case and guarded actual CLI. Its
source was reviewed for missing-root denominators, lexical selection without
replacement, exact entry-limit truncation, footer limits, sanitized parser
failure, schema collisions and projection budgets. The refreshed full CLI
report uses only invented targets substituted for the fixed target map; parser,
I/O/projection, argument parser and lifecycle code are unchanged. It retains
seven complete source cells, 13 schema slots, nine outputs totaling 140,521
bytes and two CPUs. The final inspector SHA matches this report.

The guard reports exit zero, no limit reason, 0.92281 seconds and 156,721,152
bytes peak sampled aggregate RSS under the frozen 512 MiB/120-second limits.
Nominal 20 ms sampling, the process-exit retry, brief overshoot and individual
child versus aggregate-RSS qualifications remain explicit. Passing synthetic
resource checks is not a guarantee against every malformed footer or abrupt
process failure.

## Denominator, evidence retention and interpretation

Seven source receipts are persisted one at a time. All 12 fixed footer slots
and the single CSV header slot survive in the final inventory/admission,
including absent selections and unavailable/partial sources. An inventory with
one eligible file can finish its bounded inspection while its unused second
footer slot remains explicitly unavailable; this is not full corpus coverage.
Empty or missing stores cannot become a successful schema result.

Each receipt's sanitized projection is removed and its schema marked unavailable
when it would exceed 128 KiB; metadata-region hashes and file identities remain.
All nine actual lifecycle-encoded outputs are capped at 4 MiB. A failure after
earlier receipts leaves them retained through the original lifecycle; an abrupt
kill can leave the claim incomplete and spent, not silently retried. Region
digests are evidence of inspected bytes, not a recoverable backup of the corpus.

Inventory, schema presence and historical availability remain separate. No field
presence can admit causal timing, authenticated revisions, entity mapping,
dataset completeness or financial utility. The absence of the named locations
does not establish absence elsewhere or failure of all news mechanisms. Any
further record-level or alternate-path work requires its own justified scope;
there is no automatic extraction, lag repair or alpha follow-up.

## Final gate binding

- Gate: `e85a08c4ee2878c38aa111506f5d179d83161a430e7aa925b242177bb41f5bee`.
- Inspector: `a4264c026aa9c1f7962a7835a6aa23b27db02e74ae260baf525a11a8480d74fd`.
- Charter: `eeeba0983e64c6728835929625df17cd5537009af065ba8f46a7b81842948c76`.
- Exact input specification: `ff0a5e08364701b7b2e8dade3bcaae1d63ee927709063f9ae60b7074319037a4`.

All four registered source hashes and six original runtime hashes match current
files, as do the charter and sole specification input hash. The documentary
input window exactly matches the specification-materialization observation
marker. It describes prior local design exposure, not the future inspection's
capture time or historical article availability; actual observation times are
recorded separately in source receipts.

The gate preserves every prior experiment, family and dataset definition from
the WBETH book gate. The new source-only family grants exactly one claim with
prior_attempts zero and explicitly charges the third initial MAP row8 question
after the two WBETH questions. It does not reset the broader news/LLM search or
grant a new three-trial alpha budget. Seven cells and nine output identities
match the inspector exactly. No real target claim exists at review.

No material implementation or registration blocker remains. Real source
availability, candidate schema contents, historical timing, revision integrity,
corpus authenticity, financial usefulness and external backup were not tested.
The post-run review must remain within these metadata-only boundaries.
