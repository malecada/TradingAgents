# Independent NLST4 result review

**The saved correction is internally consistent: all 32 verification checks passed. T1 passes; T2 fails; no strategy promotion or holdout claim follows.** The review used immutable saved outputs, source-file hashes, cached metadata and the reported frozen statistics. No event-return replay, model fit, bootstrap redraw, new threshold or additional statistical search was performed.

Result: `data/predlab/audit_reevaluation_2026_09_09/nlst4/result.json`.

```text
Result SHA256: 613cc7a1321eaaf3b5ac2613cbed10c7f7db0ce955f6e7ce56e39ac7e7449c53
Cohort SHA256: 5966191c57a358bce03970bd965952f74e284d9374c06bf5701462a309b2c53d
Source commit: 49fb9e47c4d9e40b9c3f1b7de475041ec63aac76
Gate SHA256: b74efa4273a38339cab652cb140b0aa64df1778a1f7f8bcb015e49c3f357e894
Correction policy SHA256: fba631d9bb458decc4b278c1b224a2441d97b75d7a328dffa0850c9799619a4d
Started UTC: 2026-09-09T16:22:04.758238+00:00
Completed UTC: 2026-09-09T16:53:53.050755+00:00
```

Both recorded output hashes match. All **11,950 original input files** currently match the hashes recorded before use and rechecked by the completed run. Every input resolves inside the original read-only `TradingAgents-predlab/data` source tree. Start/end source, gate, correction-policy and runtime provenance agree. Exactly one matching ledger record exists for `nlst4:original_new_pool_cohort_causal_v2`, with identical configuration, metrics and source commit. The result retains `promotion_eligible=False`, `causal_entry_rule_tested=False`, `holdout_evaluated=False` and `forecast_models_refit=False`.

## Cohort and chronology

The archive retains all **3,981 unique original pairs in their original order**, including **1,205 prior-history rows and 2,776 new-set rows**. Pair, quarter and new-set identity agree with the original feature table; creation blocks agree with immutable screening records. All 2,776 new-set event outcomes are available.

Every entry timestamp agrees with both the original event reference and its exact cached block header. Every selected seven-day exit timestamp agrees with its exact cached header. All raw2 windows end strictly before the entry block. Decision/feature-availability timestamps equal the exact entry timestamp, and every completion timestamp equals `max(entry_ts + 7 days, selected_exit7_ts)`. The correction delays **1,897** completion timestamps beyond the old nominal horizon. No exit precedes entry.

Creation membership remains the original development cohort: interpolated timestamps span January 1, 2021 at 00:16:12.138 UTC through March 31, 2025 at 23:25:44.048 UTC. Exact creation timestamps are not asserted. The latest exact entry is April 8, 2025 at 21:58:35 UTC; the latest selected seven-day exit is April 13 at 03:07:11 UTC. These are settlements of the fixed earlier-created cohort.

All **6,446 distinct completed-five-minute ETH quote keys required by saved entry/seven-day-exit timestamps** have finite positive cached closes. The last of these keys is April 13 at 03:00 UTC. The independent quote check filtered the source before materialization at the registered April 15, 2025 09:20 UTC exclusive cap. The unchanged helper's additional three-/fourteen-day metadata requirements and April 15 boundary were established in the pre-result inventory; this review did not replay those financial cashflows.

## Coverage qualification

The corrected new set contains **2,718 scoreable rows and 58 unavailable rows**. Feature and standardized-feature counts agree with the saved finite-value masks; every finite score satisfies the six-feature minimum. Requested and scoreable quarter totals match the result exactly.

The original cached evaluation had **2,770 scoreable new rows**. All 2,718 corrected scoreable rows belong to that old scoreable set; **52 formerly scoreable rows are now unavailable**, with no newly scoreable replacement rows. A comparison of old and corrected aggregate statistics therefore includes a changed sample and changed available-feature composition. It is not a paired estimate of the isolated effect of one correction.

| Raw feature availability in the 2,776 new rows | Available rows |
|---|---:|
| Smart-money volume share | 2,724 |
| Smart-money breadth | 2,732 |
| Serial-deployer performance | **0** |
| Serial-deployer prior count | **14** |
| Early net inflow | 2,776 |
| Buy acceleration | 2,685 |
| Verified ownership renunciation | **0** |
| Deployer supply share | 2,767 |
| Deployer age | 2,769 |
| Depth growth | 2,770 |

Ownership is unverified in every new row. Deployer-history uncertainty is explicitly retained: 2,755 new rows have unavailable count history, 2,720 have unavailable return history, and seven have unknown current deployer identity. None is silently reclassified as a known zero or a smaller complete history. The scoreable population comprises 98 rows with six standardized features and 2,620 with seven. The 58 unavailable rows have zero, two or five standardized features. These omissions qualify what the surviving composite can establish; the result does not validate all ten named mechanisms individually.

## Frozen diagnostic verdict

| Requirement / disclosure | Saved corrected result | Disposition |
|---|---:|---|
| T1 Spearman IC > 0 | 0.142362054964 | Pass |
| T1 quarter-bootstrap fifth percentile > 0 | 0.083220079538 | Pass |
| Bootstrap denominator | 1,000 / 1,000 finite draws, seed 7 | Complete |
| T2 selected cohort | 544 rows; global q80 = 0.333595175202 | Retrospective |
| Mean $1,000 net return > 0 | +19.097838% | Pass component |
| One-sided NW p < .05 | 0.228018157021 | **Fail** |
| Mean excluding largest absolute return > 0 | +0.044171% | Pass component |
| Largest absolute-return share ≤ .25 | 0.138972250546 | Pass component |
| $5,000 stress retains positive sign | −21.416442% | **Fail** |
| Median $1,000 net return | −64.948370% | Disclosure |

The saved fifth percentile agrees with the stored 1,000 bootstrap values; no draw was discarded. Every selected row has its $5,000 outcome, and the saved q80 selects exactly the reported 544 rows. Applying the frozen Boolean requirements to the saved metrics reproduces **T1 PASS, T2 FAIL and overall diagnostic FAIL**.

The corrected ranking association survives on the qualified scoreable sample. The positive selected-cohort mean coexists with a strongly negative median, a small positive ex-top mean, an insignificant NW test and negative larger-notional stress. The original global q80 uses the entire evaluated new sample and remains retrospective. No causal online entry rule, P1 test, fresh holdout or validated strategy is established.

Detailed machine-readable evidence is in `docs/reevaluation/verification/nlst4-artifact-checks.json`. Source, gates, policy, original stores and result artifacts were not modified during this review. No actionable artifact inconsistency was found.
