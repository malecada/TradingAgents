# Branch B8 state

2026-10-22 — Registered (charter, config, pre-declared plan). Universe not frozen yet; no day read.

B8-CP1 (2026-10-22 11:00) — universe frozen (`config/universe.json`): 148 tokens (112 mapped by
the Binance-spot rule, 36 by CoinGecko fallback), 17,599–53,971 hourly bars each, one symbol per
contract. Code complete (plan tasks 1–6; 16 B8 tests). Plan rulings: cross-sectional z-score is
0 when the hour's spread across tokens is zero (B4 convention; NaN would drop most sparse-series
rows); exchange activation from B6's final first-seen table. Fresh whole-branch review running;
no day read yet.
