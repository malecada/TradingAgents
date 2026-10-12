"""Eq. 1 agreement functions and objective (paper §2.2, literal)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MatchConfig:
    alpha: float
    beta0: float
    beta_final: float
    beta_rate: float
    max_iterations: int

    @classmethod
    def from_json(cls, d):
        return cls(float(d['alpha']), float(d['beta0']), float(d['beta_final']),
                   float(d['beta_rate']), int(d['max_iterations']))


def node_agreement(x1, x2):
    """s2(u, i) = exp(-mean_f (x_u - x_i)^2), shape (n1, n2)."""
    d = x1[:, None, :] - x2[None, :, :]
    return np.exp(-np.mean(d * d, axis=2))


def edge_agreement(f1, f2):
    """s1(e_a, e_b) = exp(-mean_f (f_a - f_b)^2), shape (l1, l2); empty when either side has no edges."""
    if len(f1) == 0 or len(f2) == 0:
        return np.zeros((len(f1), len(f2)))
    d = f1[:, None, :] - f2[None, :, :]
    return np.exp(-np.mean(d * d, axis=2))


def score(g1, g2, hard, alpha: float) -> float:
    """Eq. 1 on a hard assignment: [edge/(2 sqrt(l1 l2)) + alpha * node/sqrt(n1 n2)] / (1 + alpha)."""
    n1, n2 = g1.x.shape[0], g2.x.shape[0]
    l1, l2 = g1.edge_index.shape[1], g2.edge_index.shape[1]
    node = float((node_agreement(g1.x, g2.x) * hard).sum()) / np.sqrt(n1 * n2)
    edge = 0.0
    if l1 and l2:
        s1 = edge_agreement(g1.edge_attr, g2.edge_attr)
        u, v = g1.edge_index
        i, j = g2.edge_index
        both = hard[u[:, None], i[None, :]] & hard[v[:, None], j[None, :]]
        edge = float((s1 * both).sum()) / (2.0 * np.sqrt(l1 * l2))
    return (edge + alpha * node) / (1.0 + alpha)
