# Causal-data and forecast reevaluation triage — September 9, 2026

This triage used source inspection, existing gates/ledger/findings, file inventories and timestamp/field coverage only. No corrected event return, score, IC, backtest or inferential result was computed. The user has authorized reevaluation; a new committed charter must precede implementation and results.

## Recommended single DEX correction

**Rank 1: the original NLST4 cohort, corrected once as a ranking/cohort diagnostic.** Preserve all **3,981 original entered pairs: 1,205 prior-history rows and 2,776 new-set rows**. The historical scoreable count of 2,770 is not the new denominator. Retain unavailable rows and explain exclusions. Do not repeat NLST2→NLST3→NLST4 as independent discovery attempts, add pools, change signs, or search thresholds.

Prior gate: `data/predlab/gates.json:predlab_nlst4`; charter `docs/superpowers/specs/2026-09-04-nlst4-charter.md`; findings §79; original ledger line 697. The original P0 required both T1 positive IC with positive quarter-bootstrap fifth percentile and T2 positive top-quintile mean, one-sided NW p<.05, positive ex-top mean, top-1 share≤.25 and positive $5k stress. Its recorded T1 passed; economics failed. The September audit invalidated the causal-feature interpretation, so those old rank claims cannot establish the repaired signal.

Freeze the original ten signs and minimum six observed features from `scripts/predlab_nlst3_features.py:69`, smart-wallet qualification ≥3 completed prior pools and top-quintile wallet quality, original constant-product costs ($1k/$5k, .3% LP fee/side, 150k gas/swap, basefee+2 gwei), and quarter bootstrap 1,000 draws/seed7. Keep the original full-cohort q80 selection **only as a retrospective diagnostic**: `scripts/predlab_nlst4_p0.py:48` estimates it from the entire new set. Even a corrected P0 pass must not promote a strategy. A causal online entry threshold is a different prospective construction and is deferred.

### Inputs and availability

All sources below are in the original read-only `/home/malecada/master_thesis/TradingAgents-predlab/data/` tree:

- `predlab/nlst/nlst4_features.parquet`: frozen pair/new_set membership; `nlst4_events.parquet`: original reference clock. Each has 3,981 rows. Preserve pair identity and all new-set membership independently of new score availability.
- `predlab/nlst/dex_raw/{screened.jsonl,screened_nlst3_snapshot.jsonl,anchors.jsonl,headers.jsonl}` and `pools/*.json`: 9,908 cached pool files, approximately 1.29 GB. The screening snapshot separates the 3,060 earlier KEEP pools from NLST4's extension; only 1,205 earlier pools entered.
- `predlab/nlst/nlst2_raw/*.json`: 3,981 caches, approximately 1.10 GB, containing historical transfers/swaps, `b24`, supply/balance/deployer fields. Nulls: deployer/nonce/deployer balance 15 each; supply 1. These remain unknown rather than zero.
- `predlab/nlst/nlst3_raw/*.json`: 3,981 legacy ownership caches. **All lack successful retrieval-status metadata.** G7 ownership-renounced must be NaN for all; no refetch or inferred negative is authorized.
- `predlab/klines_5m/ETHUSDT.parquet`: present in the source tree, 34.7 MB, 691,925 open-labeled rows, unique index. It is absent from the isolated checkout's hardcoded default data path. All **9,918 distinct required completed-five-minute quote keys** for the cached entry/3d/7d/14d exits have finite positive closes. All **10,384 required block headers** are cached. No API fetch is needed.

Freeze exact cached entry-header time as each decision/availability timestamp. All 3,981 cached `raw2.b24` values are **strictly before** the selected entry block; therefore no row fails that source-window-before-entry check. Same/after-entry feature windows must be unavailable if encountered; do not treat a same-block window as proven prior information. Use causal normalization from strictly earlier available rows within the same quarter; require two prior finite values per standardized feature and preserve NaNs/minimum-feature counts.

Correct wallet/deployer outcome availability to **`complete_ts = max(entry_ts + 7 days, selected_7d_exit_header.ts)`** before admitting prior returns into their track records. The current unconditional `entry+7d` stamp is too early for **1,897** selected exits; timestamp-only inspection found median delay 9,884 seconds and maximum 950,578 seconds among these. No outcomes were used for this count.

The implementation must also retain every frozen creation in its history metadata when a cache field is unavailable. Known deployer identity preserves the original created-pool count; an unknown prior identity must not silently reduce later counts. Missing potentially eligible buyer/outcome history makes affected later history features unavailable, with reasons. The inventoried 15 unknown deployers can therefore affect later feature coverage as well as their own rows; that downstream coverage has not been computed. Exact pool-cache creation blocks are checked against the immutable screening record. A mismatched entry reference clock cannot donate features to later normalization.

### Frozen creation cohort and settlement bounds

| Metadata | Full original history+evaluation cohort |
|---|---|
| Earliest creation block | 11,565,093 |
| Earliest creation time | Exact header unavailable; interpolation 2021-01-01 00:16:12.138 UTC |
| Exact anchors bracketing earliest creation | 2021-01-01 00:00:00 through 18:14:45 UTC |
| Latest creation block | 22,170,164; interpolation 2025-03-31 23:25:44.048 UTC |
| Earliest exact entry | 2021-01-02 00:43:36 UTC |
| Latest exact entry | 2025-04-08 21:58:35 UTC |
| Latest selected 7d exit | 2025-04-13 03:07:11 UTC (new set alone: April 12 13:01:47) |
| Latest exit used by unchanged 3/7/14d event helper | 2025-04-15 09:21:35 UTC |

Pin the original pair/block/quarter membership. Do not invent exact creation timestamps or admit April-created pools. If the unchanged event helper is reused, the latest necessary FX candle **open** is April 15, 2025 at 09:15 UTC, completed at 09:20. April observations are settlement data for the already fixed development-created cohort. Clipping entries at March 31 would change that cohort.

Reuse `predlab_nlst2_features.build_row/per_quarter_z`, `predlab_nlst3_features.pool_buyers/smart_money/serial_deployer/flow_features/composite`, and `predlab_nlst_dex_p0.pool_event/eth_usd_at`, with the explicit chronology corrections above and a cache-only header lookup. Do not run old mains: they hardcode checkout paths, may invoke RPC, and P0 writers target old gates/results (NLST4 P0 also reads legacy filenames). No `causal_v2` output exists in the source tree. A new isolated wrapper must pin source paths/hashes and refuse writes outside its new output.

Expected cost is local JSON parsing of roughly 2.4 GB plus wallet-history loops and 1,000 bootstrap draws; no fitting or network wait. Allow minutes to tens of minutes and several GB of RAM, with progress reporting. This is a planning estimate, not a benchmark. The old feature log reached 3,900/3,981 at 7,314 seconds, but included original RPC/cache population and does not predict a cache-only replay.

**Meaning of a verdict:** the corrected frozen score may or may not order outcomes and its retrospective selected cohort may or may not retain its old economics. Either result repairs the historical evidence; neither is a new out-of-sample strategy validation. H2 pools created April 1, 2025–June 30, 2026 remain unevaluated and were not enumerated after NLST4 closed, per the gate's post-verdict note and findings §79. They are outside this correction.

## Forecast slate and skip reasons

| Priority | Lead / exact prior gate | Disposition |
|---|---|---|
| 2, optional inference-only reconciliation | `predlab_p1_classical`, `predlab_p2_ml`; runner/battery/rollup | Corrected HAC/selection policy changes what selected champions' p-values can establish. HARQ versus HAR-levels is explicitly nested; under QLIKE it has no supplied matching-loss primary test and cannot be promoted using DM or squared-error CW. Reuse archived forecasts only under a separately fixed inference scope; preserve all compared-model/cell denominators. This is evidence qualification, not new model search. |
| Already completed; do not repeat | `audit_correction_2026_09_09` / 16 ENet cells | The immutable result and 16 per-origin diagnostics already repair unavailable forecasts. All four volume comparisons materially improved relative to their original losses; hourly direction becomes close to the declared baseline. The blanket claim that ENet failed uniformly is withdrawn. Repeating the same rescore adds no information. If a further inferential audit is authorized, use those exact existing vectors and account for their selection from the complete 16-cell family. |
| Defer: weak correction rationale | `predlab_rviv_p0`, `scripts/predlab_rviv_p0.py` | Original C2 HAR-30 was 36.9%/47.0% worse than debiased DVOL, and the primary test already used NW lag30 for the 30-day horizon. A p-value policy change cannot meet its positive ≥3% effect requirement. Only a summary JSON was saved here; reproducing its forecasts would require new OLS fits. Source DVOL files exist at `data/options/{btc,eth}_dvol.parquet`; no missing-file premise justifies a rerun. |
| Defer: fixed conjunctive gate still failed | `predlab_exec_fcst`, `scripts/predlab_exec_fcst.py` | Cell b already used HAC lag5 against naive20; BTC's recorded 14.7% gain did not overcome ETH's 3.1% gain below the required 5% on both assets. The HARQ-vs-levels nesting issue must qualify the underlying selected-champion interpretation, but it does not turn this different naive20 comparison into a passing family. Cell a's 0.4% profile reduction also misses its 5% floor. |
| Skip as a new empirical lead | RV missing-period repair, `tradingagents/predlab/rv.py` | The September data audit found the inspected development price/RV clock gap-free. The complete-calendar/missing-target repair is necessary prospectively but supplies no documented changed development input here. Do not regenerate RV and refit merely to search for a better result. |
| Skip duplicate historical cycles | `predlab_nlst2`, `predlab_nlst3` | Their causal claims remain qualified, but NLST4 already contains their history and the larger fixed extension. The old NLST2 feature file now has 1,205 rows while its event file has 816, another reason not to treat that cached table as an untouched original 813-score experiment. Repeating earlier cohorts would add dependent tests without new evidence. |

P1/P2's raw `holdout_status='sealed'` is stale: the append-only corrections resolver records both forecast holdouts as **spent** through Phase5. Forecast reevaluation cannot claim a fresh April 2025–July 2026 holdout. RVIV and execution-input probes were development/report-only and do not restore that shared forecast holdout. No forecast computation or holdout access is proposed as part of the NLST4 correction.
