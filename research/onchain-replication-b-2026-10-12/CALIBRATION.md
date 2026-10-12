# Calibration — paper-scale K (label-free), N_max and compute

## 1. Graph scale K (run 2026-10-12, `cli calibrate`, `research_artifacts/onchain-replication-b/calibration/density.json`)

Rule frozen in `PROTOCOL.md` / `config/graph.json`: on four dispersed training
weeks, tabulate the directed density E/(K(K−1)) of the induced subgraph on the K
most active addresses for K ∈ {5,000, 10,000, 20,000, 34,000, 50,000}; freeze
the K whose mean density is nearest in log space to the paper's reported
Ethereum density 0.003 (§4.1), cap 50,000. No price or label was read.

| week | K | nodes | edges | density | full nodes | full edges | full density |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2022-03-07 | 5,000 | 5,000 | 17,123 | 6.85e-04 | 2,226,982 | 3,037,356 | 6.12e-07 |
| 2022-03-07 | 10,000 | 10,000 | 39,035 | 3.90e-04 | | | |
| 2022-03-07 | 20,000 | 20,000 | 79,681 | 1.99e-04 | | | |
| 2022-03-07 | 34,000 | 34,000 | 130,348 | 1.13e-04 | | | |
| 2022-03-07 | 50,000 | 50,000 | 182,743 | 7.31e-05 | | | |
| 2022-03-07 | random 50,000 (expected) | 50,000 | 1,531 | 6.12e-07 | | | |
| 2022-09-05 | 5,000 | 5,000 | 14,564 | 5.83e-04 | 1,866,052 | 2,481,446 | 7.13e-07 |
| 2022-09-05 | 10,000 | 10,000 | 33,076 | 3.31e-04 | | | |
| 2022-09-05 | 20,000 | 20,000 | 67,815 | 1.70e-04 | | | |
| 2022-09-05 | 34,000 | 34,000 | 111,661 | 9.66e-05 | | | |
| 2022-09-05 | 50,000 | 50,000 | 158,576 | 6.34e-05 | | | |
| 2022-09-05 | random 50,000 (expected) | 50,000 | 1,782 | 7.13e-07 | | | |
| 2023-03-06 | 5,000 | 5,000 | 19,573 | 7.83e-04 | 1,415,231 | 2,051,299 | 1.02e-06 |
| 2023-03-06 | 10,000 | 10,000 | 43,438 | 4.34e-04 | | | |
| 2023-03-06 | 20,000 | 20,000 | 86,170 | 2.15e-04 | | | |
| 2023-03-06 | 34,000 | 34,000 | 139,936 | 1.21e-04 | | | |
| 2023-03-06 | 50,000 | 50,000 | 194,196 | 7.77e-05 | | | |
| 2023-03-06 | random 50,000 (expected) | 50,000 | 2,560 | 1.02e-06 | | | |
| 2023-09-04 | 5,000 | 5,000 | 14,520 | 5.81e-04 | 1,419,071 | 2,089,844 | 1.04e-06 |
| 2023-09-04 | 10,000 | 10,000 | 30,439 | 3.04e-04 | | | |
| 2023-09-04 | 20,000 | 20,000 | 61,122 | 1.53e-04 | | | |
| 2023-09-04 | 34,000 | 34,000 | 102,193 | 8.84e-05 | | | |
| 2023-09-04 | 50,000 | 50,000 | 147,742 | 5.91e-05 | | | |
| 2023-09-04 | random 50,000 (expected) | 50,000 | 2,594 | 1.04e-06 | | | |

| K | mean density | log gap to 0.003 |
|---:|---:|---:|
| 5,000 | 6.58e-04 | 1.52 |
| 10,000 | 3.65e-04 | 2.11 |
| 20,000 | 1.84e-04 | 2.79 |
| 34,000 | 1.05e-04 | 3.36 |
| 50,000 | 6.83e-05 | 3.78 |

**Frozen: K = 5,000** (`config/graph.json paper_scale.K`).

Qualifications recorded before any fit:

- The paper's density lies outside the grid: every candidate is below 0.003, and
  the grid minimum is the nearest (factor 4.6, log gap 1.52). Extrapolating the
  observed trend (density roughly ∝ K^−0.8) the paper's figure corresponds to a
  top-K core of about 1,000–2,000 addresses, or to a different graph definition
  (undirected density, per-block graphs, another sampling rule). The frozen rule
  is applied as written; the grid is not extended after seeing the data.
- The random-50,000-node alternative described in the first author's earlier
  report yields an expected 1,500–2,600 induced edges per week (density equal to
  the full-chain value, ~10⁻⁶), i.e. an almost empty graph; it is tabulated and
  not used.
- Consequence if wrong: the node population differs from the paper's unknown
  one; a full-chain whole graph (Branch A's choice) differs from it by three
  orders of magnitude in density in the other direction.
- Optional secondary variant, registered now and run only after the primary M2
  table is complete: K = 20,000 (same pipeline, same seeds), reported separately
  and never substituted for the primary endpoint.

Compute note: at K = 5,000 the MCM workload is 5,000 × 32 = 160,000 cells per
week, 24,960,000 cells for 156 weeks.

## 2. N_max and compute (to be filled by Task 15 steps 1–2)

Pending: batched-solver cells/s and RSS for `n_max ∈ {32, 64}` on week
2022-03-07; GAT forward+backward time and RSS on the same week.
