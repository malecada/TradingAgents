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