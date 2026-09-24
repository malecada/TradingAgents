"""Frozen boundary objects for the independently specified pipeline."""
from __future__ import annotations
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Mapping
import numpy as np
from .provenance import require_hash, utc


@dataclass(frozen=True)
class GraphSnapshot:
    asset: str
    start_utc: str
    end_utc: str
    available_at: str
    source_hashes: tuple[str, ...]
    graph_config_hash: str
    node_ids: tuple[str, ...]
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_features: np.ndarray
    raw_count: int
    admitted_count: int
    exclusion_counts: Mapping[str, int]

    def __post_init__(self):
        for name in ('node_features', 'edge_index', 'edge_features'):
            array = np.array(getattr(self, name), copy=True)
            array.setflags(write=False)
            object.__setattr__(self, name, array)
        object.__setattr__(self, 'node_ids', tuple(self.node_ids))
        object.__setattr__(self, 'source_hashes', tuple(self.source_hashes))
        object.__setattr__(self, 'exclusion_counts', MappingProxyType(dict(self.exclusion_counts)))


@dataclass(frozen=True)
class Fold:
    id: str
    train_start: str
    train_end: str
    validation_start: str | None
    validation_end: str | None
    test_start: str
    test_end: str
    member_hash: str


@dataclass(frozen=True)
class Prediction:
    lane: str
    asset: str
    arm: str
    fold_id: str
    seed: int
    decision_at: str
    label_start: str
    label_end: str
    max_input_available_at: str
    y_true: float
    probability_up: float | None
    predicted_price: float | None
    checkpoint_hash: str


@dataclass(frozen=True)
class ArtifactKey:
    source_hashes: tuple[str, ...]
    schema_version: int
    transform_commit: str
    config_hash: str
    fold_id: str
    train_member_hash: str
    dictionary_hash: str
    seed: int
    weight_hash: str


def validate_graph(g: GraphSnapshot) -> None:
    if g.asset not in {'ETH', 'BTC'}:
        raise ValueError('unsupported asset')
    if not utc(g.start_utc) < utc(g.end_utc) <= utc(g.available_at):
        raise ValueError('invalid graph clocks')
    require_hash(g.graph_config_hash)
    if not g.source_hashes:
        raise ValueError('source identities required')
    for value in g.source_hashes:
        require_hash(value)
    n = len(g.node_ids)
    if any(not isinstance(x, str) or not x for x in g.node_ids) or len(set(g.node_ids)) != n:
        raise ValueError('duplicate or invalid node identities')
    if g.node_features.ndim != 2 or g.node_features.shape[0] != n:
        raise ValueError('node feature dimensions')
    if g.edge_index.ndim != 2 or g.edge_index.shape[0] != 2:
        raise ValueError('edge index dimensions')
    if not np.issubdtype(g.edge_index.dtype, np.integer):
        raise ValueError('integer endpoints required')
    e = g.edge_index.shape[1]
    if g.edge_features.ndim != 2 or g.edge_features.shape[0] != e:
        raise ValueError('edge feature dimensions')
    if e and (g.edge_index.min() < 0 or g.edge_index.max() >= n):
        raise ValueError('invalid endpoint')
    if len(set(map(tuple, g.edge_index.T))) != e:
        raise ValueError('duplicate aggregated edges')
    for array in (g.node_features, g.edge_features):
        if not np.issubdtype(array.dtype, np.number) or not np.isfinite(array).all():
            raise ValueError('nonfinite or nonnumeric attributes')
    counts = [g.raw_count, g.admitted_count, *g.exclusion_counts.values()]
    if any(type(c) is not int or c < 0 for c in counts):
        raise ValueError('invalid counts')
    if g.raw_count != g.admitted_count + sum(g.exclusion_counts.values()):
        raise ValueError('event conservation failed')
    if e > g.admitted_count:
        raise ValueError('more aggregate edges than admitted events')


def graph_from_dict(value: dict) -> GraphSnapshot:
    names = {f.name for f in fields(GraphSnapshot)}
    if set(value) - names:
        raise ValueError('unknown graph fields')
    if names - set(value):
        raise ValueError('missing graph fields')
    g = GraphSnapshot(**value)
    validate_graph(g)
    return g


def graph_to_dict(g: GraphSnapshot) -> dict:
    validate_graph(g)
    return {f.name: (getattr(g, f.name).tolist() if isinstance(getattr(g, f.name), np.ndarray)
                    else dict(g.exclusion_counts) if f.name == 'exclusion_counts'
                    else getattr(g, f.name)) for f in fields(g)}


@dataclass(frozen=True)
class Transaction:
    asset: str
    identity: str
    timestamp: str
    sender: str
    recipient: str | None
    value: float
    receipt_status: int
    source_hash: str
    precision: str


@dataclass(frozen=True)
class PricePanel:
    symbol: str
    dates: tuple[str, ...]
    closes: tuple[float, ...]
    missing_dates: tuple[str, ...]
    source_hash: str
    retrieved_at: str
    historical_vintage_verified: bool = False
