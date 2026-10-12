"""Weak one-hop induced neighborhoods with the declared N_max cap (spec §5.3)."""
from __future__ import annotations

from typing import NamedTuple

import numpy as np

from .weekly import WeekGraph


class Graph(NamedTuple):
    x: np.ndarray            # float64 [n, 4]
    edge_index: np.ndarray   # int64 [2, l] local indices
    edge_attr: np.ndarray    # float64 [l, 2]
    nodes: np.ndarray        # int64 [n] global node ids (sorted)
    center: int              # local index of the center


class Adjacency:
    """CSR views over a WeekGraph for fast induced-neighborhood extraction."""

    def __init__(self, week: WeekGraph):
        self.w = week
        n = week.n
        src = week.edge_index[0].astype(np.int64)
        dst = week.edge_index[1].astype(np.int64)
        self.src, self.dst = src, dst
        o = np.argsort(src, kind='stable')
        self.out_eid = o
        self.out_ptr = np.searchsorted(src[o], np.arange(n + 1))
        i = np.argsort(dst, kind='stable')
        self.in_eid = i
        self.in_ptr = np.searchsorted(dst[i], np.arange(n + 1))
        self._mask = np.zeros(n, bool)
        self._local = np.full(n, -1, np.int64)

    @classmethod
    def from_week(cls, week):
        return cls(week)

    def _incident(self, c):
        return np.concatenate([self.out_eid[self.out_ptr[c]:self.out_ptr[c + 1]],
                               self.in_eid[self.in_ptr[c]:self.in_ptr[c + 1]]])

    def neighborhood(self, center: int, n_max: int) -> Graph:
        w = self.w
        eids = self._incident(center)
        other = np.where(self.src[eids] == center, self.dst[eids], self.src[eids])
        keep = other != center
        nbr, inv = np.unique(other[keep], return_inverse=True)
        if len(nbr):
            strength = np.bincount(inv, weights=w.edge_count[eids[keep]], minlength=len(nbr))
        else:
            strength = np.zeros(0)
        order = np.lexsort((nbr, -strength))[:max(n_max - 1, 0)]
        nodes = np.sort(np.concatenate([[center], nbr[order]]).astype(np.int64))
        self._mask[nodes] = True
        self._local[nodes] = np.arange(len(nodes))
        cand = np.concatenate([self.out_eid[self.out_ptr[v]:self.out_ptr[v + 1]] for v in nodes])
        sel = cand[self._mask[self.dst[cand]]]
        ls, ld = self._local[self.src[sel]], self._local[self.dst[sel]]
        eo = np.lexsort((ld, ls))
        sel = sel[eo]
        self._mask[nodes] = False
        self._local[nodes] = -1
        return Graph(w.x[nodes].astype(np.float64),
                     np.stack([ls[eo], ld[eo]]).astype(np.int64),
                     w.edge_attr[sel].astype(np.float64),
                     nodes, int(np.searchsorted(nodes, center)))
