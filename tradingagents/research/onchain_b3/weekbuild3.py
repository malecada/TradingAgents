"""One week for B3: B2 activity/role features, whole-graph structure (F4 snapshot),
the top-20,000 graph for motifs, and the week's address keys for the history pass."""
from __future__ import annotations

import numpy as np
import pyarrow as pa

from ..onchain_b.weekly import _index, aggregate_pairs, top_k_subgraph
from ..onchain_b2.weekbuild import address_table, f1_features, role_flows
from . import history, structure


def build_week3(week, events_list, counters, exchanges, ex_bytes, cfg, week_index):
    r = cfg['roles']
    pairs = aggregate_pairs(list(events_list))
    addr = address_table(pairs)
    events = pa.concat_tables(list(events_list))
    f1 = f1_features(events, pairs, addr, list(counters), r['top_share_n'])
    del events
    f3a, whales = role_flows(pairs, addr, exchanges, r['deposit_share'], r['whales'])
    del addr
    idx = _index(pairs)
    is_ex = np.isin(idx[0], ex_bytes)
    s = cfg['structure']
    f4 = structure.structure_features(idx, is_ex, s, s['wedge_seed'] + week_index)
    keys = history.keys_from_addresses(idx[0])
    del idx
    graph = top_k_subgraph(pairs, cfg['k'], week)
    summary = {'week': week, 'counters': list(counters), 'f1': f1, 'f3a': f3a, 'f4': f4, 'whales': whales,
               'graph': dict(graph.summary)}
    return summary, graph, keys