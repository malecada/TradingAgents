# Historical perpetual settlement evidence — September 10, 2026

This follow-up investigates the terminal-accounting requirements left by the completed data-recovery replay. It is separately registered as `audit_settlement_evidence_2026_09_10`, committed at `506373e` before the new archived evidence was acquired. Initial public-source discovery is not a strategy calculation. Original source, market stores, research results and financial trial records are preserved. No strategy calculation is authorized by this documentary gate.

**The bounded public-source search recovered materially better historical rules, but no exact terminal price was admitted for any of the three contracts. No portfolio replay was performed.** The remaining requirement is an actual settlement record, or an applicable rule plus sufficiently complete observations to reproduce its result. No last-close estimate or conditional candle range is substituted for that record.

## Why these three events matter

| Original contract | Scheduled settlement, UTC | Existing affected measurements |
|---|---|---|
| LUNAUSDT | May 12, 2022 at 15:30 | All six carry cases first fail at the subsequent missing daily mark; four liquidation-fade cases are explicitly guarded at the closure-containing hour |
| BZRXUSDT | December 19, 2021 at 02:00 | Nine momentum cases first fail at the subsequent missing daily mark |
| BNXUSDT, February 2023 incarnation | March 17, 2025 at 09:00 | Three momentum cases first fail at the subsequent missing daily mark |

These are observed first blockers in the preserved artifacts, not a claim that each strategy encounters only one terminated instrument. Recovering one event can reveal a later unavailable input. The closure time is already supported by official notices; the actual terminal cashflow and its historical fee/funding treatment are the remaining questions.

## New historical evidence

| Question | Evidence recovered | What remains unresolved |
|---|---|---|
| BZRX's default settlement procedure | A May 2021 official FAQ archive describes the one-hour / 3,600-index-observation procedure; a December 20, 2021 announcement capture has the same article body as the preserved current notice, including the closure and protective-measure provisions | Actual price, event execution, rounding and any applied exception |
| LUNA's historical procedure and funding basis | Pre-event API and funding documentation establishes the available interfaces and mark-price × quantity × funding-rate calculation; positions closed before funding do not owe that payment | Actual terminal price, funding-event valuation and any special event treatment |
| BNX's default settlement averaging period | A November 4, 2024 announcement explicitly makes the 30-minute / 1,800-index-observation rule effective November 11, 2024 at 08:00 UTC, including delistings | Actual result of that rule at the March 2025 event, rounding and event-specific treatment |
| Ordinary historical fees | October 2021 documentation gives regular-user USD-M maker/taker examples of 0.02% / 0.04%; December 2024 documentation gives 0.02% / 0.05% | Automatic perpetual-delisting classification and applicable event fee; the historical 0.015% quarterly-delivery fee is not a substitute |
| Final funding | Archived rules establish quantity/mark valuation and payment only while a position exists; historical documents also disclose funding timing tolerances | The relevant actual valuation and sequencing, especially where old funding-history rows lack a mark price |

The BNX rule-change announcement is a specific improvement over the earlier report, which correctly declined to backdate the current 2026 FAQ but had not located the change's effective date. The November 2024 notice supplies direct historical default-rule evidence. Current CMS retrieval remains distinguished from an immutable historical capture, and a default rule is distinct from an observed final cashflow. [Official change announcement](https://www.binance.com/en/support/announcement/detail/4bcabddf0e81423ebca242e185bf157d).

Per-instrument evidence matrices, dated sources and receipt hashes are retained in [BZRX](bzrx.md), [LUNA](luna.md) and [BNX](bnx.md). The archived BZRX mark-price documentation describes emergency index and mark protections, but no activation record for its event was recovered. For BNX, the newly documented settlement rule is an index average; a mark-price protection provision alone does not prove that the settlement average was overridden. The absence of a recovered exception is not treated as proof of an exception either.

## What the price and API routes establish

The documented public archive route supplies index candles at one-minute resolution. The LUNA and BNX event-day ZIPs pass their provider checksums, and all requested pre-closure API rows match the archive fields exactly. These are genuine observations, but minute OHLC is not the full second-level series used by the settlement rule. The variable basic-data counts in those rows do not establish which seconds were sampled or how unchanged/missing observations were treated. Conditional candle-envelope calculations in the instrument reports remain data diagnostics; none is admitted as an exact settlement or unconditional bound on it.

The pre-event API documentation identifies `estimatedSettlePrice` as a current estimate with no historical-time argument. The former public forced-order history route had already been retired before these events. Neither route supplies the missing old automatic-settlement cashflow. The historical account income schema does distinguish settlement income, funding, commissions and realized PnL, but it requires authenticated account records. [Archived official API documentation](https://web.archive.org/web/20220502133908id_/https://binance-docs.github.io/apidocs/futures/en/).

Ordinary income history and asynchronous transaction export must be distinguished. The former's documented three-month history does not establish the latter's historical retention. The current export documentation limits a requested interval to one year and limits request frequency, but does not state an oldest retrievable date. Export availability for these events therefore remains unresolved; the public-source search does not prove that Binance or an existing account export cannot supply the records. No authenticated endpoint or account export was requested in this task.

## Evidence admission and implementation implications

The original target quantity must be valued at termination, settled once, removed from the book and prevented from reopening under the old contract. A last trade, an estimated settlement field, a current `SETTLING` status or an unrelated successor cannot perform that function. The applicable historical rule, sampling/rounding and any emergency protection override must be established before reconstructing a price.

The local carry wrapper aggregates a day's funding rates and the accounting engine applies that aggregate to opening notional. Exact intraday terminal accounting would require individual funding events and the applicable valuation of the quantity still held at each event. A continuing public funding series does not justify charging the contract after closure. Momentum and liquidation-fade omit funding under their original contracts; an evidence repair cannot silently reclassify those measurements as all-in net economics. The complete field and implementation requirements are in [accounting-admission.md](accounting-admission.md).

Minute OHLC data may sometimes bound an arithmetic mean of genuine underlying observations, but cannot generally identify it. Such a bound depends on the historically applicable rule, complete observation coverage and absence of a conflicting protection override. Substituting a midpoint is not recovery. A financial sensitivity analysis would need a separate committed registration; a favorable cashflow endpoint is not automatically an upper bound on Sharpe when later position sizing depends on NAV.

## Research status

The completed [machine-readable assessment](../../data/settlement-evidence/2026-09-10/result.json) retains all three investigations with unknown terminal prices and no exact-replay readiness. The [final verification manifest](verification/final-manifest.json) records **52 direct requests and 2,885,220 response-body bytes**: 46 HTTP-200 responses, two empty HTTP-202 responses and four timeouts. Failed retrievals remain in the denominator; supplementary web-rendered documentation is labeled separately from raw HTTP evidence.

Parent verification independently checked every saved response hash, the two provider ZIP checksums, both complete 1,440-minute event-day clocks and all 91 requested API/archive row comparisons across twelve fields. The checks also preserve all 2,377 prior recovery/replay artifacts, 222 distinct original input files, six accounting/source files and the earlier gate objects. The 428,150-byte financial ledger is unchanged, with zero new rows. No financial tests were rerun because the accounting implementation did not change. The offline [verification script](verification/verify_saved_evidence.py) and case derivation scripts are retained with the evidence.

Until admissible new measurements establish otherwise, the existing accounting interpretation remains **two conditional measured failures and 22 unavailable cases**. PRX's six post-termination persistence outcomes remain structurally unavailable; the qualified NLST4 ranking pass and economic failure remain unchanged. No holdout, model refit, parameter selection, live deployment or manuscript change is part of this evidence task.

An [unsent provider request](provider-request-draft.md) identifies the precise historical fields required. No request has been sent to Binance or anyone else, and no account access has been attempted.
