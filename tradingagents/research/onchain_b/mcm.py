"""Per-week motif convolution: similarity of every node neighborhood to every motif (paper §2.3)."""
from __future__ import annotations

import numpy as np

from .matching.batched import match_many
from .neighborhoods import Adjacency


def compute_week(week, dictionary, cfg, n_max, chunk=4096, log=None):
    """K×|motifs| float32 matrix of Eq. 1 scores between each node's neighborhood and each motif."""
    adj = Adjacency.from_week(week)
    motifs = dictionary.motifs
    K, m = week.n, len(motifs)
    out = np.zeros((K, m), np.float32)
    for start in range(0, K, chunk):
        centers = range(start, min(K, start + chunk))
        hoods = [adj.neighborhood(c, n_max) for c in centers]
        pairs = [(h, mo) for h in hoods for mo in motifs]
        scores, _ = match_many(pairs, cfg)
        out[start:start + len(hoods)] = scores.reshape(len(hoods), m)
        if log:
            log.event(event='mcm_chunk', week=week.week, done=start + len(hoods), total=K)
    return out
