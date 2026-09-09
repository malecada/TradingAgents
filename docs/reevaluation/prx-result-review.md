# PRX result review — September 9, 2026

**Disposition: the saved result is internally consistent and does not reverse the original conditional P0 failure.** Full-panel inference remains unavailable. This review read saved artifacts and verified their arithmetic and provenance; no formation regressions, market-window replay, bootstrap, forecast fit or additional research cell was executed. No source, gate, policy or result was changed.

## Result and permitted interpretation

All 50 registered months, January 2021–February 2025, are retained in order. Mean monthly selected persistence is **0.10961103267217819**, versus **0.11299999999999999** for the original random comparator. The ratio is **0.9700091386918425**, below the required 1.5; the original paired greater-Wilcoxon p-value is **0.8127852985597879**, above 0.05. Both conditional thresholds fail. The saved original ratio was 0.9427214139809006; the correction therefore does not rescue this comparator.

The correct statement is: **the corrected Engle–Granger selector fails the original conditional persistence comparison on available pair outcomes across the 50 registered months; incomplete selected-pair coverage prevents complete-panel inference.** This is not a trading-return result, validation, exhaustive rejection of pairs trading, or proof that corrected formation tests can never help another construction. The historical ordinary-ADF artifact retains its previously qualified source provenance.

`status=incomplete`, `complete_panel_verdict=unavailable` and the unavailable dependence diagnostic are appropriate. No confidence interval or bootstrap probability was produced. The fixed stationary-bootstrap parameters remain metadata for an unavailable diagnostic; they must not be described as 2,000 evaluated draws. No P1, forecast-model retraining, holdout evaluation, candidate selection or strategy validation occurred. Rolling formation regressions were recomputed as registered.

## Coverage

All calendar dates required by the saved monthly records are present. Incompleteness concerns selected-pair observations, not three absent months:

| Month | Selected / scoreable | Unavailable selected outcomes |
| --- | ---: | --- |
| November 2023 | 20 / 18 | BCH–TOMO and BTC–TOMO: 14 observations each |
| August 2024 | 20 / 17 | OP–RNDR, BCH–RNDR and MATIC–RNDR: zero observations each |
| September 2024 | 20 / 19 | MATIC–LTC: four observations |

All pair symbols above have the `USDT` suffix in the artifact. Each unavailable outcome falls below the frozen 25-observation requirement. The other 47 months are complete under the registered rules. All 50 months still have paired conditional rates; six missing outcomes were neither zero-filled nor silently removed from the requested counts. No ticker replacement or additional data recovery was attempted.

The 61,250 possible formation pairs comprise 49,508 tested pairs and 11,742 exclusions below 60 formation observations. There are 931 selected pairs, 925 scoreable selected outcomes and six unavailable outcomes. The random arm retains 1,305 attempts for 1,000 scoreable outcomes, including 305 unavailable attempts. Its monthly rates exactly match the saved original comparator in all 50 months. Seven repeated ordered draws, 12 repeated unordered draws and five reversed-pair occurrences are disclosed. Months selecting fewer than the cap of 20 are not mislabeled incomplete solely for that reason.

## Verification and provenance

The 50-row `monthly.parquet` archive matches every corresponding scalar and missing-reason field in `result.json`. Selected-pair counts, observed thresholds, p-value ordering, recorded persistence decisions and monthly rate arithmetic agree. The saved ratio and greater-Wilcoxon p-value were independently reproduced from the stored monthly rates without rebuilding the selector. The sole PRX ledger cell matches the result configuration, metrics and source commit. All three input hashes and both archived output hashes were rechecked. Start/final provenance agrees with the committed gate and correction policy.

| Item | Commit or SHA256 |
| --- | --- |
| Executed source | `49fb9e47c4d9e40b9c3f1b7de475041ec63aac76` |
| `prx/result.json` | `799662b5ec8307aa9ca4008aef0b3d219a79c40a37dddebcbb0f8606cffba3ce` |
| `prx/monthly.parquet` | `34488677809f2017952cbff7711c8e8a654800a800cdd6d9c897ea7dc6aecf42` |
| Registered gate | `b74efa4273a38339cab652cb140b0aa64df1778a1f7f8bcb015e49c3f357e894` |
| Correction policy | `fba631d9bb458decc4b278c1b224a2441d97b75d7a328dffa0850c9799619a4d` |

The source commit precedes the recorded start, 2026-09-09 16:16:18 UTC; completion is 16:18:43 UTC. Python 3.13.13, NumPy 2.3.0, SciPy 1.17.1 and statsmodels 0.14.6 are recorded. Overlapping formation windows and shared symbols remain dependence limitations of the historical Wilcoxon diagnostic. The incomplete calendar-wide observation panel must not be compressed to 47 months to manufacture the separately registered dependence sensitivity.
