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

Running (B3-CP1): `onchain-b3-weeks` (S3 weeks, 8 GiB cap) and
`onchain-b3-weeks-local` (2022–24, 5.5 GiB cap), one fresh process per week, a
killed week stays not built and blocks later stages. Address keys are kept until the
screen is done.

Next safe action: when both loops finish, record counts (B3-CP1); history pass
(without --delete-keys), dictionary, MCM in two shards, features (B3-CP2); screen,
commit selection (B3-CP3); holdout only for a non-empty committed selection (B3-CP4).
