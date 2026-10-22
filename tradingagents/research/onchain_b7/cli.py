# tradingagents/research/onchain_b7/cli.py
"""B7 stage runner: feature and target tables, walk-forward forecasts per track and target
(resumable: one file per unit), and the tables."""
from __future__ import annotations

import argparse
import json
import time

import pandas as pd

from ..onchain_b.runlog import Log
from ..onchain_b4 import dataset4, hourmarket
from ..onchain_b4.cli import _write_json
from ..onchain_b5.decisions import px_features
from . import config, features7, forecast7, targets7

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B4 = config.B4_ARTIFACTS
B6 = config.B6_ARTIFACTS
MK = ['mk_dvol', 'mk_dvol_chg24', 'mk_iv']


def load_inputs():
    c = config.load()
    raw4 = pd.read_parquet(B4 / 'features' / 'hourly_raw.parquet')[c['series']['b4']]
    raw6 = pd.read_parquet(B6 / 'features' / 'hourly_raw.parquet')[c['series']['b6']]
    flows = pd.read_parquet(B4 / 'features' / 'hourly.parquet')
    flows = flows[[x for x in flows.columns if x.startswith(tuple(c['blocks']['FA']))]]
    mk = pd.read_parquet(B6 / 'features' / 'features_B.parquet')[MK]
    bars = hourmarket.load_all(B4 / 'market' / 'hourly_dev.json', B4 / 'sealed' / 'hourly_sealed.json')
    minutes = pd.read_parquet(B6 / 'market' / 'minutes_ETH.parquet')['close']
    large = pd.concat([pd.read_parquet(p, columns=['ts', 'token', 'amount', 'direction'])
                       for p in sorted((B6 / 'large').glob('*.parquet'))], ignore_index=True)
    return c, raw4, raw6, flows, mk, bars, minutes, large


def build_tables(c, raw4, raw6, flows, mk, bars, minutes, large):
    raw = raw4.join(raw6, how='outer').sort_index()
    idx = raw.index
    market = dataset4.price_features(bars).join(px_features(bars)).reindex(idx)
    table = (features7.multiscale(raw, c['engineering'])
             .join(flows.reindex(idx)).join(market)
             .join(targets7.range_features(minutes, idx, c['range']))
             .join(features7.event_hours(large, idx, c['events']['thresholds'], c['events']['cap_hours'])))
    table = table.join(features7.interactions(table, c['interactions'])).join(mk.reindex(idx))
    targets = (dataset4.hourly_targets(bars)[['V6', 'V24']].reindex(idx)
               .join(targets7.jump_targets(bars, c['jump']).reindex(idx))
               .join(targets7.mmax_targets(minutes, idx, c['mmax'])))
    return table, targets


def stage_features(args):
    c, *inputs = load_inputs()
    table, targets = build_tables(c, *inputs)
    out = ARTIFACTS / 'features'
    out.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out / 'table.parquet')
    targets.to_parquet(out / 'targets.parquet')
    print(json.dumps({'hours': len(table), 'columns': table.shape[1], 'targets': {t: int(targets[t].notna().sum()) for t in targets.columns},
                      'base_rate': {t: round(float(targets[t].mean()), 4) for t in ('J6', 'J24')}}))


def _support(s, task):
    """Rows per year (and positives for a classification target) of one target column."""
    years = {}
    for yr, g in s.groupby(s.index.year):
        years[int(yr)] = {'n': int(g.notna().sum()), **({'pos': int(g.sum())} if task == 'classification' else {})}
    return {'n': int(s.notna().sum()), 'mean': float(s.mean()), 'years': years}


def stage_forecast(args):
    c = config.load()
    only = set(args.only.split(',')) if args.only else None
    table = pd.read_parquet(ARTIFACTS / 'features' / 'table.parquet')
    targets = pd.read_parquet(ARTIFACTS / 'features' / 'targets.parquet')
    out = ARTIFACTS / 'forecast'
    out.mkdir(parents=True, exist_ok=True)
    log = Log(ARTIFACTS / 'logs' / 'forecast.jsonl')
    n = {}
    for track in c['tracks']:
        df = forecast7.samples(track, table, targets, c)
        n[track] = {t: _support(df[t], c['targets'][t]['task']) for t in c['targets']}
        for target in c['targets']:
            unit = out / f'{track}_{target}.json'
            if (only is not None and f'{track}:{target}' not in only) or unit.exists():
                continue
            t0 = time.time()
            P, meta = forecast7.predict_all(df, target, track, c, log=log.event)
            res = forecast7.compare(P, target, track, c)
            P.to_parquet(out / f'pred_{track}_{target}.parquet')
            _write_json(unit, {'results': res, 'meta': meta, 'seconds': round(time.time() - t0, 1)})
            log.event(event='unit', track=track, target=target, seconds=round(time.time() - t0, 1), passed=sum(r['passed'] for r in res))
    units = sorted(out.glob('[AB]_*.json'))
    docs = {u.stem: json.loads(u.read_text()) for u in units}
    results = [r for d in docs.values() for r in d['results']]
    _write_json(out / 'results.json', {'results': results, 'meta': {k: d['meta'] for k, d in docs.items()}, 'n': n,
                                       'seconds': {k: d['seconds'] for k, d in docs.items()}})
    print(json.dumps({'units': len(units), 'rows': len(results), 'passed': sum(r['passed'] for r in results)}))


def stage_report(args):
    res = json.loads((ARTIFACTS / 'forecast' / 'results.json').read_text())
    lines = ['# B7 tables (generated; interpretation in RESULTS.md)', '', '## Samples', '',
             '| track | target | rows | mean | rows per year (positives) |', '|---|---|---|---|---|']
    for track, ts in res['n'].items():
        for t, v in ts.items():
            per = ', '.join(f"{yr} {d['n']}" + (f" ({d['pos']})" if 'pos' in d else '') for yr, d in sorted(v['years'].items(), key=lambda kv: int(kv[0])))
            lines.append(f"| {track} | {t} | {v['n']} | {v['mean']:.4f} | {per} |")
    lines += ['', '## Comparisons', '', forecast7.report(res['results']), '', '## Model detail', '', forecast7.detail_report(res['meta'])]
    STUDY.mkdir(parents=True, exist_ok=True)
    (STUDY / 'TABLES.md').write_text('\n'.join(lines) + '\n')
    print(f'{len(lines)} lines')


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b7')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('features').set_defaults(fn=stage_features)
    f = sub.add_parser('forecast')
    f.add_argument('--only', default=None, help='comma-separated track:target units')
    f.set_defaults(fn=stage_forecast)
    sub.add_parser('report').set_defaults(fn=stage_report)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == '__main__':
    main()
