# Accounting reevaluation artifact review — 2026-09-09

The frozen 24-cell accounting slate produced **3 measured failures and 21 unavailable cells**. No corrected gate passed. The unavailable cells do not establish negative strategy results or confirm their historical rejection. All three measurable liquidation-fade cells fail the original Sharpe and original-denominator DSR requirements. Funding remains excluded from liquidation-fade under its original specification, so these are not executable all-in net returns.

This review used saved results and return archives, byte hashes, source inspection, narrowly filtered development-period market rows, and metadata for possible alternative caches. No portfolio was rerun, no missing price was filled, no alternative cache was substituted, and no market API was invoked. Source, gates, policy, original stores and result artifacts were left unchanged. This Markdown report is the only review output.

## Artifact and denominator verification

All results identify source commit `49fb9e47c4d9e40b9c3f1b7de475041ec63aac76`, gate SHA256 `b74efa4273a38339cab652cb140b0aa64df1778a1f7f8bcb015e49c3f357e894`, and correction-policy SHA256 `fba631d9bb458decc4b278c1b224a2441d97b75d7a328dffa0850c9799619a4d`. They report no refit, selection, holdout read or holdout evaluation. Their embedded family gates, ordered cell IDs and configurations exactly match the committed registration.

| Family | Registered | Complete | Failed original conjunction | Unavailable | Original / current DSR denominator | Recorded input hashes independently matched |
|---|---:|---:|---:|---:|---:|---:|
| Momentum | 12 | 0 | 0 | 12 | 74 / 150 | 801 / 801 |
| Carry | 6 | 0 | 0 | 6 | 87 / 150 | 1,043 / 1,043 |
| Liquidation-fade | 6 | 3 | 3 | 3 | 100 / 150 | 221 / 221 |

The common current denominator is the registered policy count of 126 prior distinct strategy identities plus 24 accounting configurations. It is not an empirical estimate of independent tests. Exactly 24 corresponding trial-ledger rows exist, with 24 distinct cell names and trial IDs. Every ledger configuration and metrics object matches its saved result.

Every recorded output checksum matched, including the three liquidation-fade return Parquet files. Momentum and carry contain only their start marker and result JSON, appropriately without complete return archives. Result JSON hashes:

| Result under `data/predlab/audit_reevaluation_2026_09_09/` | SHA256 |
|---|---|
| `momentum/result.json` | `cd8edbcbc36638b87dfab722526ff715590e78016b5be7ca8d091a11a63b7b7b` |
| `carry/result.json` | `b2def83b0c8b13b418963b0d1df6008d178c12f114d6efb37d05400eaa1512ab` |
| `liq_fade/result.json` | `30a8629fa9214ac031d8a642f719bccdff60c6f1a0b473b365e699dd79f6837a` |

The three archived primary series have exactly 1,551 finite, unique daily observations on the full UTC clock from 2021-01-01 through 2025-03-31. Independent arithmetic on those saved returns reproduced their annualized Sharpe, compounded total return and maximum drawdown including initial equity with zero numeric discrepancy. This checked artifact arithmetic, not a fresh strategy run.

## All frozen cells

Dates and times below are UTC. A missing held return identifies the first fatal observation, not an exhaustive inventory of every gap that could be encountered later. `original_gate_pass` is null for every unavailable cell. The aggregate `n_original_gate_pass=0` must not be rewritten as 24 measured failures.

| Family | Cell | Corrected disposition | First unavailable held mark / measured SR |
|---|---|---|---|
| Momentum | L7_skip0_K10 | Unavailable | BZRXUSDT, 2021-12-20 00:00 |
| Momentum | L7_skip0_K20 | Unavailable | BZRXUSDT, 2021-12-20 00:00 |
| Momentum | L7_skip1_K10 | Unavailable | BZRXUSDT, 2021-12-20 00:00 |
| Momentum | L7_skip1_K20 | Unavailable | BZRXUSDT, 2021-12-20 00:00 |
| Momentum | L14_skip0_K10 | Unavailable | BZRXUSDT, 2021-12-20 00:00 |
| Momentum | L14_skip0_K20 | Unavailable | BZRXUSDT, 2021-12-20 00:00 |
| Momentum | L14_skip1_K10 | Unavailable | BZRXUSDT, 2021-12-20 00:00 |
| Momentum | L14_skip1_K20 | Unavailable | BZRXUSDT, 2021-12-20 00:00 |
| Momentum | L28_skip0_K10 | Unavailable | BNXUSDT, 2025-03-18 00:00 |
| Momentum | L28_skip0_K20 | Unavailable | BNXUSDT, 2025-03-18 00:00 |
| Momentum | L28_skip1_K10 | Unavailable | BNXUSDT, 2025-03-18 00:00 |
| Momentum | L28_skip1_K20 | Unavailable | BZRXUSDT, 2021-12-20 00:00 |
| Carry | L1_leg0.1 | Unavailable | LUNAUSDT, 2022-05-13 00:00 |
| Carry | L1_leg0.2 | Unavailable | LUNAUSDT, 2022-05-13 00:00 |
| Carry | L7_leg0.1 | Unavailable | LUNAUSDT, 2022-05-13 00:00 |
| Carry | L7_leg0.2 | Unavailable | LUNAUSDT, 2022-05-13 00:00 |
| Carry | L30_leg0.1 | Unavailable | LUNAUSDT, 2022-05-13 00:00 |
| Carry | L30_leg0.2 | Unavailable | LUNAUSDT, 2022-05-13 00:00 |
| Liquidation-fade | thr2.5_H6 | Measured FAIL | SR 0.165715 |
| Liquidation-fade | thr2.5_H24 | Unavailable | TRXUSDT, 2022-02-26 00:00 |
| Liquidation-fade | thr2.5_H48 | Unavailable | FILUSDT and LTCUSDT, 2022-02-26 00:00 |
| Liquidation-fade | thr3.5_H6 | Measured FAIL | SR 0.815429 |
| Liquidation-fade | thr3.5_H24 | Measured FAIL | SR 0.981334 |
| Liquidation-fade | thr3.5_H48 | Unavailable | FILUSDT, 2022-04-01 00:00 |

## Momentum and carry: contract lifecycle data are required

The daily source manifests already end on the dates immediately before the reported missing returns. Their current byte hashes match the files used by the frozen run. Inspection of `scripts/fetch_xsect_klines.py` establishes a Binance USDT-M perpetual source, using FAPI daily klines with a Vision futures monthly fallback. These are not spot proxies. Its `trim_trailing_zero_volume` deliberately removes trailing non-trading rows; the adjacent hourly archive retains some such rows.

| Symbol | Last daily row | Last nonzero-volume hourly row observed | Nearby hourly tail |
|---|---|---|---|
| BZRXUSDT | 2021-12-19, close 0.2301 | 2021-12-19 01:00, close 0.2301 | Final 02:00 bar has zero volume, then no further hourly rows in the inspected December interval |
| BNXUSDT | 2025-03-17, close 2.0 | 2025-03-17 09:00, close 2.0 | All 336 hours March 18–31 have constant close 2.0 and zero quote volume |
| LUNAUSDT | 2022-05-12, close 0.008 | 2022-05-12 15:00, close 0.008 | Seven May 13 bars, 00:00–06:00, have constant close 0.008 and zero volume |

This evidence is consistent with contract trading cessation and subsequent padding, rather than an isolated missing daily cache row. It does **not** prove the legal settlement timestamp, settlement price, conversion entitlement or executable close. The latest trading bar cannot be treated as an automatic settlement instruction.

Funding archives extend beyond the positive-volume tails: BZRX through December 30; BNX continues through the inspected March 31 cutoff; LUNA has a May 13 00:00 observation. Much of the inspected BZRX/BNX tail is a constant rate. Those records cannot establish that positions remained tradable, or that every recorded rate should continue to accrue after closure.

The preserved daily inventory contains FORMUSDT from March 19, 2025, opening at 2.0. Its proximity to the BNX tail is a lead for a contract-identity investigation. Neither a BNX-to-FORM position transfer nor an associated conversion ratio can be inferred from those price rows. No such mapping was performed. No local primary settlement notice was established by this review.

A future correction needs archived exchange evidence for each old perpetual contract: last trading time, forced closure/settlement time and price, fee and funding cutoff, and any explicit successor treatment. Settlement must then be represented as a position/cash event under a newly frozen data and accounting contract. Forward-filling, using zero returns indefinitely, deleting the symbol, or treating the first successor price as a settlement would invent a result. Changing the universe retrospectively would also change the original strategy.

Momentum's independent benchmark is unavailable at the same BZRX mark. Its 12 actual cells were nevertheless attempted separately. The preparation retains 442 symbols with development history and 222 rebalance dates. Carry retains the same 442 source symbols, 242 eligible carry symbols and 51 monthly refreshes. Its supplied missing funding policy remained explicit; its first fatal problem was the held LUNA price.

All simple primary, zero-fee and double-fee daily streams stopped explicitly. The carry log-as-PnL diagnostic hit `invalid_simple_return` on May 11, 2022 before the missing LUNA mark; that deliberately invalid diagnostic has no quantitative result. Preserved old scores remain labelled as invalidated historical measurements and cannot substitute for a corrected Sharpe or DSR.

## Liquidation-fade: measured failures and internal archive gaps

The primary thresholds remain SR at least 1.0 and original-denominator DSR at least 0.9, together with the remaining registered requirements. Each complete cell fails both primary requirements, so the original conjunction is conclusively false without another placebo run. The current-denominator result is reported separately.

| Cell | Preserved old SR | Corrected SR | DSR, original n=100 | DSR, current n=150 | Corrected maximum drawdown | Zero-fee SR | Double-fee SR |
|---|---:|---:|---:|---:|---:|---:|---:|
| thr2.5_H6 | 0.356240 | 0.165715 | 0.014308 | 0.009950 | 70.9672% | 0.619326 | -0.289775 |
| thr3.5_H6 | 0.961224 | 0.815429 | 0.305976 | 0.258884 | 16.6028% | 1.016919 | 0.608917 |
| thr3.5_H24 | 1.120541 | 0.981334 | 0.233004 | 0.192562 | 42.9987% | 1.093678 | 0.868015 |

The zero-fee original-denominator DSRs are 0.105815, 0.546222 and 0.292796, respectively. All remain below 0.9. Removing transaction fees alone therefore does not satisfy the original gate for any of the three measurable cells.

The correction lowers all three measured Sharpes by approximately 0.139–0.191 and increases their maximum drawdowns. No measured rejection becomes a pass. This is a historical accounting comparison, not evidence of out-of-sample validation; the family holdout remains spent. Old per-cell gate verdicts absent from the preserved metadata remain null rather than being manufactured.

The invalid log-as-PnL forensic stream is available only for thr3.5_H6 (SR -0.129438). For thr2.5_H6 and thr3.5_H24 it stops at May 12, 2022 09:00 because a log price return is below -1 and is inadmissible as a simple return. Those are unavailable counterfactual diagnostics, not failures of their measured primary books. All expensive remaining gate calls are explicitly `not_run_primary_gate_failed`; skipped shared-RNG placebo draws were advanced by the frozen, synthetically tested mechanism.

Preparation probes were usable. P0 reports 1,550 observations and correlation approximately 1. P1 observes a trigger on all five registered stress dates with no unavailable required symbol-hours. P2 passes its existential requirement through fully scoreable cells: compounded means are 0.6500%, 1.0794% and 1.1329% for thr2.5_H6, thr3.5_H6 and thr3.5_H24, respectively, above the 0.25% threshold. The other three P2 cells explicitly report 3, 21 and 7 incomplete internal event windows. No endpoint-censored events are reported. Their available-window means are not used as complete-cell statistics.

Targeted timestamp coverage inspection found the same two internal gaps in each of the preserved TRXUSDT, FILUSDT and LTCUSDT hourly files:

- 2022-02-26 00:00 through 2022-02-28 23:00: 72 missing hours.
- 2022-04-01 00:00 through 2022-04-02 23:00: 48 missing hours.

Bars exist before and after both gaps. The daily files have positive-volume bars on the inspected missing days, so these are not terminal delistings. The hourly missing-month registries do not identify those partially covered months. The daily prices cannot reconstruct the unobserved hourly path, required turnover, exits or trigger observations. Existing source code considers a month present if any bars exist, so a month-level manifest by itself does not certify full hourly coverage. This review did not establish whether the original omission arose upstream or during retrieval.

Potential alternative interval artifacts already exist at `TradingAgents/data/xsect/klines_1m/{TRXUSDT,FILUSDT,LTCUSDT}.parquet`, with derived aggregates under `TradingAgents/data/rebuild/exec_pf/agg_1h/`. Footer and manifest inspection only found 2,270,880 minute rows and 37,848 aggregate-hour rows per symbol across December 2020–March 2025. Those totals are 120 hours short of a full clock and are consistent with the same five missing days; actual recovery was not established. No alternative price rows were loaded or substituted. The two intervals originate from the same exchange archive family and cannot be presumed independent provenance.

A further data investigation would need exact interval coverage plus retrieval receipts/checksums for February and April 2022, followed by a pre-registered immutable data correction if genuine observed bars are recoverable. Only fixing the first reported timestamp would be insufficient. The three incomplete cells remain unavailable until the whole held-position clock is supported.

## Review disposition

The saved artifacts consistently preserve the frozen grid, incomplete-data status, honest denominators and original/current comparison. No artifact-integrity defect was found in this review. The actionable impediments are documented contract lifecycle events for the 18 daily cells and genuine internal hourly observations for the three incomplete liquidation-fade cells. A false rejection is not demonstrated for any measured cell, and it cannot be adjudicated for the 21 unavailable cells. No new strategy was validated or promoted.
