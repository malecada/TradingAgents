# Factor sizing and stop re-entry comparison — September 10, 2026

**Zero strategies are validated by this retrospective comparison.** All eighteen original factor configurations were retained in a fixed four-arm design. The comparison measures behavior on spent development history; it has no adoption gate or winner selection.

A00 preserves original behavior; A10 refreshes volatility sizing daily; A01 waits for the saved raw target to go flat or opposite after a price stop; A11 combines the changes. The permanent15% drawdown halt remains absorbing. A long-only target may never release the waiting policy, producing long cash periods.

## Fixed-arm overview

Counts refer to18 correlated configuration indices or36 separately simulated sleeves per arm. Active/waiting dates are sums over those sleeve books, not an executable portfolio. “Improved” is a descriptive point difference versus the same configuration’s control. A positive DD difference means a smaller drawdown. Flatness and lower exposure can reduce losses without establishing an edge.

| Arm | Complete indices /18 | Measured sleeves /36 | Positive return /measured | Positive SR /finite | Higher mean /paired | Smaller DD /paired | Active sleeve-days | Waiting sleeve-days | Price stops | Halted measured sleeves | Active dates risk >15% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A00 | 18 | 36 | 7/18 | 7/18 | — | — | 8873 | 0 | 852 | 36 | 4458 |
| A10 | 18 | 36 | 6/18 | 6/18 | 7/18 | 10/18 | 7750 | 0 | 789 | 36 | 0 |
| A01 | 18 | 36 | 10/18 | 10/18 | 14/18 | 14/18 | 7739 | 23808 | 433 | 18 | 4255 |
| A11 | 18 | 36 | 10/18 | 10/18 | 14/18 | 15/18 | 8618 | 24530 | 474 | 18 | 0 |

## All72 primary identities

Sharpe uses sqrt365, ddof1 and zero hurdle; mean is arithmetic annualized. Returns and drawdowns include all1,240 daily observations and initial NAV. BTC/ETH counts retain both sleeves. Undefined ratios remain unavailable; no cash dates are removed.

| Configuration | Arm | Status | SR | Annual mean | Compound return | Max DD | Active BTC/ETH | Waiting BTC/ETH | Unavailable/undefined reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tsmom_k7_ls | A00 | complete | 0.151 | 1.35% | 3.30% | -14.98% | 329/332 | 0/0 | — |
| tsmom_k7_ls | A10 | complete | 0.161 | 1.24% | 3.26% | -14.96% | 256/331 | 0/0 | — |
| tsmom_k7_ls | A01 | complete | 0.285 | 3.20% | 9.15% | -11.71% | 385/447 | 164/213 | — |
| tsmom_k7_ls | A11 | complete | 0.089 | 0.82% | 1.37% | -10.18% | 279/457 | 127/213 | — |
| tsmom_k14_ls | A00 | complete | 0.336 | 3.89% | 11.57% | -14.70% | 347/571 | 0/0 | — |
| tsmom_k14_ls | A10 | complete | 0.434 | 4.37% | 14.01% | -12.93% | 322/571 | 0/0 | — |
| tsmom_k14_ls | A01 | complete | 0.800 | 10.78% | 39.83% | -10.35% | 880/393 | 341/178 | — |
| tsmom_k14_ls | A11 | complete | 0.963 | 11.97% | 46.33% | -10.19% | 880/393 | 341/178 | — |
| tsmom_k30_ls | A00 | complete | 0.985 | 16.13% | 65.33% | -12.13% | 983/581 | 0/0 | — |
| tsmom_k30_ls | A10 | complete | 0.856 | 11.88% | 44.94% | -11.82% | 986/591 | 0/0 | — |
| tsmom_k30_ls | A01 | complete | 0.769 | 9.51% | 34.59% | -12.78% | 649/193 | 365/204 | — |
| tsmom_k30_ls | A11 | complete | 0.644 | 7.50% | 26.11% | -11.11% | 667/381 | 373/210 | — |
| tsmom_k90_ls | A00 | complete | -0.523 | -3.54% | -12.01% | -14.99% | 156/148 | 0/0 | — |
| tsmom_k90_ls | A10 | complete | -0.459 | -3.27% | -11.27% | -14.38% | 157/321 | 0/0 | — |
| tsmom_k90_ls | A01 | complete | 0.247 | 2.42% | 6.81% | -12.16% | 386/190 | 257/53 | — |
| tsmom_k90_ls | A11 | complete | 0.114 | 1.07% | 2.16% | -13.63% | 386/319 | 257/322 | — |
| tsmom_k7_lo | A00 | complete | -0.862 | -4.50% | -14.58% | -14.86% | 151/162 | 0/0 | — |
| tsmom_k7_lo | A10 | complete | -1.135 | -4.50% | -14.40% | -14.68% | 136/54 | 0/0 | — |
| tsmom_k7_lo | A01 | complete | -0.590 | -0.57% | -1.94% | -2.26% | 19/5 | 1187/1214 | — |
| tsmom_k7_lo | A11 | complete | -0.639 | -0.65% | -2.21% | -2.54% | 19/5 | 1187/1214 | — |
| tsmom_k14_lo | A00 | complete | -0.944 | -4.77% | -15.34% | -15.34% | 137/136 | 0/0 | — |
| tsmom_k14_lo | A10 | complete | -0.817 | -4.48% | -14.54% | -14.93% | 108/133 | 0/0 | — |
| tsmom_k14_lo | A01 | complete | -1.185 | -0.81% | -2.72% | -2.72% | 12/11 | 1144/1145 | — |
| tsmom_k14_lo | A11 | complete | -1.220 | -0.90% | -3.01% | -3.01% | 12/11 | 1144/1145 | — |
| tsmom_k30_lo | A00 | complete | -1.276 | -4.21% | -13.49% | -14.65% | 122/90 | 0/0 | — |
| tsmom_k30_lo | A10 | complete | -1.256 | -4.06% | -13.05% | -14.20% | 93/56 | 0/0 | — |
| tsmom_k30_lo | A01 | complete | -0.618 | -0.46% | -1.55% | -2.87% | 5/8 | 1136/1213 | — |
| tsmom_k30_lo | A11 | complete | -0.623 | -0.45% | -1.52% | -2.82% | 5/8 | 1136/1213 | — |
| tsmom_k90_lo | A00 | complete | -0.935 | -4.06% | -13.17% | -14.96% | 161/90 | 0/0 | — |
| tsmom_k90_lo | A10 | complete | -1.298 | -4.23% | -13.53% | -15.29% | 62/56 | 0/0 | — |
| tsmom_k90_lo | A01 | complete | -0.161 | -0.19% | -0.68% | -2.73% | 7/8 | 1214/1213 | — |
| tsmom_k90_lo | A11 | complete | -0.157 | -0.19% | -0.66% | -2.69% | 7/8 | 1214/1213 | — |
| tsmom_k180_ls | A00 | complete | -1.450 | -4.13% | -13.22% | -15.01% | 64/63 | 0/0 | — |
| tsmom_k180_ls | A10 | complete | -1.319 | -4.24% | -13.56% | -15.32% | 59/56 | 0/0 | — |
| tsmom_k180_ls | A01 | complete | 0.812 | 7.75% | 28.11% | -7.99% | 324/470 | 109/426 | — |
| tsmom_k180_ls | A11 | complete | 0.342 | 2.44% | 7.72% | -8.51% | 307/247 | 106/382 | — |
| macross_10_50_ls | A00 | complete | 0.859 | 11.38% | 42.91% | -11.79% | 462/234 | 0/0 | — |
| macross_10_50_ls | A10 | complete | 0.203 | 1.85% | 4.99% | -15.25% | 383/280 | 0/0 | — |
| macross_10_50_ls | A01 | complete | 0.712 | 10.56% | 38.00% | -14.54% | 166/654 | 296/567 | — |
| macross_10_50_ls | A11 | complete | 0.540 | 4.48% | 15.10% | -12.30% | 113/654 | 257/567 | — |
| macross_20_100_ls | A00 | complete | -0.021 | -0.19% | -1.99% | -14.62% | 630/149 | 0/0 | — |
| macross_20_100_ls | A10 | complete | -0.480 | -2.79% | -9.57% | -15.81% | 150/151 | 0/0 | — |
| macross_20_100_ls | A01 | complete | 0.354 | 3.28% | 10.17% | -13.11% | 300/189 | 341/54 | — |
| macross_20_100_ls | A11 | complete | 0.147 | 1.14% | 2.90% | -14.46% | 272/217 | 141/201 | — |
| macross_50_200_ls | A00 | complete | -0.967 | -4.00% | -12.97% | -14.77% | 121/66 | 0/0 | — |
| macross_50_200_ls | A10 | complete | -0.265 | -1.79% | -6.62% | -13.89% | 413/56 | 0/0 | — |
| macross_50_200_ls | A01 | complete | 0.327 | 2.84% | 8.73% | -11.53% | 339/310 | 882/911 | — |
| macross_50_200_ls | A11 | complete | 0.393 | 3.67% | 11.62% | -16.44% | 315/295 | 668/687 | — |
| macross_10_50_lo | A00 | complete | -1.028 | -3.96% | -12.80% | -13.97% | 104/90 | 0/0 | — |
| macross_10_50_lo | A10 | complete | -1.196 | -3.95% | -12.72% | -13.88% | 95/56 | 0/0 | — |
| macross_10_50_lo | A01 | complete | -0.225 | -0.22% | -0.77% | -2.10% | 5/8 | 1138/1213 | — |
| macross_10_50_lo | A11 | complete | -0.191 | -0.18% | -0.63% | -1.95% | 5/8 | 1138/1213 | — |
| macross_20_100_lo | A00 | complete | -0.935 | -4.06% | -13.17% | -14.96% | 161/90 | 0/0 | — |
| macross_20_100_lo | A10 | complete | -1.298 | -4.23% | -13.53% | -15.29% | 62/56 | 0/0 | — |
| macross_20_100_lo | A01 | complete | -0.161 | -0.19% | -0.68% | -2.73% | 7/8 | 1214/1213 | — |
| macross_20_100_lo | A11 | complete | -0.157 | -0.19% | -0.66% | -2.69% | 7/8 | 1214/1213 | — |
| macross_50_200_lo | A00 | complete | -0.935 | -4.06% | -13.17% | -14.96% | 161/90 | 0/0 | — |
| macross_50_200_lo | A10 | complete | -1.298 | -4.23% | -13.53% | -15.29% | 62/56 | 0/0 | — |
| macross_50_200_lo | A01 | complete | -0.161 | -0.19% | -0.68% | -2.73% | 7/8 | 1214/1213 | — |
| macross_50_200_lo | A11 | complete | -0.157 | -0.19% | -0.66% | -2.69% | 7/8 | 1214/1213 | — |
| donchian_n20_ls | A00 | complete | 0.288 | 2.56% | 7.64% | -15.03% | 269/259 | 0/0 | — |
| donchian_n20_ls | A10 | complete | 0.136 | 1.05% | 2.59% | -14.69% | 273/293 | 0/0 | — |
| donchian_n20_ls | A01 | complete | 0.152 | 1.36% | 3.34% | -14.80% | 95/155 | 289/391 | — |
| donchian_n20_ls | A11 | complete | 0.353 | 2.78% | 8.76% | -14.03% | 148/317 | 430/752 | — |
| donchian_n55_ls | A00 | complete | 0.361 | 3.45% | 10.72% | -14.38% | 564/105 | 0/0 | — |
| donchian_n55_ls | A10 | complete | -0.321 | -1.83% | -6.55% | -15.64% | 142/114 | 0/0 | — |
| donchian_n55_ls | A01 | complete | 0.480 | 6.22% | 20.07% | -15.50% | 448/255 | 185/269 | — |
| donchian_n55_ls | A11 | complete | 0.751 | 9.74% | 35.30% | -13.51% | 779/556 | 405/385 | — |
| xsmom_btc_eth_30d | A00 | complete | 0.446 | 3.46% | 11.32% | -7.46% | 244/451 | 0/0 | — |
| xsmom_btc_eth_30d | A10 | complete | 0.268 | 1.68% | 5.17% | -7.69% | 244/516 | 0/0 | — |
| xsmom_btc_eth_30d | A01 | complete | -0.099 | -0.61% | -2.70% | -12.04% | 242/151 | 412/230 | — |
| xsmom_btc_eth_30d | A11 | complete | -0.185 | -1.12% | -4.32% | -12.27% | 217/301 | 411/446 | — |

## All54 changes versus their original controls

Percentage-valued differences below are percentage points. These are paired full-calendar descriptive differences; there are no p-values, bootstrap selection or independent replication claims. The complete factorial contrasts and sleeve-level cost/exposure/risk differences are retained in result.json.

| Configuration | Arm | ΔSR | Δannual mean | Δcompound return | Δmax DD |
| --- | --- | --- | --- | --- | --- |
| tsmom_k7_ls | A10 | 0.009 | -0.11% | -0.03% | 0.03% |
| tsmom_k7_ls | A01 | 0.134 | 1.85% | 5.85% | 3.27% |
| tsmom_k7_ls | A11 | -0.062 | -0.53% | -1.93% | 4.81% |
| tsmom_k14_ls | A10 | 0.098 | 0.47% | 2.45% | 1.77% |
| tsmom_k14_ls | A01 | 0.464 | 6.88% | 28.27% | 4.35% |
| tsmom_k14_ls | A11 | 0.627 | 8.08% | 34.76% | 4.51% |
| tsmom_k30_ls | A10 | -0.129 | -4.25% | -20.39% | 0.31% |
| tsmom_k30_ls | A01 | -0.216 | -6.63% | -30.73% | -0.65% |
| tsmom_k30_ls | A11 | -0.341 | -8.63% | -39.21% | 1.02% |
| tsmom_k90_ls | A10 | 0.064 | 0.27% | 0.74% | 0.61% |
| tsmom_k90_ls | A01 | 0.770 | 5.95% | 18.82% | 2.83% |
| tsmom_k90_ls | A11 | 0.637 | 4.60% | 14.17% | 1.36% |
| tsmom_k7_lo | A10 | -0.273 | 0.00% | 0.18% | 0.18% |
| tsmom_k7_lo | A01 | 0.273 | 3.93% | 12.64% | 12.59% |
| tsmom_k7_lo | A11 | 0.224 | 3.85% | 12.36% | 12.32% |
| tsmom_k14_lo | A10 | 0.127 | 0.30% | 0.79% | 0.41% |
| tsmom_k14_lo | A01 | -0.241 | 3.96% | 12.61% | 12.61% |
| tsmom_k14_lo | A11 | -0.276 | 3.87% | 12.32% | 12.32% |
| tsmom_k30_lo | A10 | 0.020 | 0.15% | 0.44% | 0.45% |
| tsmom_k30_lo | A01 | 0.658 | 3.75% | 11.94% | 11.78% |
| tsmom_k30_lo | A11 | 0.652 | 3.76% | 11.97% | 11.82% |
| tsmom_k90_lo | A10 | -0.364 | -0.16% | -0.36% | -0.33% |
| tsmom_k90_lo | A01 | 0.774 | 3.87% | 12.49% | 12.23% |
| tsmom_k90_lo | A11 | 0.778 | 3.87% | 12.51% | 12.28% |
| tsmom_k180_ls | A10 | 0.131 | -0.11% | -0.35% | -0.32% |
| tsmom_k180_ls | A01 | 2.263 | 11.88% | 41.33% | 7.02% |
| tsmom_k180_ls | A11 | 1.793 | 6.58% | 20.94% | 6.50% |
| macross_10_50_ls | A10 | -0.655 | -9.53% | -37.92% | -3.46% |
| macross_10_50_ls | A01 | -0.146 | -0.82% | -4.91% | -2.74% |
| macross_10_50_ls | A11 | -0.318 | -6.90% | -27.80% | -0.51% |
| macross_20_100_ls | A10 | -0.460 | -2.60% | -7.57% | -1.19% |
| macross_20_100_ls | A01 | 0.375 | 3.47% | 12.16% | 1.51% |
| macross_20_100_ls | A11 | 0.168 | 1.33% | 4.89% | 0.16% |
| macross_50_200_ls | A10 | 0.701 | 2.21% | 6.35% | 0.88% |
| macross_50_200_ls | A01 | 1.293 | 6.84% | 21.70% | 3.24% |
| macross_50_200_ls | A11 | 1.360 | 7.67% | 24.59% | -1.67% |
| macross_10_50_lo | A10 | -0.167 | 0.01% | 0.08% | 0.09% |
| macross_10_50_lo | A01 | 0.804 | 3.74% | 12.04% | 11.87% |
| macross_10_50_lo | A11 | 0.838 | 3.78% | 12.17% | 12.03% |
| macross_20_100_lo | A10 | -0.364 | -0.16% | -0.36% | -0.33% |
| macross_20_100_lo | A01 | 0.774 | 3.87% | 12.49% | 12.23% |
| macross_20_100_lo | A11 | 0.778 | 3.87% | 12.51% | 12.28% |
| macross_50_200_lo | A10 | -0.364 | -0.16% | -0.36% | -0.33% |
| macross_50_200_lo | A01 | 0.774 | 3.87% | 12.49% | 12.23% |
| macross_50_200_lo | A11 | 0.778 | 3.87% | 12.51% | 12.28% |
| donchian_n20_ls | A10 | -0.153 | -1.51% | -5.05% | 0.34% |
| donchian_n20_ls | A01 | -0.136 | -1.19% | -4.30% | 0.23% |
| donchian_n20_ls | A11 | 0.064 | 0.22% | 1.12% | 1.00% |
| donchian_n55_ls | A10 | -0.682 | -5.29% | -17.27% | -1.26% |
| donchian_n55_ls | A01 | 0.119 | 2.76% | 9.35% | -1.11% |
| donchian_n55_ls | A11 | 0.391 | 6.28% | 24.58% | 0.87% |
| xsmom_btc_eth_30d | A10 | -0.178 | -1.78% | -6.15% | -0.22% |
| xsmom_btc_eth_30d | A01 | -0.545 | -4.07% | -14.02% | -4.57% |
| xsmom_btc_eth_30d | A11 | -0.631 | -4.57% | -15.64% | -4.80% |

## Accounting convention forensics

Of72 registered shadows, 72 are complete. Positive/nonpositive Sharpe labels change in 1/72 finite comparisons; compound-return labels change in 1/72. Among54 registered direct contrasts, positive/nonpositive ΔSharpe ordering changes in 2/54 finite comparisons and Δcompound-return ordering in 4/54. Undefined ratios are excluded only from the corresponding finite diagnostic denominator, while their identities remain in the tables. Invalid-log arithmetic is never used to choose a policy. Exposure, stops, funding and fees remain frozen in these shadows.

## Complete evidence and limits

[Cost sensitivities](COST_SENSITIVITY.md) retain all288 index evaluation identities. [Primary sleeve diagnostics](SLEEVE_DIAGNOSTICS.md) retain all144 primary sleeve identities. [Fixed periods](PERIODS.md) retain216 periods and [invalid convention shadows](CONVENTION_SHADOWS.md) retain72 identities. Result JSON preserves all576 registered sleeve books with explicit unavailable reasons where applicable; available trace/daily/stop artifacts retain detailed component attribution.

Independent verification passed 13,780,216 assertions across 576/576 traces, 144/144 original control traces and 72/72 original control return frames. The checker reconstructs every charged leg and target/stop transition from saved evidence without replaying policies. Source: `2dfb047d5c2f2ff821706736eb9f5508a14e7304`. Result SHA-256: `245ad6a30022a4ab7f115b1acb52d33dc5537ce43d8c0b6850e5ec25391d1006`.

The daily price proxies, assumed signed3bp/day funding, threshold stop fills and separate-sleeve index remain limitations. Cost variants each have their own stops and halt dates. Reduced risk exposure is not proof of executable alpha. The old holdout remains spent; [the prospective validation plan](fresh-validation-plan.md) requires a separately frozen candidate/family, venue economics, power/gates and a future observation window. No provider contact, paid-data purchase, paper restart or VPS deployment occurred.
