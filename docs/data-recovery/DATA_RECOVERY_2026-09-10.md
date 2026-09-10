# Market data and contract lifecycle recovery — September 10, 2026

This cycle completes the market-data priority identified in the September 9 reevaluation. **5,568 missing hours were recovered across 47 symbols; the subsequent fixed six-cell replay produced two conditional measured failures and four unavailable books. No lead was revived.** The original raw stores, gates and outcome artifacts are preserved. Recovery, the original-book exposure diagnostic and the conditional financial replay were separately registered and committed under `audit_data_recovery_2026_09_10`, `audit_lifecycle_exposure_2026_09_10` and `audit_recovered_liq_2026_09_10`. No strategy selection or holdout evaluation was performed.

## Coverage is broader than the first blocked observations

The timestamp-only inventory reads the original frozen liquidation-fade universe and eight original majors (217 distinct hourly files), plus all 799 files in the original daily manifest. All 217 hourly files and 442 daily files have observations within June 2020 through March 2025. No price or strategy statistic is calculated by the inventory.

| Inventory | Files with development observations | Files with internal holes | Internal missing periods |
|---|---:|---:|---:|
| Hourly liquidation-fade inputs | 217 | 49 | 6,832 symbol-hours |
| Daily original manifest | 442 | 0 | 0 days |

Leading and trailing unobserved periods are reported separately; they are not classified as missing trades without listing/termination evidence. An intact daily clock does not establish intact hourly prices or valid settlement accounting.

The three originally blocked files—TRXUSDT, FILUSDT and LTCUSDT—account for 360 missing hours. The same February 26–28 / April 1–2 pattern affects 47 symbols in total, with GMTUSDT missing only the April dates. BNXUSDT has additional 2022 gaps and a 518-hour February 2023 interval; ICPUSDT has a 626-hour September 2022 interval. All exact ranges and original hashes are frozen in `2026-09-10-scope-addendum.json`, committed before consumption of extra recovery ranges. The broader recovery scope is determined by timestamps, not strategy outcomes.

The demonstrated downloader defect is a coverage predicate that equates any row in a month with complete monthly coverage. The minute downloader shares the defect; alternate minute and aggregated-hour caches do not recover the original 360 hours. The repairs require a complete cadence, retry observed partial months despite stale archive-absence markers, and expose remaining incomplete coverage. An archive HTTP 404 is not proof that an instrument was unlisted.

Recovery completed under source `1375e8a`. **All 5,568 ordinary missing hours across 47 symbols are recovered**, including the original 360 hours. Every admitted hour is absent from the current checksum-valid monthly archive; complete daily archives and public API observations agree exactly, while their observed overlaps agree with the original files and monthly archives. The provider's incomplete monthly files and the local coverage shortcut jointly explain the missing data. Retrying the monthly archive alone cannot restore it; the dedicated immutable recovery writer uses the verified daily/API path.

| Recovery outcome | Symbols | Symbol-hours |
|---|---:|---:|
| Original TRX/FIL/LTC batch, verified | 3 | 360 |
| Additional ordinary gaps, verified | 44 | 5,208 |
| BNX identity quarantine | 1 | 638 |
| ICP identity quarantine | 1 | 626 |
| Full inventory denominator | 49 | 6,832 |

Independent artifact checks verified 49 original hashes, 94 Parquet outputs and 2,230 raw bodies/receipts. The 47 recovered snapshots have no internal hourly holes; every original row in their registered warmup/development window is unchanged. All 558 overlap comparisons pass, covering 81,700 compared rows including repeated controls; 1,115 planned requests downloaded 4,521,057 body bytes, with no request, checksum or overlap error. Documentary receipts are additional and remain within the aggregate 250MB bound. Detailed evidence: [hourly-recovery.md](hourly-recovery.md) and [artifact checks](verification/hourly-artifact-checks.json).

## Contract evidence

Official announcements establish scheduled forced closures for BZRXUSDT (December 19, 2021 at 02:00 UTC), LUNAUSDT (May 12, 2022 at 15:30 UTC) and BNXUSDT (March 17, 2025 at 09:00 UTC). Exact final settlement cashflows remain unestablished. Final trade bars, minute mark/index candles, continued funding records and spot conversion ratios do not supply them. The individual source receipts and distinctions are retained in [settlements.md](settlements.md).

The historical delisting FAQ copies from December 2021 and May 2022 describe a one-hour average using second-level index observations. The current February 2026 text describes 30 minutes. A current formula therefore cannot be projected backward as if it were an unchanged historical rule. Even the older snapshots do not conclusively establish every event's applicability, fee treatment or actual terminal price. [Archived official FAQ](https://web.archive.org/web/20220525030936id_/https://www.binance.com/en/support/faq/dd60dfbf654d4055aa6b217ea6d5ddba), [current official FAQ](https://www.binance.com/en/support/faq/detail/dd60dfbf654d4055aa6b217ea6d5ddba).

BNX also has a distinct February 2023 contract break. The old perpetual was scheduled to settle on February 11 at 04:00 UTC; a new BNXUSDT perpetual launched on February 22 at 14:45. Binance renamed the old futures history to `BNXUSDTSETTLED`. The 1:100 token conversion is not a transfer of futures positions. The large hourly gap includes a genuinely closed interval and cannot be filled as one continuing contract. The preserved daily file begins with the newer contract; this finding does not assert that the daily file splices both incarnations. [Old-contract closure](https://www.binance.com/en/support/announcement/detail/4d23ada51a2e4fa182835c77d51ba1a9), [new-contract launch and old-history identifier](https://www.binance.com/en/support/announcement/detail/940d0e48493e4627889c3f46371df70b).

The ICP gap also spans a contract break. The old ICPUSDT perpetual was scheduled to settle on June 10, 2022 at 09:00 UTC. A new ICPUSDT perpetual launched on September 27 at 02:30; the old identity became `ICPUSDT_SETTLED` in transaction histories. The September 1–27 gap is therefore quarantined rather than filled as a continuing contract. Two official CMS receipts are archived in `icp-identity/`. ICP and TLM are absent from the frozen June 2022 liquidation-fade universe, so this documentary finding does not add an event to the five-event original-book exposure audit. [Original closure](https://www.binance.com/en/support/announcement/detail/af469aeeab074738bb4a276070a9d11b), [new contract and old identity](https://www.binance.com/en/support/announcement/detail/adabdfbc53344094808a7bea464f101b).

## Pair-selection gaps are structural

The original TOMOUSDT, RNDRUSDT and MATICUSDT perpetuals terminate before the frozen persistence outcomes can contain the required 25 daily observations. VICUSDT, RENDERUSDT and POLUSDT are separately launched contracts. Their prices cannot complete the old fixed-beta outcomes by renaming columns. Even a verified terminal cash settlement would not create post-termination prices for the old ADF test. The six outcomes remain unavailable and all 50 months remain in the denominator; no PRX statistic was rerun. Official times, identity distinctions and request receipts are in [prx-identities.md](prx-identities.md).

## Lifecycle checks precede any financial replay

Five of the documented terminations occur while the old contract belongs to the original liquidation-fade monthly universe: LUNA in May 2022, TOMO in November 2023, RNDR in July 2024, MATIC in September 2024 and BNX in March 2025. Universe membership does not establish actual holdings. The separately registered exposure diagnostic reconstructs all six original target schedules solely to locate crossing/after-closure allocations. It produces no PnL, SR, DSR or probe statistics.

A missing-return check alone is insufficient: applying a flat target can remove the outgoing exposure while implicitly selling at an opening mark after an unbooked settlement. The execution clock and incoming position must be checked before applying the new target. An hourly close's millisecond label cannot prove that an order using that close was executable before the close became available. No terminal fill or forced flattening is fabricated by this cycle.

The original-input exposure audit completed once under source `1375e8a`, retaining six cells × five events. Four original schedules carry a 10% LUNA target during the 15:00–16:00 UTC bar containing the May 12, 2022 15:30 closure:

| Original cell | Allocation in closure-containing hour | Later nonzero hourly targets | Original-book interpretation |
|---|---:|---:|---|
| threshold 2.5 / 6h | 0% | 0 | No conflict observed in the five-event inspection; still qualified |
| threshold 2.5 / 24h | 10% | 12 | Unverified terminal valuation |
| threshold 2.5 / 48h | 10% | 36 | Unverified terminal valuation |
| threshold 3.5 / 6h | 0% | 0 | No conflict observed in the five-event inspection; still qualified |
| threshold 3.5 / 24h | 10% | 0 | Unverified terminal valuation inside the last held hour |
| threshold 3.5 / 48h | 10% | 24 | Unverified terminal valuation |

The other four registered contracts show no observed conflict in any cell. These are target schedules, not account fills or actual position quantities. Their original local LUNA lookbacks still contained 120 missing hours; the absence of a flag cannot certify the recovered schedules. The four conflicts nevertheless identify unbooked terminal assumptions in the actual original reconstruction.

**The September 9 threshold 3.5 / 24h “complete FAIL” is additionally withdrawn as an executable full-window measurement.** Its SR 0.981334 remains a preserved calculation under incomplete lifecycle accounting, not an established corrected negative result. The other three conflicted cells were already unavailable because of earlier internal gaps. No profit or corrected settlement return is inferred. The dedicated six-record forensic ledger leaves the central financial-trial ledger unchanged at the time of this exposure audit. [Independent review and hashes](verification/accounting-readiness-review.md).

## Completed conditional financial replay

The separately preregistered replay ran once from reviewed source `a87b67b97cd88ed3bbe83e2dd03eca99a5082d33`, from 07:40:04 to 07:41:15 UTC on September 10. All six original threshold/holding-period combinations were retained. Signals and holdings were reconstructed using the 47 verified snapshot replacements; the four exposure conflicts were not hardcoded exclusions. The lifecycle guard was applied before every primary, cost and convention diagnostic book.

| Threshold / holding period | Net SR | Maximum drawdown | Original DSR (n=100) | Current DSR (n=156) | Outcome |
|---|---:|---:|---:|---:|---|
| 2.5 / 6h | 0.159713 | 71.21% | 0.013861 | 0.009289 | FAIL |
| 2.5 / 24h | unavailable | unavailable | unavailable | unavailable | Unverified LUNA terminal exposure |
| 2.5 / 48h | unavailable | unavailable | unavailable | unavailable | Unverified LUNA terminal exposure |
| 3.5 / 6h | 0.815672 | 16.59% | 0.306207 | 0.254849 | FAIL |
| 3.5 / 24h | unavailable | unavailable | unavailable | unavailable | Unverified LUNA terminal exposure |
| 3.5 / 48h | unavailable | unavailable | unavailable | unavailable | Unverified LUNA terminal exposure |

Both measured cells retain all 1,551 daily observations from January 1, 2021 through March 31, 2025 and fail both original primary requirements, SR≥1 and DSR≥0.9. The original 10bp cost and funding exclusion remain fixed. Compared directly with the September 9 corrected H6 measurements, the SRs change only from 0.165715 to 0.159713 and from 0.815429 to 0.815672. These are conditional measurements under the registered five-event lifecycle scope; they do not certify every historical contract, complete funding economics or live fills.

The four unavailable books stop at the 15:00 UTC interval containing LUNA's 15:30 closure on May 12, 2022. Their primary, zero-fee, double-fee and invalid-log variants all remain unavailable, with no full-window financial statistic or gate pass inferred. The recovered bars remove the earlier internal-gap blockers but expose the later terminal-accounting problem.

The family passes the unchanged P0/P1/P2 preliminary conjunction. P0 reproduces BTC daily returns with correlation effectively 1 on 1,550 paired days. P1 retains all five benchmark days, with no unavailable data among 960 symbol-hours. P2 passes because both H6 cells are fully scoreable and exceed the original 25bp event-return floor; no incomplete cell passes from its observed subset.

| P2 threshold / horizon | All triggered windows | Scoreable | Lifecycle unavailable | Missing-return overlap within lifecycle count | Gate value |
|---|---:|---:|---:|---:|---:|
| 2.5 / 6h | 5,069 | 5,069 | 0 | 0 | 64.8364bp |
| 2.5 / 24h | 5,069 | 5,065 | 4 | 0 | unavailable |
| 2.5 / 48h | 5,069 | 5,050 | 19 | 9 | unavailable |
| 3.5 / 6h | 709 | 709 | 0 | 0 | 107.8974bp |
| 3.5 / 24h | 709 | 708 | 1 | 0 | unavailable |
| 3.5 / 48h | 709 | 698 | 11 | 6 | unavailable |

No window is endpoint-censored, and the disjoint ordinary-missing count is zero. The overlap column is already contained in the lifecycle count and must not be added again. P2 is a fixed-quantity horizon diagnostic; passing it does not establish a profitable portfolio after costs and slot competition.

Zero-fee SRs are 0.612935 and 1.017149 for the two H6 cells, but their original-denominator DSRs remain only 0.103181 and 0.546471, below 0.9. Double-fee SRs are −0.295272 and 0.609170. The invalid log-PnL convention is explicitly rejected for threshold 2.5 / 6h during the May 12 crash; for threshold 3.5 / 6h it produces SR −0.129306 and remains ineligible. Expensive placebo performance tests are skipped after primary failure or unavailable accounting; the registered source advances their RNG streams without replacement draws. No new placebo p-values are reported.

**The current interpretation of the 24 fixed accounting cases is two conditional measured failures and 22 unavailable cases:** 12 momentum, six carry and four liquidation-fade books. This supersedes the September 9 count of three measured failures and 21 unavailable cases. PRX remains a conditional failure with six structurally unavailable outcomes; NLST4's qualified ranking pass and economic failure remain unchanged. Zero validated strategies remain.

## Verification and retained evidence

The integrated offline regression suite passed **173 tests** before financial execution. Independent reviews reconciled all 272 recorded replay inputs, three ancillary outputs, all six cell identities and all seven saved return streams, including Sharpe, drawdown from initial NAV, total return, mean return and DSR under both denominators. The 411,461-byte central-ledger prefix is unchanged and exactly six unique financial rows were appended. The earlier exposure audit retains its separate six-row forensic ledger. All original registrations and September 9 result hashes remain unchanged. [Financial review](verification/recovered-replay-review.md), [lifecycle review](lifecycle-readiness-review.md), [test command](verification/integrated-tests.md), [final artifact manifest](verification/final-manifest.json).

| Immutable evidence | SHA-256 |
|---|---|
| Original three-symbol recovery result | `77174de1dd4afff71b45018b306e50b2295ee84b51563eb51db43fb7898139f2` |
| Extended recovery result | `48673ab5b47836153b7e85809e5766ccc9891773aaf62cce28bc3fc84ab13217` |
| Original-book exposure result | `9657ac0113c024b682a08c6b6c2a7c2e7a4ec83481ad78cd5a94a4e1a10ddd46` |
| Conditional financial replay result | `2a210cb47723857e2b6b8e318f174e3becd010a91bbcf9405b47fec26d7ebd66` |
| Financial replay gate | `987ecb256dcd430f7c5fce0d101cf1f5f020d1c671e8465eddcf86ce9bc9ddbf` |
| Pre-run correction policy | `6bae0081d6d114686d3ac807bb7172dbbbc63f13ac1bb07b0917bf20533cd312` |

The financial result is `data/predlab/audit_recovered_liq_2026_09_10/liq_fade/result.json`. Completion and qualifications are appended to the corrections register after execution; frozen gate criteria remain unchanged. Repeating a completed empirical cycle requires a new committed registration.

The [Git retention check](verification/git-retention.json) confirms that all 2,373 recovery files and four financial artifacts match their staged Git blobs exactly: 102,553,277 bytes in total. Only the zero-byte operational lock is excluded. The inventory includes all 47 complete recovered snapshots, insertion files, public-source receipts, documentary bodies and saved results; hashes alone are not the only retained recovery evidence. The original market stores remain outside this addition.

## Remaining evidence requirements and boundaries

The new snapshots and receipts live under `data/recovery/2026-09-10/`. All original rows admitted to a derived development snapshot retain their exact values. Only verified target timestamps may be inserted; corrupt archives, checksum failures, conflicting overlap, missing corroboration and unresolved instrument identities remain explicit unavailable ranges. The original three-symbol batch and the broader timestamp-driven batch are reported independently.

The remaining blocker is historical terminal accounting: exact settlement cashflows, applicable fees and final funding treatment for BZRX, LUNA and BNX, together with explicit contract lifetimes. The public evidence recovered here establishes scheduled closure times and identity breaks but does not establish those cashflows. Another portfolio replay is justified only after that evidence is available; substituting a last close or successor ticker would recreate an invalid measurement. PRX's original post-termination persistence outcomes cannot be repaired by settlement evidence because the old instruments cease to exist.

The minute and hourly coverage repairs are local source changes. Original raw stores and the VPS are untouched. The older S2/S3, ENet and NLST4 corrections are not repeated. No new strategy is selected and no spent holdout is reopened. The manuscript is unchanged. The correction branch retains the complete new recovery receipts and derived snapshots, exposure artifacts and financial outputs; original market stores remain in their preserved worktrees.
