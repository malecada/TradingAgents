# Lifecycle readiness and original-allocation audit review — September 10, 2026

## Scope and present disposition

Recovery of hourly rows alone does not establish liquidation-fade replay readiness. Official notices identify five terminations inside the frozen monthly universe: LUNAUSDT in May 2022, TOMOUSDT in November 2023, RNDRUSDT in July 2024, MATICUSDT in September 2024 and BNXUSDT in March 2025. The original monthly universe SHA256 is `0b9e931f7eae01d6d5f85aa6ef48fc63b2fd7453b5a7990e460b8eb0874d4e96`. BZRXUSDT was absent in December 2021 and BNXUSDT absent in February 2023; this membership check is not an exposure calculation.

The event schedules and remaining settlement evidence are documented in [PRX identities](prx-identities.md) and [settlements](settlements.md). Nonmissing frozen bars, continuing public funding records and successor tokens do not establish executable old-contract prices or a final settlement cashflow. The PRX six-outcome problem is structural under the original 25-observation and fixed-beta rules; no successor splice can complete those measurements.

The registered exposure audit is an independent diagnostic of historical allocation assumptions, not a performance replay. Its single authorized original-input reconstruction completed on September 10 at 07:26:13–07:26:21 UTC under source commit `1375e8a6528ec9e3f07c51ac4415880c056e867b`. No PnL, SR, P0/P1/P2 statistic or revised strategy outcome was computed.

## Required lifecycle semantics

The existing accounting core checks returns for desired nonzero notionals. An explicit flat target assumes that the prior opening mark was already valid. Consequently, replacing post-closure returns with missing values would still allow an incoming position to disappear at an unverified opening mark. A lifecycle check must precede target application.

The committed exposure charter fixes the clock: an hourly close with open label `t−1h` becomes available at `t`; allocation `W[t]` is requested then and valued at `t+1h`. A bar's millisecond close label cannot establish that an order was executable before information availability.

- At an exact closure boundary `t`, incoming prior-row allocation remains unresolved even when `W[t]` is zero. No pre-event exit is invented at `t−1ms`.
- A nonzero allocation over an interval containing an intrahour closure requires the unestablished terminal event cashflow. LUNA's 15:30 closure lies inside the 15:00 bar.
- A subsequent nonzero request is recorded as a post-closure assumption. The original weights are retained, including natural later timer expiry; the audit does not synthetically flatten them.
- New targets and increases in target allocation on or after the announced entry restriction are counted, including those after closure. Pre-closure counts are supplied separately. Unchanged target weights do not establish unchanged contract quantities: NAV and price drift are not reconstructed in this audit.
- An allocation flattened at a genuinely earlier decision time is distinct from flattening at the event boundary. The absence of a lifecycle flag still does not prove fill quality, full coverage or settlement readiness.

Any future executable guard needs actual incoming position state, admissible opening/valuation marks and contract-event ordering. If an unreconciled position crosses a closure, it must remain unavailable even if a later target is flat. The present diagnostic supplies evidence about requested allocations only; it does not implement a settlement extension or prove actual holdings.

## Source and output controls

The recovery-only registration at `78b4fe9` and timestamp scope addendum at `6f84e4b` were reviewed independently. The committed gate, addendum SHA256 and inventory SHA256 agree. All 49 symbols and 6,832 declared internal symbol-hours match the timestamp inventory, and the September 9 gate is unchanged. The recovery registration authorizes no strategy metrics. The 250 MB download budget applies across documentary and market-data receipts, rather than separately to each downloader.

The separate exposure registration was committed at `c11527b`. Its implementation is [audit_lifecycle_exposure_2026_09_10.py](../../scripts/audit_lifecycle_exposure_2026_09_10.py), with [synthetic tests](../../tests/predlab/test_lifecycle_exposure_audit.py). It:

- defaults to a dry run that reads no original input and creates no output state;
- requires the committed exposure gate and clean executable sources before an exclusive start marker;
- verifies all 217 original hourly hashes before reading and again before publication, together with the frozen symbol list, universe, inventory and official event receipts;
- pins the original liquidation-fade result SHA256 `30a8629fa9214ac031d8a642f719bccdff60c6f1a0b473b365e699dd79f6837a` and reused construction source at `49fb9e47c4d9e40b9c3f1b7de475041ec63aac76`;
- reads only close and quote-volume inputs, with the development cutoff applied in the Parquet read; uses log differences only inside the unchanged cascade signal;
- retains the original six cells, five events per cell, sorting, membership mask, warmup, rolling feature settings, timer resets and slot cap;
- preserves missing-input behavior for reproduction while separately reporting original input coverage and allocation uncertainty;
- writes six nonfinancial records to the exclusive `forensic-ledger.jsonl` inside the exposure output namespace, with a hashed result; the central financial trial ledger is neither appended nor counted, and its before/after hash is checked.

No broad public-price or strategy run is invoked by this wrapper. Global reconstruction failure retains all six cells and all five event records as unavailable. Complete serialization precedes either forensic-output write. A low-level interrupted disk write still needs manual provenance review; an existing start/output namespace prevents blind re-execution.

## Verification and remaining limits

The initial 13 tests failed because the audit was absent. An additional restriction regression showed that post-closure new requests were omitted from the restriction count; this was corrected without changing original weights. Six further failing regressions required the dedicated forensic ledger, denominator retention, pre-serialization and repeat refusal. **27 focused tests pass in 1.09 seconds.** Red and green logs are preserved under [verification](verification/).

The tests cover exact-boundary incoming exposure, intrabar closure, pre-event flattening, post-closure requests, restriction reporting, nonfinite allocations, incomplete clocks, frozen event timing, original-input hash/path controls, registration refusals, dry-run behavior, filtered development reads and immutable forensic writing. No empirical result is claimed from them.

The audit is bounded to five registered events. Earlier same-ticker incarnations, other terminations, unknown funding/settlement cashflows, original internal gaps and price/NAV-driven order-quantity changes remain limitations. An absent flag is never a readiness certificate.

## Completed original-input exposure findings

All six cells retain all five events. Each table entry reports **incoming previous allocation / requested boundary-bar allocation; straddling bars / post-closure allocated bars**. These are requested fractions and hourly counts, not account positions or cashflows.

| Original cell | LUNA | TOMO | RNDR | MATIC | BNX |
|---|---|---|---|---|---|
| `thr2.5_H6` | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 |
| `thr2.5_H24` | 0.1 / 0.1; 1 / 12 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 |
| `thr2.5_H48` | 0.1 / 0.1; 1 / 36 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 |
| `thr3.5_H6` | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 |
| `thr3.5_H24` | 0.1 / 0.1; 1 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 |
| `thr3.5_H48` | 0.1 / 0.1; 1 / 24 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 | 0 / 0; 0 / 0 |

Four of the thirty checks identify original LUNA exposure through the May 12, 2022 15:30 termination. The last later allocated open labels are May 13 03:00 for `thr2.5_H24`, May 14 03:00 for `thr2.5_H48` and May 13 15:00 for `thr3.5_H48`. `thr3.5_H24` instead reaches a flat target at 16:00, after holding during the straddling bar. Its original September 9 measurement was marked complete; it now has a demonstrated unresolved lifecycle assumption. The other three flagged cells were already unavailable in that saved result. This diagnosis does not supply corrected financial values or change them by assumption.

All four contracts with separate entry restrictions have zero new/increased target requests in all six cells. Actual order-quantity changes remain unmeasured. All six LUNA lookbacks contain 120 missing close and 120 missing quote-volume observations. The local lookbacks for the other events contain no such missing observations, which does not certify the complete portfolio history or future recovered-input allocations.

Saved allocation rows independently reproduce the reported straddling/post-closure counts. All 229 input hashes, output hashes, six dedicated forensic ledger rows and thirty event records were verified after completion, without reconstructing allocations again. The central financial ledger's before/after/current hash is unchanged. The execution log is [exposure-run.log](verification/exposure-run.log).

| Artifact | SHA256 |
|---|---|
| [Exposure result](../../data/recovery/2026-09-10/exposure-audit/result.json) | `9657ac0113c024b682a08c6b6c2a7c2e7a4ec83481ad78cd5a94a4e1a10ddd46` |
| [Dedicated six-row forensic ledger](../../data/recovery/2026-09-10/exposure-audit/forensic-ledger.jsonl) | `cb9fff2c5d6e196030460582d54efe182dbd64ab43face38511b6ef32e40415b` |
| Unchanged central financial trial ledger | `0b9ab125e64e9c808ccd398d703092e344b6f8772de9e6ec6e223a1e2b9f9a09` |

## Conditional six-cell replay design and implementation — not executed

A separately registered replay can determine whether verified recovery permits a measurement. It cannot promise that any cell becomes complete. The recovery manifest must pin all 47 admitted development overlays and preserve the other original inputs, universe, six-cell order, costs, clocks and original thresholds. Unresolved BNX/ICP intervals remain missing; no contract rename, retrospective universe exclusion or changed trigger is admitted.

The minimal lifecycle extension checks each full requested schedule before the existing hourly accounting call. It detects straddling exposure, incoming exposure at an exact event boundary even when the next target is zero, and every later request. For the four 08:30 restrictions followed by 09:00 closure there is no intervening hourly decision, so closure checks also cover every restricted decision. Different timings would require an explicitly registered quantity-aware extension or an unavailable status. The guard must inspect newly constructed schedules; the four original conflicting cell IDs are not hard-coded as exclusions.

P2 needs its own hypothetical-window check: each selected event retains its denominator, but a holding/exit window touching termination or an entry after the known restriction is unavailable. Endpoint censoring remains separate. The existing any-cell P2 rule may pass when at least one fully scoreable cell exceeds 25 bp; if none does and any cell is unavailable, all six stop unavailable. Missing windows cannot be dropped to obtain a conditional passing mean.

The same schedule guard must precede primary, zero-fee, double-fee and invalid-log diagnostic books and every materialized placebo book. Invalid placebo draws remain in the fixed draw denominator and make the affected 500-draw family unavailable; no redraw, date masking or survivor-only p-value is allowed. The original shared RNG and skipped-draw advancement remain unchanged. A complete primary book can coexist with incomplete remaining gates; neither is promoted to validation. Funding remains excluded only as the original registered qualification, not as a claim of all-in executable profitability.

These optional hooks are implemented in the accounting wrapper and the new pure [lifecycle helper](../../tradingagents/xsect/lifecycle.py). The recovered replay registration at `4df421b` preserves all six cells, pins all 47 overlays and declares original/current DSR denominators of 100/156. No cell is excluded by its earlier outcome.

P2's cumulative return is an entry-to-exit fixed-quantity price diagnostic. An intermediate entry restriction does not create an intermediate maintenance order. Its guard therefore checks the initial entry restriction and terminal event through final valuation availability. The actual hourly target-weight books separately reject an unresolved nonzero decision during a restriction period. This distinction is tested explicitly.

The 19 initial guard regressions failed before implementation. The final focused suite passes **44 tests in 1.13 seconds**, including 23 existing accounting-wrapper tests. A prepared-placebo integration regression confirms lifecycle rejection on the first invalid synthetic placement and unchanged advancement through the remaining shift/random draws. P2 tests verify disjoint censoring/missing/lifecycle counts and prohibit a passing gate value calculated from only the available subset. Logs are [replay-lifecycle-red.log](verification/replay-lifecycle-red.log) and [replay-lifecycle-green.log](verification/replay-lifecycle-green.log). No financial replay has been run at this documentation stage.
