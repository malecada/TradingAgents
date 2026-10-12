"""Many (G1, G2) pairs at once: same arithmetic as reference.match, bucketed by (n1, n2).

Per temperature: one gather of M[v, j], one multiply by the fixed 0.5*s1 weights,
one index_add into Q, then log-domain row and column normalization. Hardening is
vectorized across the bucket. float64 throughout.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
import torch

from .agreement import edge_agreement, node_agreement


def _products(g1, g2, n2, offset):
    u, v = g1.edge_index
    i, j = g2.edge_index
    l1, l2 = len(u), len(i)
    if l1 == 0 or l2 == 0:
        return np.zeros(0), np.zeros(0, np.int64), np.zeros(0, np.int64), l1, l2
    w = 0.5 * edge_agreement(g1.edge_attr, g2.edge_attr)                 # (l1, l2)
    gi = (offset + v[:, None] * n2 + j[None, :]).ravel()                   # read M[v, j]
    si = (offset + u[:, None] * n2 + i[None, :]).ravel()                   # add into Q[u, i]
    return w.ravel(), gi, si, l1, l2


def _solve_chunk(pairs, n1, n2, cfg):
    B = len(pairs)
    nm = n1 * n2
    V = torch.from_numpy(np.stack([node_agreement(g1.x, g2.x) for g1, g2 in pairs]).reshape(B, nm))
    ws, gis, sis, l1s, l2s, seg = [], [], [], [], [], []
    for p, (g1, g2) in enumerate(pairs):
        w, gi, si, l1, l2 = _products(g1, g2, n2, p * nm)
        ws.append(w); gis.append(gi); sis.append(si); l1s.append(l1); l2s.append(l2)
        seg.append(np.full(len(w), p, np.int64))
    w = torch.from_numpy(np.concatenate(ws))
    gi = torch.from_numpy(np.concatenate(gis))
    si = torch.from_numpy(np.concatenate(sis))
    seg = torch.from_numpy(np.concatenate(seg))
    M = V.clone()
    beta = cfg.beta0
    it = 0
    while beta <= cfg.beta_final and it < cfg.max_iterations:
        Q = cfg.alpha * V
        if len(w):
            Q = Q.reshape(-1).index_add(0, si, w * M.reshape(-1)[gi]).reshape(B, nm)
        L = (beta * Q).reshape(B, n1, n2)
        L = L - torch.logsumexp(L, dim=2, keepdim=True)
        L = L - torch.logsumexp(L, dim=1, keepdim=True)
        M = torch.exp(L).reshape(B, nm)
        beta *= 1.0 + cfg.beta_rate
        it += 1
    # greedy hardening, vectorized over pairs
    work = M.reshape(B, n1, n2).clone()
    hard = torch.zeros(B, n1, n2, dtype=torch.bool)
    ar = torch.arange(B)
    for _ in range(min(n1, n2)):
        k = torch.argmax(work.reshape(B, nm), dim=1)
        u, i = k // n2, k % n2
        hard[ar, u, i] = True
        work[ar, u, :] = -np.inf
        work[ar, :, i] = -np.inf
    hard_flat = hard.reshape(-1).to(torch.float64)
    node = (V * hard.reshape(B, nm)).sum(1) / np.sqrt(n1 * n2)
    edge = torch.zeros(B, dtype=torch.float64)
    if len(w):
        both = hard_flat[si] * hard_flat[gi]
        edge = edge.index_add(0, seg, 2.0 * w * both)
    denom = torch.tensor([2.0 * np.sqrt(l1 * l2) if l1 and l2 else 1.0 for l1, l2 in zip(l1s, l2s)], dtype=torch.float64)
    scores = ((edge / denom) + cfg.alpha * node) / (1.0 + cfg.alpha)
    return scores.numpy(), [h.numpy() for h in hard]


def match_many(pairs, cfg, max_products=20_000_000):
    """Scores and hard assignments for every (G1, G2) pair, in input order."""
    buckets = defaultdict(list)
    for p, (g1, g2) in enumerate(pairs):
        buckets[(g1.x.shape[0], g2.x.shape[0])].append(p)
    scores = np.zeros(len(pairs))
    hards = [None] * len(pairs)
    for (n1, n2), idx in buckets.items():
        chunk, load = [], 0

        def flush(chunk):
            s, h = _solve_chunk([pairs[q] for q in chunk], n1, n2, cfg)
            for q, sq, hq in zip(chunk, s, h):
                scores[q] = sq
                hards[q] = hq

        for q in idx:
            g1, g2 = pairs[q]
            cost = g1.edge_index.shape[1] * g2.edge_index.shape[1]
            if chunk and load + cost > max_products:
                flush(chunk)
                chunk, load = [], 0
            chunk.append(q)
            load += cost
        if chunk:
            flush(chunk)
    return scores, hards


def score_matrix(lefts, rights, cfg):
    """S(left, right) for all left × right pairs."""
    pairs = [(a, b) for a in lefts for b in rights]
    s, _ = match_many(pairs, cfg)
    return s.reshape(len(lefts), len(rights))
