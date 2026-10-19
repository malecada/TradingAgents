# tradingagents/research/onchain_b6/structure6.py
"""Hourly graph structure (spec §4.1) on the hour's non-self transfers."""
from __future__ import annotations

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from ..onchain_b3.structure import gini, kcore_alive, undirected_edges

NAMES = ['gs_active', 'gs_new_share', 'gs_edges', 'gs_edges_per_node', 'gs_value_gini', 'gs_top10_share',
         'gs_core2_share', 'gs_giant_share', 'gs_ex_cp', 'gs_ex_cp_new_share', 'gs_cex_cex_usd']


def hour_structure(src, dst, usd, is_ex_src, is_ex_dst, ent_src, ent_dst, bloom_contains, top_n):
    src, dst, usd = np.asarray(src, np.uint64), np.asarray(dst, np.uint64), np.asarray(usd, float)
    m = src != dst
    src, dst, usd = src[m], dst[m], usd[m]
    is_ex_src, is_ex_dst, ent_src, ent_dst = (np.asarray(x)[m] for x in (is_ex_src, is_ex_dst, ent_src, ent_dst))
    if len(src) == 0:
        return {k: 0.0 for k in NAMES}
    keys, inv = np.unique(np.concatenate([src, dst]), return_inverse=True)
    n = len(keys)
    a, b = inv[:len(src)], inv[len(src):]
    edges = len(np.unique(a.astype(np.int64) * n + b))
    known = bloom_contains(keys)
    out_usd = np.bincount(a, weights=usd, minlength=n)
    pos = np.sort(out_usd[out_usd > 0])[::-1]
    ua, ub = undirected_edges(a, b, n)
    core2 = float(kcore_alive(ua, ub, n, 2).mean()) if len(ua) else 0.0
    _, lab = connected_components(coo_matrix((np.ones(len(ua)), (ua, ub)), shape=(n, n)), directed=False)
    giant = float(np.bincount(lab).max() / n)
    one_ex = is_ex_src ^ is_ex_dst
    cp = np.unique(np.concatenate([a[one_ex & ~is_ex_src], b[one_ex & ~is_ex_dst]]))
    cross = is_ex_src & is_ex_dst & (ent_src != ent_dst)
    return {'gs_active': float(n), 'gs_new_share': float((~known).mean()), 'gs_edges': float(edges),
            'gs_edges_per_node': float(edges / n), 'gs_value_gini': gini(pos),
            'gs_top10_share': float(pos[:top_n].sum() / pos.sum()) if len(pos) else 0.0,
            'gs_core2_share': core2, 'gs_giant_share': giant, 'gs_ex_cp': float(len(cp)),
            'gs_ex_cp_new_share': float((~known[cp]).mean()) if len(cp) else 0.0,
            'gs_cex_cex_usd': float(usd[cross].sum())}
