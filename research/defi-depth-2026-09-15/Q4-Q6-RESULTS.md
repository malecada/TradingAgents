# Q4/Q6 findings: source contracts, not rejected strategies

Both registered source inspections completed using execution commitb303754.
Q4 retained24cells (16complete,8unproved),33outputs and1,140,942metadata bytes.
Q6 retained14cells (7complete,7unproved),15outputs and zero external metadata or
article-record reads. Structural verifiers reconcile both complete denominators.
Independent substantive review passed (reviews/q4-q6-postexecution-review.md). No strategy or financial result was
computed. Original source files, raw stores and prior results were not modified.

Two initial command invocations used an abbreviated source commit. Admission
rejected both before a claim or input read: full current HEAD is required. Correct
full-commit invocations created the only Q4/Q6 claims. These are two retained
preclaim command mistakes, not additional financial/source observations, and do
not erase or duplicate a spent empirical attempt.

## Q4: data exist, but the mature-token question is not yet answerable

All eight fixed metadata files exist, are regular stable files and parse within
the bounds. The four hashes match pairwise across the active and preserved
predlab roots: token_map146839bytes; pools386182; month_blocks1302;
universe36148. Thus there are four distinct byte sets, not eight independent
sources. Both month and universe dictionaries contain52date-shaped keys from
2021-01-01 through2025-04-01. This is useful preserved history. It is not proof
of a complete token census, causal supply, trade execution or365-day portfolios.

The specific stored pipeline has several limits:

- `scripts/predlab_smw_map.py:64` maps saved perpetual symbols using a later
  CoinGecko/Binance spot identity snapshot. The documented snapshot date is
  2026-09-04; fallback identity selection uses contemporaneous capitalization
  ranks, and decimals are requested at latest state. It attempts to retain
  unmapped/delisted-symbol cases, so the result is not simply a current-winner
  list. Nevertheless, historical identity/eligibility and complete failed-token
  coverage cannot be established by this later mapping alone.
- `scripts/predlab_smw_pools.py:48` enumerates current factory mappings for the
  selected token roster. Deterministic pool addresses can help identity, but
  this is not a census of historically eligible tokens and failed pools.
- `scripts/predlab_smw_depth.py:85` selects monthly exchange-volume members and
  historical quote balances, then forms an aggregate depth threshold. Quote
  balances and a factor-of-two depth proxy are not two-way executable sell
  quotes, token transfer restriction checks or terminal recovery evidence.
- `scripts/predlab_smw_fetch.py:116` acquires wallet-flow logs for that inherited
  universe; its block anchors support interpolation, not automatically exact
  event-time availability. Reusing buyer breadth/flows would inherit the
  already-searched SMW signal family.
- `scripts/predlab_nlst_dex_fetch.py:1` explicitly describes first-day screening
  and a16-day event window for newly created pools. That panel has a different
  age/horizon from a mature-token365-day allocation. The old pipeline comments
  are not evidence that every raw segment is present or complete.

The inspected metadata schema does not supply admitted historical circulating
supply, dilution/unlock vintages, product-adoption-to-tokenholder value capture,
or end-to-end sellability. Unknown/dynamic schema keys were deliberately
sanitized, so their nonappearance in a report is not proof those concepts are
absent everywhere. The narrower conclusion is that the fixed evidence packet
has not established them.

**Decision:** retain the metadata and code as reusable infrastructure. F4 is
unavailable for a defensible financial test from this packet; no economic rejection
or prediction that small tokens cannot work is justified. A descendant needs a
causal roster including failures, historical eligibility/supply/unlock records,
a specific value-capture measure and matched two-way execution. Changing a cap,
choosing present-day winners or copying old wallet features would not cure this.
The45imported records and one source claim remain spent/linked.

## Q6: producer behavior clarifies which clocks can be trusted

All seven exact source files parsed as code; none was imported or executed.
Substantive source reading gives a more useful result than a field-name search:

- `scripts/backfill_alpaca_news.py:105` records created time separately from
  retrieval and updated time, labels a retrieved snapshot and rejects a source
  update later than retrieval. A newly downloaded old article is therefore
  available at its retrieval, not automatically at historical publication.
- `scripts/ingest_hf_bitcoin_news.py:64` similarly assigns retrieval availability
  to a downloaded snapshot. Its main deduplicates URL and article IDs before
  upsert (`:99`), so the stored helper's version preservation does not prove
  that every distinct source-file revision survives within that ingestion.
- `scripts/backfill_gdelt.py:113` sets availability equal to the supplied event
  time and does not supply a retrieval/version basis. This alone is inadequate
  for historical availability. `vintages.with_availability` assigns a missing
  basis `legacy_unverified`; strict queries reject such nonempty rows. The
  comment saying publication-time observation is not independent evidence.
- `tradingagents/dataflows/sentiment_store.py:40` uses article ID plus as-of time
  to merge versions. `tradingagents/dataflows/vintages.py:33` rejects conflicting
  same-key content and archives the previous file before replacement. These are
  useful engineering controls, not proof that historical versions were captured.
- `tradingagents/dataflows/crypto_sentiment_pit.py:31` uses end-of-day UTC as
  availability cutoff. A future strategy deciding earlier that day would need
  its own actual decision cutoff; the date-only interface cannot justify an
  intraday decision. `news_data_pit.py` explicitly refuses unsupported sources.

No connection from these seven files to the named external full_articles.csv
was established. This conclusion is limited to the inspected files; no claim
is made that no exporter exists elsewhere. The external CSV was not reopened
or hashed, no article records were read, and the prior13-byte finding remains.

**Decision:** the historical information-strategy source remains unqualified.
The reusable prospective contract is to preserve exact response bytes, source
identity/version, publication and first-observed retrieval times, later revisions,
causal coin tags and decision cutoffs, with failures retained. No collection or
observer has started. No news alpha or model trial is justified by code capability
alone. The12imported direct records and one Q6 claim remain spent/linked; wider
information-family multiplicity remains unknown.

## Program consequences

Q4/Q6 consume two source questions, not financial recipes. Q5's earlier reviewed
carry books remain actual negative economic findings specific to those recipes;
these source limitations are a different result category. Q3 later closed after an execution-root HEAD error; see Q3-RESULT.md. F1/F3 still lack a complete qualified annual protocol
panel after R1's preserved provider-limit failure. Useful questions remain under
assessment; this document does not declare the entire phase exhausted.
