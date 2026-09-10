# Current funding capture and safe paper admission

The current public-funding pipeline and its optional paper adapter are implemented on `fix/prospective-funding-capture-2026-09-10`, source commit `7d2a0ae9ef4ad707774360d2f67af40258a7d2e3`. The historical Binance support route remains ended at the user's instruction. Missing BZRX/LUNA/BNX terminal cashflows remain unavailable. **Two conditional measured failures and 22 unavailable accounting cases remain; zero validated strategies.** No financial replay, model fit, gate amendment, ledger append, account request, provider message, paper journal start or VPS change occurred.

## Scope and observed defects

The previous downloader had a fixed historical end date and replaced its output store. A separate public-only collector now creates immutable run directories containing raw responses, request receipts, normalized events and a final manifest. It uses a fixed exchange-time cutoff, nine UTC calendar dates, current instrument metadata and explicit bounded history requests. Associated marks and event types are retained. Exact duplicates are retained in raw evidence and deduplicated only when their values agree; conflicts, malformed data and unsupported types remain unavailable. Full-page boundary checks prevent a conflicting same-timestamp record from being skipped. Interrupted rate-limit bodies preserve known status and headers before collection stops.

The public pilot identified millisecond timestamp jitter that the exact-hour coverage comparison rejected. The committed [timestamp amendment](2026-09-10-timestamp-amendment.md), `7654889`, permits derived hourly comparison labels only for raw timestamps in `[hour, hour + 1 second]`. Rates, raw times, event marks and availability remain unchanged. Daily summation retains `[D 00:00, D+1 00:00)` membership and requires an actually captured following boundary. Off-grid times and multiple raw events mapping to one hour remain unavailable. The one-second bound is an engineering policy, not a provider guarantee.

Metadata inspection also identified five valid Chinese-symbol contracts omitted by the first collector's ASCII-only guard. The [identifier correction](2026-09-10-universe-amendment.md) is committed with the fix as `17c3649`. Exact Unicode provider identifiers are now preserved; separators, control characters and traversal are rejected. The first 523-name run is retained as restricted evidence. The declared market denominator includes two INDEX instruments and the COIN instruments; present eligibility does not reconstruct historical membership.

## Preserved public captures

The final full-universe snapshot is `data/operational_funding/2026-09-10/20260910T112655Z-856c79c5`, captured on collector source `17c3649`. Its fixed query window is **2026-09-02T00:00:00+00:00 through 2026-09-10T11:26:55.783000+00:00**; acquisition completed at 2026-09-10T11:36:07.072031+00:00. Raw metadata establishes 528 eligible current contracts: 526 COIN and two INDEX, with no omitted or out-of-criteria requested identities. All **528/528** history queries were captured, comprising **24,506 Regular funding events and 532 HTTP-200 requests**. Raw/normalized hashes, request logs, declared collector bytes and exact current-universe membership were verified by `verification/check_captures.py`.

| Retained capture | Requested / current eligible | Public requests | Events | Latest completed day admitted / requested |
|---|---:|---:|---:|---:|
| Three-symbol pilot | 3 / 528 | 7 | 78 | 3 / 3 |
| First, ASCII-restricted universe | 523 / 528 | 527 | 24,277 | 520 / 523 |
| Corrected current universe | 528 / 528 | 532 | 24,506 | 525 / 528 |

All three runs are retained: 1,066 capture requests, 2,126 files and 19,772,914 bytes. The earlier captures are not replaced or passed off as full-universe evidence. Their contents overlap; their event counts must not be summed as distinct market events.

Independent final data review verified all five Unicode raw/normalized identities and found no added/removed timestamps or rate/mark/type revisions across the 523 shared instruments and 24,277 overlapping events. Receipt availability differs between captures and is preserved separately. This observed agreement does not create an automatic cross-run revision policy. Review evidence is in `verification/final-data-review.json`.

For September 9, **525/528 contracts satisfy the qualified daily coverage rule**. `SKRUSDT`, `TUSDT` and `ZKCUSDT` retain unavailable coverage. Each has all six observed four-hour events and the following midnight event, but the prior seven-day minimum spacing is hourly, leaving 18 labels absent from that inferred grid. Current metadata reports four-hour intervals and is consistent with observed transitions; it does not prove historical effective schedules. The inference rule was not relaxed. Details are preserved in `verification/cadence-forensic.json`.

The final capture's admitted counts for September 2–9 are respectively **0, 525, 525, 525, 524, 525, 524, 525 out of 528**. September 2 has no preceding cadence observations inside this bounded capture. September 10 is the partial acquisition date and is not reported as a complete daily funding measurement. Maximum observed event offset is nine milliseconds; no raw timestamp is rounded or rewritten. Complete per-symbol/day denominators and reasons are in `verification/capture-checks.json`. These are data-coverage diagnostics, not strategy performance or proof of every economically due event.

## Paper admission

The snapshot reader validates raw and normalized hashes, query exhaustion, original contract identity/onboarding, acquisition time, metadata observations and declared source provenance. An explicitly configured missing or invalid snapshot never falls back to the legacy store. Captured query exhaustion is reported separately from qualified daily coverage; missing or quarantined symbols remain in the denominator.

With `--funding-snapshot` or `S1_FUNDING_SNAPSHOT`, both unchanged paper algorithms prepare their rows before either append. Missing relevant funding, held closing prices, required current quotes or valid prior state returns WAIT. A late snapshot can be retried the same day without permanently breaking the journal. Quote admission includes prior holdings that disappear from the new target. Initial flat state and genuine overlay warmup remain valid; existing broken or gapped chains are preserved. Journal provenance includes the immutable manifest hash, source/acquisition identity and all symbol denominators, with detailed coverage restricted to the settlement day to avoid repeating the entire history.

Paired admission is not a two-file filesystem transaction or a concurrency lock. Operator serialization is required. A crash between appends preserves the first row; a same-day retry must retain it and admit the remaining book. Daily funding remains an opening-notional approximation, not event-marked account cashflow reconciliation. Prior seven-day minimum-spacing inference can miss unknown faster events. Current schedule metadata is observed now and cannot prove historical schedules. These limitations are not removed by successful API retrieval.

## Verification and preservation

**584 integrated Python tests passed**, including 95 new collector/snapshot/admission cases and 489 existing accounting, paper, execution, monitoring, backup and recovery checks. Four preservation-verifier self-tests also passed. The five Python dependency warnings are unchanged. No frontend code changed; the previous 25-test frontend/build evidence remains preserved rather than rerun. Independent reviews reproduced and resolved interrupted-response, pagination, provenance, prior-held-quote, timestamp and identifier defects. The finite final reviews are recorded in `verification/reviews.md`.

The preservation verifier checks 3,805 prior local artifacts, 222 original external inputs, all six September 9 result files and 61 gate entries in five files. Historical operational source versions remain in their old commits/manifests; intentionally superseded source checks are explicitly excluded from the byte-preservation claim. The financial ledger remains 730 rows / 428,150 bytes, SHA-256 `710a4f087325bfb408ed8d051963a473e8d8a47b445ffae0238c565aff6dc791`. New public captures occupy a separate operational directory and do not overwrite original market stores.

## Prepared source and remaining operational boundary

The [local source archive](/home/malecada/master_thesis/funding-release-2026-09-10/ta-source-7d2a0ae9ef4ad707774360d2f67af40258a7d2e3.tar.gz) contains 288 allowlisted files, 1,125,182 compressed bytes, SHA-256 `3d3dbc688322abba70a0f0a208bf6bbaee0ca42cbb8791d01d9584a87606490c`. Every packaged source file was checked against the commit. Its strict `SOURCE_COMMIT` marker was verified from an extracted archive without Git; the collector also rejects unrelated enclosing repositories. The package contains source and the existing built frontend, with no research data or credentials. The prior monitor package remains intact. No upload, runtime upgrade or deployment occurred.

[Manual collection instructions](MANUAL_COLLECTION.md) specify explicit paths, a persistent lock, proposed hourly collection around `:20` UTC, shared-IP quota handling and immutable retries. No scheduler was installed. The next operational step is controlled staging with interpreter/dependency and actual scheduler inspection, followed by fresh input verification and an explicit paper measurement boundary. Collection alone does not establish production readiness or strategy validation.
