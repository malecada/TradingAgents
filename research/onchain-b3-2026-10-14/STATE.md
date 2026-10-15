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

Next safe action: history pass (keys kept until after the screen), dictionary, MCM
in two shards, features (B3-CP2); screen, commit selection (B3-CP3); holdout only for
a non-empty committed selection (B3-CP4).
