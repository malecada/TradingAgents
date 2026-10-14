# Onchain B3 Graph-Structure Screen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compute 29 whole-graph structure features on every weekly ETH graph plus motif features on a 20k-address graph, and screen them for seven targets (incl. a 4-week horizon) on 2017–2024 with a one-shot sealed 2025–26 confirmation.

**Architecture:** New subpackage `tradingagents/research/onchain_b3/` that imports — never edits — `onchain_b2` (day reader, labels, market, activity/role features, targets, transforms, screen primitives, holdout guards) and `onchain_b` (aggregation, top-K graph, dictionary, MCM). New modules: graph-structure features (`structure.py`), cross-week address history (`history.py`), one-week builder, 4-week targets, dataset, screen/holdout wrappers driven by `config/b3.json`, and a CLI.

**Tech Stack:** Python 3.13 `.venv`, NumPy 2.3, SciPy 1.17 (`sparse`, `csgraph`), pyarrow 23, pandas 2.3, scikit-learn 1.7, PyTorch CPU (MCM), networkx (test oracle only), pytest.

**Spec:** `docs/superpowers/specs/2026-10-14-onchain-b3-graph-structure-design.md`

## Global Constraints

- Worktree `/home/malecada/master_thesis/TradingAgents-onchain-b`, branch `research/onchain-replication-b-2026-10-12`. Do not modify `tradingagents/research/onchain_b/`, `tradingagents/research/onchain_b2/`, B2 study/artifact files, or Branch A paths.
- Weeks 2017-01-02 … 2026-10-05 (510), windows and graph lag exactly as B2 (`onchain_b2.periods`). Development prices end 2024-12-31 (`onchain_b2.market.load_dev`); sealed market and labels are B2's frozen files under `research_artifacts/onchain-b2/`.
- K = 20,000 for the motif graph; dictionary seed 11, 512 samples, 32 motifs, n_max 32, weeks 2017-01-02 … 2018-12-24; matching config `onchain_b.config.load('matching')`.
- F4: Hill k = max(50, ⌈0.01 N⌉); cores {2, 3, 5, 10}; PageRank damping 0.85, tol 1e-10 (L1), max_iter 100, self-loops ignored; 200,000 wedges, seed 20261014 + week index; Bloom 2³³ bits, 5 hashes; address key = first 16 hex digits after `0x`.
- Targets T1–T5 as B2; T6 = log(close[m+28]/close[m]); T7 = log √Σ r² over m+1 … m+28. Purge = horizon (1 / 7 / 28 days); bootstrap blocks 14 days (T1), 4 weeks (T2–T5), 8 weeks (T6–T7); 2,000 draws; seed 20261014.
- Sets S0 f0 · S1 f0+f1 · S5 S1+f4 · S6 S5+f5 · S7 S6+f3a; comparisons (S5,S1), (S6,S5), (S7,S0); 42 total.
- Linear alpha grid {0.1, 1, 10, 100, 1e3, 1e4, 1e5}, fallback 100, inner search only when train ≥ 2 × inner_len (52 weekly / 365 daily); trees max_iter 100, learning_rate 0.05, max_leaf_nodes 7, min_samples_leaf 30, l2 1.0, random_state 11.
- Gate as B2 (upper bound < 0 and ≥ 4 of 6 years); select ≤ 3 by upper bound / comparator loss, ties prefer S6/S7; screen never overwrites `selection.json`; holdout one-shot lock, Holm α = 0.05.
- Week builds: one fresh process per week; S3 loop cap 8 GiB, local-span loop cap 5.5 GiB; torch only in dictionary/MCM stages, threads 2.
- Documentation impersonal (no "we/our"). Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Test command: `cd /home/malecada/master_thesis/TradingAgents-onchain-b && OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3 -q`.

## Review Focus

1. A week graph with no reciprocated edge, no wedge or a single component → every F4 value finite (0 where undefined), no crash (Task 2 `test_degenerate_graphs_are_finite`).
2. Addresses with only self-transfers (total degree 0) → counted in N, not leaves, no division by zero (Task 2 `test_self_only_nodes`).
3. An unavailable week in the middle → its history features None, the next four weeks' window features NaN, the Bloom filter continues (Task 3 `test_missing_week_poisons_window_not_bloom`).
4. A 4-week label that would reach past 2024-12-31 in development → target missing, never computed from sealed prices (Task 5 `test_dev_four_week_targets_stop_at_cutoff`).
5. MCM or history stage started before all 510 weeks are built or marked → refused (Task 7 `test_late_stages_refuse_incomplete_capture`).

---

### Task 1: Skeleton, configuration, registration

**Files:**
- Create: `tradingagents/research/onchain_b3/__init__.py`, `tradingagents/research/onchain_b3/config.py`
- Create: `research/onchain-b3-2026-10-14/config/b3.json`, `research/onchain-b3-2026-10-14/gates.json`, `research/onchain-b3-2026-10-14/CHARTER.md`, `research/onchain-b3-2026-10-14/STATE.md`
- Modify: `.gitignore` (append `/research_artifacts/onchain-b3/`)
- Test: `tests/research/onchain_b3/__init__.py`, `tests/research/onchain_b3/test_config.py`

**Interfaces:**
- Produces: `config.ROOT`, `config.STUDY`, `config.ARTIFACTS`, `config.B2_ARTIFACTS` (Paths), `config.load() -> dict`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b3/test_config.py
from tradingagents.research.onchain_b3 import config


def test_frozen_numbers():
    c = config.load()
    assert c['k'] == 20000 and c['dictionary']['seed'] == 11 and c['structure']['cores'] == [2, 3, 5, 10]
    assert c['structure']['wedges'] == 200000 and c['history']['bloom_bits_log2'] == 33
    assert set(c['targets']) == {'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'}
    assert c['targets']['T6']['horizon'] == 28 and c['targets']['T7']['block'] == 8
    assert c['comparisons'] == [['S5', 'S1'], ['S6', 'S5'], ['S7', 'S0']] and c['gate']['seed'] == 20261014
    assert c['models']['fallback_alpha'] == 100.0 and c['models']['trees']['min_samples_leaf'] == 30


def test_paths_and_ignore():
    assert config.B2_ARTIFACTS.name == 'onchain-b2' and config.ARTIFACTS.name == 'onchain-b3'
    assert '/research_artifacts/onchain-b3/' in (config.ROOT / '.gitignore').read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_config.py -q`
Expected: collection error (`ModuleNotFoundError: tradingagents.research.onchain_b3`)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b3/__init__.py
"""Branch B3: whole-graph structure features and 20k motifs (spec 2026-10-14-onchain-b3-graph-structure-design.md)."""
```

```python
# tradingagents/research/onchain_b3/config.py
"""Frozen B3 configuration (research/onchain-b3-2026-10-14/config/b3.json)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'research' / 'onchain-b3-2026-10-14'
ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b3'
B2_ARTIFACTS = ROOT / 'research_artifacts' / 'onchain-b2'


def load() -> dict:
    return json.loads((STUDY / 'config' / 'b3.json').read_text())
```

`research/onchain-b3-2026-10-14/config/b3.json`:

```json
{
 "k": 20000,
 "n_max": 32,
 "dictionary": {"seed": 11, "first_week": "2017-01-02", "last_week": "2018-12-24", "sample_count": 512, "size": 32},
 "roles": {"deposit_share": 0.9, "whales": 100, "top_share_n": 100},
 "structure": {"hill_min": 50, "hill_frac": 0.01, "cores": [2, 3, 5, 10],
               "pagerank": {"damping": 0.85, "tol": 1e-10, "max_iter": 100},
               "wedges": 200000, "wedge_seed": 20261014},
 "history": {"bloom_bits_log2": 33, "bloom_hashes": 5},
 "transforms": {"z_window": 8, "z_min": 6, "z_clip": 10.0},
 "targets": {
  "T1": {"kind": "daily", "task": "classification", "horizon": 1, "block": 14},
  "T2": {"kind": "weekly", "task": "classification", "horizon": 7, "block": 4},
  "T3": {"kind": "weekly", "task": "regression", "horizon": 7, "block": 4},
  "T4": {"kind": "weekly", "task": "regression", "horizon": 7, "block": 4},
  "T5": {"kind": "weekly", "task": "regression", "horizon": 7, "block": 4},
  "T6": {"kind": "weekly", "task": "regression", "horizon": 28, "block": 8},
  "T7": {"kind": "weekly", "task": "regression", "horizon": 28, "block": 8}},
 "sets": {"S0": ["f0_"], "S1": ["f0_", "f1_"], "S5": ["f0_", "f1_", "f4_"],
          "S6": ["f0_", "f1_", "f4_", "f5_"], "S7": ["f0_", "f1_", "f4_", "f5_", "f3a_"]},
 "comparisons": [["S5", "S1"], ["S6", "S5"], ["S7", "S0"]],
 "graph_sets": ["S6", "S7"],
 "families": ["linear", "trees"],
 "folds": {"test_years": [2019, 2020, 2021, 2022, 2023, 2024], "inner_len": {"weekly": 52, "daily": 365}},
 "models": {"alphas": [0.1, 1, 10, 100, 1000, 10000, 100000], "fallback_alpha": 100.0,
            "trees": {"max_iter": 100, "learning_rate": 0.05, "max_leaf_nodes": 7, "min_samples_leaf": 30,
                      "l2_regularization": 1.0, "random_state": 11}},
 "gate": {"draws": 2000, "seed": 20261014, "min_year_wins": 4, "max_selected": 3, "alpha": 0.05}
}
```

`research/onchain-b3-2026-10-14/gates.json`:

```json
{
 "registered": "2026-10-14",
 "spec": "docs/superpowers/specs/2026-10-14-onchain-b3-graph-structure-design.md",
 "targets": "T1-T5 as B2; T6 4-week log return; T7 4-week log realised volatility",
 "comparisons": [["S5", "S1"], ["S6", "S5"], ["S7", "S0"]],
 "families": ["linear", "trees"],
 "screen_gate": "pooled loss difference 95% circular block-bootstrap interval entirely below 0 AND lower loss in >= 4 of 6 test years (2019-2024)",
 "selection": "at most 3 passing configurations by interval upper bound divided by comparator loss; ties prefer S6/S7; selection.json committed before any holdout read; screen never overwrites it",
 "holdout_gate": "one-shot lock with selection commit and blob; refit on all development samples; one-sided bootstrap p; Holm-adjusted p < 0.05 and mean difference < 0",
 "sealed_window": "ETH weekly decisions 2025-01-06..2026-10-05 (never read by B2); daily 2025-01-01..2026-10-11",
 "no_tuning": "no feature, model or threshold change after any holdout read"
}
```

`research/onchain-b3-2026-10-14/CHARTER.md`:

```markdown
# Branch B3 charter — whole-graph structure and 20k motifs

Registered 2026-10-14 before any B3 data pass or outcome. Spec:
`docs/superpowers/specs/2026-10-14-onchain-b3-graph-structure-design.md`; numbers in
`config/b3.json`; rules in `gates.json`.

Question: do structural features of the full weekly ETH transaction graph (degree
inequality, connectivity, reciprocity, dense cores, centrality concentration,
clustering, address turnover) or motif features on a 20,000-address graph add
out-of-sample information to price/volume history and activity, for next-day,
next-week and 4-week targets? Development 2017-10 → 2024 (walk-forward 2019–2024);
the sealed ETH window 2025-01-06 → 2026-10-05, never read by B2, is opened once and
only for a committed, non-empty selection. Prior: B2 found no on-chain information
in activity, role flows or top-5,000 motifs.
```

`research/onchain-b3-2026-10-14/STATE.md`:

```markdown
# Branch B3 state

2026-10-14 — Charter, configuration and gates registered. No data pass, feature or
fit. Next: implement `tradingagents/research/onchain_b3` per
`docs/superpowers/plans/2026-10-14-onchain-b3-graph-structure.md`.
```

Append to `.gitignore`:

```
# Branch B3 artifacts (weeks, graphs, keys, history, MCM, features, logs)
/research_artifacts/onchain-b3/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_config.py -q`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b3 tests/research/onchain_b3 research/onchain-b3-2026-10-14 .gitignore
git commit -m "feat(onchain-b3): register B3 charter, config and gates"
```

---

### Task 2: Whole-graph structure features (F4 §4.1–4.6)

**Files:**
- Create: `tradingagents/research/onchain_b3/structure.py`
- Test: `tests/research/onchain_b3/test_structure.py`

**Interfaces:**
- Consumes: `onchain_b.weekly._index(pairs) -> (addresses S42[N], s int[E], d int[E], count int64[E], value float64[E])`.
- Produces: `gini(x) -> float`; `hill(d, k_min, frac) -> float`; `undirected_edges(s, d, n) -> (a, b)` (int arrays, a < b, unique, self-loops dropped); `kcore_alive(a, b, n, k, alive=None) -> bool[n]`; `pagerank(s, d, w, n, damping, tol, max_iter) -> float[n]`; `transitivity_estimate(a, b, n, samples, seed) -> (float, float)`; `structure_features(idx, is_ex: bool[n], cfg: dict, seed: int) -> dict` with the 25 keys `f4_indeg_gini, f4_outdeg_gini, f4_deg_gini, f4_deg_tail, f4_leaf_share, f4_maxdeg_share, f4_components, f4_giant_node_share, f4_giant_value_share, f4_pair_components, f4_recip_edge_share, f4_recip_value_share, f4_core2_share, f4_core3_share, f4_core5_share, f4_core10_share, f4_core3_value_share, f4_pr_top100_share, f4_pr_gini, f4_pr_ex_share, f4_prv_top100_share, f4_prv_gini, f4_prv_ex_share, f4_transitivity, f4_log_wedges`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b3/test_structure.py
import math

import networkx as nx
import numpy as np
import pyarrow as pa
import pytest

from tradingagents.research.onchain_b.weekly import _index
from tradingagents.research.onchain_b3 import structure as ST

CFG = {'hill_min': 50, 'hill_frac': 0.01, 'cores': [2, 3, 5, 10],
       'pagerank': {'damping': 0.85, 'tol': 1e-12, 'max_iter': 1000}, 'wedges': 200000}


def addr(i):
    return '0x' + f'{i:040x}'


def pairs(edges):
    return pa.table({'src': [addr(a) for a, b, c, v in edges], 'dst': [addr(b) for a, b, c, v in edges],
                     'count': [c for *_, c, v in edges], 'value_eth': [float(v) for *_, v in edges]})


def test_gini_and_hill():
    assert ST.gini([1, 1, 1, 1]) == pytest.approx(0.0) and ST.gini([0, 0, 0, 4]) == pytest.approx(0.75)
    rng = np.random.default_rng(0)
    x = (1 - rng.random(200000)) ** (-1 / 2.0)              # Pareto, tail index 2
    assert ST.hill(x, 50, 0.01) == pytest.approx(2.0, abs=0.2)


def test_against_networkx_on_random_graph():
    rng = np.random.default_rng(1)
    g = nx.gnm_random_graph(400, 1600, seed=2, directed=True)
    edges = [(u, v, 1, float(rng.integers(1, 10))) for u, v in g.edges()]
    idx = _index(pairs(edges))
    addresses, s, d, count, value = idx
    n = len(addresses)
    f = ST.structure_features(idx, np.zeros(n, bool), CFG, seed=7)
    # rebuild the same graph in networkx on the index's node numbering
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    for a, b, w in zip(s, d, value):
        if a != b:
            G.add_edge(int(a), int(b), weight=float(w))
    U = G.to_undirected()
    assert f['f4_components'] == nx.number_connected_components(U)
    pr = nx.pagerank(G, alpha=0.85, tol=1e-12, max_iter=1000, weight=None)
    p = ST.pagerank(s, d, np.ones(len(s)), n, 0.85, 1e-12, 1000)
    assert max(abs(p[i] - pr[i]) for i in range(n)) < 1e-8
    prv = nx.pagerank(G, alpha=0.85, tol=1e-12, max_iter=1000, weight='weight')
    pv = ST.pagerank(s, d, value, n, 0.85, 1e-12, 1000)
    assert max(abs(pv[i] - prv[i]) for i in range(n)) < 1e-8
    core = nx.core_number(nx.Graph(U))
    for k in (2, 3, 5, 10):
        assert f[f'f4_core{k}_share'] == pytest.approx(sum(1 for v in core.values() if v >= k) / n)
    assert f['f4_transitivity'] == pytest.approx(nx.transitivity(nx.Graph(U)), abs=0.01)
    recip = sum(1 for a, b in G.edges() if G.has_edge(b, a)) / G.number_of_edges()
    assert f['f4_recip_edge_share'] == pytest.approx(recip)


def test_hand_graph_values():
    # A->B 2x(10), B->A 1x(5), B->C (1), C->D (1), E->E self (3), F->G (1)
    e = [(1, 2, 2, 10), (2, 1, 1, 5), (2, 3, 1, 1), (3, 4, 1, 1), (5, 5, 1, 3), (6, 7, 1, 1)]
    idx = _index(pairs(e))
    n = len(idx[0])
    f = ST.structure_features(idx, np.zeros(n, bool), CFG, seed=1)
    assert n == 7
    assert f['f4_components'] == 3 and f['f4_pair_components'] == 1      # {1,2,3,4}, {5}, {6,7}
    assert f['f4_giant_node_share'] == pytest.approx(4 / 7)
    assert f['f4_giant_value_share'] == pytest.approx(17 / 18)            # non-self ETH: 10+5+1+1+1
    assert f['f4_recip_edge_share'] == pytest.approx(2 / 5) and f['f4_recip_value_share'] == pytest.approx(15 / 18)
    assert f['f4_leaf_share'] == pytest.approx(4 / 7)                     # nodes 1, 4, 6, 7 have one counterparty
    assert f['f4_maxdeg_share'] == pytest.approx(2 / 8)                   # node 2 has 2 counterparties; sum of degrees 8


def test_self_only_nodes():
    e = [(1, 1, 1, 2.0), (2, 3, 1, 1.0)]
    idx = _index(pairs(e))
    n = len(idx[0])
    f = ST.structure_features(idx, np.zeros(n, bool), CFG, seed=1)
    assert n == 3 and f['f4_leaf_share'] == pytest.approx(2 / 3) and f['f4_components'] == 2
    assert all(math.isfinite(v) for k, v in f.items() if k != 'f4_deg_tail')


def test_degenerate_graphs_are_finite():
    idx = _index(pairs([(1, 2, 1, 1.0)]))
    f = ST.structure_features(idx, np.zeros(2, bool), CFG, seed=1)
    assert f['f4_transitivity'] == 0.0 and f['f4_log_wedges'] == 0.0 and f['f4_recip_edge_share'] == 0.0
    assert f['f4_core2_share'] == 0.0 and f['f4_components'] == 1
    assert all(math.isfinite(v) for k, v in f.items() if k != 'f4_deg_tail')


def test_exchange_pagerank_share():
    e = [(1, 9, 1, 1.0), (2, 9, 1, 1.0), (3, 9, 1, 1.0), (9, 4, 1, 1.0)]
    idx = _index(pairs(e))
    is_ex = np.array([a.decode() == addr(9) for a in idx[0]])
    f = ST.structure_features(idx, is_ex, CFG, seed=1)
    p = ST.pagerank(idx[1], idx[2], np.ones(len(idx[1])), len(idx[0]), 0.85, 1e-12, 1000)
    assert f['f4_pr_ex_share'] == pytest.approx(p[is_ex].sum() / p.sum())
```

Hand-graph expectations for `test_hand_graph_values`: undirected counterparties — 1:{2}, 2:{1,3}, 3:{2,4}, 4:{3}, 5:{} (self only), 6:{7}, 7:{6}; total degree [1,2,2,1,0,1,1], sum 8; leaves (degree 1) = nodes 1, 4, 6, 7 → 4/7.

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_structure.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b3/structure.py
"""Whole-graph structure features F4 §4.1–4.6 on the full weekly directed pair graph.

Self-loops are ignored throughout (degree, components, reciprocity, cores, PageRank, clustering).
All arrays are indexed by the node numbering of `onchain_b.weekly._index`.
"""
from __future__ import annotations

import math

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components


def gini(x):
    x = np.sort(np.asarray(x, float))
    n, s = len(x), x.sum()
    if n == 0 or s <= 0:
        return 0.0
    i = np.arange(1, n + 1)
    return float(2 * (i * x).sum() / (n * s) - (n + 1) / n)


def hill(d, k_min=50, frac=0.01):
    d = np.sort(np.asarray(d, float))[::-1]
    d = d[d > 0]
    n = len(d)
    k = min(max(k_min, math.ceil(frac * n)), n - 1)
    if k < 1:
        return float('nan')
    m = float(np.mean(np.log(d[:k] / d[k])))
    return 1.0 / m if m > 0 else float('nan')


def undirected_edges(s, d, n):
    m = s != d
    a = np.minimum(s[m], d[m]).astype(np.int64)
    b = np.maximum(s[m], d[m]).astype(np.int64)
    key = np.unique(a * n + b)
    return key // n, key % n


def kcore_alive(a, b, n, k, alive=None):
    alive = np.ones(n, bool) if alive is None else alive.copy()
    while True:
        e = alive[a] & alive[b]
        deg = np.bincount(a[e], minlength=n) + np.bincount(b[e], minlength=n)
        drop = alive & (deg < k)
        if not drop.any():
            return alive
        alive &= ~drop


def pagerank(s, d, w, n, damping, tol, max_iter):
    m = s != d
    s, d, w = s[m], d[m], np.asarray(w, float)[m]
    out = np.bincount(s, weights=w, minlength=n)
    P = sp.csr_matrix((w / out[s], (d, s)), shape=(n, n))
    dangling = out == 0
    p = np.full(n, 1.0 / n)
    for _ in range(max_iter):
        new = damping * (P @ p + p[dangling].sum() / n) + (1 - damping) / n
        done = np.abs(new - p).sum() < tol
        p = new
        if done:
            break
    return p


def transitivity_estimate(a, b, n, samples, seed):
    deg = np.bincount(a, minlength=n) + np.bincount(b, minlength=n)
    w = deg.astype(float) * (deg - 1) / 2
    W = w.sum()
    if W <= 0:
        return 0.0, 0.0
    rows = np.concatenate([a, b])
    cols = np.concatenate([b, a])
    order = np.lexsort((cols, rows))
    rows, cols = rows[order], cols[order]
    indptr = np.concatenate([[0], np.cumsum(np.bincount(rows, minlength=n))])
    keys = rows.astype(np.int64) * n + cols
    rng = np.random.Generator(np.random.PCG64(seed))
    c = rng.choice(n, size=samples, p=w / W)
    dc = deg[c]
    i = (rng.random(samples) * dc).astype(np.int64)
    j = (rng.random(samples) * (dc - 1)).astype(np.int64)
    j += j >= i
    u, v = cols[indptr[c] + i], cols[indptr[c] + j]
    q = u.astype(np.int64) * n + v
    pos = np.minimum(np.searchsorted(keys, q), len(keys) - 1)
    return float((keys[pos] == q).mean()), float(math.log(W))


def _share(x, total):
    return float(x / total) if total > 0 else 0.0


def structure_features(idx, is_ex, cfg, seed):
    addresses, s, d, count, value = idx
    n = len(addresses)
    s, d = s.astype(np.int64), d.astype(np.int64)
    m = s != d
    sm, dm, vm = s[m], d[m], np.asarray(value, float)[m]
    tot = vm.sum()
    f = {}
    indeg = np.bincount(dm, minlength=n)
    outdeg = np.bincount(sm, minlength=n)
    a, b = undirected_edges(s, d, n)
    deg = np.bincount(a, minlength=n) + np.bincount(b, minlength=n)
    f['f4_indeg_gini'], f['f4_outdeg_gini'], f['f4_deg_gini'] = gini(indeg), gini(outdeg), gini(deg)
    f['f4_deg_tail'] = hill(deg, cfg['hill_min'], cfg['hill_frac'])
    f['f4_leaf_share'] = float((deg == 1).mean())
    f['f4_maxdeg_share'] = _share(deg.max(), deg.sum())

    U = sp.csr_matrix((np.ones(len(a)), (a, b)), shape=(n, n))
    ncomp, labels = connected_components(U, directed=False)
    sizes = np.bincount(labels)
    g = int(sizes.argmax())
    f['f4_components'] = int(ncomp)
    f['f4_giant_node_share'] = float(sizes[g] / n)
    f['f4_giant_value_share'] = _share(vm[labels[sm] == g].sum(), tot)
    f['f4_pair_components'] = int((sizes == 2).sum())

    k1 = np.sort(sm * n + dm)
    k2 = dm * n + sm
    if len(k1):
        pos = np.minimum(np.searchsorted(k1, k2), len(k1) - 1)
        recip = k1[pos] == k2
    else:
        recip = np.zeros(0, bool)
    f['f4_recip_edge_share'] = float(recip.mean()) if len(recip) else 0.0
    f['f4_recip_value_share'] = _share(vm[recip].sum(), tot)

    alive, core3 = None, None
    for k in cfg['cores']:
        alive = kcore_alive(a, b, n, k, alive)
        f[f'f4_core{k}_share'] = float(alive.mean())
        if k == 3:
            core3 = alive.copy()
    f['f4_core3_value_share'] = _share(vm[core3[sm] & core3[dm]].sum(), tot)

    pc = cfg['pagerank']
    for name, w in (('pr', np.ones(len(s))), ('prv', value)):
        p = pagerank(s, d, w, n, pc['damping'], pc['tol'], pc['max_iter'])
        f[f'f4_{name}_top100_share'] = _share(np.sort(p)[::-1][:100].sum(), p.sum())
        f[f'f4_{name}_gini'] = gini(p)
        f[f'f4_{name}_ex_share'] = _share(p[is_ex].sum(), p.sum())

    f['f4_transitivity'], f['f4_log_wedges'] = transitivity_estimate(a, b, n, cfg['wedges'], seed)
    return f
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_structure.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b3/structure.py tests/research/onchain_b3/test_structure.py
git commit -m "feat(onchain-b3): whole-graph degree, connectivity, reciprocity, core, PageRank and clustering features"
```

---

### Task 3: Address history (keys, Bloom filter, sequential pass)

**Files:**
- Create: `tradingagents/research/onchain_b3/history.py`
- Test: `tests/research/onchain_b3/test_history.py`

**Interfaces:**
- Produces: `keys_from_addresses(addresses) -> np.ndarray[uint64]` (sorted unique); `Bloom(log2_bits, hashes)` with `.add(keys)`, `.contains(keys) -> bool[]`; `history_pass(weeks: list[str], load_keys: Callable[[str], np.ndarray | None], log2_bits: int, hashes: int) -> dict[str, dict | None]` with keys `f4_new_share, f4_prev1_share, f4_prev4_share, f4_return_share`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b3/test_history.py
import math

import numpy as np
import pytest

from tradingagents.research.onchain_b3 import history as H


def test_keys_from_addresses():
    a = np.array([b'0x0123456789abcdef0000000000000000000000ff', b'0xffffffffffffffff000000000000000000000000',
                  b'0x0123456789abcdef1111111111111111111111ff'], dtype='S42')
    k = H.keys_from_addresses(a)
    assert k.dtype == np.uint64 and k.tolist() == [0x0123456789ABCDEF, 0xFFFFFFFFFFFFFFFF]


def test_bloom_no_false_negatives_and_low_false_positive_rate():
    rng = np.random.default_rng(0)
    seen = np.unique(rng.integers(0, 2**63, 10000, dtype=np.uint64))
    other = np.setdiff1d(np.unique(rng.integers(0, 2**63, 10000, dtype=np.uint64)), seen)
    b = H.Bloom(20, 5)
    b.add(seen)
    assert b.contains(seen).all()
    assert b.contains(other).mean() < 0.01


def _seq(**weeks):
    return {w: np.array(sorted(v), dtype=np.uint64) if v is not None else None for w, v in weeks.items()}


def test_history_shares():
    keys = _seq(w0=[1, 2, 3], w1=[2, 3, 4, 5], w2=[1, 6], w3=[6], w4=[7], w5=[8], w6=[1, 9])
    out = H.history_pass(list(keys), keys.get, 20, 5)
    assert out['w0']['f4_new_share'] == 1.0 and out['w0']['f4_prev1_share'] == 0.0
    assert out['w1'] == {'f4_new_share': 0.5, 'f4_prev1_share': 0.5, 'f4_prev4_share': 0.5, 'f4_return_share': 0.0}
    assert out['w2']['f4_new_share'] == 0.5 and out['w2']['f4_prev1_share'] == 0.0 and out['w2']['f4_prev4_share'] == 0.5
    # w6 = {1, 9}; previous four weeks w2..w5 = {1, 6, 7, 8}: 1 is in the window (not returning), 9 is new
    assert out['w6'] == {'f4_new_share': 0.5, 'f4_prev1_share': 0.0, 'f4_prev4_share': 0.5, 'f4_return_share': 0.0}


def test_missing_week_poisons_window_not_bloom():
    keys = _seq(w0=[1, 2], w1=None, w2=[1, 3], w3=[3], w4=[3], w5=[3], w6=[2])
    out = H.history_pass(list(keys), keys.get, 20, 5)
    assert out['w1'] is None
    assert math.isnan(out['w2']['f4_prev1_share']) and math.isnan(out['w2']['f4_prev4_share'])
    assert math.isnan(out['w5']['f4_prev4_share']) and not math.isnan(out['w6']['f4_prev4_share'])
    assert out['w2']['f4_new_share'] == 0.5 and out['w6']['f4_new_share'] == 0.0     # 2 was seen in w0
    assert out['w6']['f4_return_share'] == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_history.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b3/history.py
"""Cross-week address history (spec §4.7): 64-bit address keys, a Bloom filter of every
earlier week, and exact last-week / last-four-weeks membership."""
from __future__ import annotations

import numpy as np

_C = (0x9E3779B97F4A7C15, 0xC2B2AE3D27D4EB4F, 0x165667B19E3779F9, 0xD6E8FEB86659FD93,
      0xFF51AFD7ED558CCD, 0xC4CEB9FE1A85EC53, 0x94D049BB133111EB)
_LUT = np.zeros(256, np.uint64)
for _i, _c in enumerate(b'0123456789abcdef'):
    _LUT[_c] = _i
for _i, _c in enumerate(b'ABCDEF'):
    _LUT[_c] = 10 + _i


def keys_from_addresses(addresses):
    raw = np.asarray(addresses).astype('S42').view(np.uint8).reshape(-1, 42)[:, 2:18]
    nib = _LUT[raw]
    shifts = np.arange(60, -1, -4, dtype=np.uint64)
    return np.unique(np.bitwise_or.reduce(nib << shifts, axis=1))


class Bloom:
    def __init__(self, log2_bits, hashes):
        self.log2, self.k = log2_bits, hashes
        self.bits = np.zeros(1 << (log2_bits - 3), np.uint8)

    def _positions(self, keys):
        keys = np.asarray(keys, np.uint64)
        return [(keys * np.uint64(_C[j])) >> np.uint64(64 - self.log2) for j in range(self.k)]

    def add(self, keys):
        for p in self._positions(keys):
            np.bitwise_or.at(self.bits, (p >> np.uint64(3)).astype(np.int64),
                             np.left_shift(np.uint8(1), (p & np.uint64(7)).astype(np.uint8)))

    def contains(self, keys):
        ok = np.ones(len(keys), bool)
        for p in self._positions(keys):
            byte = self.bits[(p >> np.uint64(3)).astype(np.int64)]
            ok &= ((byte >> (p & np.uint64(7)).astype(np.uint8)) & 1).astype(bool)
        return ok


def history_pass(weeks, load_keys, log2_bits, hashes):
    bloom = Bloom(log2_bits, hashes)
    prev, out = [], {}
    nan = float('nan')
    for w in weeks:
        keys = load_keys(w)
        if keys is None:
            out[w] = None
            prev = (prev + [None])[-4:]
            continue
        known = bloom.contains(keys)
        last = prev[-1] if prev else np.empty(0, np.uint64)
        incomplete = any(x is None for x in prev[-4:])
        window = [x for x in prev[-4:] if x is not None]
        union = np.unique(np.concatenate(window)) if window else np.empty(0, np.uint64)
        in4 = np.isin(keys, union, assume_unique=True)
        out[w] = {'f4_new_share': float((~known).mean()),
                  'f4_prev1_share': nan if last is None else float(np.isin(keys, last, assume_unique=True).mean()),
                  'f4_prev4_share': nan if incomplete else float(in4.mean()),
                  'f4_return_share': nan if incomplete else float((known & ~in4).mean())}
        bloom.add(keys)
        prev = (prev + [keys])[-4:]
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_history.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b3/history.py tests/research/onchain_b3/test_history.py
git commit -m "feat(onchain-b3): address keys, Bloom filter and sequential history features"
```

---

### Task 4: One-week builder and 4-week targets

**Files:**
- Create: `tradingagents/research/onchain_b3/weekbuild3.py`, `tradingagents/research/onchain_b3/targets3.py`
- Test: `tests/research/onchain_b3/test_weekbuild3.py`

**Interfaces:**
- Consumes: `onchain_b.weekly.{admitted_events, aggregate_pairs, top_k_subgraph, _index}`; `onchain_b2.weekbuild.{address_table, f1_features, role_flows}`; `structure.structure_features`; `history.keys_from_addresses`; `onchain_b2.targets._rets`.
- Produces: `build_week3(week, events_list, counters, exchanges: pa.Array, ex_bytes: np.ndarray[S42], cfg, week_index) -> (summary: dict, graph: WeekGraph, keys: np.ndarray[uint64])` (summary keys `week, counters, f1, f3a, f4, whales, graph`); `targets3.t6(prices, m)`, `targets3.t7(prices, m)` → `float | None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b3/test_weekbuild3.py
import math
from datetime import date, timedelta

import numpy as np
import pyarrow as pa
import pytest

from tradingagents.research.onchain_b.weekly import admitted_events
from tradingagents.research.onchain_b3 import config, targets3 as T3, weekbuild3 as WB

A, B, C, E = ('0x' + c * 40 for c in 'abce')
EX = pa.array([E])
EXB = np.array([E], dtype='S42')


def _day(rows):
    return pa.table({'hash': ['0x' + f'{i:064x}' for i in range(len(rows))],
                     'block_timestamp': pa.array([0] * len(rows), pa.timestamp('ns')),
                     'from_address': [r[0] for r in rows], 'to_address': [r[1] for r in rows],
                     'value': [r[2] * 1e18 for r in rows], 'receipt_status': [1] * len(rows)})


def test_build_week3_outputs():
    cfg = {**config.load(), 'k': 3}
    ev, c = admitted_events(_day([(A, B, 1.0), (B, C, 2.0), (C, A, 1.5), (A, E, 4.0), (B, A, 0.5)]))
    summary, graph, keys = WB.build_week3('2019-06-03', [ev], [c], EX, EXB, cfg, week_index=127)
    assert summary['f1']['f1_transfers'] == 5 and summary['f3a']['f3a_ex_in_value'] == pytest.approx(4.0)
    assert len([k for k in summary['f4'] if k.startswith('f4_')]) == 25
    assert summary['f4']['f4_components'] == 1 and summary['f4']['f4_recip_edge_share'] == pytest.approx(2 / 5)
    assert graph.n == 3 and keys.dtype == np.uint64 and len(keys) == 4


def _px(f, n=90):
    d0 = date(2020, 1, 1)
    return {d0 + timedelta(days=i): f(i) for i in range(n)}


def test_four_week_targets():
    p = _px(lambda i: 100.0 * 1.01 ** i)
    m = date(2020, 1, 10)
    assert T3.t6(p, m) == pytest.approx(28 * math.log(1.01))
    q = _px(lambda i: 100.0 * (1.02 if i % 2 else 1.0))
    assert T3.t7(q, m) == pytest.approx(math.log(math.sqrt(28) * math.log(1.02)))
    assert T3.t6(p, date(2020, 3, 1)) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_weekbuild3.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b3/targets3.py
"""4-week targets T6 (log return) and T7 (log realised volatility), spec §6."""
from __future__ import annotations

import math
from datetime import timedelta

from ..onchain_b2.targets import _rets


def t6(p, m):
    a, b = p.get(m), p.get(m + timedelta(days=28))
    return None if a is None or b is None else math.log(b / a)


def t7(p, m):
    r = _rets(p, m, 1, 28)
    return None if r is None else math.log(max(math.sqrt(sum(x * x for x in r)), 1e-8))
```

```python
# tradingagents/research/onchain_b3/weekbuild3.py
"""One week for B3: B2 activity/role features, whole-graph structure (F4 snapshot),
the top-20,000 graph for motifs, and the week's address keys for the history pass."""
from __future__ import annotations

import numpy as np
import pyarrow as pa

from ..onchain_b.weekly import _index, aggregate_pairs, top_k_subgraph
from ..onchain_b2.weekbuild import address_table, f1_features, role_flows
from . import history, structure


def build_week3(week, events_list, counters, exchanges, ex_bytes, cfg, week_index):
    r = cfg['roles']
    pairs = aggregate_pairs(list(events_list))
    addr = address_table(pairs)
    events = pa.concat_tables(list(events_list))
    f1 = f1_features(events, pairs, addr, list(counters), r['top_share_n'])
    del events
    f3a, whales = role_flows(pairs, addr, exchanges, r['deposit_share'], r['whales'])
    del addr
    idx = _index(pairs)
    is_ex = np.isin(idx[0], ex_bytes)
    s = cfg['structure']
    f4 = structure.structure_features(idx, is_ex, s, s['wedge_seed'] + week_index)
    keys = history.keys_from_addresses(idx[0])
    del idx
    graph = top_k_subgraph(pairs, cfg['k'], week)
    summary = {'week': week, 'counters': list(counters), 'f1': f1, 'f3a': f3a, 'f4': f4, 'whales': whales,
               'graph': dict(graph.summary)}
    return summary, graph, keys
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_weekbuild3.py -q`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b3/weekbuild3.py tradingagents/research/onchain_b3/targets3.py tests/research/onchain_b3/test_weekbuild3.py
git commit -m "feat(onchain-b3): one-week builder with structure, keys and 20k graph; 4-week targets"
```

---

### Task 5: Dataset (transforms, weekly samples with T6/T7, feature sets)

**Files:**
- Create: `tradingagents/research/onchain_b3/dataset3.py`
- Test: `tests/research/onchain_b3/test_dataset3.py`

**Interfaces:**
- Consumes: `onchain_b2.periods.{week_end, weekly_window}`; `onchain_b2.targets.{f0, t2, t3, t4, t5}`; `targets3.{t6, t7}`; `onchain_b2.dataset.raw_table`.
- Produces: `value3(name, x)`; `transform3(raw, z_window, z_min, z_clip) -> DataFrame` (`<name>__z8`, `<name>__d1`); `weekly_samples3(trans, prices, volumes, window) -> (DataFrame, excluded)` with `T2…T7`; `columns3(df, set_name, cfg) -> list[str]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b3/test_dataset3.py
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2 import dataset as DS2, periods
from tradingagents.research.onchain_b3 import config, dataset3 as D3


def test_value3_rules():
    assert D3.value3('f4_deg_gini', 0.4) == 0.4 and D3.value3('f4_transitivity', 0.1) == 0.1
    assert D3.value3('f4_components', np.e - 1) == pytest.approx(1.0) and D3.value3('f5_mean_3', 0.2) == 0.2
    assert D3.value3('f1_transfers', np.e - 1) == pytest.approx(1.0) and D3.value3('f3a_ex_net_value', -(np.e - 1)) == pytest.approx(-1.0)


def _market():
    d0 = date(2016, 12, 1)
    days = [d0 + timedelta(days=i) for i in range((periods.DEV_END - d0).days + 1)]
    rng = np.random.default_rng(0)
    p = dict(zip(days, 1000 * np.exp(np.cumsum(rng.normal(0, 0.02, len(days))))))
    return p, {d: 5e8 for d in days}


def _trans():
    rows = {w: {'f1_transfers': 1000.0 + i, 'f4_deg_gini': 0.3 + 0.01 * (i % 5), 'f5_mean_0': 0.1 + 0.001 * (i % 7)}
            for i, w in enumerate(periods.all_weeks())}
    return D3.transform3(DS2.raw_table(rows), 8, 6, 10.0)


def test_dev_four_week_targets_stop_at_cutoff():
    p, v = _market()
    df, _ = D3.weekly_samples3(_trans(), p, v, 'dev')
    assert len(df) == 378 and {'T2', 'T6', 'T7'} <= set(df.columns)
    last_ok = df[df['T6'].notna()].index.max()
    assert last_ok == pd.Timestamp('2024-12-02')                 # 2024-12-02 + 28 days = 2024-12-30
    assert df.loc[pd.Timestamp('2024-12-09'), ['T6', 'T7']].isna().all()
    assert pd.notna(df.loc[pd.Timestamp('2024-12-23'), 'T2'])          # 7-day targets still reach 2024-12-30


def test_columns3_from_config():
    p, v = _market()
    df, _ = D3.weekly_samples3(_trans(), p, v, 'dev')
    cfg = config.load()
    s5, s1 = set(D3.columns3(df, 'S5', cfg)), set(D3.columns3(df, 'S1', cfg))
    assert s5 - s1 == {c for c in df.columns if c.startswith('f4_')}
    assert all(c.startswith('f0_') for c in D3.columns3(df, 'S0', cfg))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_dataset3.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b3/dataset3.py
"""B3 transforms and weekly samples (B2 rules plus F4/F5 value rules and T6/T7)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..onchain_b2 import periods
from ..onchain_b2 import targets as T
from . import targets3 as T3

SIGNED = {'f3a_ex_net_value', 'f3a_whale_net_to_ex'}
F4_LOG = {'f4_components', 'f4_pair_components'}


def value3(name, x):
    if name in SIGNED:
        return np.sign(x) * np.log1p(np.abs(x))
    if name.startswith('f4_'):
        return np.log1p(x) if name in F4_LOG else x
    if name.startswith('f5_') or name.endswith('_share') or name == 'f1_mean_degree':
        return x
    return np.log1p(x)


def transform3(raw, z_window=8, z_min=6, z_clip=10.0):
    out = {}
    for name in raw.columns:
        x = value3(name, raw[name].astype(float))
        prev = x.shift(1)
        mean = prev.rolling(z_window, min_periods=z_min).mean()
        std = prev.rolling(z_window, min_periods=z_min).std(ddof=0)
        z = (x - mean) / std
        z[(std == 0) & x.notna()] = 0.0
        out[f'{name}__z8'] = z.clip(-z_clip, z_clip)
        out[f'{name}__d1'] = x - prev
    return pd.DataFrame(out, index=raw.index)


def columns3(df, set_name, cfg):
    return sorted(c for c in df.columns if c.startswith(tuple(cfg['sets'][set_name])))


def weekly_samples3(trans, prices, volumes, window):
    rows, excluded = {}, []
    available = set(trans.index[trans.notna().any(axis=1)])
    for w in trans.index:
        m = periods.week_end(w)
        if periods.weekly_window(m) != window:
            continue
        if w not in available:
            excluded.append((m.isoformat(), 'week_unavailable'))
            continue
        feats = trans.loc[w]
        if feats.isna().any():
            excluded.append((m.isoformat(), 'features_incomplete'))
            continue
        f0 = T.f0(prices, volumes, m)
        if f0 is None:
            excluded.append((m.isoformat(), 'f0_unavailable'))
            continue
        rows[pd.Timestamp(m)] = {**feats.to_dict(), **f0, 'week': w,
                                 'T2': T.t2(prices, m), 'T3': T.t3(prices, m), 'T4': T.t4(prices, m),
                                 'T5': T.t5(volumes, m), 'T6': T3.t6(prices, m), 'T7': T3.t7(prices, m)}
    df = pd.DataFrame.from_dict(rows, orient='index').sort_index()
    return df.astype({c: float for c in df.columns if c != 'week'}), excluded
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_dataset3.py -q`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b3/dataset3.py tests/research/onchain_b3/test_dataset3.py
git commit -m "feat(onchain-b3): structure-aware transforms and weekly samples with 4-week targets"
```

---

### Task 6: Screen and holdout (config-driven targets, purges, blocks, comparisons)

**Files:**
- Create: `tradingagents/research/onchain_b3/screen3.py`
- Test: `tests/research/onchain_b3/test_screen3.py`

**Interfaces:**
- Consumes: `onchain_b2.screen.{folds, fit_predict, row_loss, report}`; `onchain_b.evaluate.{block_bootstrap, _bootstrap_means}`; `onchain_b2.holdout.holm`; `dataset3.columns3`.
- Produces: `run_screen3(samples: dict[kind, DataFrame], cfg) -> list[dict]` (B2 result schema: `target, kind, task, family, set, comparator, n, mean_diff, lo, hi, wins, years, years_loss, alphas, n_missing_target, passed, loss_set, loss_comparator, extra`); `select3(results, cfg) -> list[dict]`; `evaluate3(dev, hold, selection, cfg) -> list[dict]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b3/test_screen3.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b3 import config, screen3 as S3


def _frames(rng):
    idx = pd.date_range('2017-10-02', '2024-12-23', freq='7D')
    n = len(idx)
    sig = rng.normal(size=n)
    w = pd.DataFrame({'f0_r__x': rng.normal(size=n), 'f1_a__z8': rng.normal(size=n), 'f4_sig__z8': sig,
                      'f5_noise__z8': rng.normal(size=n), 'f3a_noise__z8': rng.normal(size=n)}, index=idx)
    for t in ('T3', 'T4', 'T5', 'T6'):
        w[t] = rng.normal(size=n)
    w['T7'] = 2 * sig + 0.3 * rng.normal(size=n)
    w['T2'] = (rng.random(n) > 0.5).astype(float)
    di = pd.date_range('2017-10-02', '2024-12-30', freq='D')
    d = pd.DataFrame({c: rng.normal(size=len(di)) for c in ('f0_r__x', 'f1_a__z8', 'f4_sig__z8', 'f5_noise__z8', 'f3a_noise__z8')}, index=di)
    d['T1'] = (rng.random(len(di)) > 0.5).astype(float)
    return {'weekly': w, 'daily': d}


def test_screen3_counts_purges_and_signal():
    cfg = config.load()
    res = S3.run_screen3(_frames(np.random.default_rng(4)), cfg)
    assert len(res) == 7 * 2 * 3
    get = {(r['target'], r['family'], r['set']): r for r in res}
    assert get[('T7', 'linear', 'S5')]['passed'] and get[('T7', 'linear', 'S7')]['passed']
    assert not get[('T3', 'linear', 'S5')]['passed'] and not get[('T1', 'linear', 'S5')]['passed']
    sel = S3.select3(res, cfg)
    assert 1 <= len(sel) <= 3 and all(s['target'] == 'T7' for s in sel)


def test_purge_uses_target_horizon():
    idx = pd.date_range('2017-10-02', '2024-12-23', freq='7D')
    folds = S3.folds_for(idx, 'T6', config.load())
    year, train, test = folds[0]
    assert idx[train].max() == pd.Timestamp('2018-12-03')         # + 28 days <= 2019-01-01


def test_evaluate3_on_synthetic_holdout():
    rng = np.random.default_rng(6)
    def frame(a, b):
        idx = pd.date_range(a, b, freq='7D')
        sig = rng.normal(size=len(idx))
        return pd.DataFrame({'f0_r__x': rng.normal(size=len(idx)), 'f1_a__z8': rng.normal(size=len(idx)), 'f4_sig__z8': sig,
                             'T7': 2 * sig + 0.3 * rng.normal(size=len(idx))}, index=idx)
    sel = {'selected': [{'target': 'T7', 'family': 'linear', 'set': 'S5', 'comparator': 'S1'}]}
    res = S3.evaluate3({'weekly': frame('2017-10-02', '2024-12-23')}, {'weekly': frame('2025-01-06', '2026-10-05')}, sel, config.load())
    assert res[0]['n'] == 92 and res[0]['passed']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_screen3.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b3/screen3.py
"""B3 screen and holdout evaluation: B2 primitives with targets, purges, blocks, sets and
comparisons read from config/b3.json."""
from __future__ import annotations

import numpy as np

from ..onchain_b.evaluate import _bootstrap_means, block_bootstrap
from ..onchain_b2.holdout import holm
from ..onchain_b2.screen import folds, fit_predict, row_loss
from .dataset3 import columns3


def folds_for(dates, target, cfg):
    return folds(dates, cfg['folds']['test_years'], cfg['targets'][target]['horizon'])


def run_screen3(samples, cfg):
    g, fcfg = cfg['gate'], cfg['folds']
    sets = sorted({s for pair in cfg['comparisons'] for s in pair})
    results = []
    for target, tc in cfg['targets'].items():
        kind, task = tc['kind'], tc['task']
        df = samples[kind]
        n_missing = int(df[target].isna().sum())
        df = df[df[target].notna()].sort_index()
        y = df[target].to_numpy(float)
        fl = folds_for(df.index, target, cfg)
        tested = np.zeros(len(df), bool)
        for _, _, te in fl:
            tested |= te
        yt = df.index.year.to_numpy()[tested]
        for family in cfg['families']:
            preds, alphas = {}, {}
            for s in sets:
                X = df[columns3(df, s, cfg)].to_numpy(float)
                p = np.full(len(df), np.nan)
                alphas[s] = {}
                for yr, tr, te in fl:
                    info = {}
                    p[te] = fit_predict(family, task, X[tr], y[tr], X[te], fcfg['inner_len'][kind], cfg, info)
                    alphas[s][int(yr)] = info['alpha']
                preds[s] = p
            loss = {s: row_loss(task, y[tested], preds[s][tested]) for s in sets}
            for a, b in cfg['comparisons']:
                diff = loss[a] - loss[b]
                lo, hi = block_bootstrap(diff, block=tc['block'], draws=g['draws'], seed=g['seed'])
                per_year = {int(yr): float(diff[yt == yr].mean()) for yr in fcfg['test_years']}
                years_loss = {int(yr): [float(loss[a][yt == yr].mean()), float(loss[b][yt == yr].mean())]
                              for yr in fcfg['test_years']}
                wins = sum(v < 0 for v in per_year.values())
                if task == 'classification':
                    extra = {f'accuracy_{s}': float(((preds[s][tested] > 0.5) == (y[tested] > 0.5)).mean()) for s in (a, b)}
                    extra.update({f'brier_{s}': float(((preds[s][tested] - y[tested]) ** 2).mean()) for s in (a, b)})
                else:
                    extra = {f'r2_vs_S0_{s}': float(1 - loss[s].mean() / loss['S0'].mean()) if 'S0' in loss else float('nan')
                             for s in (a, b)}
                results.append({'target': target, 'kind': kind, 'task': task, 'family': family, 'set': a, 'comparator': b,
                                'n': int(len(diff)), 'mean_diff': float(diff.mean()), 'lo': lo, 'hi': hi, 'wins': int(wins),
                                'years': per_year, 'years_loss': years_loss, 'alphas': {a: alphas[a], b: alphas[b]},
                                'n_missing_target': n_missing,
                                'passed': bool(hi < 0 and wins >= g['min_year_wins']),
                                'loss_set': float(loss[a].mean()), 'loss_comparator': float(loss[b].mean()), 'extra': extra})
    return results


def select3(results, cfg):
    passing = [r for r in results if r['passed']]
    passing.sort(key=lambda r: (r['hi'] / r['loss_comparator'], 0 if r['set'] in cfg['graph_sets'] else 1))
    return [{'target': r['target'], 'family': r['family'], 'set': r['set'], 'comparator': r['comparator'],
             'dev_mean_diff': r['mean_diff'], 'dev_hi': r['hi']} for r in passing[:cfg['gate']['max_selected']]]


def evaluate3(dev, hold, selection, cfg):
    g, fcfg = cfg['gate'], cfg['folds']
    out = []
    for s in selection['selected']:
        tc = cfg['targets'][s['target']]
        kind, task = tc['kind'], tc['task']
        d = dev[kind][dev[kind][s['target']].notna()].sort_index()
        h = hold[kind][hold[kind][s['target']].notna()].sort_index()
        yd, yh = d[s['target']].to_numpy(float), h[s['target']].to_numpy(float)
        loss = {}
        for name in (s['set'], s['comparator']):
            cols = columns3(d, name, cfg)
            pred = fit_predict(s['family'], task, d[cols].to_numpy(float), yd, h[cols].to_numpy(float),
                               fcfg['inner_len'][kind], cfg)
            loss[name] = row_loss(task, yh, pred)
        diff = loss[s['set']] - loss[s['comparator']]
        means = _bootstrap_means(diff, block=tc['block'], draws=g['draws'], seed=g['seed'])
        out.append({**{k: s[k] for k in ('target', 'family', 'set', 'comparator')}, 'n': int(len(diff)),
                    'mean_diff': float(diff.mean()), 'p': float((means >= 0).mean())})
    for r, adj in zip(out, holm([r['p'] for r in out]) if out else []):
        r['p_holm'] = adj
        r['passed'] = bool(adj < g['alpha'] and r['mean_diff'] < 0)
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_screen3.py -q`
Expected: 3 passed (about a minute)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/research/onchain_b3/screen3.py tests/research/onchain_b3/test_screen3.py
git commit -m "feat(onchain-b3): config-driven screen, selection and holdout evaluation"
```

---

### Task 7: CLI stages

**Files:**
- Create: `tradingagents/research/onchain_b3/cli.py`
- Test: `tests/research/onchain_b3/test_cli3.py`

**Interfaces:**
- Consumes: `onchain_b2.{s3source, labels, market, periods, motiffeat, dataset.raw_table, dataset.daily_samples, screen.report, holdout.committed_selection, holdout.selection_identity}`; `onchain_b.weekly.{admitted_events, save, load}`; B3 modules above.
- Produces: `main(argv)` with `weeks [--start] [--end]`, `history [--delete-keys]`, `dictionary`, `mcm [--shard I/N]`, `features`, `screen`, `holdout`; `build_one3(week, scratch) -> dict`; `capture_complete() -> bool`; `week_status(week) -> str | None`; module attributes `ARTIFACTS`, `STUDY`, `B2` (patchable).

- [ ] **Step 1: Write the failing test**

```python
# tests/research/onchain_b3/test_cli3.py
import json

import numpy as np
import pyarrow as pa
import pytest

from tradingagents.research.onchain_b2 import s3source
from tradingagents.research.onchain_b3 import cli

A, B, C, E = ('0x' + c * 40 for c in 'abce')


def _day(day):
    rows = [(A, B, 1.0), (B, C, 2.0), (C, A, 1.0), (A, E, 3.0)]
    return pa.table({'hash': ['0x' + f'{abs(hash((day, i))) % 10**12:064x}' for i in range(len(rows))],
                     'block_timestamp': pa.array([0] * len(rows), pa.timestamp('ns')),
                     'from_address': [r[0] for r in rows], 'to_address': [r[1] for r in rows],
                     'value': [r[2] * 1e18 for r in rows], 'receipt_status': [1] * len(rows)})


def _setup(tmp_path, monkeypatch, fail=None):
    art, b2 = tmp_path / 'b3', tmp_path / 'b2'
    (b2 / 'labels').mkdir(parents=True)
    (b2 / 'labels' / 'labels.json').write_text(json.dumps({E: {'name': 'X', 'added': None, 'sources': ['spellbook']}}))
    monkeypatch.setattr(cli, 'ARTIFACTS', art)
    monkeypatch.setattr(cli, 'B2', b2)

    def fake(day, *, scratch, **kw):
        if fail and day == fail[0]:
            raise fail[1]
        return _day(day), {'day': day, 'source': 'test', 'rows': 4}

    monkeypatch.setattr(s3source, 'read_day', fake)
    return art


def test_week_build_writes_summary_graph_and_keys(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch)
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-03'])
    s = json.loads((art / 'weeks' / '2019-06-03.json').read_text())
    assert s['f1']['f1_transfers'] == 28 and 'f4_transitivity' in s['f4'] and len(s['receipts']) == 7
    assert np.load(art / 'keys' / '2019-06-03.npy').dtype == np.uint64 and (art / 'graphs' / '2019-06-03' / 'summary.json').exists()


def test_failures_are_recorded_and_isolated(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch, fail=('2019-06-05', ValueError('duplicate transaction hash in day')))
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-10'])
    assert 'duplicate' in json.loads((art / 'weeks' / '2019-06-03.failed.json').read_text())['error']
    assert (art / 'weeks' / '2019-06-10.json').exists()


def test_late_stages_refuse_incomplete_capture(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    cli.main(['weeks', '--start', '2019-06-03', '--end', '2019-06-03'])
    for stage in (['history'], ['mcm', '--shard', '0/1'], ['features']):
        with pytest.raises(SystemExit, match='capture incomplete'):
            cli.main(stage)


def test_screen_never_overwrites_selection(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(cli, 'STUDY', tmp_path)
    (tmp_path / 'selection.json').write_text('{"selected": []}')
    with pytest.raises(SystemExit, match='exists'):
        cli.main(['screen'])


def test_cli_import_does_not_load_torch():
    import subprocess, sys
    out = subprocess.run([sys.executable, '-c', 'import sys, tradingagents.research.onchain_b3.cli; print("torch" in sys.modules)'],
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == 'False'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_cli3.py -q`
Expected: collection error (module missing)

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/research/onchain_b3/cli.py
"""B3 stage runner. Week builds run one week per process (shell loop), write the summary last,
and record failures; later stages refuse to start until all 510 weeks are built or marked."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np

from ..onchain_b import config as b_config
from ..onchain_b import weekly as W
from ..onchain_b.matching.agreement import MatchConfig
from ..onchain_b.runlog import Log
from ..onchain_b.weekly import admitted_events
from ..onchain_b2 import dataset as DS2
from ..onchain_b2 import holdout as H2
from ..onchain_b2 import labels, market, motiffeat, periods, s3source
from ..onchain_b2 import screen as SC2
from . import config, dataset3, history, screen3, weekbuild3

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B2 = config.B2_ARTIFACTS


def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))
    os.replace(tmp, path)


def _torch():
    import torch
    torch.set_num_threads(2)


def _peak_rss_mb():
    try:
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmHWM:'):
                return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        pass
    return None


def week_status(week):
    wdir = ARTIFACTS / 'weeks'
    if (wdir / f'{week}.json').exists():
        return None
    for kind in ('unavailable', 'failed'):
        p = wdir / f'{week}.{kind}.json'
        if p.exists():
            doc = json.loads(p.read_text())
            return f"{kind}: {doc.get('day') or doc.get('error', '?')}"
    return 'not_built'


def capture_complete():
    return all(week_status(w) != 'not_built' for w in periods.all_weeks())


def _require_capture():
    if not capture_complete():
        raise SystemExit('capture incomplete: build or mark all 510 weeks first')


def build_one3(week, scratch):
    cfg = config.load()
    out = ARTIFACTS / 'weeks' / f'{week}.json'
    if out.exists():
        return {'week': week, 'status': 'skip'}
    events, counters, receipts = [], [], []
    for day in periods.week_days(week):
        try:
            t, r = s3source.read_day(day, scratch=scratch)
        except s3source.DayUnavailable as e:
            _write_json(ARTIFACTS / 'weeks' / f'{week}.unavailable.json', {'week': week, 'day': e.day, 'errors': e.errors})
            return {'week': week, 'status': 'unavailable', 'day': e.day}
        ev, c = admitted_events(t)
        del t
        events.append(ev)
        counters.append(c)
        receipts.append(r)
    ex = labels.exchange_array(B2 / 'labels' / 'labels.json')
    ex_bytes = np.array(ex.to_pylist(), dtype='S42')
    summary, graph, keys = weekbuild3.build_week3(week, events, counters, ex, ex_bytes, cfg,
                                                  periods.all_weeks().index(week))
    del events
    summary['receipts'] = receipts
    gdir = ARTIFACTS / 'graphs' / week
    if gdir.exists():
        shutil.rmtree(gdir)
    W.save(graph, gdir)
    kdir = ARTIFACTS / 'keys'
    kdir.mkdir(parents=True, exist_ok=True)
    tmpk = kdir / f'.{week}.tmp.npy'
    np.save(tmpk, keys)
    os.replace(tmpk, kdir / f'{week}.npy')
    _write_json(out, summary)
    for stale in ('unavailable', 'failed'):
        (ARTIFACTS / 'weeks' / f'{week}.{stale}.json').unlink(missing_ok=True)
    return {'week': week, 'status': 'done', 'rows': sum(r['rows'] for r in receipts)}


def stage_weeks(args):
    log = Log(ARTIFACTS / 'logs' / 'weeks.jsonl')
    weeks = [w for w in periods.all_weeks() if (args.start or '0') <= w <= (args.end or '9')]
    (ARTIFACTS / 'scratch').mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ARTIFACTS / 'scratch') as scratch:
        for w in weeks:
            if (ARTIFACTS / 'weeks' / f'{w}.json').exists():
                continue
            t = time.time()
            try:
                res = build_one3(w, scratch)
            except Exception as e:
                _write_json(ARTIFACTS / 'weeks' / f'{w}.failed.json', {'week': w, 'error': repr(e), 'traceback': traceback.format_exc()})
                res = {'week': w, 'status': 'failed', 'error': repr(e)}
            log.event(event='week', seconds=round(time.time() - t, 1), peak_rss_mb=_peak_rss_mb(), **res)


def stage_history(args):
    _require_capture()
    c = config.load()['history']
    weeks = periods.all_weeks()

    def load(w):
        p = ARTIFACTS / 'keys' / f'{w}.npy'
        return np.load(p) if week_status(w) is None and p.exists() else None

    out = history.history_pass(weeks, load, c['bloom_bits_log2'], c['bloom_hashes'])
    built = sum(1 for w in weeks if week_status(w) is None)
    computed = sum(1 for v in out.values() if v is not None)
    if computed != built:
        raise SystemExit(f'history covers {computed} weeks but {built} are built')
    _write_json(ARTIFACTS / 'history.json', out)
    if args.delete_keys:
        shutil.rmtree(ARTIFACTS / 'keys')
    print(json.dumps({'weeks': computed, 'keys_deleted': bool(args.delete_keys)}))


def stage_dictionary(args):
    _require_capture()
    _torch()
    from ..onchain_b import dictionary as D
    c, cfg = config.load()['dictionary'], config.load()
    out = ARTIFACTS / 'dictionary'
    if (out / 'dictionary.json').exists():
        return
    weeks = {w: W.load(ARTIFACTS / 'graphs' / w) for w in periods.dictionary_weeks() if week_status(w) is None}
    d = D.build(weeks, MatchConfig.from_json(b_config.load('matching')), c['sample_count'], c['size'], cfg['n_max'], c['seed'])
    D.save(d, out)
    print(json.dumps({'weeks': len(weeks), 'motif_sizes': [int(m.x.shape[0]) for m in d.motifs]}))


def stage_mcm(args):
    _require_capture()
    _torch()
    from ..onchain_b import dictionary as D
    from ..onchain_b import mcm
    i, n = map(int, args.shard.split('/'))
    log = Log(ARTIFACTS / 'logs' / f'mcm-{i}of{n}.jsonl')
    d = D.load(ARTIFACTS / 'dictionary')
    cfg = MatchConfig.from_json(b_config.load('matching'))
    out = ARTIFACTS / 'mcm'
    out.mkdir(parents=True, exist_ok=True)
    for w in [w for w in periods.all_weeks() if week_status(w) is None][i::n]:
        target = out / f'{w}.npy'
        if target.exists():
            continue
        t = time.time()
        F = mcm.compute_week(W.load(ARTIFACTS / 'graphs' / w), d, cfg, config.load()['n_max'])
        tmp = out / f'.{w}.{i}.tmp.npy'
        np.save(tmp, F)
        os.replace(tmp, target)
        log.event(event='week', week=w, seconds=round(time.time() - t, 1), cells=int(F.size))


def stage_features(args):
    _require_capture()
    import pyarrow as pa
    import pyarrow.parquet as pq
    hist = json.loads((ARTIFACTS / 'history.json').read_text())
    exchanges = set(labels.load(B2 / 'labels' / 'labels.json'))
    rows, missing = {}, {}
    for w in periods.all_weeks():
        why = week_status(w)
        if why is None and not (ARTIFACTS / 'mcm' / f'{w}.npy').exists():
            why = 'no_mcm'
        if why is None and hist.get(w) is None:
            why = 'no_history'
        if why:
            missing[w] = why
            continue
        s = json.loads((ARTIFACTS / 'weeks' / f'{w}.json').read_text())
        mf = motiffeat.motif_features(np.load(ARTIFACTS / 'mcm' / f'{w}.npy'), W.load(ARTIFACTS / 'graphs' / w),
                                      exchanges, set(s['whales']))
        f5 = {'f5_' + k[3:]: v for k, v in mf.items() if k.startswith('f2_')}
        rows[w] = {**s['f1'], **s['f3a'], **s['f4'], **hist[w], **f5}
    raw = DS2.raw_table(rows)
    (ARTIFACTS / 'features').mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(raw, preserve_index=True), ARTIFACTS / 'features' / 'weekly_raw.parquet')
    _write_json(ARTIFACTS / 'features' / 'missing.json', missing)
    print(json.dumps({'weeks': len(rows), 'missing': len(missing), 'columns': raw.shape[1]}))


def _samples(trans, prices, volumes, window):
    weekly, ex_w = dataset3.weekly_samples3(trans, prices, volumes, window)
    daily, ex_d = DS2.daily_samples(trans, prices, volumes, window)
    return {'weekly': weekly, 'daily': daily}, {'weekly': ex_w, 'daily': ex_d}


def _transformed():
    import pyarrow.parquet as pq
    raw = pq.read_table(ARTIFACTS / 'features' / 'weekly_raw.parquet').to_pandas()
    t = config.load()['transforms']
    return dataset3.transform3(raw, t['z_window'], t['z_min'], t['z_clip'])


def stage_screen(args):
    if (STUDY / 'selection.json').exists():
        raise SystemExit('selection.json exists: the B3 screen has already run')
    cfg = config.load()
    prices, volumes = market.load_dev(B2 / 'market' / 'dev.json', periods.DEV_END)
    samples, excluded = _samples(_transformed(), prices, volumes, 'dev')
    results = screen3.run_screen3(samples, cfg)
    selection = screen3.select3(results, cfg)
    _write_json(ARTIFACTS / 'screen' / 'screen.json', {'results': results, 'excluded': excluded,
                                                     'n': {k: len(v) for k, v in samples.items()}})
    head = (f"# B3 screen — development 2017-10 → 2024 (walk-forward 2019–2024)\n\n"
            f"Samples: weekly {len(samples['weekly'])} (excluded {len(excluded['weekly'])}), "
            f"daily {len(samples['daily'])} (excluded {len(excluded['daily'])}).\n\n")
    (STUDY / 'SCREEN.md').write_text(head + SC2.report(results, selection) + '\n')
    _write_json(STUDY / 'selection.json', {'registered_from': 'screen.json', 'selected': selection})
    print(SC2.report(results, selection))


def stage_holdout(args):
    lock = ARTIFACTS / 'screen' / 'holdout.lock.json'
    if lock.exists():
        raise SystemExit(f'holdout already opened ({lock}); it is one-shot')
    cfg = config.load()
    selection = H2.committed_selection(STUDY / 'selection.json', config.ROOT)
    if not selection['selected']:
        print('screen negative: holdout not opened')
        return
    identity = H2.selection_identity(STUDY / 'selection.json', config.ROOT)
    _write_json(lock, {'opened_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), **identity})
    trans = _transformed()
    p_dev, v_dev = market.load_dev(B2 / 'market' / 'dev.json', periods.DEV_END)
    p_all, v_all = market.load_all(B2 / 'market' / 'dev.json', B2 / 'sealed' / 'market_sealed.json')
    dev, _ = _samples(trans, p_dev, v_dev, 'dev')
    hold, excluded = _samples(trans, p_all, v_all, 'holdout')
    res = screen3.evaluate3(dev, hold, selection, cfg)
    _write_json(ARTIFACTS / 'screen' / 'holdout.json', {'results': res, 'excluded': excluded, **identity})
    lines = ['# B3 holdout — sealed 2025-01-06 → 2026-10-05', '',
             f"Opened once from selection.json blob {identity['blob']} at commit {identity['head']}.", '',
             '| target | family | comparison | n | mean loss diff | p (one-sided) | p Holm | pass |', '|---|---|---|---|---|---|---|---|']
    lines += [f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n']} | {r['mean_diff']:+.5f} | "
              f"{r['p']:.4f} | {r['p_holm']:.4f} | {'PASS' if r['passed'] else '—'} |" for r in res]
    (STUDY / 'HOLDOUT.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b3')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('weeks')
    a.add_argument('--start')
    a.add_argument('--end')
    a.set_defaults(fn=stage_weeks)
    a = sub.add_parser('history')
    a.add_argument('--delete-keys', action='store_true')
    a.set_defaults(fn=stage_history)
    sub.add_parser('dictionary').set_defaults(fn=stage_dictionary)
    a = sub.add_parser('mcm')
    a.add_argument('--shard', default='0/1')
    a.set_defaults(fn=stage_mcm)
    sub.add_parser('features').set_defaults(fn=stage_features)
    sub.add_parser('screen').set_defaults(fn=stage_screen)
    sub.add_parser('holdout').set_defaults(fn=stage_holdout)
    args = p.parse_args(argv)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    args.fn(args)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3/test_cli3.py -q`
Expected: 5 passed

- [ ] **Step 5: Run the whole B3 suite and commit**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests/research/onchain_b3 tests/research/onchain_b2 tests/research/onchain_b -q`
Expected: all pass (B3 ≈ 25, B2 58, B 69)

```bash
git add tradingagents/research/onchain_b3/cli.py tests/research/onchain_b3/test_cli3.py
git commit -m "feat(onchain-b3): stage runner for week builds, history, motifs, features, screen and holdout"
```

---

### Task 8: Data pass (B3-CP1)

Operational.

- [ ] **Step 1: Measure one heavy week before launching**

Run: `P=$PWD; /usr/bin/time -v .venv/bin/python -m tradingagents.research.onchain_b3.cli weeks --start 2024-03-11 --end 2024-03-11 2>&1 | grep -E 'Maximum resident|Elapsed'`
Expected: peak below 5.5 GB; record time and peak in `STATE.md`. If above, stop and report.

- [ ] **Step 2: Launch two loops (one fresh process per week)**

```bash
P=$PWD; A=research_artifacts/onchain-b3; mkdir -p $A
cat > $A/loop_s3.sh <<EOF
#!/bin/bash
cd $P
for w in \$($P/.venv/bin/python -c "from tradingagents.research.onchain_b2 import periods; print(' '.join(w for w in periods.all_weeks() if not ('2022-01-03' <= w <= '2024-12-23')))"); do
  [ -f $A/weeks/\$w.json ] && continue
  $P/.venv/bin/python -m tradingagents.research.onchain_b3.cli weeks --start \$w --end \$w || exit 1
done
EOF
sed -e "s/if not ('2022-01-03' <= w <= '2024-12-23')/if '2022-01-03' <= w <= '2024-12-23'/" $A/loop_s3.sh > $A/loop_local.sh
chmod +x $A/loop_s3.sh $A/loop_local.sh
systemd-run --user --unit onchain-b3-weeks -p MemoryMax=8G -p WorkingDirectory=$P $P/$A/loop_s3.sh
systemd-run --user --unit onchain-b3-weeks-local -p MemoryMax=5632M -p WorkingDirectory=$P $P/$A/loop_local.sh
```
Expected: `logs/weeks.jsonl` gains `week` events; ≈ 15–18 h. Restart a loop if its unit fails (finished weeks are skipped).

- [ ] **Step 3: Record B3-CP1**

When both units are inactive: count `weeks/*.json`, `*.unavailable.json`, `*.failed.json`, `keys/*.npy`; write the counts and the peak memory per period to `STATE.md`; commit `STATE.md` (`docs(onchain-b3): B3-CP1 data pass record`).

---

### Task 9: History, dictionary, MCM, features (B3-CP2)

Operational.

- [ ] **Step 1: History pass (keys deleted after verification)**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b3.cli history --delete-keys`
Expected: `{"weeks": <built>, "keys_deleted": true}` ≈ 1 h; peak ≈ 1.5 GB (Bloom 1 GiB).

- [ ] **Step 2: Dictionary and MCM (two shards)**

```bash
OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b3.cli dictionary
P=$PWD; for s in 0 1; do systemd-run --user --unit onchain-b3-mcm$s -p MemoryMax=3G -p WorkingDirectory=$P \
  $P/.venv/bin/python -m tradingagents.research.onchain_b3.cli mcm --shard $s/2; done
```
Expected: 32 motifs; `mcm/*.npy` = built weeks; ≈ 3.5 h.

- [ ] **Step 3: Feature table**

Run: `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b3.cli features`
Expected: `{"weeks": <built>, "missing": <unavailable+failed>, "columns": 14 + 10 + 25 + 4 + 96}` = 149.

- [ ] **Step 4: Record B3-CP2 and commit `STATE.md`**

---

### Task 10: Screen, selection, holdout (B3-CP3, B3-CP4)

Operational. The selection commit precedes the holdout.

- [ ] **Step 1:** `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b3.cli screen` — expect 42 rows in `SCREEN.md` and `selection.json`.
- [ ] **Step 2:** Commit `SCREEN.md`, `selection.json`, `STATE.md` (`research(onchain-b3): B3-CP3 screen and committed selection`).
- [ ] **Step 3:** `OMP_NUM_THREADS=2 .venv/bin/python -m tradingagents.research.onchain_b3.cli holdout` — either "screen negative: holdout not opened" or `HOLDOUT.md`.
- [ ] **Step 4:** Write `FORENSICS.md` for a negative screen (harness check against a constant forecast, feature counts, partial correlations of F4 with targets after F0, as in B2) or for a positive one (per-year and per-feature-block detail); update `STATE.md`, memory note, and the audit page; commit (`research(onchain-b3): B3-CP4 result`).

---

## Self-review

**Spec coverage:** §3 data pass → Tasks 4, 7, 8; §4.1–4.6 → Task 2; §4.7 → Tasks 3, 9; §5 → Tasks 7, 9; §6 → Tasks 4, 5; §7 → Tasks 1, 5, 6; §8 → Task 6; §9 → Tasks 6, 7, 10; §10 → Tasks 8–9; §11 layout → as listed; §12 testing → Tasks 2–7; §13 checkpoints → Tasks 8–10.

**Placeholders:** none; test expectations are enumerated next to the assertions.

**Type consistency:** `structure_features(idx, is_ex, cfg, seed)` used by `build_week3`; `build_week3(...) -> (summary, graph, keys)` used by `build_one3`; `history_pass(weeks, load_keys, log2, k)`; `columns3(df, set, cfg)` used by `run_screen3`/`evaluate3`; result dicts match B2's `report`.

**Review Focus coverage:** 1 → Task 2 `test_degenerate_graphs_are_finite`; 2 → Task 2 `test_self_only_nodes`; 3 → Task 3 `test_missing_week_poisons_window_not_bloom`; 4 → Task 5 `test_dev_four_week_targets_stop_at_cutoff`; 5 → Task 7 `test_late_stages_refuse_incomplete_capture`.
