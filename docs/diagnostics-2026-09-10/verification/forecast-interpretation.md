# Saved-forecast interpretation — September 10, 2026

The completed sixteen-cell diagnostic supports lower saved ENet volume-forecast loss than the original seasonal-naive baselines. It does not establish a new selected model or validated strategy. The other targets remain mixed: all four mean-return comparisons have negative point improvements, hourly direction gains miss the accuracy floor, BTC variance loss is worse, and ETH variance improves with substantial qualifications.

This interpretation reads the immutable `data/diagnostics/2026-09-10/forecast/result.json` and its saved paired/bootstrap outputs. No loss series, forecasts, fits or bootstrap samples were regenerated. Source commit: `cd8d9e3f064bb40273ba493e597e371e6f199b66`. Result SHA-256: `acbe21b51a346211a8c13c9c04ca82844c6fe90b12f9ac5a604b1dca15ef9cdc`. Registration: `38d9a67e6ff042cb1fd870877b3e0222f40fdc08`; policy: `docs/diagnostics-2026-09-10/forecast-charter.md`.

## All sixteen fixed comparisons

Improvement is `100 × (baseline loss − effective ENet loss) / baseline loss`; positive values favor ENet. The intervals are the saved percentile 95% conditional bootstrap intervals. Losses are squared error for returns, Brier for direction, normalized QLIKE for variance, and absolute error on log volume. The common positive MASE scale cancels in the volume relative improvement. Stability signs refer, in order, to 2021–2022, 2023–2024 and 2025Q1, over each asset's registered clock; `0` means exactly zero differential.

| Asset/grid | Target and declared baseline | Improvement % | Conditional 95% interval % | Raw diagnostic p | Stability signs |
|---|---|---:|---:|---:|:---:|
| BTC 1h | Return / zero | −0.366285 | [−0.952024, −0.006968] | 0.903048 | − − + |
| BTC 1h | Direction / base rate | +0.162711 | [−0.076061, +0.349943] | 0.053973 | − + + |
| BTC 1h | Variance / HAR levels | −35.577542 | [−52.213400, −22.633868] | 1.000000 | − − − |
| BTC 1h | Log volume / seasonal naive m24 | +38.823981 | [+36.994710, +40.479874] | 0.000499750 | + + + |
| BTC 24h | Return / zero | −3.754632 | [−8.650656, −0.380012] | 0.915542 | − − − |
| BTC 24h | Direction / base rate | −2.074467 | [−4.236928, −0.295103] | 0.969015 | − − + |
| BTC 24h | Variance / HAR levels | −69.192688 | [−127.192560, −19.037233] | 0.980510 | − − + |
| BTC 24h | Log volume / seasonal naive m7 | +17.164354 | [+13.002321, +21.402475] | 0.000499750 | + + + |
| ETH 1h | Return / zero | −0.026641 | [−0.087098, +0.031392] | 0.834083 | − − + |
| ETH 1h | Direction / base rate | +0.251114 | [−0.161631, +0.553546] | 0.057971 | − + + |
| ETH 1h | Variance / HAR levels | +10.284864 | [+0.126566, +18.990223] | 0.023988 | − + + |
| ETH 1h | Log volume / seasonal naive m24 | +37.146948 | [+35.223110, +38.738859] | 0.000499750 | + + + |
| ETH 24h | Return / zero | −0.902396 | [−2.091925, −0.199705] | 0.964018 | 0 − − |
| ETH 24h | Direction / base rate | −2.884849 | [−5.499981, −0.460671] | 0.983508 | 0 − − |
| ETH 24h | Variance / HAR levels | +5.858461 | [−29.705277, +31.573500] | 0.412294 | 0 + + |
| ETH 24h | Log volume / seasonal naive m7 | +22.366691 | [+18.636143, +25.808454] | 0.000499750 | + + + |

The twelve return/direction/variance rows have `eligible_primary_p = null`, `holm_adjusted_p = null` and Holm input one because nesting and penalized-estimation test applicability remain unresolved. Their raw p-values above are conditional diagnostics, not eligible primary tests. In particular, the ETH hourly-variance p-value must not be reported as a multiplicity-adjusted discovery. All sixteen `formal_model_class_p` values are null.

## Four volume comparisons

Each volume comparison has raw p = `0.0004997501249375312` and sixteen-slot Holm-adjusted p = `0.0079960019990005`, with `conditional_family_reject = true`. The raw value is the finite-resolution minimum `1/2001`, not zero. All four exceed the historical 5% point-effect descriptor, and every saved relative interval lies above that floor. Positive loss differentials occur in all three fixed periods, with at least thirty paired origins in every period. These are successful conditional descriptors under the frozen diagnostic, not retroactive original-gate passes.

| Volume cell | Prior baseline MASE | Corrected ENet MASE | Paired / full-clock origins | Raw-valid coverage of scoreable origins | Baseline fallback origins | Paired counts in the three stability periods |
|---|---:|---:|---:|---:|---:|---|
| BTC 1h | 1.093871095 | 0.669186788 | 37,200 / 37,201 | 97.448925% | 949 | 17,520 / 17,543 / 2,137 |
| ETH 1h | 1.123166692 | 0.705944550 | 29,184 / 29,185 | 97.053180% | 860 | 9,504 / 17,543 / 2,137 |
| BTC 24h | 0.903588171 | 0.748493097 | 1,551 / 1,551 | 94.003868% | 93 | 730 / 731 / 90 |
| ETH 24h | 0.759745759 | 0.589815774 | 1,217 / 1,217 | 92.851274% | 87 | 396 / 731 / 90 |

The MASE figures are the prior means retained in the new result, not newly estimated training scales. Current bootstrap loss means are unscaled absolute errors on log volume; those units must not be labeled MASE. The comparisons include valid fallback origins with zero paired differential, so the gain is for the frozen effective ENet-plus-fallback forecast stream rather than an assumed always-available ENet model.

Historical LGB context remains separate. The earlier scalar comparison recorded lower LGB volume MASEs than corrected ENet in all four cells: approximately 0.635784 versus 0.669187 for BTC 1h; 0.668895 versus 0.705945 for ETH 1h; 0.703607 versus 0.748493 for BTC 24h; and 0.531613 versus 0.589816 for ETH 24h. These are previously inspected historical scalars, outside this sixteen-baseline inference family. Competitor forecasts were not reopened, rescored, paired, or newly checked for coverage parity. Thus the present results do not establish ENet superiority over LGB or justify selecting ENet over the original alternatives.

## Direction, variance and mean-return qualifications

Hourly direction improves Brier point loss only modestly, and both 95% relative intervals include zero. BTC accuracy is 52.455579% versus baseline 50.678745%, an edge of 1.776834 percentage points; ETH accuracy is 52.177488% versus 50.265547%, an edge of 1.911941 points. Both are below the fixed 2-point accuracy floor. Their point AUCs are 0.531445 and 0.534407. Daily accuracy edges are negative: BTC −0.515796 points with AUC 0.499815, and ETH −0.821693 points with AUC 0.483859. No AUC confidence interval was supplied for any direction cell, so the original conjunctive effect descriptor remains null in all four. The hourly stability descriptor is met; the daily descriptor is not.

ETH variance has lower point QLIKE than HAR at both frequencies, whereas BTC has higher loss at both. ETH hourly improves 10.284864%, with a conditional interval just above zero; its early period is negative and the later two are positive. ETH daily improves 5.858461%, but its interval spans approximately −29.7% to +31.6%; the early differential is exactly zero under the preserved stream, followed by two positive periods. Both ETH cells meet the historical 2% point-effect and two-positive-period descriptors. Neither is eligible for a formal primary test here. BTC hourly and daily loss deteriorate 35.577542% and 69.192688%, respectively, and neither meets the stability or effect descriptors. This compares each saved model with its own baseline and clock; it is not a statistical test of an ETH-versus-BTC difference.

All four mean-return point OOS-R² values are negative: BTC hourly −0.003662850, BTC daily −0.037546325, ETH hourly −0.000266410 and ETH daily −0.009023963. None reaches the fixed positive floor or stability descriptor. ETH hourly's interval includes zero; the other three saved intervals lie below zero. These outcomes concern the four tested effective streams against zero and do not prove that the entire mean-return forecasting class lacks useful signal.

## Clock, fallback and artifact checks

All sixteen cells are available in the result, and all saved paired files retain their full registered UTC clock: BTC from January 1, 2021 and ETH from December 1, 2021, each ending March 31, 2025 at 00:00 UTC. The four hourly variance/volume cells retain one unavailable score at October 28, 2024 20:00 UTC. For variance, the original row is present but unscoreable; for volume, the omitted origin is explicitly inserted as unavailable. Every other cell is fully scoreable. No compressed clock or imputed target is used.

Stored paired flags agree with the result's full-clock, scoreable, missing-origin and fallback counts. All sixteen saved bootstrap files contain 2,000 rows, and all 32,000 stored draws are flagged valid for both difference and relative inference. For the masked hourly cells, stored sampled scoreable counts range from 37,195 to 37,201 for BTC and 29,179 to 29,185 for ETH; this is consistent with masks traveling with the sampled physical clock. These checks inspect existing artifacts only.

Raw-valid coverage is materially lower for return and direction: BTC hourly/daily 72.057203%/72.598324%, ETH hourly/daily 67.551825%/67.214462%, with 10,395/425 BTC and 9,470/399 ETH fallback origins. Variance coverage is BTC hourly/daily 69.548387%/71.115409% and ETH hourly/daily 67.249178%/66.885785%, with 11,328/448 and 9,558/403 fallback origins. The effective forecast stream's complete scoreability therefore must not be described as complete raw-model availability.

The result records prior-receipt agreement, unchanged pinned inputs and an unchanged 748-row financial ledger with SHA-256 `4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601`. Its separate sixteen-row forensic ledger has SHA-256 `0ce191637e10d9529616f7b121f1479822878dccd71638e9855b14bd018a4e18`. No financial backtest, new forecast fit, network request or holdout read occurred. Full independent provenance verification is reported separately.

Inference remains retrospective and conditional on the saved predictions, prior selection, expanding estimation, preserved availability masks and a weak-dependence/stationarity approximation using one fixed 21-day block policy. Holm accounts for sixteen current slots; it does not remove the wider historical research search. No original gate is reversed, no fresh validation is created, and no trading strategy is promoted.
