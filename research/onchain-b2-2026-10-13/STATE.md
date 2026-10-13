# Branch B2 state

2026-10-13 — Code complete (tasks 1–11 of the plan; 44 tests pass). Capture
running (B2-CP1 in progress). No feature table, no screen, no holdout read.

Captured and frozen (gitignored artifacts under `research_artifacts/onchain-b2/`):
- Exchange labels: 4,961 addresses — Spellbook `cex_evms_addresses` at commit
  e98fc1f2aa… (4,957 parsed, 0 unparsed) ∪ eth-labels `mainnet/exchange` at
  commit 6fb076bf27… (372). Full hashes in `labels/meta.json`.
- Market: Coin Metrics PriceUSD 2,953 development days (2016-12-01 → 2024-12-31)
  and 650 sealed days; Binance ETHUSDT quote volume 2,694 development days
  (2017-08-17 → 2024-12-31) and 650 sealed days. Sealed values and every raw
  response live only under `sealed/`.
- Smoke reads: 2017-03-06 57,020 rows in 5.6 s; 2025-06-02 1,417,405 rows in 42 s
  (S3 throughput varies 8–42 s per day).

Running: `onchain-b2-weeks` (2 workers, 10 GiB cap) building 510 weeks; 2017
weeks ≈ 35 s each. Independent whole-branch review of the B2 code in progress.

Next safe action: when the build finishes, record counts in `DATA.md` (B2-CP1);
apply any review fixes; dictionary → MCM → features (B2-CP2); screen and commit
selection (B2-CP3) before the single holdout run (B2-CP4).
