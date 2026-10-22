# B8 pre-declared analysis plan (committed before any day is read)

All items run once; `RESULTS.md` reports every row, including negatives.

## Comparisons

Pooled panel, one model across tokens per fold; test years 2022–2026 (window 2020-06-01 →
2026-07-29), purge = horizon, expanding training, min_train 50,000 rows. Targets V6, V24 (log
realised volatility of the token's hourly returns over the next 6 / 24 h), XV24 (V24 minus the
hour's mean V24 over tokens, ≥ 20 tokens). Sets P0 = price (`h0_`), intraday (`px_`) and the
cross-sectional z-scores of `h0_rv24`, `h0_lvol24`; P1 = P0 + B7's six transforms of the seven
token-hour series (42); P2 = P1 + cross-sectional z-scores of the `__s24z` and `__ex1`
columns (14). Families ridge and trees_es (B7 rules, min_tail_pos irrelevant for regression).
Comparisons P1 vs P0, P2 vs P1, P2 vs P0 → 3 × 2 families × 3 targets = 18 rows.

Statistics: per-row squared-error differences averaged per hour across tokens (one value per
hour), the mean over hours, a 95 % circular block-bootstrap interval over hours (block 168,
2,000 draws, seed 20261023), per-year means, the loss of the training-mean constant.
Criterion: upper end < 0 and better in ≥ 3 of 5 years. About one chance pass is expected
among 18 rows; a finding needs both families.

Post hoc (labelled): per-token mean differences for every comparison (CSV), read by
liquidity tercile of mean quote volume.

## Reporting

`TABLES.md` (generated) holds every row with per-year rows, hours and tokens; `RESULTS.md`
reads it. Post hoc additions are labelled.

## Amendment 1 (2026-10-22, before any day is read)

Fresh review findings, applied before the pass: (1) Binance "1000X" perps are quoted per
1,000 tokens, so the per-token USD price is the close divided by the symbol's multiplier
(1000BONK, 1000FLOKI, 1000PEPE, 1000SHIB); (2) `1000SATSUSDT` (map: "Satoshis Vision", the
perp is the BRC-20 SATS) and `OMNIUSDT` (map: "OmniCat", the perp is Omni Network) are
excluded as wrong contracts, leaving 146 tokens; (3) days marked unavailable are retried on
every relaunch of the pass and the marker is removed on success; (4) V6 / V24 are missing,
not −18.4, when the future window has no price change; (5) feature columns are float32 and
the cross-section is built in place (memory). Reporting: differences, intervals and years are
hour-weighted; losses and gains row-weighted, labelled in `TABLES.md`.
