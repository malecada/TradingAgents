# B2 screen — development 2017-10 → 2024 (walk-forward 2019–2024)

Samples: weekly 378 (excluded 0), daily 2647 (excluded 0).

40 comparisons are screened, each against a 95 % interval; about 2 false passes are expected by chance, which is why the sealed holdout exists.

| target | family | comparison | n | mean loss diff | 95 % CI | years better | pass | detail |
|---|---|---|---|---|---|---|---|---|
| T1 | linear | S1 vs S0 | 2191 | +0.00242 | [-0.00181, +0.00677] | 3/6 | — | accuracy_S1 0.5212, accuracy_S0 0.5148, brier_S1 0.2520, brier_S0 0.2511 |
| T1 | linear | S2 vs S1 | 2191 | +0.00611 | [+0.00097, +0.01201] | 3/6 | — | accuracy_S2 0.5126, accuracy_S1 0.5212, brier_S2 0.2542, brier_S1 0.2520 |
| T1 | linear | S3 vs S1 | 2191 | +0.03358 | [+0.01441, +0.05834] | 2/6 | — | accuracy_S3 0.5167, accuracy_S1 0.5212, brier_S3 0.2608, brier_S1 0.2520 |
| T1 | linear | S4 vs S2 | 2191 | +0.02756 | [+0.01102, +0.04977] | 1/6 | — | accuracy_S4 0.5167, accuracy_S2 0.5126, brier_S4 0.2612, brier_S2 0.2542 |
| T1 | trees | S1 vs S0 | 2191 | +0.00049 | [-0.01125, +0.01331] | 2/6 | — | accuracy_S1 0.5267, accuracy_S0 0.5071, brier_S1 0.2654, brier_S0 0.2661 |
| T1 | trees | S2 vs S1 | 2191 | +0.00985 | [-0.00173, +0.02288] | 1/6 | — | accuracy_S2 0.5262, accuracy_S1 0.5267, brier_S2 0.2685, brier_S1 0.2654 |
| T1 | trees | S3 vs S1 | 2191 | +0.00333 | [-0.00827, +0.01537] | 2/6 | — | accuracy_S3 0.5240, accuracy_S1 0.5267, brier_S3 0.2664, brier_S1 0.2654 |
| T1 | trees | S4 vs S2 | 2191 | -0.00748 | [-0.02005, +0.00492] | 6/6 | — | accuracy_S4 0.5276, accuracy_S2 0.5262, brier_S4 0.2659, brier_S2 0.2685 |
| T2 | linear | S1 vs S0 | 312 | -0.00030 | [-0.01670, +0.01493] | 3/6 | — | accuracy_S1 0.4904, accuracy_S0 0.4968, brier_S1 0.2524, brier_S0 0.2526 |
| T2 | linear | S2 vs S1 | 312 | +0.01413 | [-0.00264, +0.03034] | 1/6 | — | accuracy_S2 0.5128, accuracy_S1 0.4904, brier_S2 0.2576, brier_S1 0.2524 |
| T2 | linear | S3 vs S1 | 312 | +0.04682 | [+0.00059, +0.10168] | 3/6 | — | accuracy_S3 0.5288, accuracy_S1 0.4904, brier_S3 0.2638, brier_S1 0.2524 |
| T2 | linear | S4 vs S2 | 312 | +0.05677 | [+0.01568, +0.10647] | 3/6 | — | accuracy_S4 0.5064, accuracy_S2 0.5128, brier_S4 0.2735, brier_S2 0.2576 |
| T2 | trees | S1 vs S0 | 312 | +0.07050 | [-0.00836, +0.15066] | 2/6 | — | accuracy_S1 0.4872, accuracy_S0 0.5000, brier_S1 0.3172, brier_S0 0.2940 |
| T2 | trees | S2 vs S1 | 312 | -0.00138 | [-0.05568, +0.05214] | 2/6 | — | accuracy_S2 0.4840, accuracy_S1 0.4872, brier_S2 0.3171, brier_S1 0.3172 |
| T2 | trees | S3 vs S1 | 312 | +0.02434 | [-0.06485, +0.11727] | 3/6 | — | accuracy_S3 0.4744, accuracy_S1 0.4872, brier_S3 0.3228, brier_S1 0.3172 |
| T2 | trees | S4 vs S2 | 312 | -0.00143 | [-0.08433, +0.07931] | 2/6 | — | accuracy_S4 0.5032, accuracy_S2 0.4840, brier_S4 0.3148, brier_S2 0.3171 |
| T3 | linear | S1 vs S0 | 312 | +0.00138 | [+0.00020, +0.00267] | 3/6 | — | r2_vs_S0_S1 -0.0928, r2_vs_S0_S0 0.0000 |
| T3 | linear | S2 vs S1 | 312 | +0.00215 | [+0.00092, +0.00357] | 1/6 | — | r2_vs_S0_S2 -0.2369, r2_vs_S0_S1 -0.0928 |
| T3 | linear | S3 vs S1 | 312 | +0.00478 | [+0.00114, +0.00920] | 2/6 | — | r2_vs_S0_S3 -0.4131, r2_vs_S0_S1 -0.0928 |
| T3 | linear | S4 vs S2 | 312 | +0.00062 | [-0.00137, +0.00262] | 2/6 | — | r2_vs_S0_S4 -0.2785, r2_vs_S0_S2 -0.2369 |
| T3 | trees | S1 vs S0 | 312 | -0.00158 | [-0.00445, +0.00109] | 2/6 | — | r2_vs_S0_S1 0.0777, r2_vs_S0_S0 0.0000 |
| T3 | trees | S2 vs S1 | 312 | +0.00030 | [-0.00106, +0.00172] | 2/6 | — | r2_vs_S0_S2 0.0628, r2_vs_S0_S1 0.0777 |
| T3 | trees | S3 vs S1 | 312 | -0.00157 | [-0.00357, +0.00043] | 6/6 | — | r2_vs_S0_S3 0.1552, r2_vs_S0_S1 0.0777 |
| T3 | trees | S4 vs S2 | 312 | -0.00138 | [-0.00378, +0.00111] | 5/6 | — | r2_vs_S0_S4 0.1310, r2_vs_S0_S2 0.0628 |
| T4 | linear | S1 vs S0 | 312 | +0.04875 | [+0.01349, +0.10409] | 0/6 | — | r2_vs_S0_S1 -0.1890, r2_vs_S0_S0 0.0000 |
| T4 | linear | S2 vs S1 | 312 | +0.01418 | [+0.00004, +0.03112] | 2/6 | — | r2_vs_S0_S2 -0.2440, r2_vs_S0_S1 -0.1890 |
| T4 | linear | S3 vs S1 | 312 | +0.02941 | [-0.01460, +0.06540] | 2/6 | — | r2_vs_S0_S3 -0.3030, r2_vs_S0_S1 -0.1890 |
| T4 | linear | S4 vs S2 | 312 | +0.00944 | [-0.05099, +0.05324] | 3/6 | — | r2_vs_S0_S4 -0.2806, r2_vs_S0_S2 -0.2440 |
| T4 | trees | S1 vs S0 | 312 | -0.00200 | [-0.02904, +0.02535] | 2/6 | — | r2_vs_S0_S1 0.0066, r2_vs_S0_S0 0.0000 |
| T4 | trees | S2 vs S1 | 312 | +0.02295 | [+0.00001, +0.04582] | 2/6 | — | r2_vs_S0_S2 -0.0691, r2_vs_S0_S1 0.0066 |
| T4 | trees | S3 vs S1 | 312 | +0.02859 | [-0.00133, +0.06025] | 3/6 | — | r2_vs_S0_S3 -0.0878, r2_vs_S0_S1 0.0066 |
| T4 | trees | S4 vs S2 | 312 | +0.00973 | [-0.02066, +0.04151] | 2/6 | — | r2_vs_S0_S4 -0.1012, r2_vs_S0_S2 -0.0691 |
| T5 | linear | S1 vs S0 | 312 | +0.05284 | [+0.02436, +0.08981] | 0/6 | — | r2_vs_S0_S1 -0.4036, r2_vs_S0_S0 0.0000 |
| T5 | linear | S2 vs S1 | 312 | +0.04366 | [+0.00387, +0.09325] | 2/6 | — | r2_vs_S0_S2 -0.7372, r2_vs_S0_S1 -0.4036 |
| T5 | linear | S3 vs S1 | 312 | +0.66881 | [+0.46661, +0.91661] | 0/6 | — | r2_vs_S0_S3 -5.5123, r2_vs_S0_S1 -0.4036 |
| T5 | linear | S4 vs S2 | 312 | +0.88322 | [+0.65715, +1.13454] | 0/6 | — | r2_vs_S0_S4 -7.4835, r2_vs_S0_S2 -0.7372 |
| T5 | trees | S1 vs S0 | 312 | +0.04438 | [-0.01246, +0.10862] | 3/6 | — | r2_vs_S0_S1 -0.0558, r2_vs_S0_S0 0.0000 |
| T5 | trees | S2 vs S1 | 312 | +0.00806 | [-0.02634, +0.04329] | 2/6 | — | r2_vs_S0_S2 -0.0659, r2_vs_S0_S1 -0.0558 |
| T5 | trees | S3 vs S1 | 312 | +0.17093 | [+0.08740, +0.25646] | 0/6 | — | r2_vs_S0_S3 -0.2705, r2_vs_S0_S1 -0.0558 |
| T5 | trees | S4 vs S2 | 312 | +0.13421 | [+0.03702, +0.23649] | 0/6 | — | r2_vs_S0_S4 -0.2345, r2_vs_S0_S2 -0.0659 |

## Selected for the holdout

- none: screen negative, holdout stays unused
