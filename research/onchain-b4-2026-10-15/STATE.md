# Branch B4 state

2026-10-15 — Registered (charter, config, gates). Code: plan tasks 1–8 complete
(27 B4 tests; 182 with B/B2/B3).

B4-CP1 (2026-10-15) — market data stored, sealed parts unread:
- Binance ETHUSDT 1 h: 64,524 development bars (2017-08-17 04:00 → 2024-12-31 23:00;
  128 missing bars in 28 outage runs, longest 33 h) and 15,600 sealed bars. Missing
  bars make 4,367 of 63,552 development hours from 2017-10-02 ineligible through the
  168-hour price windows (2018 1,082; 2019 868; 2020 1,271; 2021 977; 2023 169), as
  registered (spec §4.5).
- Coin Metrics daily: 2,922 development days (2017-01-01 → 2024-12-31, no gaps except
  USDC before 2018-09 and DAI before 2019-11, counted as 0) and 650 sealed days.

Heavy-day probe (2025-06-02, S3, fresh label-only state): 1.39M successful
transactions, 677k admitted ETH transfers, 505k stablecoin transfers, 7,129 blocks;
read 44 s, flows + entity update 1.2 s, peak 1.75 GB. Labels-only state that day:
inflow 551k ETH and $4.65B stablecoins; 91.8k first-send candidates.

Pre-launch review (fresh reviewer): 0 Critical, 5 Important — fixed with tests
(`71e18cbd0`): relaunch retries a stopped run of unavailable days, token addresses
normalised, non-42-character addresses fail the day, disk guards. At launch the length
guard caught contract creations stored with the recipient string 'None' (2017-01-04);
fixed (`reader.py`, test) and the pass relaunched from 2017-01-01. One real day per year
2017–2026 read cleanly; ERC-20 stablecoin transfers are sparse before mid-2019 (37 on
2018-03-01, 1,824 on 2019-03-01). token_transfers has no partition for 2020-11-01
(that day will be marked unavailable).

B4-CP2 (2026-10-17) — chain pass complete: 3,569 days built, 2 unavailable
(2020-11-01: no token_transfers partition; 2025-09-24: S3 timeouts on all three
attempts, kept as registered). Interruptions, all resumed from snapshots with identical
outputs: user reboot (restart from scratch after the gas-price fix), laptop suspend
(watchdog fix `c93b82b0c`), one OOM kill at the 8 GiB cap on 2025-12-06 (prefetch 2 → 1,
`411cb34ca`). Final state: 87.8M candidates, 84.8M deposit addresses; peak 7.0 GB.
Feature tables: 85,704 hours × 32 registered hourly columns; 20 daily columns.

Sanity (features only, no targets): deposit-expanded ETH inflow is below labels-only
inflow in every year (e.g. 2019: 244k vs 450k ETH/day) because entity grouping makes
sweeps, gas top-ups and exchange-internal moves internal; daily log inflow correlates
with Coin Metrics FlowInExNtv at 0.85 (deposit-expanded) and 0.92 (labels-only),
2019–24. No zero-transfer day; no day after 2019-06 with < 1,000 stablecoin transfers.

B4-CP3 (2026-10-17) — screen run once on the development window: 3 of 42 comparisons
pass (`SCREEN.md`; about 2 false passes expected by chance); `selection.json` committed
before any holdout command:
1. V6 next-6-hour log realised volatility, linear, HS (price + stablecoin flows) vs H0:
   −0.00443 MSE, interval upper −0.00282, better in 4/6 years; R² vs constant 0.405 vs 0.397.
2. V6, trees, HE (price + ETH flows) vs H0: −0.00353, upper −0.00198, 5/6; R² 0.478 vs 0.472.
3. R7 7-day log return, trees, DA (price + all Coin Metrics) vs D0: −0.00089, upper −0.00005,
   5/6; both arms lose to a constant forecast (R² −0.271 vs −0.337), the B3 near-miss pattern.

Next safe action: holdout dry run on development data only (simulated cutoff), then the
one-shot holdout for the committed selection (B4-CP4), forensics.
