"""Admitted events → ordered-pair aggregates → paper-scale top-K induced subgraph (spec §5)."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

ADDR = r'^0x[0-9a-f]{40}$'


def admitted_events(table: pa.Table):
    """Filter one day's rows to admitted transfers; return (events, exclusion counters)."""
    n = table.num_rows
    if pc.count_distinct(table.column('hash')).as_py() != n:
        raise ValueError('duplicate transaction hash in day')
    status_ok = pc.equal(table.column('receipt_status'), 1)
    to_lower = pc.utf8_lower(table.column('to_address'))
    from_lower = pc.utf8_lower(table.column('from_address'))
    recipient_ok = pc.fill_null(pc.match_substring_regex(to_lower, ADDR), False)
    value_ok = pc.greater(table.column('value'), 0.0)
    if not pc.all(pc.fill_null(pc.match_substring_regex(from_lower, ADDR), False)).as_py():
        raise ValueError('malformed sender address')

    def count(mask):
        return int(pc.sum(pc.cast(mask, pa.int64())).as_py() or 0)

    counters = {'rows': n,
                'failed': count(pc.invert(status_ok)),
                'null_recipient': count(pc.and_(status_ok, pc.invert(recipient_ok))),
                'zero_value': count(pc.and_(pc.and_(status_ok, recipient_ok), pc.invert(value_ok)))}
    mask = pc.and_(pc.and_(status_ok, recipient_ok), value_ok)
    out = pa.table({'from_address': from_lower, 'to_address': to_lower,
                    'value_eth': pc.divide(table.column('value'), 1e18)}).filter(mask)
    counters['admitted'] = out.num_rows
    return out, counters


def aggregate_pairs(tables) -> pa.Table:
    t = pa.concat_tables(tables)
    g = t.group_by(['from_address', 'to_address']).aggregate([('value_eth', 'sum'), ('value_eth', 'count')])
    return g.rename_columns(['src', 'dst', 'value_eth', 'count']).select(['src', 'dst', 'count', 'value_eth'])


@dataclass
class WeekGraph:
    week: str
    addresses: np.ndarray          # S42, lexicographically sorted
    x: np.ndarray                  # float32 [K, 4]
    edge_index: np.ndarray         # int32 [2, E] local (src, dst)
    edge_attr: np.ndarray          # float32 [E, 2]
    edge_count: np.ndarray         # int64 [E] raw transaction counts
    summary: dict = field(default_factory=dict)

    @property
    def n(self):
        return len(self.addresses)

    @property
    def e(self):
        return self.edge_index.shape[1]


def _index(pairs):
    src = np.asarray(pairs.column('src').to_numpy(zero_copy_only=False)).astype('S42')
    dst = np.asarray(pairs.column('dst').to_numpy(zero_copy_only=False)).astype('S42')
    count = pairs.column('count').to_numpy().astype(np.int64)
    value = pairs.column('value_eth').to_numpy().astype(np.float64)
    addresses, inverse = np.unique(np.concatenate([src, dst]), return_inverse=True)
    return addresses, inverse[:len(src)], inverse[len(src):], count, value


def full_summary(pairs) -> dict:
    addresses, s, d, count, value = _index(pairs)
    n, e = len(addresses), len(s)
    return {'full_nodes': int(n), 'full_edges': int(e),
            'full_density': float(e / (n * (n - 1))) if n > 1 else 0.0,
            'full_transactions': int(count.sum())}


def top_k_subgraph(pairs: pa.Table, k: int, week: str) -> WeekGraph:
    addresses, s, d, count, value = _index(pairs)
    n = len(addresses)
    activity = np.bincount(s, weights=count, minlength=n) + np.bincount(d, weights=count, minlength=n)
    order = np.lexsort((np.arange(n), -activity))           # activity desc, then address asc
    keep = np.zeros(n, bool)
    keep[order[:min(k, n)]] = True
    sel = np.flatnonzero(keep)                               # lexicographic because addresses are sorted
    local = -np.ones(n, np.int64)
    local[sel] = np.arange(len(sel))
    m = keep[s] & keep[d]
    ls, ld, lc, lv = local[s[m]], local[d[m]], count[m], value[m]
    eo = np.lexsort((ld, ls))
    ls, ld, lc, lv = ls[eo], ld[eo], lc[eo], lv[eo]
    kk = len(sel)
    x = np.stack([np.log1p(np.bincount(ld, weights=lc, minlength=kk)),
                  np.log1p(np.bincount(ls, weights=lc, minlength=kk)),
                  np.log1p(np.bincount(ld, weights=lv, minlength=kk)),
                  np.log1p(np.bincount(ls, weights=lv, minlength=kk))], 1).astype(np.float32)
    edge_attr = np.stack([np.log1p(lc), np.log1p(lv)], 1).astype(np.float32)
    summary = {**full_summary(pairs), 'k_requested': int(k), 'k_effective': int(kk), 'edges': int(len(ls)),
               'density': float(len(ls) / (kk * (kk - 1))) if kk > 1 else 0.0,
               'min_activity_kept': float(activity[sel].min()) if kk else 0.0}
    return WeekGraph(week, addresses[sel], x, np.stack([ls, ld]).astype(np.int32), edge_attr,
                     lc.astype(np.int64), summary)


def save(g: WeekGraph, directory: Path):
    directory = Path(directory)
    if directory.exists():
        raise FileExistsError(f'week output exists: {directory}')
    directory.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(dir=directory.parent, prefix='.tmp-'))
    np.save(tmp / 'addresses.npy', g.addresses)
    np.save(tmp / 'x.npy', g.x)
    np.save(tmp / 'edge_index.npy', g.edge_index)
    np.save(tmp / 'edge_attr.npy', g.edge_attr)
    np.save(tmp / 'edge_count.npy', g.edge_count)
    (tmp / 'summary.json').write_text(json.dumps({'week': g.week, **g.summary}, indent=1, sort_keys=True))
    os.replace(tmp, directory)


def load(directory: Path) -> WeekGraph:
    directory = Path(directory)
    s = json.loads((directory / 'summary.json').read_text())
    week = s.pop('week')
    return WeekGraph(week, np.load(directory / 'addresses.npy'), np.load(directory / 'x.npy'),
                     np.load(directory / 'edge_index.npy'), np.load(directory / 'edge_attr.npy'),
                     np.load(directory / 'edge_count.npy'), s)
