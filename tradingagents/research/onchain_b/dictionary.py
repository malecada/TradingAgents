"""Paper §2.1: sampled neighborhoods → average-linkage clusters → medoid motifs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import cut_tree, linkage
from scipy.spatial.distance import squareform

from .matching.batched import score_matrix
from .neighborhoods import Adjacency, Graph


def _layout(weeks):
    keys = sorted(weeks)
    offsets, o = {}, 0
    for k in keys:
        offsets[k] = o
        o += weeks[k].n
    return keys, offsets


def _initial_weights(weeks):
    return np.ones(sum(w.n for w in weeks.values()), np.float64)


def _halve_inside(weeks, weights, drawn, n_max, adjacency=None):
    """After drawing `drawn`, zero its weight and halve the weights of centers inside its neighborhood."""
    keys, offsets = _layout(weeks)
    week, center = drawn
    adj = adjacency[week] if adjacency else Adjacency.from_week(weeks[week])
    g = adj.neighborhood(center, n_max)
    weights[offsets[week] + g.nodes] *= 0.5
    weights[offsets[week] + center] = 0.0


def sample_centers(weeks, n_samples, n_max, seed):
    keys, offsets = _layout(weeks)
    weights = _initial_weights(weeks)
    adjacency = {k: Adjacency.from_week(weeks[k]) for k in keys}
    owner = np.concatenate([[k] * weeks[k].n for k in keys])
    local = np.concatenate([np.arange(weeks[k].n) for k in keys])
    rng = np.random.Generator(np.random.PCG64(seed))
    out = []
    for _ in range(n_samples):
        total = weights.sum()
        if total <= 0:
            raise ValueError('insufficient candidates')
        k = int(rng.choice(len(weights), p=weights / total))
        drawn = (str(owner[k]), int(local[k]))
        out.append(drawn)
        _halve_inside(weeks, weights, drawn, n_max, adjacency)
    return out


def pairwise_distance(graphs, cfg):
    S = score_matrix(graphs, graphs, cfg)
    D = 1.0 - 0.5 * (S + S.T)
    np.fill_diagonal(D, 0.0)
    return D


def cluster_medoids(D, n_clusters):
    Z = linkage(squareform(D, checks=False), method='average')
    labels = cut_tree(Z, n_clusters=n_clusters).ravel()
    medoids = []
    for c in range(n_clusters):
        members = np.flatnonzero(labels == c)
        sums = D[np.ix_(members, members)].sum(1)
        medoids.append(int(members[int(np.argmin(sums))]))      # argmin → first index on ties
    return medoids


@dataclass
class Dictionary:
    motifs: list
    centers: list
    medoids: list
    seed: int
    n_max: int


def build(weeks, cfg, n_samples, n_clusters, n_max, seed) -> Dictionary:
    centers = sample_centers(weeks, n_samples, n_max, seed)
    adjacency = {k: Adjacency.from_week(weeks[k]) for k in weeks}
    graphs = [adjacency[w].neighborhood(c, n_max) for w, c in centers]
    if len(graphs) < n_clusters:
        raise ValueError('fewer samples than clusters')
    D = pairwise_distance(graphs, cfg)
    med = cluster_medoids(D, n_clusters)
    return Dictionary([graphs[m] for m in med], centers, med, seed, n_max)


def save(d: Dictionary, path: Path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    arrays = {}
    for k, g in enumerate(d.motifs):
        arrays[f'x{k}'] = g.x
        arrays[f'ei{k}'] = g.edge_index
        arrays[f'ea{k}'] = g.edge_attr
        arrays[f'nodes{k}'] = g.nodes
    np.savez(path / 'motifs.npz', **arrays)
    (path / 'dictionary.json').write_text(json.dumps(
        {'centers': [list(c) for c in d.centers], 'medoids': d.medoids, 'seed': d.seed, 'n_max': d.n_max,
         'centers_of_motifs': [list(d.centers[m]) for m in d.medoids]}, indent=1))


def load(path: Path) -> Dictionary:
    path = Path(path)
    meta = json.loads((path / 'dictionary.json').read_text())
    z = np.load(path / 'motifs.npz')
    motifs = [Graph(z[f'x{k}'], z[f'ei{k}'], z[f'ea{k}'], z[f'nodes{k}'], 0) for k in range(len(meta['medoids']))]
    return Dictionary(motifs, [tuple(c) for c in meta['centers']], meta['medoids'], meta['seed'], meta['n_max'])
