"""Motif features that keep the distribution instead of one mean (spec §5.3):
best-motif histogram, mean and ETH-volume-weighted mean score per motif (F2), and
mean score per motif over exchange and whale nodes of the top-K graph (F3b)."""
from __future__ import annotations

import numpy as np


def motif_features(F, graph, exchanges, whales):
    K, m = F.shape
    F = F.astype(np.float64)
    out = {}
    hist = np.bincount(F.argmax(1), minlength=m) / K
    mean = F.mean(0)
    w = np.expm1(graph.x[:, 2].astype(np.float64)) + np.expm1(graph.x[:, 3].astype(np.float64))
    vw = (w[:, None] * F).sum(0) / w.sum() if w.sum() > 0 else mean
    addrs = [a.decode() if isinstance(a, bytes) else str(a) for a in graph.addresses]
    for name, members in (('ex', exchanges), ('wh', whales)):
        mask = np.array([a in members for a in addrs], bool)
        role = F[mask].mean(0) if mask.any() else np.zeros(m)
        out[f'f3b_{name}_n'] = int(mask.sum())
        for k in range(m):
            out[f'f3b_{name}_{k}'] = float(role[k])
    for k in range(m):
        out[f'f2_hist_{k}'] = float(hist[k])
        out[f'f2_mean_{k}'] = float(mean[k])
        out[f'f2_vw_{k}'] = float(vw[k])
    return out