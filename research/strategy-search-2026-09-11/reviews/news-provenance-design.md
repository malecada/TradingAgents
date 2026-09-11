# Fixed news provenance inventory design

September 11, 2026. Proposed source-only question, not registration or an
executed audit: **Can the specifically documented local article sources be
located and shown to expose separate observation/retrieval/version metadata,
without reading article content or fitting a signal?** This is useful even
without a directional trading claim: it determines whether a causal news input
can be admitted at all and prevents a different corpus from being substituted.

## Evidence already inspected before registration

Only directory names/existence and tracked source code were inspected. No CSV,
Parquet, article metadata record, notebook, external script, environment file or
corpus body was opened. The literal documented Alpaca/GDELT directories below
were absent during discovery. The external corpus has a nested directory with
`full_articles.csv`, separately named athlete CSVs and code/environment material.
Those names do not establish a crypto corpus or its historical identity.
Private/environment/dot directories and unrelated athlete files are excluded.

Tracked source references:

- `tradingagents/dataflows/sentiment_store.py:3` documents monthly Parquet stores;
  its schema names event_ts, as_of_ts, id, headline/content/summary, symbols,
  source, author and url.
- `scripts/backfill_gdelt.py:118` parses seendate; lines123–124 assign event_ts
  and as_of_ts to that value. Its publication-time comment is an assumption,
  not independent evidence of the actual historical article version.
- `scripts/backfill_alpaca_news.py:105` uses retrieval time, source update time
  and `availability_basis="retrieved_snapshot"` in the revised normalizer.
- `tradingagents/dataflows/vintages.py:10` defines availability columns and
  known labels, with legacy-unverified defaults and timestamp consistency
  guards. Modern code cannot retroactively authenticate old stored bytes.
- `docs/research/DATA_CATALOG.md:43` explicitly records absent corpus inventory/
  vintage/backup verification. Findings §63's historical count is a separate
  narrative assertion, not proof the external CSV is that store.

## Seven fixed source slots

No recursive workspace search, glob expansion into other worktrees, network
request, alternative path, symlink following or credential inspection. Each
slot produces a retained receipt even when absent or forbidden.

| Slot | Exact absolute target | Permitted format inspection |
|---|---|---|
| audit-alpaca | /home/malecada/master_thesis/TradingAgents-audit-fixes/data/sentiment/alpaca | Directory inventory; monthly Parquet footer/schema only if present |
| audit-gdelt | /home/malecada/master_thesis/TradingAgents-audit-fixes/data/sentiment/gdelt | Same |
| original-alpaca | /home/malecada/master_thesis/TradingAgents/data/sentiment/alpaca | Same |
| original-gdelt | /home/malecada/master_thesis/TradingAgents/data/sentiment/gdelt | Same |
| predlab-alpaca | /home/malecada/master_thesis/TradingAgents-predlab/data/sentiment/alpaca | Same |
| predlab-gdelt | /home/malecada/master_thesis/TradingAgents-predlab/data/sentiment/gdelt | Same |
| external-csv | /home/malecada/master_thesis/News_fulltext/News_fulltext/full_articles.csv | File identity/size and narrowly bounded header schema only; no records |

Freeze these literal targets before any payload/schema inspection. Missing
directories remain missing slots, not replacement opportunities. If they remain
absent, the run is still informative: source locations required for an existing
historical claim were not found at the documented paths. It does not prove the
files were destroyed or nonexistent elsewhere.

For each directory, enumerate only children matching four-digit year directories
and their `01.parquet` through `12.parquet` files; ignore all other names without
opening them. Maximum1,000 encountered entries per slot, including excluded
entries; overflow is partial inventory, not complete absence. Select at most
the first two lexical monthly paths per slot, without inspecting contents first.
Selection denominator is always two footer slots for each directory, including
unavailable placeholders: **12 footer slots plus one CSV-header slot**. Never
select a substitute after a chosen file fails. This is a bounded schema sample,
not full source coverage.

## Permitted fields and privacy boundaries

Record target ID, format, absence/type/symlink status, file byte size, observation
clock, and source schema evidence. Filesystem mtime can be recorded as a local
file attribute only, never an availability timestamp. Pin inspected header/footer
byte-region hashes and offsets, not a full CSV-body hash that would require
reading article content. Check file identity/size before and after to flag
concurrent changes. Preserve original stores; do not copy full corpora.

Parquet inspection must read only bounded footer/schema metadata. Disable row-
group statistics and arbitrary key-value metadata publication: min/max of a
headline column can expose content. Do not read data pages or article records.
Footer cap1MiB per selected file; reject excessive/invalid metadata without
trying another file. Record schema presence/type only for the whitelist below,
with column count and hashed unknown names, never raw content-field statistics.

CSV inspection may read only the first physical line, maximum64KiB, no buffered
read-ahead into records. Require strict UTF-8 and a complete, strict CSV header
on that line; embedded-newline headers are unavailable rather than expanded.
Recognize header names case-insensitively only from the whitelist; do not print
arbitrary unknown names. Preserve unknown-column count and per-name digest.
Do not persist arbitrary raw header text if it could be a headerless article
row. If the line lacks any plausible identifier/time provenance field, retain
only digest/length and classify header semantics unavailable. No CSV records,
article text, headline, summary, author or URL value is read or emitted.

Recognized schema fields (presence/type only): event_ts, as_of_ts, retrieved_at,
source_updated_at, availability_basis, id, url, symbols, source, published_at,
created_at, updated_at, date, seendate. Content/headline/summary/author columns
may be reported as present by name only; no values or statistics. A name such
as date or timestamp carries no automatic meaning. The exact whitelist and
normalization must be frozen, with collisions retained as ambiguous.

## Denominators, limits and interpretation

Seven source cells, plus13 fixed subordinate schema slots. Suggested nine
outputs: seven sanitized source receipts, one inventory and one admission
summary. All missing/partial/unavailable outcomes retained. Maximum4MiB total
serialized output, 64KiB CSV header, 1MiB each selected footer, 512MiB sampled
aggregate RSS, two CPUs and120seconds wall. No retries or detached processes.
Independent hostile-footer/header/path/symlink/resource tests precede execution.
Coordinator should narrow limits or schema scope if implementation cannot
enforce these boundaries; no actual corpus outcome justifies broadening them.

Separate dimensions avoid misleading PASS labels:

1. **Inventory** complete/missing/partial/unavailable for each exact target.
2. **Schema** present/absent/ambiguous/unavailable for each frozen field/slot.
3. **Historical availability** remains unverified at this stage even when all
   named columns exist. No row-level timestamp order, revision preservation,
   asset mapping, completeness, source precision or extraction accuracy has
   been tested. Column presence is not causal admission.

The decision can justify a second, separately registered metadata-column-only
record audit if a suitable Parquet store is found, with first-seen/retrieval
semantics and exact file hashes bound before reading rows. CSV text-bearing
records are not implicitly admitted: either an existing content-free metadata
sidecar must be located through a new bounded registration, or a separately
reviewed projection/privacy workflow is needed. A corpus with only publisher
dates is unavailable for historical version-aware inference until supported;
no arbitrary two-day lag repairs missing first-observation evidence.

## Ancestry and stopping boundary

This is a new source inventory, not an alpha attempt or revival of failed C1/C3,
NLST/SMW/DEX, factor combo or scalar-LLM configurations. It inherits all news/
attention searches, C1's permitted amendment and spent development/holdout
history. It grants no virgin sample. No new extraction tier, label, event
prediction, sentiment score, return join, provider contact, paid product or
financial experiment follows automatically. Model cutoff/vintage restrictions
remain; current model recollections cannot label historical surprises honestly.
All22 settlement-blocked cases remain deferred.

Useful completion means reporting the exact bounded source-location/schema
evidence and naming the next dependency, even if every old monthly root is
missing. It does not mean searching until a convenient corpus appears, claiming
the whole news family failed, or spending repeated metadata runs without an
identifiable path to an economically meaningful causal question.
