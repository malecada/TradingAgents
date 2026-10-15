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

Next safe action: whole-branch review fixes (if any), then launch the chain pass
(`onchain-b4-pass`, 6 GiB cap, ≥ 5 GB disk free), features (B4-CP2), screen and
committed selection (B4-CP3), holdout only for a non-empty committed selection (B4-CP4).
