# Coverage reranking and value_rev readiness — September 15, 2026

## Decision

The highest-value independent work available immediately is a bounded offline
readiness correction for the already registered `value_rev` source-stability
question. Its second vintage remains unavailable until September 18 or later;
no early P0, breadth, publication-lag, ratio or return evaluation is justified.
A definite implementation/charter mismatch can be corrected and tested with
invented inputs before that date. This engineering work does not grant another
factor family, four-cell grid or empirical attempt.

The active options episode remains the primary prospective investigation.
[STATE](../STATE.md) records the twentieth identity, nineteen preserved
predecessors (16 complete, 3 failed), the consumed effective options cap of five,
and a finite VPS launcher awaiting its first operational source check at this
review's read time. The [actual claim](../../../research_runs/options-episode-20260911/claim.json)
and [grant](../options-episode-grant-20260915.json) govern the single episode.
No interim financial inspection, additional expiry, replacement episode or
extra short quote probe follows from resumption. Temporary observation waits do
not establish research-program exhaustion.

## Coverage and eligibility

The ranking uses [MAP](../MAP.md), [BACKLOG](../BACKLOG.md),
[HISTORY](../HISTORY.md), [SOURCES](../SOURCES.md), the linked decisions, and
[the earlier coverage review](coverage-after-options-preparation.md).

| Question | Current eligibility and next material dependency |
|---|---|
| Existing value_rev source stability | Highest-value immediate readiness work; the actual second vintage is time-blocked. Preserve its four cells and inherited value/factor trials. No new empirical registration is needed for this source-code audit. |
| Sole options selling episode | Admitted and consuming effective fifth allowance. Await frozen source collection and externally verified return/stop admission; no economic result yet. |
| Binance–Bitrue funding differential | One of three investigation slots used, but remaining slots do not supply missing final funding events, event marks, current fees or account applicability. Exact public final-event evidence or a separately reviewed finite prospective final-event design is needed. Generic documentation searches have already received bounded follow-ups. See [Decision 11](../decision-11.md) and [source review](bitrue-funding-history-source.md). |
| Economically linked relative value | WBETH used two mechanism questions; positive primary cash failed every frozen 3% relevance screen. Historical contractual ratio could improve attribution, but cannot rescue the retained same-quantity cash result. A materially distinct payer/claim and admitted hedge cashflows are needed; increasing leverage or choosing another window is not sufficient. See [Decision 14](../decision-14.md). |
| News/on-chain information | Seven exact sources and thirteen schemas were unavailable; the third MAP-row-8 claim was used after two WBETH claims. A versioned source manifest with availability, revisions and entity lineage is needed. Broad path fishing or repeated extraction is not a new source question. See [Decision 15](../decision-15.md). |
| Funding carry | Three incremental investigations used; all eight cash books failed economics. Historical carry attempts remain charged. No fee/date/asset sweep is justified. |
| Dated basis and derivatives | Effective seventh attempt consumed, including retained failures. The last attempt failed its 120-second resource bound after retaining three outputs; independent reconstruction retained eight negative books and no frictionless relevance rescue. No eighth attempt or rerun. |
| Liquidity/dislocation | Three questions used. Gross discrepancies did not survive assumed fees in supported states; unsupported cutoff bins remain flagged. Public depth does not supply queue position or realized execution. Another threshold grid is not an independent mechanism. |

Nominal unused mechanism slots are not transferable around an exhausted broader
family. Momentum, carry, value, liquidity, calendar, stress and information
ancestors in HISTORY remain charged; renamed variants do not reset those counts.
The 22 historical settlement-blocked cases remain explicitly deferred.

## Concrete value_rev readiness findings

Authority is the unchanged [September 4 charter](../../../docs/superpowers/specs/2026-09-04-value-rev-charter.md)
and `value_rev` object in [gates.json](../../../data/rebuild/gates.json).
The [earlier factor review](factor-information-next-question.md) already ranked
this source question behind the subsequently completed news inventory.
Only source code, registration text, directory existence and snapshot manifest
metadata were inspected here. No panel, raw response body, revision outcome,
breadth or financial number was read or computed.

1. **P0 uses the wrong observational unit.** The charter requires common
   protocol-days. `scripts/value_rev_dev.py:57–80` reads token-level parquet
   aggregates and compares only `fees_usd`, yet emits `n_protocol_days`.
   `scripts/fetch_defillama_fees.py:97–125` establishes that multiple protocol
   series are summed into each token panel. Opposing protocol revisions can
   cancel within a token, and token aggregation changes the denominator.
   Restore comparison from retained protocol-level raw identities before any
   actual P0 evaluation. The grid also contains revenue; the frozen text does
   not precisely resolve how the two metrics share the P0 denominator. That
   interpretation must be explicitly reviewed before outcomes, rather than
   silently preserving fees-only coverage or inventing a pooled gate.
2. **Labels do not establish elapsed observation time.** The P0 code checks
   the difference between supplied date labels. The fetcher accepts an arbitrary
   label and saves one `fetched_utc` timestamp at capture start, without
   per-response retrieval times. A new wrapper must enforce actual current
   retrieval eligibility and retain request start/end, response identity,
   hashes, failures and a bounded completion seal. September 18 is the earliest
   calendar date; the first manifest starts at 07:56:59 UTC on September 4.
   Per-member first-vintage retrieval times are not established by that start
   timestamp. Do not claim an exact per-member 14-day gap without a supported
   first-vintage completion bound; document this limitation or admit a
   conservative bound before capture.
3. **Admission is not bound to the snapshot pair.** `main_probes` accepts a
   mutable `p0_restatement.json` with a truthy `pass`, without validating its
   snapshot pair or hashes against `--snap1`; `main_grid` similarly trusts a
   mutable probes file. The minimal safe route binds each immutable stage
   result to source hashes, exact protocol/metric policy, preceding stage and
   registered identity, and refuses a mismatch or repeat. Preserve old files;
   do not execute the historical mains directly.
4. **Missing observations need an explicit source interpretation.** The
   fetcher sums columns containing missing protocol observations, and
   `build_inputs` fills missing daily fee/revenue entries with zero before the
   trailing sum. P0 also drops non-positive initial fee values. These operations
   can hide source absence or undefined percentage changes. An offline
   synthetic audit should distinguish observed zero from missing/failed data,
   retain the excluded denominator, and escalate any required interpretation
   before an empirical result. The charter's ordered P0→P1→P2 sequence and
   numerical thresholds must remain unchanged. The P1 `any(metric)` and P2
   median aggregation also require explicit consistency review; this review
   does not choose replacement gates.

## Preserved source location and metadata

The consolidated checkout does not currently contain the expected
`data/xsect/fees/2026-09-04`, `data/xsect/fees_raw/2026-09-04`,
`data/xsect/fundamentals`, or `data/rebuild/value_rev` paths. Exact corresponding
paths were checked in the three documented preserved sibling worktrees.
The first three sources exist, without a symlink at the checked path, under
`/home/malecada/master_thesis/TradingAgents/`; no `value_rev` result directory
exists at any of the four checked locations. This is a bounded path finding,
not proof of absence elsewhere or proof that no historical look occurred.

The first-vintage manifest is:

- Path: `/home/malecada/master_thesis/TradingAgents/data/xsect/fees/2026-09-04/manifest.json`.
- Bytes: 110724.
- SHA256: `89a9eb8ccbe073c1530047faa3bd64ca22085a79f933d782dcd2098a870d5151`.
- Snapshot label: `2026-09-04`; `fetched_utc`: `2026-09-04T07:56:59.543672+00:00`.
- 704 raw-file manifest entries, each declaring bytes and SHA256; 220 symbol mappings.

The manifest alone does not prove that each raw member still matches, that
normalized panels reproduce it, that acquisition completed at a particular time,
or that an externally recoverable copy exists. Those are next admission checks.
A declared read-only source-root mapping is needed in the consolidated checkout;
no silent refetch, copy over originals or execution in the preserved worktree.

## Minimal next work, without a new empirical grant

Prepare a bounded local value_rev source-admission implementation with ownership
assigned by the coordinator: validate the first-vintage manifest and members,
record a portable immutable inventory, resolve the timing/metric/zero-denominator
interpretations above with independent review, and test protocol-level revision
comparison and stage binding entirely on invented fixtures. Include cancelling
revisions within one token, missing revenue, zero baseline, forged date labels,
wrong snapshot pairs and missing raw members. Register any necessary source
protocol clarification before collecting the second vintage, retaining the
original charter and all prior trial counts.

The eventual second-vintage capture requires an exact finite source recipe,
resource bound, failures retained, actual retrieval eligibility and source
admission. It does not authorize P1/P2 or the financial grid until P0 passes.
A later P0 pass measures revision stability only; it does not prove historical
first-publication availability, economic ownership of protocol revenue or an
untouched holdout. Those inferences need separate admission before a financial
claim. No extra cell, replacement market-cap series, relaxed breadth gate or
new window is proposed.

## Validation and limits

Read-only checks used the checkout-local interpreter for manifest metadata and
hashing. No network, market request, legacy experiment main, empirical output,
new grant, historical mutation or source-code change occurred. This document is
the only assigned file written. No test suite was run for a documentation-only
review. The source-code defects above are structural observations; their effect
on actual P0 results has deliberately not been measured.
