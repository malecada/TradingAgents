# Market data and contract lifecycle recovery — September 10, 2026

This cycle follows the market-data priority identified in the September 9 reevaluation. The original raw stores, gates and outcome artifacts are preserved. Recovery is registered under `audit_data_recovery_2026_09_10`; the separate `audit_lifecycle_exposure_2026_09_10` gate permits an original-book exposure diagnostic only. Neither gate permits strategy performance selection or a holdout.

## Coverage is broader than the first blocked observations

The timestamp-only inventory reads the original frozen liquidation-fade universe and eight original majors (217 distinct hourly files), plus all 799 files in the original daily manifest. All 217 hourly files and 442 daily files have observations within June 2020 through March 2025. No price or strategy statistic is calculated by the inventory.

| Inventory | Files with development observations | Files with internal holes | Internal missing periods |
|---|---:|---:|---:|
| Hourly liquidation-fade inputs | 217 | 49 | 6,832 symbol-hours |
| Daily original manifest | 442 | 0 | 0 days |

Leading and trailing unobserved periods are reported separately; they are not classified as missing trades without listing/termination evidence. An intact daily clock does not establish intact hourly prices or valid settlement accounting.

The three originally blocked files—TRXUSDT, FILUSDT and LTCUSDT—account for 360 missing hours. The same February 26–28 / April 1–2 pattern affects 47 symbols in total, with GMTUSDT missing only the April dates. BNXUSDT has additional 2022 gaps and a 518-hour February 2023 interval; ICPUSDT has a 626-hour September 2022 interval. All exact ranges and original hashes are frozen in `2026-09-10-scope-addendum.json`, committed before consumption of extra recovery ranges. The broader recovery scope is determined by timestamps, not strategy outcomes.

The demonstrated downloader defect is a coverage predicate that equates any row in a month with complete monthly coverage. The minute downloader shares the defect; alternate minute and aggregated-hour caches do not recover the original 360 hours. The repairs require a complete cadence, retry observed partial months despite stale archive-absence markers, and expose remaining incomplete coverage. An archive HTTP 404 is not proof that an instrument was unlisted.

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

## Evidence and boundaries

The new snapshots and receipts live under `data/recovery/2026-09-10/`. All original rows admitted to a derived development snapshot retain their exact values. Only verified target timestamps may be inserted; corrupt archives, checksum failures, conflicting overlap, missing corroboration and unresolved instrument identities remain explicit unavailable ranges. The original three-symbol batch and the broader timestamp-driven batch are reported independently.

The minute and hourly coverage repairs are local source changes. Original raw stores and the VPS are untouched. The older S2/S3, ENet and NLST4 corrections are not repeated. No new strategy is selected and no spent holdout is reopened. Recovery evidence supports a future reproducible measurement only when both prices and instrument accounting are established; it does not itself validate an edge.
