# Branch B8 state

2026-10-22 — Registered (charter, config, pre-declared plan). Universe not frozen yet; no day read.

B8-CP1 (2026-10-22 11:00) — universe frozen (`config/universe.json`): 148 tokens (112 mapped by
the Binance-spot rule, 36 by CoinGecko fallback), 17,599–53,971 hourly bars each, one symbol per
contract. Code complete (plan tasks 1–6; 16 B8 tests). Plan rulings: cross-sectional z-score is
0 when the hour's spread across tokens is zero (B4 convention; NaN would drop most sparse-series
rows); exchange activation from B6's final first-seen table. Fresh whole-branch review running;
no day read yet.

2026-10-22 11:30 — One-day probe of the pass (2020-06-01, outputs discarded): 13.7 s read + rows,
peak 631 MB, 30,950 universe transfers, 39 of 148 tokens active, USD series only for the 3
tokens with bars on that day (prices start at each token's listing). Projection: 9–15 h for
2,250 days. B7 commits fast-forwarded into `research/onchain-paper-replication-2026-09-24`
(f5ce7d227); audit page v8 published.
