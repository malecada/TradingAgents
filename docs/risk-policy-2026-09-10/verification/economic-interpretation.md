# Economic interpretation of the fixed factor risk-policy comparison

Read-only interpretation of the saved September 10, 2026 result. No strategy replay, return calculation, refit, resampling, new hypothesis, selection or source change was performed for this note. Tables format existing scalar outputs and registered contrasts; counts describe the retained identities. Independent arithmetic and preservation checks are separate.

## Evidence and scope

- [Frozen result](../../../data/risk-policy/2026-09-10/results/result.json): SHA-256 `245ad6a30022a4ab7f115b1acb52d33dc5537ce43d8c0b6850e5ec25391d1006`.
- Execution source: `2dfb047d5c2f2ff821706736eb9f5508a14e7304`. Registered experiment: `risk_policy_2026_09_10`; [charter](../charter.md).
- All 72 identities, 288 index evaluations, 576 separate sleeve books and 72 frozen-exposure invalid-log shadows are complete. All 144 control traces and 72 control return frames passed the registered parity comparison. These controls preserve the earlier corrected execution on `27640882822d812c6d0478340495e033a11d3915`; they do not reinstate superseded historical accounting.
- The result reports 72 appended financial identities, preserving the 748-row prefix and yielding 820 rows. The exact recorded ledger hashes are reproduced below. This note does not independently verify ledger bytes.
- Every return stream retains all 1,240 daily dates, November 8, 2021 through March 31, 2025, including absorbing cash tails. The index is the daily mean of two separate sleeve returns, not an executable pooled account.

A00 retains saved sizing and immediate re-entry; A10 resizes daily with immediate re-entry; A01 retains saved sizing and waits for a new saved target episode; A11 combines daily sizing and waiting. These are four fixed policies over all eighteen configurations. The 54 changed policies are new retrospective counterfactuals, not repaired A00 outcomes or independently validated strategies.

## Economic conclusion

Waiting changes several unfavorable development paths and reduces repeated stop exposure. Its economic benefit is heterogeneous: it also removes gains from the prior 30-day long/short momentum and 10/50 moving-average references, and turns the cross-sectional momentum index negative. Daily causal resizing satisfies its engineering risk constraint but does not produce a broad improvement in return. Combining the two changes does not uniformly improve on waiting alone.

The result makes the identified stop/re-entry mechanism more credible as an explanation of particular historical paths. It does not make a historical lead validated, overturn any prior gate, establish a model-class advantage, or select a policy. Exposure suppression, avoided early halts, costs and later opportunities interact. The positive cases remain descriptions of spent development history under proxy prices, threshold fills and assumed signed funding.

## Complete denominators and directional counts

A positive Sharpe is a zero-hurdle point descriptor; it is not a success gate. No full-clock index Sharpe is null in these 288 evaluations. Positive compound-return counts need not match positive mean-return/Sharpe counts.

| Arm | Primary positive SR | Zero-execution positive SR | Double-execution positive SR | Zero-funding positive SR | Primary positive compound return |
|---|---:|---:|---:|---:|---:|
| A00 | 7/18 | 8/18 | 6/18 | 7/18 | 7/18 |
| A10 | 6/18 | 6/18 | 5/18 | 6/18 | 6/18 |
| A01 | 10/18 | 10/18 | 9/18 | 10/18 | 10/18 |
| A11 | 10/18 | 10/18 | 9/18 | 10/18 | 10/18 |

Across all 72 identities, positive SR counts are 33 primary, 34 zero-execution, 29 double-execution and 33 zero-funding. Positive compound-return counts are 33, 33, 29 and 32, respectively. Every denominator includes the eighteen repeated controls. The long-only TSMOM90, MA20/100 and MA50/200 identities have identical observed streams in this grid; their separate registration does not provide independent confirmations.

The following primary contrasts are counted against each configuration's own A00. For maximum drawdown, a positive difference is shallower because the stored drawdown is negative. These are descriptive counts, with no p-values or multiplicity-adjusted adoption claim.

| Changed arm | Higher mean return | Higher SR | Higher compound return | Shallower drawdown | Lower realized volatility | Higher mean and shallower drawdown |
|---|---:|---:|---:|---:|---:|---:|
| A10 | 7/18 | 7/18 | 7/18 | 10/18 | 14/18 | 7/18 |
| A01 | 14/18 | 13/18 | 14/18 | 14/18 | 9/18 | 13/18 |
| A11 | 14/18 | 13/18 | 14/18 | 15/18 | 12/18 | 13/18 |

The exposure distinction is material. Each row below sums counts across 36 separately accounted primary sleeves, hence 44,640 sleeve-days per arm. It does not pool sleeve dollars or imply independent observations.

| Arm | Sleeves ever halted | Active days | Waiting days | Permanently halted cash days | Other flat days | Price stops | Applied risk proxy above 0.15 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A00 | 36/36 | 8,873 | 0 | 34,625 | 1,142 | 852 | 4,458 |
| A10 | 36/36 | 7,750 | 0 | 35,748 | 1,142 | 789 | 0 |
| A01 | 18/36 | 7,739 | 23,808 | 11,836 | 1,257 | 433 | 4,255 |
| A11 | 18/36 | 8,618 | 24,530 | 10,176 | 1,316 | 474 | 0 |

The daily arms have zero applied-budget exceedances under the registered lagged-volatility proxy. This is an engineering constraint on each admitted target, not a guarantee of subsequent realized portfolio volatility or a hard intrabar loss bound. The waiting arms each retain eighteen halted sleeves and lengthy blocked cash periods; the remaining sleeves are not thereby proven economically viable. All seven long-only configurations remain negative under every arm and cost scenario. Their smaller losses in waiting arms are substantially capital-preservation outcomes from suppressed exposure.

## All eighteen primary paired comparisons

Each table entry is **change in arithmetic annual mean (percentage points) / change in Sharpe / change in maximum drawdown (percentage points)** against the same row's A00. Annual mean is mean daily simple return multiplied by 365, not CAGR. Positive drawdown change means shallower drawdown. Full unrounded exposure, risk, turnover, cost, sleeve and period contrasts remain in `direct_contrasts` and `factorial_contrasts` in the immutable result.

| Configuration | A10 minus A00 | A01 minus A00 | A11 minus A00 |
|---|---:|---:|---:|
| `tsmom_k7_ls` | -0.1081 / +0.0094 / +0.0265 | +1.8479 / +0.1342 / +3.2740 | -0.5311 / -0.0622 / +4.8074 |
| `tsmom_k14_ls` | +0.4741 / +0.0975 / +1.7734 | +6.8848 / +0.4641 / +4.3455 | +8.0840 / +0.6270 / +4.5111 |
| `tsmom_k30_ls` | -4.2522 / -0.1287 / +0.3113 | -6.6284 / -0.2162 / -0.6519 | -8.6315 / -0.3407 / +1.0243 |
| `tsmom_k90_ls` | +0.2709 / +0.0637 / +0.6095 | +5.9548 / +0.7696 / +2.8257 | +4.6038 / +0.6366 / +1.3557 |
| `tsmom_k7_lo` | +0.0037 / -0.2725 / +0.1769 | +3.9289 / +0.2726 / +12.5938 | +3.8475 / +0.2236 / +12.3221 |
| `tsmom_k14_lo` | +0.2974 / +0.1270 / +0.4111 | +3.9628 / -0.2415 / +12.6150 | +3.8746 / -0.2759 / +12.3227 |
| `tsmom_k30_lo` | +0.1465 / +0.0201 / +0.4461 | +3.7524 / +0.6582 / +11.7756 | +3.7622 / +0.6523 / +11.8244 |
| `tsmom_k90_lo` | -0.1628 / -0.3638 / -0.3287 | +3.8688 / +0.7737 / +12.2326 | +3.8743 / +0.7775 / +12.2759 |
| `tsmom_k180_ls` | -0.1062 / +0.1307 / -0.3164 | +11.8768 / +2.2626 / +7.0205 | +6.5760 / +1.7925 / +6.4950 |
| `macross_10_50_ls` | -9.5336 / -0.6555 / -3.4575 | -0.8153 / -0.1463 / -2.7423 | -6.8960 / -0.3182 / -0.5050 |
| `macross_20_100_ls` | -2.6047 / -0.4596 / -1.1944 | +3.4652 / +0.3746 / +1.5056 | +1.3293 / +0.1678 / +0.1601 |
| `macross_50_200_ls` | +2.2137 / +0.7014 / +0.8761 | +6.8426 / +1.2935 / +3.2435 | +7.6734 / +1.3598 / -1.6688 |
| `macross_10_50_lo` | +0.0071 / -0.1671 / +0.0918 | +3.7366 / +0.8039 / +11.8740 | +3.7775 / +0.8378 / +12.0276 |
| `macross_20_100_lo` | -0.1628 / -0.3638 / -0.3287 | +3.8688 / +0.7737 / +12.2326 | +3.8743 / +0.7775 / +12.2759 |
| `macross_50_200_lo` | -0.1628 / -0.3638 / -0.3287 | +3.8688 / +0.7737 / +12.2326 | +3.8743 / +0.7775 / +12.2759 |
| `donchian_n20_ls` | -1.5068 / -0.1527 / +0.3436 | -1.1916 / -0.1361 / +0.2341 | +0.2238 / +0.0643 / +0.9992 |
| `donchian_n55_ls` | -5.2856 / -0.6821 / -1.2573 | +2.7643 / +0.1188 / -1.1125 | +6.2831 / +0.3905 / +0.8723 |
| `xsmom_btc_eth_30d` | -1.7768 / -0.1784 / -0.2244 | -4.0694 / -0.5451 / -4.5722 | -4.5737 / -0.6308 / -4.8035 |

Mean and Sharpe can move in opposite directions: TSMOM7-LS A10 has a slightly higher SR but a lower mean, while TSMOM14-LO waiting has much smaller losses but a more negative SR. A smaller denominator is not an economic gain by itself. MA50/200-LS A11 gains mean and SR while its drawdown deepens from −14.7702% to −16.4390%.

## Fixed cost sensitivities across all cells

Primary assumes fee 4 bp, slippage 5 bp, spread 1 bp and quadratic impact coefficient 0.00005, plus signed assumed funding 3 bp/day on opening exposure. Positive funding charges longs and credits shorts. The stopped-day funding approximation remains. Zero execution removes all four execution charges; double execution doubles all four. Zero funding removes only funding. Each scenario has its own stops and absorbing halt; a cost sensitivity is not a subtraction from the primary return stream.

Zero execution raises SR in all 72 identities, but changes the sign only for MA20/100-LS A00: −0.020635 to +0.002860. That zero-execution index still has a negative compound return. Thus removing assumed execution costs does not broadly rescue the negative configurations.

Double execution lowers SR in 65 identities and raises it in seven. The exceptions are A10 for TSMOM90-LO, TSMOM180-LS, MA20/100-LS, MA20/100-LO, MA50/200-LO and Donchian55-LS, and A11 for MA50/200-LS. These are different realized policy/halt paths, not evidence that a higher fee is beneficial holding behavior fixed. Four positive-primary identities become nonpositive: Donchian20-LS A00/A10 and TSMOM7-LS A01/A11.

Zero funding raises SR in 51 identities and lowers it in 21, with no SR sign changes. Funding removal is not uniformly favorable because funding is signed and the halt path is recomputed. Donchian20-LS A00 falls from SR +0.288407 to +0.004368, with a negative compound return under zero funding. This is a concrete dependence on the assumed carry/path, rather than observed venue funding evidence.

The complete cost and convention table follows in original configuration/arm order. `P`, `Z`, `D`, `F` are primary, zero execution, double execution and zero funding SR. `L` is the invalid frozen-exposure log shadow, included only to expose accounting distortion. Final columns are primary compound return and maximum drawdown in percent. The immutable result also retains complete cost-case means, volatility, drawdown, periods, and separate sleeve components; no cost-case outcome was selected for a headline.

| Configuration | Arm | P SR | Z SR | D SR | F SR | Invalid L SR | P total % | P DD % |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `tsmom_k7_ls` | A00 | +0.151295 | +0.243534 | +0.070722 | +0.123086 | +0.249939 | +3.2972 | -14.9839 |
| `tsmom_k7_ls` | A10 | +0.160706 | +0.326427 | +0.058226 | +0.139108 | +0.249451 | +3.2630 | -14.9573 |
| `tsmom_k7_ls` | A01 | +0.285469 | +0.380576 | -0.051921 | +0.277274 | +0.351745 | +9.1454 | -11.7099 |
| `tsmom_k7_ls` | A11 | +0.089048 | +0.339425 | -0.001687 | +0.071287 | +0.162364 | +1.3687 | -10.1765 |
| `tsmom_k14_ls` | A00 | +0.336140 | +0.421911 | +0.293567 | +0.351327 | +0.400183 | +11.5657 | -14.7000 |
| `tsmom_k14_ls` | A10 | +0.433655 | +0.509166 | +0.360802 | +0.415852 | +0.496486 | +14.0144 | -12.9266 |
| `tsmom_k14_ls` | A01 | +0.800252 | +0.920594 | +0.687423 | +0.798697 | +0.830734 | +39.8339 | -10.3545 |
| `tsmom_k14_ls` | A11 | +0.963145 | +1.106661 | +0.820789 | +0.968602 | +0.985216 | +46.3288 | -10.1889 |
| `tsmom_k30_ls` | A00 | +0.985098 | +1.070207 | +0.906936 | +1.010040 | +0.975064 | +65.3250 | -12.1329 |
| `tsmom_k30_ls` | A10 | +0.856372 | +0.976313 | +0.251053 | +0.860342 | +0.863477 | +44.9367 | -11.8216 |
| `tsmom_k30_ls` | A01 | +0.768890 | +0.840252 | +0.696035 | +0.770033 | +0.775176 | +34.5944 | -12.7847 |
| `tsmom_k30_ls` | A11 | +0.644436 | +0.731291 | +0.567499 | +0.650597 | +0.642906 | +26.1142 | -11.1086 |
| `tsmom_k90_ls` | A00 | -0.522876 | -0.518068 | -0.543050 | -0.522547 | -0.446339 | -12.0102 | -14.9880 |
| `tsmom_k90_ls` | A10 | -0.459140 | -0.410198 | -0.634247 | -0.607519 | -0.338748 | -11.2676 | -14.3785 |
| `tsmom_k90_ls` | A01 | +0.246697 | +0.267588 | +0.211418 | +0.230822 | +0.343836 | +6.8100 | -12.1622 |
| `tsmom_k90_ls` | A11 | +0.113769 | +0.142142 | +0.082210 | +0.094270 | +0.195725 | +2.1624 | -13.6323 |
| `tsmom_k7_lo` | A00 | -0.862231 | -0.841777 | -1.086680 | -0.829690 | -0.985146 | -14.5769 | -14.8575 |
| `tsmom_k7_lo` | A10 | -1.134749 | -1.085009 | -1.151165 | -1.096298 | -1.236073 | -14.3994 | -14.6806 |
| `tsmom_k7_lo` | A01 | -0.589612 | -0.553995 | -0.624491 | -0.563253 | -0.625993 | -1.9415 | -2.2637 |
| `tsmom_k7_lo` | A11 | -0.638597 | -0.601638 | -0.674734 | -0.612340 | -0.673304 | -2.2141 | -2.5354 |
| `tsmom_k14_lo` | A00 | -0.943819 | -0.922904 | -0.959625 | -0.929167 | -1.056514 | -15.3376 | -15.3376 |
| `tsmom_k14_lo` | A10 | -0.816825 | -0.782929 | -0.835213 | -0.781694 | -0.919820 | -14.5428 | -14.9265 |
| `tsmom_k14_lo` | A01 | -1.185277 | -1.145620 | -1.221092 | -1.158851 | -1.200301 | -2.7226 | -2.7226 |
| `tsmom_k14_lo` | A11 | -1.219680 | -1.181990 | -1.253431 | -1.194499 | -1.233291 | -3.0149 | -3.0149 |
| `tsmom_k30_lo` | A00 | -1.275786 | -0.929114 | -1.469124 | -1.113774 | -1.408628 | -13.4864 | -14.6485 |
| `tsmom_k30_lo` | A10 | -1.255729 | -1.233752 | -1.296802 | -1.227152 | -1.361397 | -13.0485 | -14.2024 |
| `tsmom_k30_lo` | A01 | -0.617602 | -0.586217 | -0.647697 | -0.602109 | -0.643724 | -1.5504 | -2.8730 |
| `tsmom_k30_lo` | A11 | -0.623486 | -0.588991 | -0.656449 | -0.607422 | -0.650103 | -1.5172 | -2.8242 |
| `tsmom_k90_lo` | A00 | -0.934554 | -0.759496 | -1.088863 | -0.870511 | -1.050802 | -13.1711 | -14.9650 |
| `tsmom_k90_lo` | A10 | -1.298315 | -1.187614 | -1.292118 | -1.258064 | -1.348002 | -13.5287 | -15.2937 |
| `tsmom_k90_lo` | A01 | -0.160849 | -0.149849 | -0.171745 | -0.148446 | -0.190440 | -0.6804 | -2.7324 |
| `tsmom_k90_lo` | A11 | -0.157020 | -0.145960 | -0.167977 | -0.144554 | -0.186395 | -0.6616 | -2.6891 |
| `tsmom_k180_ls` | A00 | -1.450072 | -1.436519 | -1.471245 | -1.441491 | -1.495246 | -13.2152 | -15.0082 |
| `tsmom_k180_ls` | A10 | -1.319420 | -1.315041 | -1.314493 | -1.294528 | -1.364995 | -13.5604 | -15.3247 |
| `tsmom_k180_ls` | A01 | +0.812491 | +0.850052 | +0.770757 | +0.822113 | +0.813667 | +28.1110 | -7.9877 |
| `tsmom_k180_ls` | A11 | +0.342465 | +0.402367 | +0.282950 | +0.413124 | +0.398254 | +7.7226 | -8.5132 |
| `macross_10_50_ls` | A00 | +0.858507 | +0.895914 | +0.821087 | +0.851473 | +0.931352 | +42.9058 | -11.7940 |
| `macross_10_50_ls` | A10 | +0.203027 | +0.253923 | +0.141494 | +0.192325 | +0.314240 | +4.9891 | -15.2515 |
| `macross_10_50_ls` | A01 | +0.712246 | +0.752215 | +0.672297 | +0.750354 | +0.661214 | +37.9987 | -14.5363 |
| `macross_10_50_ls` | A11 | +0.540271 | +0.719537 | +0.471408 | +0.610438 | +0.512021 | +15.1025 | -12.2990 |
| `macross_20_100_ls` | A00 | -0.020635 | +0.002860 | -0.149509 | -0.048346 | +0.069505 | -1.9923 | -14.6155 |
| `macross_20_100_ls` | A10 | -0.480280 | -0.429449 | -0.473862 | -0.451362 | -0.406143 | -9.5655 | -15.8100 |
| `macross_20_100_ls` | A01 | +0.353971 | +0.866907 | +0.331386 | +0.297805 | +0.529807 | +10.1720 | -13.1100 |
| `macross_20_100_ls` | A11 | +0.147118 | +0.158740 | +0.114243 | +0.150593 | +0.322391 | +2.9018 | -14.4555 |
| `macross_50_200_ls` | A00 | -0.966855 | -0.106932 | -0.986621 | -0.990514 | -0.947620 | -12.9721 | -14.7702 |
| `macross_50_200_ls` | A10 | -0.265489 | -0.219985 | -0.301249 | -0.246417 | -0.148507 | -6.6232 | -13.8941 |
| `macross_50_200_ls` | A01 | +0.326632 | +0.348262 | +0.304998 | +0.406582 | +0.199231 | +8.7263 | -11.5267 |
| `macross_50_200_ls` | A11 | +0.392955 | +0.419517 | +0.448129 | +0.476799 | +0.271689 | +11.6169 | -16.4390 |
| `macross_10_50_lo` | A00 | -1.028438 | -0.758636 | -1.215575 | -0.877543 | -1.153257 | -12.8029 | -13.9743 |
| `macross_10_50_lo` | A10 | -1.195587 | -1.180528 | -1.229247 | -1.167904 | -1.302939 | -12.7243 | -13.8825 |
| `macross_10_50_lo` | A01 | -0.224548 | -0.210163 | -0.238694 | -0.210539 | -0.260330 | -0.7672 | -2.1003 |
| `macross_10_50_lo` | A11 | -0.190665 | -0.175659 | -0.205447 | -0.176362 | -0.227191 | -0.6280 | -1.9467 |
| `macross_20_100_lo` | A00 | -0.934554 | -0.759496 | -1.088863 | -0.870511 | -1.050802 | -13.1711 | -14.9650 |
| `macross_20_100_lo` | A10 | -1.298315 | -1.187614 | -1.292118 | -1.258064 | -1.348002 | -13.5287 | -15.2937 |
| `macross_20_100_lo` | A01 | -0.160849 | -0.149849 | -0.171745 | -0.148446 | -0.190440 | -0.6804 | -2.7324 |
| `macross_20_100_lo` | A11 | -0.157020 | -0.145960 | -0.167977 | -0.144554 | -0.186395 | -0.6616 | -2.6891 |
| `macross_50_200_lo` | A00 | -0.934554 | -0.759496 | -1.088863 | -0.870511 | -1.050802 | -13.1711 | -14.9650 |
| `macross_50_200_lo` | A10 | -1.298315 | -1.187614 | -1.292118 | -1.258064 | -1.348002 | -13.5287 | -15.2937 |
| `macross_50_200_lo` | A01 | -0.160849 | -0.149849 | -0.171745 | -0.148446 | -0.190440 | -0.6804 | -2.7324 |
| `macross_50_200_lo` | A11 | -0.157020 | -0.145960 | -0.167977 | -0.144554 | -0.186395 | -0.6616 | -2.6891 |
| `donchian_n20_ls` | A00 | +0.288407 | +0.320712 | -0.010139 | +0.004368 | +0.403591 | +7.6351 | -15.0337 |
| `donchian_n20_ls` | A10 | +0.135698 | +0.140508 | -0.048033 | +0.107670 | +0.235470 | +2.5873 | -14.6901 |
| `donchian_n20_ls` | A01 | +0.152284 | +0.166799 | +0.108575 | +0.153304 | +0.103973 | +3.3398 | -14.7996 |
| `donchian_n20_ls` | A11 | +0.352716 | +0.418731 | +0.298437 | +0.398181 | +0.267529 | +8.7586 | -14.0344 |
| `donchian_n55_ls` | A00 | +0.360765 | +0.386031 | +0.331601 | +0.353302 | +0.425346 | +10.7184 | -14.3827 |
| `donchian_n55_ls` | A10 | -0.321379 | -0.297437 | -0.299446 | -0.316813 | -0.241707 | -6.5496 | -15.6400 |
| `donchian_n55_ls` | A01 | +0.479560 | +0.495948 | +0.463149 | +0.828389 | +0.470556 | +20.0685 | -15.4952 |
| `donchian_n55_ls` | A11 | +0.751285 | +0.800375 | +0.732061 | +0.500911 | +0.668654 | +35.3022 | -13.5104 |
| `xsmom_btc_eth_30d` | A00 | +0.446214 | +0.521306 | +0.389163 | +0.422285 | +0.465575 | +11.3237 | -7.4645 |
| `xsmom_btc_eth_30d` | A10 | +0.267807 | +0.391880 | +0.164367 | +0.262196 | +0.287918 | +5.1711 | -7.6890 |
| `xsmom_btc_eth_30d` | A01 | -0.098844 | -0.080061 | -0.143169 | -0.107194 | -0.101412 | -2.6978 | -12.0368 |
| `xsmom_btc_eth_30d` | A11 | -0.184629 | -0.144372 | -0.261333 | -0.174575 | -0.158410 | -4.3159 | -12.2680 |

## Invalid-log signs and policy orders

All 72 shadows are defined. Only one primary identity changes the sign of its mean, Sharpe and compound return: MA20/100-LS A00, whose simple SR is −0.020635 and invalid-log SR is +0.069505. The other 71 retain those signs. A preserved sign does not make log accounting valid.

Among the 54 registered direct policy contrasts, invalid accounting reverses two SR orders and four mean/compound-return orders. There are also nine drawdown-order reversals. The table lists every mean, SR or compound-return reversal; values are taken from the saved convention diagnostics. Mean and return values are percentage-point differences, while SR differences are dimensionless.

| Configuration | Changed arm | Reversed metric | Simple difference | Invalid-log difference |
|---|---|---|---:|---:|
| `tsmom_k7_ls` | A10 | SR | +0.009410 | -0.000489 |
| `tsmom_k90_lo` | A10 | Annual mean (pp) | -0.162774 | +0.127133 |
| `tsmom_k90_lo` | A10 | Compound return (pp) | -0.357676 | +0.486496 |
| `macross_20_100_lo` | A10 | Annual mean (pp) | -0.162774 | +0.127133 |
| `macross_20_100_lo` | A10 | Compound return (pp) | -0.357676 | +0.486496 |
| `macross_50_200_lo` | A10 | Annual mean (pp) | -0.162774 | +0.127133 |
| `macross_50_200_lo` | A10 | Compound return (pp) | -0.357676 | +0.486496 |
| `donchian_n20_ls` | A11 | Annual mean (pp) | +0.223760 | -1.553491 |
| `donchian_n20_ls` | A11 | SR | +0.064309 | -0.136062 |
| `donchian_n20_ls` | A11 | Compound return (pp) | +1.123575 | -5.374409 |

The nine drawdown-order reversals are TSMOM7-LS A10; TSMOM90-LS A11; TSMOM90-LO A10; MA20/100-LO A10; MA50/200-LO A10; Donchian20-LS A10/A01; Donchian55-LS A11; and cross-sectional momentum A10. The three repeated long-only streams retain their separate identities but represent the same observed order distortion.

The shadows freeze actual primary exposures, stop dates, charges and funding fractions and replace only gross simple-return accounting with the log term. They are neither a second simulator nor an alternative economically admissible book. No choice of policy or return convention follows from the direction of these reversals.

## Which historical interpretations change

The two previously emphasized corrected references are not improved by any changed policy. TSMOM30-LS moves from SR 0.985098 to 0.856372/0.768890/0.644436 for A10/A01/A11; compound return falls from 65.3250% to 44.9367%/34.5944%/26.1142%. MA10/50-LS moves from 0.858507 to 0.203027/0.712246/0.540271, and all three changed arms also have deeper drawdowns. This does not support a general stale-sizing or re-entry repair of the prior positive references.

Four previously negative long/short configurations become positive under both waiting arms, and retain positive SR under each fixed cost scenario: TSMOM90, TSMOM180, MA20/100 and MA50/200. Their primary A00/A01/A11 SRs are respectively −0.522876/0.246697/0.113769, −1.450072/0.812491/0.342465, −0.020635/0.353971/0.147118 and −0.966855/0.326632/0.392955. This describes a new policy mechanism, not a reversal of the original negative result. It is not uniform across periods or risk measures:

- TSMOM90's waiting arms still halt both sleeves by 2023; the final 2025 quarter is cash, not fresh positive evidence.
- TSMOM180's control halts in January 2022 after only 64/63 active Bitcoin/Ethereum dates. Waiting A01 admits 324/470 active dates and A11 admits 307/247, so this improvement cannot be explained solely by less exposure. The timing of losses and the absorbing halt determine which later opportunities survive. A11's 2023–2024 mean is negative; both waiting arms have a cash final quarter.
- MA20/100's positive full-clock waiting outcomes coexist with negative 2023–2024 means and a cash final quarter. Its large A01 zero-execution SR increase (0.353971 to 0.866907) reflects costs and changed state paths together.
- MA50/200 A01 avoids the permanent halt but has 882/911 waiting days in the two sleeves, negative first-period and final-quarter means, and positive middle-period mean. A11 halts both sleeves in August 2024 and has a deeper primary drawdown despite its positive SR. Neither pattern is uniformly successful through time.

The remaining grid also constrains the interpretation. TSMOM14-LS improves under waiting, while TSMOM7-LS waiting signs fail under doubled execution costs. Donchian55-LS daily sizing alone turns negative, although its waiting arms remain positive; removing funding affects those two waiting arms in opposite directions. The cross-sectional momentum reference falls from SR 0.446214 to −0.098844/−0.184629 under waiting, remaining negative in all cost scenarios. Every long-only configuration remains negative. These retained adverse cases prevent a favorable subset from standing in for the full eighteen-configuration comparison.

Costs cannot be assigned a universal mechanism from SR alone. For example, TSMOM30-LS A01 reduces primary execution charges but also removes profitable exposure, whereas the MA10/50-LS Ethereum waiting sleeve remains active much longer and incurs more charges than its early-halted control. The result retains each sleeve's gross dollars, signed funding, linear charges, impact, turnover and halt stages. Their cash amounts must not be added into a fictitious pooled account or interpreted as a controlled fee effect when the path changes.

## Limits on subsequent claims

This fixed comparison supports the engineering implementation and shows economically consequential, heterogeneous interactions between stale sizing, stop blocks and permanent halts. It supplies no formal sampling inference and no validated improvement, prospective performance claim, new model-class result or chosen winner. The eighteen configurations and their policy/cost cases share prices and many decisions; directional counts are not independent replications.

The development period is spent. Saved prices remain proxy inputs, signed daily funding and execution rates remain assumptions, threshold fills retain their disclosed gap/envelope convention, and the daily sleeve-return index has no modeled capital-transfer or pooled-rebalancing costs. A 15% halt is a decision rule, not a guaranteed maximum loss. Cash-only period Sharpe remains null rather than a favorable substituted zero.

Any fresh validation needs the exact model/policy/family, venue and funding/cost evidence, duration and decision criteria committed before the first eligible observation, with the prospective window no earlier than September 11, 2026. The present cycle does not select that policy or authorize future collection or trading. The research program retains zero validated strategies.

Recorded financial-ledger metadata (not independently byte-verified in this interpretation):

```json
{
  "new_rows": 72,
  "prefix_rows": 748,
  "prefix_sha256": "4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601",
  "rows": 820,
  "sha256_after": "4459ddc70d41d9a99db06ab53d9ad4c8f42b6f4d282abd93b4857b4474041927"
}
```
