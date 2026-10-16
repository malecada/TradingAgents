# Branch B3 state

2026-10-14 17:00 — Code complete (plan tasks 1–7; 28 B3 tests, 155 with B/B2).
Independent pre-launch review: 0 Critical; Important k-core peeling cost fixed
(`a24c52ba6`); pre-outcome amendment adds `f4_avg_clustering` because registered
global transitivity is 0.0 on real weeks (`gates.json` amendments). No feature table,
screen or holdout read yet.

Pre-launch measurements: 2024-03-11 (local, 8.85M rows) 3.36 GB / 76 s;
2026-01-12 (S3, 17.1M rows) 4.13 GB under the 8 GiB cap / 7.9 min (2.1 min CPU).
Example real-week values (2026-01-12): giant component 91.6 % of addresses,
2-core 29.7 %, exchange PageRank share 6.5 %, average clustering 0.041, global
transitivity 0.0.

B3-CP1 (2026-10-15 08:30) — data pass complete: 510 of 510 weeks built,
0 unavailable, 0 failed, 510 key files (6.1 GB), 20k graphs 1.3 GB. Loops ran
2026-10-14 16:53 → 2026-10-15 ≈ 08:25.

| Period | Weeks | Admitted rows / week (mean, max) | Seconds / week (mean, max) | Peak RSS |
|---|---|---|---|---|
| S3 2017–2021 | 261 | 5.39M, 11.07M | 126, 437 | 4.89 GB |
| Retained 2022–24 (local) | 156 | 7.80M, 9.21M | 47, 119 | 3.77 GB |
| S3 2024-12-30 – 2026-10-05 | 93 | 12.36M, 21.78M | 253, 473 | 5.52 GB |

All peaks stayed under the unit caps (8 GiB S3, 5.5 GiB local).

B3-CP2 (2026-10-15 12:10) — history pass 510/510 weeks (40.8 min CPU; new +
previous-4-week + returning shares sum to 1); dictionary from 104 weeks 2017–18,
32 motifs (1–18 nodes); MCM 510/510 weeks (20,000 × 32 cells, ≈ 45–52 s/week/shard,
two shards, 08:32 → 12:05); feature table 510 weeks, 0 missing, 150 columns
(F1 14, F3a 10, F4 30, F5 96), no NaN, infinite or constant column. Address keys
(6.1 GB) kept until the screen is done.

B3-CP3 (2026-10-15 12:20) — screen run once on the development window: 0 of 42
comparisons pass (`SCREEN.md`); `selection.json` is empty and committed before any
holdout command. Closest: trees S5 vs S1 on T6 4-week return (−0.00729, interval
upper +0.00008, 4/6 years) and on T3 weekly return (−0.00130, upper +0.00011, 4/6).
Linear on-chain sets are significantly worse on T4/T5 (as in B2).

B3-CP4 (2026-10-15 12:45) — holdout command refused on the empty committed
selection ("screen negative: holdout not opened"); no lock written; the sealed
2025-01-06 → 2026-10-05 window is unread. Forensics (`FORENSICS.md`): harness detects
volatility and volume persistence (S0 vs constant R² T4 0.213, T7 0.089, T5 0.955);
the tree near misses on T3/T6 lose 12–16 % MSE to a constant forecast with every set;
F4 partial correlations after F0 stay below a circular-shift null for every target.
Intermediates deleted 2026-10-16 with user approval (record:
`research_artifacts/onchain-b3/DELETED.md`): address keys 6.1 GB, 20k graphs 1.3 GB,
MCM 1.3 GB. Kept: weekly summaries, `history.json`, dictionary, the screened feature
table, `screen.json`, exploration outputs and logs; the screen can be re-run from them.

B3 is closed: negative. Together with M2 (0.490) and B2 (0 of 40), the weekly
on-chain graph line for ETH is closed in this programme. Open user decisions: a
Bitcoin run (draft `docs/superpowers/specs/2026-10-14-onchain-b2-btc-plan.md`) and
any future registered use of the unread sealed window.
