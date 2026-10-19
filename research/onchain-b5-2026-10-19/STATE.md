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

Next safe action: implement plan tasks 2–8; fetch option trades, DVOL and BTC bars
(B5-CP1); decision tables (B5-CP2); forecast comparison and backtests (B5-CP3); event
study, Tron probe, `RESULTS.md` (B5-CP4).
