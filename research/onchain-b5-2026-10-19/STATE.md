# Branch B5 state

2026-10-19 — Registered (charter, config, pre-declared plan). No B5 data read yet.

Pre-run review (fresh reviewer, 0 Critical, 4 Important + 2 re-graded): fixed with tests
and recorded as `PLAN.md` amendments 1–6 before any decision table (`54984dadd`):
event-study alignment, zero-IV trades, clamped symmetric spreads, 07:30–08:00 TWAP
settlement, log-RV bias in the signal, and the metric of the positive reading.

B5-CP1 (2026-10-19) — data stored, no unavailable day:
- Deribit option trades: ETH 2,029 days, 15.47M trades (2021 1.51M … 2025 3.27M);
  BTC 2,029 days, 21.94M trades (2021 2.08M … 2025 5.30M); 0.5 GB.
- DVOL hourly: ETH and BTC 48,696 hours each, 2021-03-24 00:00 → 2026-10-12 23:00.
- Binance BTCUSDT hourly: 80,124 bars; ETH bars from B4.
- Settlement TWAPs (07:30–08:00, 1-minute): 2,030 dates per asset, missing 2021-04-25
  and 2021-09-29 (Binance gaps; those expiries are excluded).
- Tron probe: go, labels-only via SQD (`TRON_PROBE.md`).

B5-CP2 (2026-10-19) — decision tables: BTC_S24 1985 rows (neg raw spread 38%); BTC_S6 1987 rows (neg raw spread 41%); ETH_S24 1980 rows (neg raw spread 32%); ETH_S6 1983 rows (neg raw spread 33%). Eligible decisions per
year 2022–2025: 356–366; 2021 from April; 2026 to 12 October.

B5-CP3/CP4 (2026-10-19) — all pre-declared analyses run once (`TABLES.md`) and read in
`RESULTS.md`: option-market information dominates price history (7 of 8 cells); flows add
nothing reliable on top (1 of 16 cells, reversed in 2025–26); straddle rules with and
without flows differ inside noise (pre-declared criterion met literally in 7 of 24 cells,
consistent with chance); the 6-hour short-straddle premium is independent of flows and
disappears with strike-level pricing plus one tick per leg (post hoc); event study shows
no post-inflow volatility surprise. Tron: go (labels-only via SQD).

B5 is closed: no flow-based trading strategy. A possible later study concerns the
short-dated volatility premium itself (quote-level spreads, margin, forward test).
