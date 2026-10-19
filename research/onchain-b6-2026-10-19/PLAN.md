# B6 pre-declared analysis plan (committed before any pass output is read)

All items run once and are reported in `RESULTS.md`, including negatives.

## Q1, Q2, Q4 — forecast comparisons
Tracks A (2017-10 → 2024-12; test years 2019–2024) and B (2021-04 → 2026-10-12; test
years 2022–2026, groups 2022–24 and 2025–26). Targets V6, V24. Families linear, trees.
Sets X0 = base, X1 = X0 + F, X2 = X1 + S, X3 = X1 + E, X4 = X1 + S + E; with Tron
X5 = X4 + T. Comparisons X1 vs X0, X2 vs X1, X3 vs X1, X4 vs X1 (X5 vs X4 if Tron ran):
mean squared-error difference, 95 % circular block-bootstrap interval (block 168),
per-year differences. Positive reading: track A — upper end < 0 and better in ≥ 4 of 6
years; track B — upper end < 0 in 2022–24 and mean difference < 0 in 2025–26.

## Q3 — minute-level events
ETH primary, BTC cross-check. Events: deposits and withdrawals of ≥ $10M stablecoin or
≥ 5,000 ETH (tier 1) and ≥ $50M or ≥ 20,000 ETH (tier 2), first per 30 minutes per
direction and tier. Responses from m + 1: log realised volatility over the next 5, 15,
30, 60 minutes minus the previous 60 minutes; signed log return over the next 1, 5, 15,
30, 60 minutes; signed return over the 15 minutes before m. Placebo minutes matched by
year and hour of day, ≥ 60 minutes from any event. Means with block-bootstrap intervals
(block 10 events), groups 2019–24 and 2025–26.

## Reporting
`TABLES.md` (generated) holds every row; `RESULTS.md` reads them. Post hoc additions
are labelled.
