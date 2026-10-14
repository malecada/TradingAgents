# Branch B3 — whole-graph structure features with a 20k motif graph

Status: design approved in conversation 2026-10-14, written before any B3 data pass
or outcome. Branch `research/onchain-replication-b-2026-10-12`. B2 (weekly activity,
exchange/whale flows, top-5,000 motifs) was negative on 2019–2024
(`research/onchain-b2-2026-10-13/`); its sealed 2025-01-06 → 2026-10-05 window was
never opened. B3 asks one more predictive question with features B2 did not have.

## 1. Decisions taken with the user (2026-10-14)

1. Goal: prediction, one more try, screened on 2017–2024; survivors (if any) get the
   single sealed 2025–26 ETH test.
2. Targets: B2's five plus a 4-week horizon (return and realised volatility).
3. Scope: structural features on the **full** weekly graph (all addresses); motif
   features recomputed on the **top 20,000** addresses (4× B2).
4. Approach A: one new data pass computing everything per week; no full pair tables
   stored (≈ 60–75 GB, not available).

## 2. Question

Does the structure of the whole weekly ETH transaction graph — degree inequality,
connectivity, reciprocity, dense cores, centrality concentration, clustering,
address turnover — or motif structure on a 4× larger graph add out-of-sample
information to price/volume history and B2's activity features, for next-day,
next-week and next-4-week targets?

## 3. Data pass

Reuses B2 unchanged: `onchain_b2.s3source` (S3 days 2017–2021 and 2025–26, retained
spans 2022–24), B2's frozen labels (`research_artifacts/onchain-b2/labels/labels.json`,
4,961 addresses) and B2's market files (`market/dev.json`, `sealed/market_sealed.json`).
Weeks 2017-01-02 … 2026-10-05 (510). Same admission rule
(`onchain_b.weekly.admitted_events`) and pair aggregation.

Per week, one fresh process (as in B2's final capture) computes and writes:

1. `weeks/<week>.json` — B2 F1 activity and F3a role flows (recomputed by the same
   functions) and the F4 snapshot features of §4.1–4.6;
2. `graphs/<week>/` — top-20,000 induced subgraph (`onchain_b.weekly.top_k_subgraph`,
   K = 20,000);
3. `keys/<week>.npy` — sorted unique uint64 address keys (first 16 hex digits of the
   lower-case address; ETH addresses are hash-derived, so collisions are negligible),
   temporary input to §4.7.

Markers, failure isolation and resumption follow B2 (`.unavailable.json`,
`.failed.json`, summary written last). Two loops: S3 weeks (8 GiB cap) and
retained-span weeks 2022–24 (5.5 GiB cap).

## 4. Whole-graph structure features (F4, prefix `f4_`)

Graph: G = directed aggregated pair graph of the week (all admitted transfers);
self-loops are ignored for degree, components, core, reciprocity and clustering.
U = undirected simple version of G. N = addresses, E = distinct ordered pairs.

### 4.1 Degree (6)

In-degree = distinct senders, out-degree = distinct receivers, total degree =
distinct counterparties in U. `f4_indeg_gini`, `f4_outdeg_gini`, `f4_deg_gini`
(Gini over all nodes); `f4_deg_tail` = Hill estimator of total degree on the top
k = max(50, ⌈0.01 N⌉) nodes, α = 1 / mean(log(d_i / d_(k+1))); `f4_leaf_share` = share
of nodes with total degree 1; `f4_maxdeg_share` = max total degree / Σ total degree.

### 4.2 Connectivity (4)

Weakly connected components of U (`scipy.sparse.csgraph.connected_components`):
`f4_components` (count), `f4_giant_node_share`, `f4_giant_value_share` (ETH on edges
inside the largest component / total non-self ETH), `f4_pair_components` (components
of exactly two nodes).

### 4.3 Reciprocity (2)

Over non-self directed edges: `f4_recip_edge_share` = share of edges (u,v) whose
reverse (v,u) exists; `f4_recip_value_share` = ETH on reciprocated edges / total.

### 4.4 Dense core (5)

k-core of U by iterative vectorised peeling: `f4_core2_share`, `f4_core3_share`,
`f4_core5_share`, `f4_core10_share` (nodes in the k-core / N) and
`f4_core3_value_share` (ETH on edges with both ends in the 3-core / total non-self ETH).

### 4.5 Centrality concentration (6)

PageRank on G (damping 0.85, uniform teleport, dangling mass redistributed
uniformly, stop at L1 change < 1e-10 or 100 iterations), unweighted and ETH-weighted
(edge weight = summed ETH). `f4_pr_top100_share`, `f4_pr_gini`,
`f4_prv_top100_share`, `f4_prv_gini`, `f4_pr_ex_share`, `f4_prv_ex_share` (PageRank
mass on labelled exchanges).

### 4.6 Clustering (2)

Global transitivity of U estimated from 200,000 wedges: centre chosen with
probability ∝ d(d−1)/2, two distinct neighbours uniformly, closed if they are
adjacent; seed = 20261014 + week index. `f4_transitivity`; `f4_log_wedges` =
log(total wedges Σ d(d−1)/2).

### 4.7 Address history (4; sequential pass over `keys/`)

Weeks in order from 2017-01-02. A Bloom filter (2³³ bits = 1 GiB, 5 hash positions
from multiply-shift of the 64-bit key) holds every key seen in earlier weeks
(false-positive rate ≈ 4 × 10⁻⁴ at 400M keys). `f4_new_share` = share of the week's
addresses not in the filter ("new since 2017-01-02"); `f4_prev1_share` = share
active in week w−1; `f4_prev4_share` = share active in any of w−4 … w−1;
`f4_return_share` = share not active in w−4 … w−1 but present in the filter. Early
2017 weeks over-count "new" (no pre-2017 history); development samples start at
2017-10-02 and features enter as 8-week z-scores. Key files are deleted after the
pass once counts are verified.

Total F4 = 29 raw features.

## 5. Motifs on the top-20,000 graph (F5, prefix `f5_`)

Dictionary rebuilt with B2's rules (seed 11, 512 samples, 32 medoids, n_max 32,
matching config from `onchain_b.config.load('matching')`) from the 20k graphs of
weeks 2017-01-02 … 2018-12-24. MCM per week (20,000 × 32 cells). Features as B2 F2:
best-motif histogram, mean score, ETH-volume-weighted mean score (96).

## 6. Targets

B2's T1–T5 unchanged, plus:

| ID | Sample | Definition | Loss |
|---|---|---|---|
| T6 | weekly | 4-week log return log(close[m+28]/close[m]) | MSE |
| T7 | weekly | 4-week log realised volatility log √Σ r², daily log returns m+1 … m+28 | MSE |

Windows as B2 (development 2017-10-02 → 2024-12-31, sealed holdout from 2025-01-01,
last label 2026-10-12). A weekly sample enters a target only if that target's whole
label window lies in its window; development prices end at 2024-12-31, so no T6/T7
label can reach the sealed period.

## 7. Feature sets and comparisons

| Set | Contents |
|---|---|
| S0 | F0 price/volume (B2) |
| S1 | F0 + F1 activity (B2) |
| S5 | S1 + F4 structure |
| S6 | S5 + F5 20k motifs |
| S7 | S6 + F3a role flows (all on-chain) |

All features enter as B2's causal transforms (8-week z-score clipped to ±10, one-week
change). Comparisons: **S5 vs S1** (does structure add to activity?), **S6 vs S5**
(do 20k motifs add to structure?), **S7 vs S0** (does anything on-chain beat price
alone?). 7 targets × 2 families × 3 comparisons = **42**.

## 8. Screen

- Folds: expanding walk-forward, test years 2019–2024; purge = label length (T1 1 day,
  T2–T5 7 days, T6–T7 28 days).
- Linear: logistic (T1, T2) / ridge (others), alpha grid {0.1, 1, 10, 100, 1e3, 1e4,
  1e5}, inner validation on the last 52 weeks / 365 days only when the training window
  holds ≥ 2× that; otherwise registered fallback alpha 100; chosen alpha recorded.
- Trees: HistGradientBoosting, max_iter 100, learning_rate 0.05, max_leaf_nodes 7,
  min_samples_leaf 30, l2_regularization 1.0, random_state 11.
- Bootstrap blocks: 14 days (T1), 4 weeks (T2–T5), 8 weeks (T6–T7); 2,000 draws; seed
  20261014.
- Gate, selection, report: as B2 after its amendments (interval upper end < 0 and
  better in ≥ 4 of 6 years; ≤ 3 selected by relative upper bound, ties prefer S6/S7;
  Brier, per-year losses, missing-target counts, multiplicity disclosure).

## 9. Holdout

As B2: the screen refuses to overwrite `selection.json`; the holdout runs only for a
committed, non-empty selection, writes a one-shot lock with commit and blob before any
sealed read, refits on all development samples, Holm at α = 0.05. If the selection is
empty, the sealed window stays unread.

## 10. Compute and storage

- Data pass ≈ 15–18 h (two loops); peak ≈ 5 GB per S3 week (B2 measured ≈ 4 GB at 17M
  rows plus the full-graph arrays).
- History pass ≈ 1 h; key files ≈ 8 GB temporary.
- Dictionary ≈ 2 min; MCM 20k ≈ 50 s/week → ≈ 3.5 h with two shards after the pass
  completes.
- Storage kept: ≈ 1.2 GB graphs + 1.3 GB MCM + small JSON. Free space at design time:
  21 GB.

## 11. Package layout

```
tradingagents/research/onchain_b3/
  structure.py  # F4 §4.1–4.6 from a pair table
  history.py    # keys, Bloom filter, §4.7 sequential pass
  weekbuild3.py # one week: B2 F1/F3a + F4 + 20k graph + keys
  targets3.py   # T6, T7 (T1–T5 from onchain_b2.targets)
  dataset3.py   # feature sets S0/S1/S5/S6/S7, per-target windows
  screen3.py    # targets, purges, blocks and comparisons from config
  cli.py        # weeks, history, dictionary, mcm, features, screen, holdout
tests/research/onchain_b3/
research/onchain-b3-2026-10-14/   # CHARTER.md, config/b3.json, gates.json, STATE.md
research_artifacts/onchain-b3/     # gitignored
```

`onchain_b2` and `onchain_b` are imported, not edited (B2's registered code stays as
it was screened).

## 12. Testing

Hand-built graphs with known answers for every F4 feature (Gini, Hill on a synthetic
power law, components, reciprocity, k-core sizes, PageRank against a dense reference
on a small graph, transitivity estimate against exact on a small graph); Bloom filter
false-positive bound and history shares on toy week sequences; T6/T7 on toy prices;
per-target purge and windows (no T6/T7 label beyond 2024-12-31 in development);
screen comparisons and blocks from config; week build idempotence and failure markers;
sealing and one-shot holdout guards reused from B2.

## 13. Checkpoints

- **B3-CP1:** 510 weeks with F1/F3a/F4 snapshot features, 20k graphs and keys.
- **B3-CP2:** history features, dictionary, MCM, feature table.
- **B3-CP3:** screen and committed selection.
- **B3-CP4:** holdout result, or the recorded decision not to open it.
