# Saved dated-carry economic breakdown

This supplement aggregates the existing 48 entry cases and 432 conditional measurement rows. No quotes were fetched, calculator/collector rerun, scenarios generated, gates changed or financial ledger appended. Basis and fee decomposition uses only saved quantities, VWAPs and cash components; the twelve reference rows reconcile to saved profit within 1e-20 USDT.

Measurement ledger SHA-256: `7624f2809c604e51c72726fc375c3d27785675cc2992f031a913c2df813aa985`. Entries SHA-256: `cedaf343c7ec0fd529a4afa5e927344f3218f1a29c2240efc3adee016606d89f`. The [JSON supplement](supplemental-descriptive-check.json) retains exact values, denominators, formulas and all twelve source measurement IDs.

## Signs and reserve coverage

**All 432 modeled net-cash outcomes are negative: zero positive, zero exactly zero.** This holds across each asset, capital amount, reserve assumption, fee case, terminal-price level and adverse-exit assumption. The 0%, 3% and 5% benchmark excesses are also negative in all 432 rows each. The failure therefore exists before imposing a positive cash-benchmark hurdle.

All 48 entries are constrained by the capital budget; none reaches the displayed-depth capacity limit. More depth levels may still be consumed at larger size, worsening the average futures sale price even though depth capacity is not exhausted.

Terminal reserve is insufficient in **72/432 rows**, all under the one-third reserve and terminal index twice the initial spot ask: 24 entry cases, each repeated over the three spot/index mismatch assumptions. The same shortage repeats across those mismatch assumptions because spot disposal changes do not inject cash into the modeled isolated futures reserve. There are 0/216 terminal shortfalls in the full-reserve cases. This is a terminal scenario result only: positive terminal reserve does not prove maintenance compliance, pathwise margin survival, timely collateral transfers or liquidation protection.

## Fixed reference economics

These ranges span the three preserved snapshots for each asset/capital pair, using full reserve, the registered base fee assumptions, unchanged terminal index and no terminal sale/index mismatch. Capital is USDT already available, not priced fiat conversion. Percentages are returns on the entire capital budget; simple annualization is a scale descriptor, not evidence of repeated opportunities.

| Asset | Capital USDT | Net cash range USDT | Full-capital return range % | Simple annualized range % | Matched gross basis range bp | All-four-fee drag range bp |
|---|---:|---:|---:|---:|---:|---:|
| BTC | 1000 | -0.5780 to -0.5468 | -0.0578 to -0.0547 | -1.4392 to -1.3616 | 17.515 to 18.188 | 30.032 to 30.032 |
| BTC | 10000 | -6.4936 to -6.0496 | -0.0649 to -0.0605 | -1.6170 to -1.5064 | 16.828 to 17.736 | 30.020 to 30.021 |
| ETH | 1000 | -0.9028 to -0.8009 | -0.0903 to -0.0801 | -2.2480 to -1.9943 | 11.865 to 13.913 | 30.025 to 30.026 |
| ETH | 10000 | -9.8956 to -8.2563 | -0.0990 to -0.0826 | -2.4640 to -2.0559 | 10.197 to 13.480 | 30.016 to 30.017 |

Matched gross basis is `q*(future VWAP-spot VWAP)`, normalized by `q*spot VWAP` for basis points. Fee drag uses the BASE entry commission valued at entry VWAP, the cash futures entry fee, the saved expiry fee and the saved spot-sale fee, with the same denominator. The BASE fee is explanatory attribution; it is not subtracted twice from profit. The residual is preserved, and its price change is included in the reconciliation. In these twelve reference rows spot entry uses one ask level and terminal spot equals that ask, so the residual price-change contribution is zero; the residual's principal and sale fee remain accounted for.

## Why 10,000 does not rescue the observed setup

The spread being acquired is smaller than the registered proportional fee drag. Increasing capital does not amortize a dominant fixed cash setup charge: it principally increases the amount committed to the same negative unit economics. The larger futures sale also consumes deeper bids, lowering the matched gross basis in every paired snapshot relative to the 1,000 case. Reduced lot residuals or unused cash do not bridge the difference. Every larger-capital scenario remains negative, as do all one-third-reserve scenarios; using less reserve increases capital efficiency and collateral risk rather than creating a missing spread.

The warranted conclusion is **no-go for these two selected September 25 contracts at the captured books under the registered cost scenarios**, including the 1,000 and 10,000 capital choices. The four necessary screens fail; there is no positive case hidden elsewhere in the registered Cartesian grid. This does not establish that every maturity, date, account fee schedule or venue must fail. It also does not authorize searching those alternatives after observing this result. Exact fees, fee assets/rounding, settlement applicability, account availability, spot freshness and margin survival remain unverified, so these are conditional measurements rather than executable or realized outcomes. No strategy is validated.
