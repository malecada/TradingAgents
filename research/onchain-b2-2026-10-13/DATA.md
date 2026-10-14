# Branch B2 data record (B2-CP1)

Captured 2026-10-13 → 2026-10-14. Artifacts are gitignored under `research_artifacts/onchain-b2/`; this file records
their identities and counts.

## Transactions

- Weeks built: 510 of 510 (2017-01-02 → 2026-10-05); unavailable 0; failed 0.
- Days read: 2,474 streamed from S3 (2017–2021, 2025–2026, 2024-12-30 week tail) and 1,096 from Branch B retained spans (2022–2024).
- Rows read 3,771,996,104; admitted transfers 1,769,732,072 (46.9%).

| year | weeks | rows read |
|---|---:|---:|
| 2017 | 52 | 102,902,304 |
| 2018 | 53 | 254,349,235 |
| 2019 | 52 | 242,286,953 |
| 2020 | 52 | 345,671,396 |
| 2021 | 52 | 460,605,282 |
| 2022 | 52 | 406,946,164 |
| 2023 | 52 | 382,357,866 |
| 2024 | 53 | 435,413,780 |
| 2025 | 52 | 525,946,206 |
| 2026 | 40 | 615,516,918 |

## Exchange labels

- Union 4,961 addresses, labels.json sha256 `2a87dc56f3c7b22f4118b85e4c6e422adffa60a67c8e9ea49877dbd72c606166`.
- Spellbook `dbt_subprojects/hourly_spellbook/models/_sector/cex/addresses/chains/cex_evms_addresses.sql` at commit `e98fc1f2aa08bb84bb87768e6e12fc5c183d28a4`: 4,957 parsed, 0 unparsed; raw sha256 `9e93064f65b368edf3a7c94faa54bb05dc5a2b0210093bbd27773b4dc5fe551f`.
- eth-labels `src/mainnet/exchange/all.json` at commit `6fb076bf279d986b3f451e4875d8de802fc1f39e`: 372; raw sha256 `fe4df0f8df756dcafea5343d01fc03b180e9d824211e9b4605baec94006371a0`.
- Static 2026 snapshot applied to all years (declared look-ahead in address identity only).

## Market

- Coin Metrics PriceUSD: 2,953 development days (2016-12-01 → 2024-12-31), 650 sealed days.
- Binance ETHUSDT quote volume: 2,694 development days (2017-08-17 → 2024-12-31), 650 sealed days.
- Raw responses (sealed directory): Coin Metrics `24a3a694a0eae9cf…`; Binance 4 pages.

## Features

- 510 weeks × 186 raw columns (F1 14, F3a 10, F2 96, F3b 66), none missing.
- Dictionary: seed 11, 512 samples from the 104 weeks 2017-01-02 … 2018-12-24, 32 motifs of 1–27 nodes.
- MCM: 510 weeks × 5,000 nodes × 32 motifs, ≈ 12 s per week.
- The screen used a table built from the first 473 weeks; after the last 37 (2026) weeks were added, all 418
  development rows were verified identical (causal transforms), so the screen result stands.

## Operations

- First run stopped at 30 weeks for projected memory (review C1); after the fix a 8.85M-row week peaked at 2.9 GB.
- Two OOM kills by unit caps (local worker at 3.5 GB, S3 worker at 5 GB on 17M-row 2026 weeks); both resumed
  without loss (summary written last). Final caps 4.5 GB local, 8 GB S3.
