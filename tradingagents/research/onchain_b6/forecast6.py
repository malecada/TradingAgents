# tradingagents/research/onchain_b6/forecast6.py
"""Forecast comparisons (spec §5) on B5's walk-forward runner, one run per track and target."""
from __future__ import annotations

import numpy as np

from ..onchain_b5 import forecast as F5

SETS = ['X0', 'X1', 'X2', 'X3', 'X4']


def set_prefixes(name, track, cfg, with_tron):
    blocks = cfg['set_blocks'][name]
    if 'T' in blocks and not with_tron:
        raise ValueError('Tron block not available')
    out = list(cfg['tracks'][track]['base'])
    for b in blocks:
        out += cfg['blocks'][b]
    return out


def _run_cfg(track, target, cfg, with_tron):
    tc = cfg['tracks'][track]
    sets = SETS + (['X5'] if with_tron else [])
    comps = cfg['comparisons'] + ([cfg['tron_comparison']] if with_tron else [])
    return {'sets': {s: set_prefixes(s, track, cfg, with_tron) for s in sets}, 'comparisons': comps,
            'families': cfg['families'], 'folds': {'test_years': tc['test_years'], 'inner_len': cfg['folds']['inner_len'],
                                                   'min_train': cfg['folds']['min_train']},
            'groups': tc['groups'], 'gate': cfg['gate'], 'models': cfg['models']}


def _passed(r, track_cfg, group_rows, min_wins):
    if track_cfg['criterion'] == 'years':
        return bool(r['hi'] < 0 and r['wins'] >= min_wins)
    first, second = list(track_cfg['groups'])
    if r['group'] != first:
        return bool(r['mean_diff'] < 0)
    other = group_rows.get(second)
    return bool(r['hi'] < 0 and other is not None and other['mean_diff'] < 0)


def run_all(samples_by_track, cfg, with_tron):
    results = []
    for track, df in samples_by_track.items():
        tc = cfg['tracks'][track]
        for target, h in cfg['targets'].items():
            d = df[df[target].notna()].copy()
            d['y'], d['tau_h'] = d[target], float(h)
            _, res = F5.run(d, _run_cfg(track, target, cfg, with_tron))
            for r in res:
                r['track'], r['target'] = track, target
            by = {}
            for r in res:
                by.setdefault((r['family'], r['set'], r['comparator']), {})[r['group']] = r
            for r in res:
                r['passed'] = _passed(r, tc, by[(r['family'], r['set'], r['comparator'])], cfg['folds']['min_year_wins'])
            results += res
    return results


def report(results):
    lines = ['| track | target | family | comparison | group | n | mean diff | 95 % CI | years better | pass |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for r in results:
        yrs = len(r['years']) if r['years'] else 0
        lines.append(f"| {r['track']} | {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['group']} | {r['n']} | "
                     f"{r['mean_diff']:+.5f} | [{r['lo']:+.5f}, {r['hi']:+.5f}] | {r['wins']}/{yrs} | {'PASS' if r['passed'] else '—'} |")
    return '\n'.join(lines)
