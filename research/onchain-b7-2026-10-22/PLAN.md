# B7 pre-declared analysis plan (committed before any B7 table is built)

All items run once; `RESULTS.md` reports every row, including negatives.

## Comparisons

Tracks A′ (2019-04-01 → 2024-12-31; test years 2020–2024; group 2020–24) and B
(2021-04-01 → 2026-10-12; test years 2022–2026; groups 2022–24 and 2025–26). Targets V6,
V24 (log realised volatility of hourly returns, next 6 / 24 h), J6, J24 (1 if |log return
over the next 6 / 24 h| > 3·σ̂·√k, σ̂² = mean squared hourly return over the previous 720
hours; log loss), M6, M24 (log of the largest absolute 5-minute log return in the next 6 /
24 h; squared error). Sets X0 = price (`h0_`), intraday (`px_`), range (`rg_`), plus DVOL
and near-expiry implied volatility (`mk_`) in track B; X1 = X0 + B4's 22 flow columns;
X1a = X0 + B4's transforms of all 15 series; Y1 = X0 + the new engineering of the 15 B4
series + event-time + interactions; Y2 = Y1 + the new engineering of the 39 B6 series.
Families ridge (logistic for J) and trees_es; trees_fixed on Y2 only.

Per track, target and family: Y1 vs X1, Y1 vs X1a, Y2 vs Y1, X1 vs X0, Y2 vs X0; plus
trees_es(Y2) vs trees_fixed(Y2): 11 comparisons × 6 targets × 2 tracks = 132 (track B
rows per group). Statistics: mean per-row loss difference, 95 % circular block-bootstrap
interval (block 168 rows, 2,000 draws, seed 20261022), per-year differences, the loss of
a constant forecast (training mean or base rate) for every row.

Positive reading: A′ — upper end < 0 and better in ≥ 3 of 5 years; B — upper end < 0 in
2022–24 and mean difference < 0 in 2025–26 (the 2025–26 row alone is sign-only and is
labelled so). With 132 comparisons about 7 interval passes are expected by chance; a
result counts as a finding only if it holds in both families or both tracks.

Reading guide: Q1 — Y1 vs X1, Y1 vs X1a, Y2 vs Y1 and trees_es vs trees_fixed on V6/V24;
Q2 — X1 vs X0 and Y2 vs X0 on J and M targets, with V6/V24 as the reference.

## Reporting

`TABLES.md` (generated) holds every row with chosen alphas and iteration counts per fold;
`RESULTS.md` reads them. Post hoc additions are labelled.
