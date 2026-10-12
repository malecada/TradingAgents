"""Per-pair literal Algorithm 1 (paper §2.2.3) with greedy hardening. Readable, not fast."""
from __future__ import annotations

from typing import NamedTuple

import numpy as np
from scipy.special import logsumexp

from .agreement import edge_agreement, node_agreement, score


class Result(NamedTuple):
    hard: np.ndarray
    score: float
    iterations: int
    soft: np.ndarray


def harden(soft: np.ndarray) -> np.ndarray:
    """Repeatedly fix the global maximum (row-major ties) and delete its row and column."""
    n1, n2 = soft.shape
    work = soft.copy()
    hard = np.zeros((n1, n2), bool)
    for _ in range(min(n1, n2)):
        k = int(np.argmax(work))          # first occurrence → row-major ties
        u, i = divmod(k, n2)
        hard[u, i] = True
        work[u, :] = -np.inf
        work[:, i] = -np.inf
    return hard


def match(g1, g2, cfg) -> Result:
    V = node_agreement(g1.x, g2.x)
    u, v = g1.edge_index
    i, j = g2.edge_index
    W = 0.5 * edge_agreement(g1.edge_attr, g2.edge_attr)      # (l1, l2); the literal half coefficient
    M = V.copy()
    beta = cfg.beta0
    iterations = 0
    while beta <= cfg.beta_final and iterations < cfg.max_iterations:
        Q = cfg.alpha * V.copy()
        for a in range(len(u)):
            for b in range(len(i)):
                Q[u[a], i[b]] += W[a, b] * M[v[a], j[b]]
        L = beta * Q
        L = L - logsumexp(L, axis=1, keepdims=True)
        L = L - logsumexp(L, axis=0, keepdims=True)
        M = np.exp(L)
        beta *= 1.0 + cfg.beta_rate
        iterations += 1
    hard = harden(M)
    return Result(hard, score(g1, g2, hard, cfg.alpha), iterations, M)
