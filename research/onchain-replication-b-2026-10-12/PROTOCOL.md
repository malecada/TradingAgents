# Branch B protocol — paper-scale replication of Çelik & Sefer (2026), ETH initial fold

Frozen 2026-10-12 before any dictionary, calibration or fit. The executable
numbers live in `config/*.json`; this page states what each file governs and
the rules that are not numbers. Design rationale: the spec in
`docs/superpowers/specs/2026-10-12-onchain-replication-b-design.md`.
Branch A (Codex) is untouched; comparison checkpoints are listed at the end.

## Data

- Transactions: retained AWS public-blockchain ETH daily parquets 2022-01-01 …
  2024-12-31, mapped by `research/onchain-graph-2026-09-16/fullpanel/plan.json`;
  read in place through hash-verified span reassembly (`sources.py`). Admitted
  event: `receipt_status == 1`, `value > 0`, well-formed recipient; a day with a
  duplicated transaction hash is rejected. Exclusion counters are kept per day.
- Prices: Coin Metrics daily `PriceUSD` (declared deviation from Yahoo Finance).
  Close of UTC day *d* is available at the start of *d+1*.

## Weekly graphs (`config/graph.json`)

Complete Monday-anchored UTC weeks 2022-01-03 … 2024-12-23 (156). Ordered
address pairs aggregated to `count` and `value_eth`. The **paper-scale** graph
is the induced subgraph on the K most active addresses (activity = in + out
admitted transaction count, ties by address). K is calibrated label-free on four
training weeks to the paper's reported density 0.003 (log-space nearest among
5,000 / 10,000 / 20,000 / 34,000 / 50,000; cap 50,000) and then written into
`graph.json` with the table in `CALIBRATION.md`. Node features are log1p
in/out count and volume; edge features log1p count and value; self-loops kept.

## Neighborhoods and dictionary (`config/dictionary.json`)

Weak one-hop induced neighborhood of a center inside the paper-scale graph,
capped at `n_max` nodes (center plus strongest-interaction neighbors). `n_max`
is frozen after the compute calibration (32 unless 64 fits the budget).
Dictionary per seed: 512 seeded draws over (training week, center) with
overlap halving, pairwise distance `1 − (S(A,B)+S(B,A))/2`, average linkage,
32 medoids. Only weeks available before the first 2024 decision date are used.

## Matching (`config/matching.json`)

Literal Algorithm 1: `M = V`; while `β ≤ 30` and fewer than 50 iterations,
`Q = 0.5·Σ s1·M + α·V`, `M = exp(βQ)` normalised once by rows then once by
columns in the log domain, `β ← 1.075·β` (48 temperatures); greedy global-maximum
hardening with row-major ties. Score is Eq. 1 on the hard assignment with the
printed `2·sqrt(l1·l2)` denominator. The batched solver must agree with the
per-pair reference within 1e-9.

## Model and training (`config/model.json`, `config/training.json`)

MLP 32→64→32 → GAT (4×16 concat, ELU; 1×32) over incoming edges plus self →
mean pool → per-day concat with the training-scaled close → LSTM 64 → additive
attention 32 → regression scalar or two logits. Joint training, Adam 1e-3,
batch 16 chronological days, 100 epochs, clip 1, no validation, seeds
11/23/37/51/71. Baselines: LSTM, GRU, HLSTM (4×7-day two-level), SVM.
Diagnostics: `constant_graph`, `label_permutation`.

## Chronology (`config/calendar.json`)

Decision date *d* uses closes up to *d* and weeks whose end (next Monday) is
≤ *d*. Train decision dates: 2022-02-06 … 2023-12-30 (label < 2024-01-01).
Test: 2024-01-01 … 2024-12-30. Warm-up days lacking a full window are excluded
and counted. Scaling, calibration and dictionary never read 2024 data.

## Gates (`gates.json`)

Primary: full-model 2024 direction accuracy, mean over seeds, signed difference
to 80.4 %, 14-day moving-block bootstrap (2,000 draws, seed 20260924);
"numerically close" if |Δ| ≤ 2 pp. Secondary: Δ vs price-only LSTM with
bootstrap; regression MAE/RMSE/MAPE in USD. Chance control: label permutation.
One-shot: every arm-seed is trained and evaluated once; failures are retained.

## Resources

Laptop only: ≤ 12 GiB resident (`systemd-run --user -p MemoryMax=12G`),
all cores, no GPU, no network, no paid resources. Artifacts under
`research_artifacts/onchain-replication-b/` (gitignored), budget ≤ 6 GB.

## Checkpoints shared with Branch A

CP1 156 paper-scale graphs + calibration · CP2 dictionaries and MCM features
with measured cells/s · CP3 measured joint training step and one full arm-seed ·
CP4 M2 result table on sealed 2024.
