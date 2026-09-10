# Interpretation of saved factor risk diagnostics

The saved diagnostic is complete for all36 BTC/ETH sleeves from the original18 configurations. It ran under source `cd8d9e3f064bb40273ba493e597e371e6f199b66`. This interpretation reads only its `result.json`, dated daily annotations and stop-event tables under `data/diagnostics/2026-09-10/risk/`. No diagnostic function, strategy engine, alternative policy or new Sharpe calculation was run. All72 consumed Parquet payload hashes matched the saved result manifest. Result SHA-256: `d37d6f7ab18b307aa12f4b5f57212ee0dbffd7611358ba3a1beaf8638982f9fa`.

The useful finding is a distinction between entry-time sizing and later risk. Raw factor targets are set at entry/flip; actual books then maintain those weights against drifted holdings. Increasing underlying volatility can therefore increase the nominal risk proxy without a new sizing decision. Price stops generally flatten only until the next daily decision, often restoring the same target with its existing sizing reference. These are observed mechanics, not proof that continuous resizing, a cooldown or different stops would improve results.

## Denominators and full-grid observations

There are44,640 sleeve-date observations:36×1240. Of these,8,873 have a nonzero applied opening exposure,34,625 are already halted cash dates, and1,142 are other flat dates. All684 unavailable volatility rows are initial warmup rows (36×19); no applied-active risk proxy is unavailable. Configurations overlap in both asset and date, so these counts are not independent observations or independent trials. Cross-grid quantiles below describe sleeve-date records and deliberately weight longer-active sleeves more heavily.

| Exposure measured | Nonzero sleeve-date risk observations | Risk proxy median / p90 / maximum | Risk/reference-entry ratio median / p90 / maximum |
| --- | ---: | --- | --- |
| Latent requested target, including suppressed post-halt targets | 43,259 | 14.23% / 23.74% / 80.02% | 0.949 / 1.582 / 5.335 |
| Incoming marked holding before rebalance | 8,010 | 15.17% / 25.73% / 79.47% | 1.012 / 1.716 / 5.298 |
| Applied opening target | 8,873 | 15.01% / 25.32% / 80.02% | 1.000 / 1.688 / 5.335 |
| Closing marked holding | 8,010 | 15.20% / 25.72% / 79.94% | 1.014 / 1.715 / 5.329 |

Risk proxy means absolute exposure weight×the original causal20-day underlying-volatility estimate, annualized with sqrt252. It is not realized account volatility. Incoming ratios have8,005 defined observations: on five other incoming-active dates, the current raw target is flat and its current sizing reference is unavailable. All other displayed ratio counts equal their risk counts. Latent post-halt exposures are not positions held by the book.

The sizing formula's nominal entry budget is15%, not a continuously maintained10% account-volatility target: 10% target×0.5Kelly×3confidence-one leverage, subject to the leverage cap. Applied risk exceeds its own sizing-date reference on4,458/8,873 active sleeve-dates (50.24%). Applied risk p99 is48.08%, and its reference ratio p99 is3.205. No latent, incoming, applied or closing weight exceeds the3×leverage cap; the observed risk expansion therefore is not evidence of a leverage-cap breach.

Applied exposures use a sizing reference with median age23 daily bars, p9094, p99214.28 and maximum266 across the8,873 active records. Existing applied exposure persists while the volatility entry gate is closed on939/8,873 active dates (10.58%). That gate restricts new raw sizing decisions; it was not specified as a daily liquidation rule.

There are852 recorded price-stop events:726 next-day same-sign re-entries,93 opposite-sign entries,25 permanent-halt successors and8 flat successors; none is end-of-window censored. Thus819/852 stops are followed by next-day entry. All726 same-sign re-entries reuse their prior sizing reference. Across those726 events, the reference age at re-entry is median13, p9060 and maximum160 bars. Across all819 re-entries, the corresponding ages are10,59 and160. There are264 stop events immediately following another stop event; this counts adjacent events within chains, not264 independent episodes.

All36 sleeves halt permanently:35 cross the15% drawdown threshold before exit charges and one afterward. The saved post-halt cash dates remain in the clock. These books therefore do not establish an ongoing restartable strategy.

## The four motivating sleeves

These examples were specified before the diagnostic run. Each retains the full1240-day return clock; active counts below mean nonzero applied opening exposure. The observed entry/flip risk proxy is15% for every active sizing event in these four sleeves (52,28,10 and6 events respectively).

| Sleeve | Active dates | Applied risk median / p90 / max | Current/reference risk p90 / max | Sizing age median / p90 / max, bars | Above reference | Active with entry gate closed |
| --- | ---: | --- | --- | --- | ---: | ---: |
| 30-day LS momentum, BTC | 983 | 15.09% / 27.98% / 51.08% | 1.865 / 3.405 | 15 / 47.8 / 97 | 519/983 | 46/983 |
| 30-day LS momentum, ETH | 581 | 15.00% / 28.92% / 64.44% | 1.928 / 4.296 | 15 / 48 / 84 | 277/581 | 58/581 |
| 10/50 MA LS, BTC | 462 | 15.04% / 48.77% / 80.02% | 3.252 / 5.335 | 26 / 66 / 101 | 234/462 | 46/462 |
| 10/50 MA LS, ETH | 234 | 14.61% / 29.60% / 38.56% | 1.973 / 2.571 | 34.5 / 81 / 101 | 104/234 | 43/234 |

For a concrete scale example, the10/50 BTC maximum is February18,2023: applied weight1.599450×underlying-volatility estimate0.500302=0.800209, using a39-bar-old sizing reference. This is an exposure-risk diagnostic, not an80% observed account-volatility estimate. The30-day BTC maximum on the same date uses weight1.020975 and a42-bar-old reference, giving0.510796.

| Sleeve | Price stops | Same-sign / opposite-sign next-day entries | Other immediate successor | Reused-reference re-entry age median / p90 / max, bars |
| --- | ---: | --- | --- | --- |
| 30-day LS momentum, BTC | 46 | 32 / 13 | 1 permanent halt | 2 / 12.9 / 16, n=32 |
| 30-day LS momentum, ETH | 39 | 29 / 9 | 1 permanent halt | 6 / 14.2 / 19, n=29 |
| 10/50 MA LS, BTC | 19 | 19 / 0 | None | 7 / 22.2 / 32, n=19 |
| 10/50 MA LS, ETH | 7 | 7 / 0 | None | 2 / 27.2 / 29, n=7 |

## Charges and halts

Charges below are saved dollar fee/slippage/spread charges plus impact for each separate10000-initial-NAV sleeve. No BTC/ETH or cross-configuration dollar totals are pooled. Opening-from-flat includes post-stop re-entry, so the re-entry column is a subset and must not be added again. Price-stop exits are a subset of all risk exits. Direct flips refer to changing the sign of an incoming nonzero holding; an opposite-sign entry after a previous day's stop belongs to opening-from-flat.

| Sleeve | Maintenance | Opening from flat | Of which next-day stop re-entry | Direct flips | All risk exits | Of which price-stop exits | Total execution charges |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30-day LS momentum, BTC | 92.79 | 237.55 | 234.93 | 490.52 | 247.51 | 247.51 | 1068.36 |
| 30-day LS momentum, ETH | 51.62 | 128.86 | 126.86 | 150.03 | 127.66 | 127.66 | 458.17 |
| 10/50 MA LS, BTC | 48.86 | 63.96 | 61.35 | 81.65 | 92.52 | 62.07 | 286.99 |
| 10/50 MA LS, ETH | 27.73 | 18.54 | 16.53 | 22.81 | 21.33 | 16.42 | 90.41 |

Across36 sleeves, the within-sleeve maintenance share of execution charges has median5.97%, p9017.97% and range1.59–30.68%. The next-day stop re-entry share has median38.55% and range18.28–47.67%; price-stop exit share has median40.48% and range18.17–48.18%. These are distributions of36 separate cost fractions; the medians must not be summed into an aggregate fraction. The observed charges suggest that repeatedly stopping and reopening deserves scrutiny. They do not measure the net effect of suppressing re-entry: exposure and later returns would change too.

| Sleeve | Permanent halt | Threshold crossed | Drawdown before / after exit charges | Gross dollars from recorded peak to halt | Signed funding | Fee+impact | Net peak-to-halt change |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 30-day LS momentum, BTC | 2024-08-05 | Before exit | 15.871784% / 15.899941% | −3857.83 | +17.77 | 95.79 | −3935.85 |
| 30-day LS momentum, ETH | 2023-06-30 | After exit | 14.999356% / 15.032114% | −2036.94 | −24.05 | 173.65 | −2234.64 |
| 10/50 MA LS, BTC | 2023-03-03 | Before exit | 16.195509% / 16.345139% | −3193.50 | −99.55 | 33.38 | −3326.43 |
| 10/50 MA LS, ETH | 2022-07-18 | Before exit | 15.986371% / 16.021878% | −2241.11 | +38.78 | 12.30 | −2214.63 |

The unique post-exit case is30-day ETH: its price stop has `portfolio_stop_hit=False` before exit, then4.779256 fee plus0.090382 impact crosses the permanent threshold. This identifies the recorded boundary crossing only. It does not establish what an earlier cost change would do to the entire path or whether subsequent trading would benefit. In all four displayed peak-to-halt decompositions, gross losses account for most of the decline; stop-related charges are not a sufficient general explanation of the halts.

## Interpretation limits and research question

The evidence supports a bounded question about the consistency of entry-time sizing, existing-position volatility controls, price-stop re-entry and a permanent drawdown latch. It does not yet support choosing a new volatility target, stop distance, cooldown or restart rule. Removing either fees or stops from the narrative would omit changed exposure, potential protection and subsequent losses. A causal comparison requires a separate pre-result design that retains the full grid and tests an explicit mechanism; the selected examples cannot serve as a fresh selection or validation set.

The original factor exercise is a benchmark comparison, not a passed standalone adoption gate. These are separate BTC/ETH proxy-price books with assumed daily funding and threshold stop fills. Existing holdouts are spent. The new diagnostic neither changes the corrected benchmark measurements nor adds a validated strategy.
