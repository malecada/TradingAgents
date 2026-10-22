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

2026-10-22 12:10 — Fresh whole-branch review (fable): flow semantics, activation, NaN-USD,
per-hour cross-section, hour-weighted bootstrap and atomic day files verified; one Critical
("1000X" perps priced per 1,000 tokens → USD and `big_cnt` 1000× off for five tokens) and
three Important (two wrong contracts in the universe; unavailable days never retried; panel
stage peak ≈ 12 GB) fixed with tests before the pass (PLAN.md amendment 1); universe
re-frozen at 146 tokens. Pass launched as `onchain-b8-pass` (6 GiB cap, restart on stall).

2026-10-22 12:45 — Pass check after 150 days (to 2020-10-28): 64 tokens active, 27 priced; USD per
exchange deposit from $514 (LRC) to $43k (YFI), no decimal or multiplier anomaly; 12 s per day,
peak 731 MB; projected end ≈ 19:45.

B8-CP2 (2026-10-22 22:03) — pass complete in 11.5 h without a stall or restart: 2,249 days built,
1 unavailable (2020-11-01, no token_transfers partition, as in B4/B6); 18.4 s per day on average
(12 s in 2020–23, 30 s in 2025, 39 s in 2026), peak 3.6 GB; day files 118 MB. Panel stage running.

B8-CP3 (2026-10-22 22:10) — panel built in 4.8 min (peak 6.0 GB): 5,166,317 token-hours × 75
columns (146 tokens, 2020-07-01 → 2026-07-29), 4,647,052 rows with complete features; per test
year 596k (2022), 818k (2023), 1,146k (2024), 1,083k (2025), 574k (2026) V6 rows; median 103
tokens per hour. Forecast unit `onchain-b8-forecast` launched (9 GiB cap, resumable per target).
