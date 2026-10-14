# Branch B2 state

2026-10-14 05:00 — **B2-CP3: development screen negative.** 0 of 40 comparisons pass
(`SCREEN.md`); `selection.json` is empty and committed, so the sealed 2025–26 holdout is
not opened under the registered rule. `FORENSICS.md` explains the null: the harness
detects volatility (R² 0.22) and volume (R² 0.96) persistence from price history, but
activity, exchange/whale flows and motif features add nothing out of sample; motif sets
are under-regularised (227–379 features vs 65–312 training rows) and a post-hoc
compressed variant also shows no gain. Screen run on the dev feature table built from
473 completed weeks (all 418 development weeks complete).

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

Independent whole-branch review (range 8b185c344..77b8c82f6): development screen
verified leakage-free; 1 Critical (capture memory: projected 12–17 GB with two
workers), 2 Important (one failing week ended the stage; holdout not enforced
one-shot) and re-graded Minors fixed in `d91074e53` before any feature or screen
(58 B2 tests). Pre-outcome amendments are dated in `gates.json`.

The first capture run was stopped at 30/510 weeks before the memory peak; those
weeks are kept. Measured after the fix: 8.85M-row week (2024-03-11) peaks at
2.93 GB in 35 s. Running: `onchain-b2-weeks` as one fresh process per week, one
worker, 5 GiB cap (host has ~5.4 GB free with swap full); ETA ~12–15 h.

Next safe action: when the build finishes, record counts in `DATA.md` (B2-CP1);
apply any review fixes; dictionary → MCM → features (B2-CP2); screen and commit
selection (B2-CP3) before the single holdout run (B2-CP4).
