# Primary mechanism interpretation — fixed factor policy comparison

The daily-sizing rule met its algebraic risk objective without resolving the immediate-reentry books' permanent halts. Waiting reduced repeated stop re-entry and preserved more books, but much of the apparent improvement came from long-only sleeves ceasing to trade. Neither result establishes a new return signal, executable performance or validation.

Scope: the primary scenario of all18 original configurations ×4 registered arms, in original order. Only the completed saved `result.json` and existing schema/charter were read; no strategy was replayed, target rebuilt, parameter changed, alternative simulated or financial metric refitted. Figures below count or compare the saved metrics/diagnostics. No sleeve dollars are pooled. Root's separate independent checker owns the full arithmetic/input/output verification.

Source commit: `2dfb047d5c2f2ff821706736eb9f5508a14e7304`. Completion: `2026-09-10T15:20:32.939946+00:00`. Result SHA-256: `245ad6a30022a4ab7f115b1acb52d33dc5537ce43d8c0b6850e5ec25391d1006`. The artifact reports72 complete identities, no winner selection, no formal inference, and zero validated strategies. The four cost scenarios total288 indices and576 sleeves, but this interpretation covers only72 primary indices/144 primary sleeves.

A00 = saved size/immediate re-entry; A10 = daily size/immediate re-entry; A01 = saved size/new-target-episode re-entry; A11 = daily size/new-target-episode re-entry. Each arm contains36 sleeves ×1,240 dates =44,640 sleeve-dates. Counts overlap the same assets, dates and related configurations and are not independent observations. Repeated or identical configurations remain in the registered denominator.

## Risk, activity and stop clocks

| Saved primary diagnostic | A00 | A10 | A01 | A11 |
|---|---:|---:|---:|---:|
| Active sleeve-dates |8,873|7,750|7,739|8,618|
| Waiting/blocked sleeve-dates |0|0|23,808|24,530|
| Permanently halted cash sleeve-dates |34,625|35,748|11,836|10,176|
| Other flat sleeve-dates |1,142|1,142|1,257|1,316|
| Applied risk proxy above0.15 |4,458/8,873|0/7,750|4,255/7,739|0/8,618|
| Maximum active applied risk proxy |0.800209|0.150000|0.800209|0.150000|
| Price-stop events |852|789|433|474|
| Next-day same-sign re-entry after stop |726|662|0|0|
| Next-day opposite entry after stop |93|91|68|76|
| Next-day waiting after stop |0|0|349|382|
| Next-day permanent halt after stop |25|28|8|7|
| Next-day ordinary flat after stop |8|8|8|9|
| Sleeves halted /36 |36|36|18|18|
| First halt crossing before/after exit |35/1|35/1|17/1|18/0|

The four activity classes sum to44,640 within every arm, and the five successor classes sum to its stop count. Stop successors describe the **next saved daily decision**, whereas waiting counts describe **every suppressed nonzero request**;23,808 waiting dates do not represent23,808 distinct stop events. All primary stop-fill-envelope exceptions are zero. This observation does not validate the general threshold-fill convention for other paths or venues.

Daily sizing removes all admitted applied-risk exceedances, versus50.24% of active A00 dates and54.98% of active A01 dates. This is the promised decision-time `abs(weight) × causal sigma` cap with sqrt252 volatility; it is not a guarantee of continuous risk, annual realized volatility or a maximum drawdown. Incoming risk still exceeds0.15 on2,844/6,953 active A10 dates and3,602/8,132 active A11 dates; closing risk exceeds it on3,474/6,953 and4,067/8,133 dates respectively. Held exposures and NAV drift between decisions, and the next sigma can change. Applied-risk/reference denominators have no active missing values. Tiny maxima above0.15 at floating-point precision are within the registered tolerance.

Same-sign opening adjustments change from7,792 unchanged-target-maintenance rows in A00 to6,742 resize rows in A10; A01 has7,124 maintenance rows and A11 has7,951 resize rows. These are turnover classifications, not independent causal cost estimates. Resizing preserves the original price-stop anchor; it does not reset stop age daily.

## Long-only cash is the major survival qualification

There are7 long-only configurations/14 sleeves. Both waiting arms retain exactly118 active,16,671 waiting, zero permanently halted and571 other-flat sleeve-dates out of17,360. Only0.68% of those dates are active and96.03% are blocked. Every one of the14 waiting long-only sleeves remains negative in both saved gross and net dollars; all7 long-only indices remain negative. Avoiding the drawdown halt here is mainly loss limitation through persistent non-participation, not profitable continued operation. A01 and A11 have identical activity counts in this subset despite different sizing and cashflows.

The remaining11 configurations/22 sleeves therefore account for only4 unhalted sleeves in each waiting arm. The identities differ: A01 leaves BTC14-day momentum, ETH10/50MA, and both50/200MA sleeves unhalted; A11 leaves the first two plus ETH20-day Donchian and BTC55-day Donchian unhalted. Adding daily sizing can lose one form of survival and gain another. The two50/200MA sleeves halt under A11 although neither halts under A01.

## Saved gross, net, cost and exposure implications

| Paired primary comparison against A00 | A10 | A01 | A11 |
|---|---:|---:|---:|
| Index compound return higher /18 |7|14|14|
| Index compound return lower /18 |11|4|4|
| Sleeve gross dollars higher /36 |11|30|29|
| Sleeve net dollars higher /36 |15|30|27|
| Sleeve linear execution charges lower /36 |19|27|23|
| Sleeve quadratic impact higher /36 |28|11|14|
| Integrated absolute applied exposure lower /36 |25|23|22|
| Halt earlier/later/same/not reached /36 |23/11/2/0|2/14/2/18|2/15/1/18|

All counts are descriptive comparisons of the complete saved calendars, retaining halted and waiting cash. Exposure suppression is common, but is not universal: delayed/avoided halts can allow more cumulative participation. Daily sizing alone still halts all36 sleeves, often earlier, and raises quadratic impact in28/36 despite reducing total applied exposure in25/36. Engineering risk conformance is therefore distinct from economic improvement.

Waiting's14/18 higher index returns include all7 long-only cases becoming **smaller losses**. Among the other11 configurations,7 improve and4 deteriorate. All18 index signs are retained: A00 has7 positive/11 negative, A10 has6/12, and each waiting arm has10/8. The gross-dollar improvements in30/36 A01 sleeves show that the difference cannot be explained solely by fewer fees. However, removed/replaced exposures, changed marks after different entry anchors, NAV-dependent sizing/costs and permanent-halt timing all interact; gross improvement does not isolate an intrinsic signal improvement. There is no same-path causal attribution or significance claim here.

A11 compared with A01 raises the saved index compound return in9/18 configurations, including5/7 long-only smaller-loss cases and4/11 remaining configurations. This mixed result does not support a general claim that combining both controls always improves a waiting book.

The two motivating examples named before registration both have lower saved index compound returns under **every changed arm**:

| Previously motivating configuration | A00 | A10 | A01 | A11 |
|---|---:|---:|---:|---:|
|30-day long/short momentum |65.33%|44.94%|34.59%|26.11%|
|10/50 long/short MA |42.91%|4.99%|38.00%|15.10%|

These are stored full-clock compound returns of the daily mean of two separate sleeve returns, not new recomputations or a pooled executable account. The examples are retained because they motivated the registration, not because they rank best. For30-day momentum both sleeves still halt under every arm;10/50MA's ETH sleeve survives in the waiting arms while its BTC sleeve still halts. Better survival and a lower index return can coexist.

## Complete configuration-level mechanism denominator

Every entry is **active dates / waiting dates / halted sleeves / price stops**, across its two separately simulated sleeves. Each row-arm has2,480 sleeve-dates; halted-sleeve count is out of2. Other flat and halted-cash dates are retained in the saved artifacts and aggregate table above.

| Original configuration | A00 | A10 | A01 | A11 |
|---|---:|---:|---:|---:|
|tsmom_k7_ls|661 / 0 / 2 / 92|587 / 0 / 2 / 85|832 / 377 / 2 / 99|736 / 340 / 2 / 90|
|tsmom_k14_ls|918 / 0 / 2 / 82|893 / 0 / 2 / 81|1273 / 519 / 1 / 91|1273 / 519 / 1 / 91|
|tsmom_k30_ls|1564 / 0 / 2 / 85|1577 / 0 / 2 / 90|842 / 569 / 2 / 45|1048 / 583 / 2 / 60|
|tsmom_k90_ls|304 / 0 / 2 / 32|478 / 0 / 2 / 44|576 / 310 / 2 / 25|705 / 579 / 2 / 35|
|tsmom_k7_lo|313 / 0 / 2 / 45|190 / 0 / 2 / 32|24 / 2401 / 0 / 5|24 / 2401 / 0 / 5|
|tsmom_k14_lo|273 / 0 / 2 / 45|241 / 0 / 2 / 35|23 / 2289 / 0 / 7|23 / 2289 / 0 / 7|
|tsmom_k30_lo|212 / 0 / 2 / 41|149 / 0 / 2 / 29|13 / 2349 / 0 / 4|13 / 2349 / 0 / 4|
|tsmom_k90_lo|251 / 0 / 2 / 40|118 / 0 / 2 / 31|15 / 2427 / 0 / 2|15 / 2427 / 0 / 2|
|tsmom_k180_ls|127 / 0 / 2 / 38|115 / 0 / 2 / 31|794 / 535 / 2 / 17|554 / 488 / 2 / 14|
|macross_10_50_ls|696 / 0 / 2 / 26|663 / 0 / 2 / 34|820 / 863 / 1 / 34|767 / 824 / 1 / 34|
|macross_20_100_ls|779 / 0 / 2 / 36|301 / 0 / 2 / 27|489 / 395 / 2 / 9|489 / 342 / 2 / 8|
|macross_50_200_ls|187 / 0 / 2 / 37|469 / 0 / 2 / 31|649 / 1793 / 0 / 13|610 / 1355 / 2 / 8|
|macross_10_50_lo|194 / 0 / 2 / 36|151 / 0 / 2 / 29|13 / 2351 / 0 / 2|13 / 2351 / 0 / 2|
|macross_20_100_lo|251 / 0 / 2 / 40|118 / 0 / 2 / 31|15 / 2427 / 0 / 2|15 / 2427 / 0 / 2|
|macross_50_200_lo|251 / 0 / 2 / 40|118 / 0 / 2 / 31|15 / 2427 / 0 / 2|15 / 2427 / 0 / 2|
|donchian_n20_ls|528 / 0 / 2 / 41|566 / 0 / 2 / 42|250 / 680 / 2 / 28|465 / 1182 / 1 / 39|
|donchian_n55_ls|669 / 0 / 2 / 16|256 / 0 / 2 / 14|703 / 454 / 2 / 9|1335 / 790 / 1 / 14|
|xsmom_btc_eth_30d|695 / 0 / 2 / 80|760 / 0 / 2 / 92|393 / 642 / 2 / 39|518 / 857 / 2 / 57|

The first post-exit-only halt belongs to ETH30-day momentum in A00, BTC7-day momentum in A10, and BTC20-day Donchian in A01; A11 has none. The original permanent15% halt remains an absorbing state, rather than a restart opportunity. Differences in stopped tails are part of these fixed policies, so an apparent return change is not an equal-duration active-exposure comparison.

Limits remain unchanged: signed assumed funding0.0003 per day, synthetic linear/impact costs, stopped-day funding approximation, daily price proxies and threshold fills, sqrt252 sizing versus sqrt365 headline metrics, development reset and spent historical windows. Funding credits and charges are retained in net dollars; no observed all-in venue funding claim is made. Cost sensitivities and invalid-log shadows are separate saved diagnostics, not selected alternatives in this interpretation. No winner, validated strategy, fresh holdout claim or proposed parameter change follows from this descriptive comparison.
