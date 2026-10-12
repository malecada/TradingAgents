# Onchain replication, Branch B — design

Status: design frozen 2026-10-12 before any empirical fit. Branch
`research/onchain-replication-b-2026-10-12`, forked from the Codex replication
branch at `312460acd`. Branch A (Codex, `research/onchain-paper-replication-2026-09-24`)
continues independently; the two branches share the goal and will be compared at
the checkpoints in §12. Nothing in Branch A's research directory or package is
modified by this branch.

Decisions recorded here were taken under the session's AFK autonomy grant: where
a choice was offered, the recommended option was selected and is marked
`[afk-grant]`.

## 1. Goal

Implement the method of Çelik and Sefer, *Analyzing Transaction Graphs via
Motif-Based Graph Representation Learning for Cryptocurrency Price Prediction*
(Comput Econ 67:2055–2076, 2026), and evaluate it on Ethereum under a
pre-registered protocol that is feasible on the available machine.

First deliverable (**M2**, `[afk-grant]`): the initial ETH fold — train on
2022–2023, test on 2024 — with the full motif → MCM → MLP → GAT → attention-LSTM
model and the four price-only baselines (LSTM, HLSTM, GRU, SVM), for both the
direction task and the regression task, five seeds, one sealed test year.
Paper rows targeted for comparison: Table 1 ETH (regression) and Table 2 ETH
(direction, reported accuracy 80.4 %).

Not in scope for M2: BTC, folds other than 2024, Table 3 graph comparators,
Tables 4–6 treatments, author contact, paid compute.

## 2. Why a separate protocol

The audit of Branch A (published 2026-10-12) found that its "whole weekly graph,
no truncation" choice contradicts the paper's own evidence and makes the
computation infeasible locally:

- Paper §4.1 reports ETH graph density 0.003. The full-chain weekly graph has
  ~2.8M nodes and ~3.5M directed edges (density ≈ 4.6 × 10⁻⁷). Density 0.003 at
  comparable edge counts implies tens of thousands of nodes per graph.
- The first author's retained project report states that a random 50,000-node
  sample per graph was used because full graphs exceeded available compute.
- The paper's experiments ran on a single Colab P100.

Branch B therefore treats graph scale as a declared protocol assumption
(`paper_scale`), calibrated on a reported statistic, and records the whole-graph
interpretation as an alternative not pursued here.

## 3. Resources `[afk-grant]`

This laptop only: 12 cores, 16 GB RAM, budget ≤ 12 GiB resident for any stage,
no GPU, no money. Disk: artifacts under `research_artifacts/onchain-replication-b/`
(root partition, 24 GB free at design time); budget ≤ 6 GB. Raw sources are read
in place and never copied.

## 4. Data

### 4.1 Transactions

Retained AWS public-blockchain ETH daily transaction parquets, 2022-01-01 …
2024-12-31 (1,096 days, 1,207,460,745 rows, 107 GB of hash-verified zstd byte
spans). Day → directory mapping is the frozen
`research/onchain-graph-2026-09-16/fullpanel/plan.json` (`captures[day]`,
`expected_rows[day]`); 2024-01-01 is the special prototype capture. Span
reassembly reuses Branch A's hash-verified reader (`eth_source.projected_parquet`
and `AcquiredReader`), copied into this package with attribution so the branch
does not depend on Branch A's lifecycle modules. Columns read:
`block_timestamp, from_address, to_address, value, receipt_status`.

Admitted event: `receipt_status == 1`, `value > 0`, `to_address` present and
well-formed. Duplicated transaction hashes within a day are rejected. Each
admitted event contributes exactly once; exclusion counters are retained per day.

### 4.2 Prices

Coin Metrics daily `PriceUSD` for ETH, retained in
`research_artifacts/onchain-paper-replication-2026-09-24/sources/paper-prices-coinmetrics-eth-20260924/capture/<sha>/response.bin`
(2016-01-01 … 2024-12-31). Declared deviation from the paper's Yahoo Finance
source. Close of UTC day *d* is assumed available at the start of day *d+1*.

## 5. Weekly graphs

### 5.1 Full-week aggregation

Weeks are complete Monday-anchored UTC weeks. The first complete week is
2022-01-03, the last 2024-12-23 (156 weeks; 2024-12-30 is incomplete and
excluded). For each week, admitted events from its seven days are aggregated
with pyarrow/duckdb into ordered address pairs: `count`, `value_eth` (sum of
`value / 1e18`, float64). Node attributes are in/out counts and in/out native
volumes. Self-transfers are retained as self-edges. The full-week aggregate is
not stored; only its summary (nodes, edges, exclusion counters) and the
paper-scale subgraph are.

### 5.2 Paper-scale subgraph (`paper_scale`, declared assumption F01b)

The induced subgraph on the **K most active addresses** of the week, activity =
in-count + out-count, ties broken by lexicographic address. Node and edge
features are recomputed on the induced subgraph: node
`[log1p(in_count), log1p(out_count), log1p(in_volume), log1p(out_volume)]`,
edge `[log1p(count), log1p(value_eth)]`.

K is **calibrated once, label-free**, on four dispersed training weeks
(2022-03-07, 2022-09-05, 2023-03-06, 2023-09-04): the directed density
E / (K(K−1)) of the induced subgraph is tabulated for K ∈ {5,000, 10,000,
20,000, 34,000, 50,000}, and K is fixed to the value whose mean density is
closest in log-space to the paper's 0.003, subject to a hard cap K ≤ 50,000 for
compute. The table and the chosen K are committed in
`research/onchain-replication-b-2026-10-12/CALIBRATION.md` before any dictionary
or fit is run. The random-50,000-node alternative is tabulated alongside for the
record (it is expected to yield a near-empty induced graph) but is not used.

### 5.3 Node neighborhoods (declared assumption F04b)

Weak one-hop induced neighborhood of a center within the paper-scale graph: the
center plus its in- and out-neighbors, with all induced directed edges. To bound
matching cost, a neighborhood retains at most `N_max` nodes: the center plus the
`N_max − 1` neighbors with the largest interaction count with the center (ties
by address). `N_max = 32` unless the compute calibration in §9 shows that 64 fits
the budget; the value is frozen in `config/dictionary.json` before any fit.
Neighborhoods are never silently truncated elsewhere; `N_max` is the single
declared cap.

Storage per week: `nodes.npy` (addresses as fixed-width bytes), `node_features.npy`
(K×4 float32), `edge_index.npy` (2×E int32), `edge_features.npy` (E×2 float32),
`summary.json`. Expected ≤ 20 MB/week.

## 6. Motif dictionary (per fold, training weeks only)

Paper §2.1 with the same numeric choices as Branch A for comparability:

- 512 neighborhoods sampled without replacement over (training week, center),
  seeded PCG64; initial weights equal; after each draw the weights of remaining
  centers that fall inside the drawn neighborhood (same week) are halved.
- Pairwise distance `1 − (S(A,B) + S(B,A)) / 2` with the matching score of §7.
- Average-linkage agglomerative clustering (scipy) into 32 clusters; the medoid
  (minimum within-cluster distance sum, ties by sample index) of each cluster is
  the motif.
- One dictionary per (fold, seed). Dictionary for seed *s* uses PCG64(s).

## 7. Graph matching (literal Algorithm 1)

Agreement functions on standardized-by-definition log features:
`s2(u,i) = exp(−mean_f (x_u − x_i)²)` for nodes, `s1` identically for edge
features; absent edge → 0. Objective Eq. 1 with α = 1 and the printed
`2·sqrt(l1·l2)` edge denominator; node term divided by `sqrt(n1·n2)`; total
divided by `1 + α`. Empty-edge graphs contribute 0 to the edge term.

Solver, transcribed from the rendered Algorithm 1 exactly as Branch A did
(D01/D03 of its decision register, adopted here as declared assumptions so the
two branches match on arithmetic):

```
M = V                                   # node agreement n1×n2
beta = 1.0
while beta <= 30.0 and iterations < 50:
    Q[u,i] = 0.5 * sum_{(u,v)∈E1,(i,j)∈E2} s1(e_uv, e_ij) * M[v,j] + alpha * V[u,i]
    M = exp(beta * Q); normalize rows (sum 1); normalize columns (sum 1)   # one pass each, log-domain
    beta *= 1.075
hard assignment: repeatedly take the global maximum of M, fix it, delete its
row and column; stop after min(n1,n2) picks; ties row-major.
score = Eq. 1 on the hard assignment.
```

The schedule yields 48 temperatures. Rectangular soft matrices are not forced
doubly stochastic; only the hard assignment is injective.

**Implementation**: two solvers with one contract.

- `reference.py`: per-pair, scalar/NumPy float64, written for readability. Used
  in tests and for the dictionary's 512×512 pairwise matrix.
- `batched.py`: many (neighborhood, motif) pairs at once. Pairs are grouped by
  shape bucket; within a bucket the edge-product lists of all pairs are
  concatenated with pair offsets; per temperature the update is one gather of
  `M[v,j]`, one multiply by the precomputed `0.5·s1` weights, one segment
  scatter-add into `Q`, then padded row/column log-sum-exp normalization in
  torch (CPU, float64). Hardening runs per pair on the final soft matrix.
  Required agreement with `reference.py`: scores within `atol 1e-9, rtol 1e-9`
  and identical hard assignments on tie-free fixtures.

Per-week MCM: for every node of the paper-scale graph and every motif, the
similarity score (Eq. 1 on the hard assignment) → `mcm.npy` (K×32 float32).
Per-week outputs are written atomically and skipped if present, so the stage is
resumable at week granularity.

## 8. Model, training, baselines

Architecture identical to Branch A's frozen `model.json` so results are
comparable on method (declared assumptions; the paper gives no widths):

- MLP 32 → 64 → 32, ReLU.
- GAT: layer 1 four heads × 16 (concat, ELU), layer 2 one head × 32 (identity);
  neighbors = incoming edges plus self once; LeakyReLU 0.2; no dropout.
- Graph vector: arithmetic mean over nodes → 32.
- Daily sequence of 28 steps; each step concatenates the graph vector of the
  latest complete week available at that step (week end + 1 day) with the
  training-scaled close → 33 inputs. LSTM 64, one layer. Additive attention
  (width 32) querying the final state over all steps. Head: regression scalar or
  two classification logits.
- Joint training of MLP, GAT, LSTM, attention and head. Dictionary and raw
  similarities are fixed. Within one batch each distinct week's graph is
  encoded once and reused for every day that references it; gradients still
  flow from every reference.
- Adam 1e-3, betas (0.9, 0.999), batch 16 chronological daily examples, 100
  fixed epochs, gradient-norm clip 1, no validation set, no early stopping, no
  seed selection. Seeds 11, 23, 37, 51, 71. Deterministic CPU execution.
- Regression target: next-day close, scaled by training mean/std; reported in
  USD. Direction target: `close[d+1] > close[d]`, ties → 0, cross-entropy.

Baselines on the same 28-day price window, same scaling, seeds and folds:
LSTM(64), GRU(64), HLSTM (shared lower LSTM(128) over four 7-day chunks, upper
LSTM(128) over chunk vectors; declared adaptation of Hou et al.), SVM (SVR / SVC
with RBF kernel on the flattened window; seed-independent).

Diagnostics (not paper rows, same training recipe): `constant_graph` (graph
input zeroed; isolates the price path) and `label_permutation` (training labels
permuted once with PCG64(20260924); must perform at chance).

## 9. Compute calibration (before freezing N_max)

On one training week, with the calibrated K: measure batched-solver throughput
(cells/s) and peak RSS for `N_max ∈ {32, 64}`, and GAT forward+backward time and
RSS on the paper-scale graph. Projected totals must fit: MCM for 156 weeks
≤ 48 h wall, one training arm-seed ≤ 6 h, RSS ≤ 12 GiB. The measurement and
the chosen `N_max` are committed in `CALIBRATION.md`. If neither value fits,
the next declared lever is K (re-calibrated downward with its density
consequence recorded), never silent subsampling.

## 10. Chronology and leakage controls

- Decision date *d* (UTC midnight starting day *d+1*): uses closes up to day
  *d* and weekly graphs whose week ended on or before *d* (end + 1 day lag).
- Fold: train labels end strictly before 2024-01-01; test decision dates are
  2024-01-01 … 2024-12-30 (label day ≤ 2024-12-31). Warm-up days without a
  full 28-step window or a required week are excluded and listed.
- Dictionary sampling, feature scaling and K/N_max calibration use training
  weeks only. The 2024 graphs are built in the same pass but never read by the
  dictionary or calibration stages (asserted by the stage's week filter and by
  a test).
- One-shot holdout: every arm-seed is trained once and evaluated on 2024 once.
  Failures are retained as failed cells; no reruns with changed settings.

## 11. Gates (pre-registered, `research/onchain-replication-b-2026-10-12/gates.json`)

Primary endpoint: ETH 2024 direction accuracy of the full model, mean over the
five seeds, with the signed difference to the paper's 80.4 % and a 2,000-draw
14-day moving-block bootstrap interval. Descriptive label "numerically close"
when |difference| ≤ 2 pp. Secondary: full model minus price-only LSTM accuracy
with the same bootstrap; regression MAE/RMSE/MAPE in USD. Chance control:
`label_permutation` accuracy within its bootstrap interval of the majority-class
rate. None of these is a stopping rule or a tuning target.

## 12. Checkpoints shared with Branch A

| CP | Branch B artifact | Comparable Branch A evidence |
|---|---|---|
| CP1 | 156 paper-scale weekly graphs + `CALIBRATION.md` | retained whole-graph builds (7–9 weeks) |
| CP2 | fold-2024 dictionaries (5 seeds) + MCM features for all 156 weeks + measured cells/s | pilot39 counters (59.3 cells/s) |
| CP3 | measured joint training step (time, RSS) and one full arm-seed run | neural resource pilot (refused) |
| CP4 | M2 result: all arms × 5 seeds on sealed 2024 + diagnostics | — |

Comparison is on reaching the checkpoint, measured throughput, and the fidelity
qualifications each branch carries; not on who matches 80.4 %.

## 13. Package layout

```
tradingagents/research/onchain_b/
  __init__.py
  sources.py        # day mapping from plan.json; span reassembly (copied, attributed)
  weekly.py         # admitted events → full-week aggregate → paper-scale subgraph
  calendar.py       # weeks, decision dates, availability, fold membership
  prices.py         # Coin Metrics reader, scaling, labels
  neighborhoods.py  # weak one-hop induced neighborhoods with N_max
  matching/
    agreement.py    # s1, s2, Eq. 1 score
    reference.py    # per-pair literal Algorithm 1
    batched.py      # bucketed multi-pair solver
  dictionary.py     # sampling, pairwise distances, average linkage, medoids
  mcm.py            # per-week K×32 features
  model.py          # MLP, GAT, pooling, LSTM, attention, heads; baselines
  data.py           # daily examples, batching, week-graph cache
  train.py          # one arm-seed fit; checkpoints; deterministic seeding
  evaluate.py       # metrics, bootstrap, result ledger
  cli.py            # stages: build-graphs, calibrate, dictionary, mcm, fit, evaluate, report
tests/research/onchain_b/   # focused tests per module
research/onchain-replication-b-2026-10-12/
  PROTOCOL.md  config/*.json  gates.json  CALIBRATION.md  STATE.md  RESULT.md
research_artifacts/onchain-replication-b/   # gitignored arrays, checkpoints, logs
```

Execution is plain Python under `nohup` with per-stage logs; stages are
idempotent at week / arm-seed granularity. Resource limits are enforced with
`systemd-run --user -p MemoryMax=12G` for long stages; RSS is sampled into the
stage log. No lease, owner, seal or receipt machinery.

## 14. Testing

- `weekly`: toy day fixtures → exact pair aggregates, exclusion counters, self
  edges, top-K selection ties.
- `calendar`: availability inequality, fold boundaries, warm-up exclusion, 156
  expected weeks.
- `matching`: Eq. 1 against hand-computed values; reference solver vs brute-force
  best assignment on ≤ 4-node graphs (solver score ≤ optimum, equality on
  trivial cases); `batched` vs `reference` on random bucket mixes at 1e-9;
  relabeling invariance on tie-free fixtures.
- `dictionary`: seeded reproducibility; overlap halving; medoid rule.
- `model`: finite nonzero gradients in every block; permutation invariance of
  the graph vector; padding contributes zero attention; synthetic learning test
  (loss ↓ ≥ 80 % in 500 updates).
- `data`: no 2024 week or close reachable from a 2023 decision date.
- `evaluate`: metrics on fixed vectors; bootstrap determinism.

## 15. Open assumptions ledger (`fidelity-b.json`)

Carries Branch A's F01–F14 dispositions where unchanged, replaces F01/F04 with
F01b (paper-scale top-K) and F04b (N_max neighborhood cap), and adds the
calibration records. Every entry names its source locator, the choice made, and
the consequence if wrong. `exact_reproduction_eligible = false`.
