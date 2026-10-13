"""One week: admitted events → ordered-pair aggregates → activity (F1), exchange/whale
role flows (F3a) and the top-K graph used for motifs (spec §5.2–5.3)."""
from __future__ import annotations

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

from ..onchain_b.weekly import admitted_events, aggregate_pairs, top_k_subgraph
from . import config


def _sum(x):
    v = pc.sum(x).as_py()
    return float(v) if v is not None else 0.0


def _sums(pairs, key, prefix):
    g = pairs.group_by(key).aggregate([('value_eth', 'sum'), ('count', 'sum')])
    return pa.table({'address': g[key], f'{prefix}_value': g['value_eth_sum'], f'{prefix}_count': g['count_sum']})


def address_table(pairs):
    t = _sums(pairs, 'src', 'out').join(_sums(pairs, 'dst', 'in'), keys='address', join_type='full outer')
    cols = {'address': t['address']}
    for name in ('out_value', 'out_count', 'in_value', 'in_count'):
        cols[name] = pc.fill_null(t[name], 0)
    return pa.table(cols)


def f1_features(events, pairs, addr, counters, top_n):
    rows = sum(c['rows'] for c in counters)
    n = events.num_rows
    vol = addr['out_value'].to_numpy() + addr['in_value'].to_numpy()
    q = pc.quantile(events['value_eth'], q=[0.5, 0.9], interpolation='linear').to_pylist()
    selfs = int(pc.sum(pc.cast(pc.equal(events['from_address'], events['to_address']), pa.int64())).as_py() or 0)
    active = addr.num_rows
    return {'f1_transfers': n,
            'f1_failed_share': sum(c['failed'] for c in counters) / rows,
            'f1_zero_share': sum(c['zero_value'] for c in counters) / rows,
            'f1_null_share': sum(c['null_recipient'] for c in counters) / rows,
            'f1_active': active,
            'f1_senders': int(pc.count_distinct(pairs['src']).as_py()),
            'f1_receivers': int(pc.count_distinct(pairs['dst']).as_py()),
            'f1_eth_moved': _sum(events['value_eth']),
            'f1_median_size': float(q[0]), 'f1_p90_size': float(q[1]),
            'f1_top_share': float(np.sort(vol)[::-1][:top_n].sum() / vol.sum()),
            'f1_self_share': selfs / n,
            'f1_edges': pairs.num_rows,
            'f1_mean_degree': pairs.num_rows / active}


def role_flows(pairs, addr, exchanges, deposit_share, n_whales):
    src_ex = pc.is_in(pairs['src'], value_set=exchanges)
    dst_ex = pc.is_in(pairs['dst'], value_set=exchanges)
    val, cnt = pairs['value_eth'], pairs['count']
    inflow = pc.and_(pc.invert(src_ex), dst_ex)
    outflow = pc.and_(src_ex, pc.invert(dst_ex))
    f = {'f3a_ex_in_value': _sum(pc.filter(val, inflow)), 'f3a_ex_in_count': int(_sum(pc.filter(cnt, inflow))),
         'f3a_ex_out_value': _sum(pc.filter(val, outflow)), 'f3a_ex_out_count': int(_sum(pc.filter(cnt, outflow)))}
    f['f3a_ex_net_value'] = f['f3a_ex_in_value'] - f['f3a_ex_out_value']

    # deposit-like: non-exchange, >= 1 transfer to E, >= deposit_share of outgoing ETH sent to E
    to_ex = pairs.filter(inflow).group_by('src').aggregate([('value_eth', 'sum')])
    to_ex = pa.table({'address': to_ex['src'], 'to_ex': to_ex['value_eth_sum']})
    a = addr.join(to_ex, keys='address', join_type='left outer')
    a_addr = np.asarray(a['address'].to_pylist(), dtype=object)
    a_out = a['out_value'].to_numpy()
    a_vol = a_out + a['in_value'].to_numpy()
    a_to_ex = pc.fill_null(a['to_ex'], 0.0).to_numpy()
    a_is_ex = np.asarray(pc.is_in(a['address'], value_set=exchanges).to_pylist(), dtype=bool)
    dep_mask = (~a_is_ex) & (a_to_ex > 0) & (a_to_ex >= deposit_share * a_out)
    deposits = pa.array(sorted(a_addr[dep_mask].tolist()), pa.string())
    src_dep = pc.is_in(pairs['src'], value_set=deposits)
    dst_dep = pc.is_in(pairs['dst'], value_set=deposits)
    src_other = pc.and_(pc.invert(src_ex), pc.invert(src_dep))
    f['f3a_dep_count'] = int(dep_mask.sum())
    f['f3a_dep_received_value'] = _sum(pc.filter(val, pc.and_(dst_dep, src_other)))
    to_e_or_d = pc.and_(pc.or_(dst_ex, dst_dep), src_other)
    f['f3a_ex_senders'] = int(pc.count_distinct(pc.filter(pairs['src'], to_e_or_d)).as_py())

    # whales: largest ETH moved among non-exchange addresses, ties by address
    cand = np.flatnonzero(~a_is_ex)
    order = cand[np.lexsort((a_addr[cand].astype(str), -a_vol[cand]))][:n_whales]
    whales = a_addr[order].tolist()
    w = pa.array(whales, pa.string())
    src_w, dst_w = pc.is_in(pairs['src'], value_set=w), pc.is_in(pairs['dst'], value_set=w)
    f['f3a_whale_net_to_ex'] = _sum(pc.filter(val, pc.and_(src_w, dst_ex))) - _sum(pc.filter(val, pc.and_(src_ex, dst_w)))
    f['f3a_whale_share'] = float(a_vol[order].sum() / a_vol.sum()) if a_vol.sum() > 0 else 0.0
    return f, whales


def build_week(week, day_tables, exchanges, cfg=None):
    c = cfg or config.load()
    r = c['roles']
    evs, counters = zip(*(admitted_events(t) for t in day_tables))
    events = pa.concat_tables(evs)
    pairs = aggregate_pairs(list(evs))
    addr = address_table(pairs)
    f1 = f1_features(events, pairs, addr, list(counters), r['top_share_n'])
    f3a, whales = role_flows(pairs, addr, exchanges, r['deposit_share'], r['whales'])
    graph = top_k_subgraph(pairs, c['k'], week)
    summary = {'week': week, 'counters': list(counters), 'f1': f1, 'f3a': f3a, 'whales': whales,
               'graph': dict(graph.summary)}
    return summary, graph