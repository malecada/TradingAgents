# tradingagents/research/onchain_b5/cli.py
"""B5 stage runner: fetch option trades / DVOL / BTC bars, build decision tables, run the
forecast comparison, the straddle backtests and the event study, and write the tables."""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

from ..onchain_b.runlog import Log
from ..onchain_b2 import market
from ..onchain_b4 import hourmarket
from . import config, decisions, deribit, events, forecast, implied, straddle

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B4 = config.B4_ARTIFACTS


def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True, default=lambda o: None if o != o else str(o)))
    os.replace(tmp, path)


def _opt_dir(asset):
    return ARTIFACTS / 'options' / asset


def options_complete(asset):
    d = _opt_dir(asset)
    return all((d / f'{day}.parquet').exists() or (d / f'{day}.unavailable.json').exists() for day in config.days(config.load()))


def trades_loader(asset):
    cache = {}

    def load(day):
        if day not in cache:
            p = _opt_dir(asset) / f'{day}.parquet'
            cache.clear()
            cache[day] = implied.prepare(deribit.load_day(p)) if p.exists() else None
        return cache[day]
    return load


def stage_fetch_options(args):
    c = config.load()
    log = Log(ARTIFACTS / 'logs' / f'options-{args.asset}.jsonl')
    for day in config.days(c):
        out = _opt_dir(args.asset) / f'{day}.parquet'
        if out.exists():
            continue
        t = time.time()
        try:
            df = deribit.with_retries(lambda: deribit.fetch_day(market.http_get, args.asset, day, c), c['deribit']['retries'])
        except deribit.Unavailable as e:
            _write_json(_opt_dir(args.asset) / f'{day}.unavailable.json', {'day': day, 'errors': e.errors})
            log.event(event='day', day=day, status='unavailable')
            continue
        deribit.save_day(df, out)
        (_opt_dir(args.asset) / f'{day}.unavailable.json').unlink(missing_ok=True)
        log.event(event='day', day=day, status='done', trades=int(len(df)), seconds=round(time.time() - t, 1))


def stage_fetch_dvol(args):
    c = config.load()
    w = c['window']
    for asset in c['assets']:
        s = deribit.fetch_dvol(market.http_get, asset, w['start'], w['end'], c)
        p = ARTIFACTS / 'market' / f'dvol_{asset}.parquet'
        p.parent.mkdir(parents=True, exist_ok=True)
        s.to_frame().to_parquet(p)
        print(json.dumps({'asset': asset, 'hours': len(s), 'first': str(s.index.min()), 'last': str(s.index.max())}))


def stage_fetch_bars(args):
    c = config.load()
    b = c['binance']
    bars, _ = hourmarket.fetch(market.http_get, b['BTC'], b['start'], b['end'])
    p = ARTIFACTS / 'market' / 'btc_hourly.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(sorted(bars.items()))))
    print(json.dumps({'btc_hours': len(bars)}))


def _bars(asset):
    if asset == 'ETH':
        return hourmarket.load_all(B4 / 'market' / 'hourly_dev.json', B4 / 'sealed' / 'hourly_sealed.json')
    return decisions.load_bars(ARTIFACTS / 'market' / 'btc_hourly.json')


def _flows(cfg):
    f = pd.read_parquet(B4 / 'features' / 'hourly.parquet')
    return f[[c for c in f.columns if c.startswith(tuple(cfg['flow_prefixes']))]]


def stage_decisions(args):
    c = config.load()
    for asset in c['assets']:
        if not options_complete(asset):
            raise SystemExit(f'options incomplete for {asset}: fetch or mark every day first')
    flows, counts = _flows(c), {}
    for asset in c['assets']:
        bars = _bars(asset)
        dvol = pd.read_parquet(ARTIFACTS / 'market' / f'dvol_{asset}.parquet')['dvol']
        for sched in c['schedules']:
            df = decisions.build(sched, bars, dvol, flows, trades_loader(asset), c)
            p = ARTIFACTS / 'decisions' / f'{asset}_{sched}.parquet'
            p.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(p)
            counts[f'{asset}_{sched}'] = {'rows': len(df), 'by_year': df.index.year.value_counts().sort_index().to_dict()}
    _write_json(ARTIFACTS / 'decisions' / 'counts.json', counts)
    print(json.dumps(counts, default=str))


def _tables(c):
    return {f'{a}_{s}': pd.read_parquet(ARTIFACTS / 'decisions' / f'{a}_{s}.parquet') for a in c['assets'] for s in c['schedules']}


def stage_forecast(args):
    c = config.load()
    allres = {}
    (ARTIFACTS / 'forecast').mkdir(parents=True, exist_ok=True)
    for key, df in _tables(c).items():
        preds, res = forecast.run(df, c)
        preds.to_parquet(ARTIFACTS / 'forecast' / f'{key}_preds.parquet')
        allres[key] = res
    _write_json(ARTIFACTS / 'forecast' / 'results.json', allres)


def stage_backtest(args):
    c = config.load()
    out = {}
    for key, df in _tables(c).items():
        preds = pd.read_parquet(ARTIFACTS / 'forecast' / f'{key}_preds.parquet')
        cols = [f'{f}:{v}' for f in c['families'] for v in c['straddle']['variants']]
        out[key] = straddle.backtest(df, preds[cols], c)
    _write_json(ARTIFACTS / 'backtest' / 'results.json', out)


def stage_events(args):
    c = config.load()
    trans = pd.read_parquet(B4 / 'features' / 'hourly.parquet')
    raw = pd.read_parquet(B4 / 'features' / 'hourly_raw.parquet')
    groups = {'2019-24': list(range(2019, 2025)), '2025-26': [2025, 2026]}
    out = {}
    for asset in c['assets']:
        bars = _bars(asset)
        S = events.surprises(bars, c)
        _, R = events.vol_targets(bars, c['events']['kmax'])
        iv = events.iv_series(trades_loader(asset), config.days(c), c)
        sets = {'inflow': events.flow_events(raw, trans, 'inflow', c), 'outflow': events.flow_events(raw, trans, 'outflow', c)}
        sets['placebo'] = events.placebo_events(bars, len(sets['inflow']), c)
        out[asset] = {}
        for name, ev in sets.items():
            ev = pd.DatetimeIndex(ev)
            out[asset][name] = {g: events.responses([e for e in ev if e.year in yrs], S, R, iv, c['events']['kmax'], c['gate'])
                                for g, yrs in groups.items()}
    _write_json(ARTIFACTS / 'events' / 'results.json', out)


def _fmt(x, d=4):
    return '—' if x is None or x != x else f'{x:+.{d}f}'


def stage_report(args):
    c = config.load()
    lines = ['# B5 tables (generated; interpretation in RESULTS.md)', '', '## Q1 forecast comparison', '',
             '| table | family | comparison | group | n | mean diff | 95 % CI | years better |', '|---|---|---|---|---|---|---|---|']
    for key, res in json.loads((ARTIFACTS / 'forecast' / 'results.json').read_text()).items():
        for r in res:
            lines.append(f"| {key} | {r['family']} | {r['set']} vs {r['comparator']} | {r['group']} | {r['n']} | "
                         f"{_fmt(r['mean_diff'], 5)} | [{_fmt(r['lo'], 5)}, {_fmt(r['hi'], 5)}] | {r['wins']}/{len(r['years'])} |")
    lines += ['', '## Q2 straddle backtest (USD per coin)', '',
              '| table | rule | family | variant | θ | group | trades | mean/trade | 95 % CI | total | hit | Sharpe | max DD | long mean (n) | short mean (n) |',
              '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for key, res in json.loads((ARTIFACTS / 'backtest' / 'results.json').read_text()).items():
        for r in res:
            for g, m in r['groups'].items():
                lines.append(f"| {key} | {r['rule']} | {r['family'] or '—'} | {r['variant'] or '—'} | {r['theta'] if r['theta'] is not None else '—'} | {g} | "
                             f"{m['trades']} | {_fmt(m['mean_trade'], 2)} | [{_fmt(m['lo'], 2)}, {_fmt(m['hi'], 2)}] | {_fmt(m['total'], 0)} | "
                             f"{_fmt(m['hit'], 2)} | {_fmt(m['sharpe'], 2)} | {_fmt(m['maxdd'], 0)} | {_fmt(m['long_mean'], 2)} ({m['long_n']}) | "
                             f"{_fmt(m['short_mean'], 2)} ({m['short_n']}) |")
    ev_path = ARTIFACTS / 'events' / 'results.json'
    if ev_path.exists():
        lines += ['', '## Q4 event study (k = 1, 3, 6, 12 h)', '',
                  '| asset | events | group | k | n | post vol surprise | pre vol surprise | Δ implied vol | signed return |', '|---|---|---|---|---|---|---|---|---|']
        for asset, sets in json.loads(ev_path.read_text()).items():
            for name, groups in sets.items():
                for g, rows in groups.items():
                    for r in rows:
                        if r['k'] in (1, 3, 6, 12):
                            cell = lambda s: f"{_fmt(s['mean'], 3)} [{_fmt(s['lo'], 3)}, {_fmt(s['hi'], 3)}]"
                            lines.append(f"| {asset} | {name} | {g} | {r['k']} | {r['n']} | {cell(r['post_vol'])} | {cell(r['pre_vol'])} | "
                                         f"{cell(r['d_iv'])} | {cell(r['ret'])} |")
    (STUDY / 'TABLES.md').write_text('\n'.join(lines) + '\n')
    print(f'{len(lines)} lines')


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b5')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('fetch-options')
    a.add_argument('--asset', required=True, choices=['ETH', 'BTC'])
    a.set_defaults(fn=stage_fetch_options)
    for name, fn in (('fetch-dvol', stage_fetch_dvol), ('fetch-bars', stage_fetch_bars), ('decisions', stage_decisions),
                     ('forecast', stage_forecast), ('backtest', stage_backtest), ('events', stage_events), ('report', stage_report)):
        sub.add_parser(name).set_defaults(fn=fn)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == '__main__':
    main()
