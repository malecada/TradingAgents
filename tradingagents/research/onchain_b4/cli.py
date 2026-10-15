# tradingagents/research/onchain_b4/cli.py
"""B4 stage runner. The chain pass is sequential (exchange state), prefetches reads in threads,
snapshots the state every N days and resumes from the last snapshot; later stages refuse to run
until every day is built or marked unavailable."""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from ..onchain_b.runlog import Log
from ..onchain_b2 import holdout as H2
from ..onchain_b2 import labels, market
from ..onchain_b2.s3source import DayUnavailable
from . import cmdaily, config, dataset4, flows, hourmarket, reader, screen4
from .entities import Entities

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B2 = config.B2_ARTIFACTS
ROOT = config.ROOT


def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))
    os.replace(tmp, path)


def _peak_rss_mb():
    try:
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmHWM:'):
                return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        pass
    return None


def filesystem():
    import pyarrow.fs as pafs
    return pafs.S3FileSystem(anonymous=True, region=config.load()['s3']['region'])


def _cutoff_hour(c):
    return c['windows']['dev_end'] + 'T23'


def stage_market(args):
    c = config.load()
    if (ARTIFACTS / 'market' / 'hourly_dev.json').exists():
        raise SystemExit('hourly market data already stored')
    b = c['binance']
    bars, pages = hourmarket.fetch(market.http_get, b['symbol'], b['start'], b['end'])
    print(json.dumps(hourmarket.store(bars, pages, ARTIFACTS, _cutoff_hour(c))))


def stage_cm(args):
    c = config.load()
    if (ARTIFACTS / 'market' / 'cm_dev.json').exists():
        raise SystemExit('Coin Metrics data already stored')
    m = c['cm']
    eth, p1 = cmdaily.fetch(market.http_get, ['eth'], m['eth'], m['start'], m['end'])
    st, p2 = cmdaily.fetch(market.http_get, m['stables'], ['SplyCur'], m['start'], m['end'])
    frame = cmdaily.to_frame({**eth, **st}, m['eth'], m['stables'])
    print(json.dumps(cmdaily.store(frame, p1 + p2, ARTIFACTS, c['windows']['dev_end'])))


def _hours_dir():
    return ARTIFACTS / 'hours'


def day_status(day):
    if (_hours_dir() / f'{day}.parquet').exists():
        return 'done'
    if (_hours_dir() / f'{day}.unavailable.json').exists():
        return 'unavailable'
    return None


def pass_complete():
    return all(day_status(d) is not None for d in config.days(config.load()))


def _new_entities(c):
    keys = reader.addr_keys(np.array(sorted(labels.load(B2 / 'labels' / 'labels.json')), object))
    e = c['entities']
    return Entities(keys, e['bloom_bits_log2'], e['bloom_hashes'], e['deposit_share'])


def stage_pass(args):
    c = config.load()
    days = [d for d in config.days(c) if args.end is None or d <= args.end]
    snap = ARTIFACTS / 'state' / 'entities.npz'
    ent = Entities.load(snap) if snap.exists() else _new_entities(c)
    todo = [d for d in days if ent.last_day is None or d > ent.last_day]
    log = Log(ARTIFACTS / 'logs' / 'pass.jsonl')
    fs, p = filesystem(), c['pass']
    hours = _hours_dir()
    hours.mkdir(parents=True, exist_ok=True)

    def fetch(day):
        return reader.read_day(day, filesystem=fs, root=c['s3']['bucket'], tokens=c['tokens'], retries=c['s3']['retries'])

    consecutive, since = 0, 0
    with ThreadPoolExecutor(max_workers=max(1, p['prefetch'])) as pool:
        futures = {}
        for i, day in enumerate(todo):
            for nxt in todo[i:i + p['prefetch'] + 1]:
                if nxt not in futures:
                    futures[nxt] = pool.submit(fetch, nxt)
            t = time.time()
            try:
                d = futures.pop(day).result()
            except DayUnavailable as e:
                _write_json(hours / f'{day}.unavailable.json', {'day': day, 'errors': e.errors})
                log.event(event='day', day=day, status='unavailable')
                ent.last_day = day
                consecutive += 1
                if consecutive >= p['max_consecutive_unavailable']:
                    ent.save(snap)
                    raise SystemExit(f'{consecutive} consecutive unavailable days up to {day}: stopping the pass')
                continue
            consecutive = 0
            rows = flows.hourly(day, d, ent.is_exchange, ent.is_labelled, c['flows'])
            tmp = hours / f'.{day}.tmp.parquet'
            rows.to_parquet(tmp)
            os.replace(tmp, hours / f'{day}.parquet')
            (hours / f'{day}.unavailable.json').unlink(missing_ok=True)
            ent.update(d.src, d.dst, d.block, day)
            log.event(event='day', day=day, status='done', seconds=round(time.time() - t, 1), transfers=int(len(d.src)),
                      candidates=int(len(ent.c_keys)), deposits=int(len(ent.deposits)), peak_rss_mb=_peak_rss_mb(), **d.rows)
            del d
            since += 1
            if since >= p['snapshot_every']:
                ent.save(snap)
                since = 0
    ent.save(snap)


def _require_pass():
    if not pass_complete():
        raise SystemExit('pass incomplete: build or mark every day first')


def stage_features(args):
    _require_pass()
    c = config.load()
    days = config.days(c)
    raw = dataset4.hourly_table(_hours_dir(), days)
    trans = dataset4.transform_hourly(raw, c['hourly'])
    out = ARTIFACTS / 'features'
    out.mkdir(parents=True, exist_ok=True)
    raw.to_parquet(out / 'hourly_raw.parquet')
    trans.to_parquet(out / 'hourly.parquet')
    prices, volumes = market.load_dev(B2 / 'market' / 'dev.json', config.windows(c)['dev_end'])
    cm = cmdaily.load_dev(ARTIFACTS / 'market' / 'cm_dev.json', c['windows']['dev_end'])
    daily = dataset4.transform_daily(dataset4.cm_values(cm, prices), c['daily'])
    daily.to_parquet(out / 'daily_dev.parquet')
    missing = [d for d in days if day_status(d) == 'unavailable']
    _write_json(out / 'missing.json', missing)
    print(json.dumps({'days': len(days), 'unavailable': len(missing), 'hourly_rows': len(trans),
                      'hourly_columns': len([x for x in trans.columns if not x.startswith('lab_')]),
                      'daily_columns': daily.shape[1]}))


def _samples(window):
    c = config.load()
    trans = pd.read_parquet(ARTIFACTS / 'features' / 'hourly.parquet')
    if window == 'dev':
        bars = hourmarket.load_dev(ARTIFACTS / 'market' / 'hourly_dev.json', _cutoff_hour(c))
        prices, volumes = market.load_dev(B2 / 'market' / 'dev.json', config.windows(c)['dev_end'])
        cm = cmdaily.load_dev(ARTIFACTS / 'market' / 'cm_dev.json', c['windows']['dev_end'])
    else:
        bars = hourmarket.load_all(ARTIFACTS / 'market' / 'hourly_dev.json', ARTIFACTS / 'sealed' / 'hourly_sealed.json')
        prices, volumes = market.load_all(B2 / 'market' / 'dev.json', B2 / 'sealed' / 'market_sealed.json')
        cm = cmdaily.load_all(ARTIFACTS / 'market' / 'cm_dev.json', ARTIFACTS / 'sealed' / 'cm_sealed.json')
    daily_trans = dataset4.transform_daily(dataset4.cm_values(cm, prices), c['daily'])
    hourly, ex_h = dataset4.hourly_samples(trans, bars, window, c)
    daily, ex_d = dataset4.daily_samples(daily_trans, prices, volumes, window, c)
    return {'hourly': hourly, 'daily': daily}, {'hourly': ex_h, 'daily': ex_d}


def stage_screen(args):
    if (STUDY / 'selection.json').exists():
        raise SystemExit('selection.json exists: the B4 screen has already run')
    _require_pass()
    cfg = config.load()
    samples, excluded = _samples('dev')
    results = screen4.run_screen4(samples, cfg)
    selection = screen4.select4(results, cfg)
    _write_json(ARTIFACTS / 'screen' / 'screen.json', {'results': results, 'excluded': excluded,
                                                     'n': {k: len(v) for k, v in samples.items()}})
    head = (f"# B4 screen — development 2017-10 → 2024 (walk-forward 2019–2024)\n\n"
            f"Samples: daily {len(samples['daily'])} (excluded {excluded['daily']}), "
            f"hourly {len(samples['hourly'])} (excluded {excluded['hourly']}).\n\n")
    report = screen4.report4(results, selection)
    (STUDY / 'SCREEN.md').write_text(head + report + '\n')
    _write_json(STUDY / 'selection.json', {'registered_from': 'screen.json', 'selected': selection})
    print(report)


def stage_holdout(args):
    lock = ARTIFACTS / 'screen' / 'holdout.lock.json'
    if lock.exists():
        raise SystemExit(f'holdout already opened ({lock}); it is one-shot')
    cfg = config.load()
    selection = H2.committed_selection(STUDY / 'selection.json', ROOT)
    if not selection['selected']:
        print('screen negative: holdout not opened')
        return
    identity = H2.selection_identity(STUDY / 'selection.json', ROOT)
    _write_json(lock, {'opened_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), **identity})
    dev, _ = _samples('dev')
    hold, excluded = _samples('holdout')
    res = screen4.evaluate4(dev, hold, selection, cfg)
    _write_json(ARTIFACTS / 'screen' / 'holdout.json', {'results': res, 'excluded': excluded, **identity})
    lines = ['# B4 holdout — sealed 2025-01-01 → 2026-10-12', '',
             f"Opened once from selection.json blob {identity['blob']} at commit {identity['head']}.", '',
             '| target | family | comparison | n | mean loss diff | p (one-sided) | p Holm | pass |',
             '|---|---|---|---|---|---|---|---|']
    lines += [f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n']} | {r['mean_diff']:+.6f} | "
              f"{r['p']:.4f} | {r['p_holm']:.4f} | {'PASS' if r['passed'] else '—'} |" for r in res]
    (STUDY / 'HOLDOUT.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b4')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('market').set_defaults(fn=stage_market)
    sub.add_parser('cm').set_defaults(fn=stage_cm)
    a = sub.add_parser('pass')
    a.add_argument('--end', default=None)
    a.set_defaults(fn=stage_pass)
    sub.add_parser('features').set_defaults(fn=stage_features)
    sub.add_parser('screen').set_defaults(fn=stage_screen)
    sub.add_parser('holdout').set_defaults(fn=stage_holdout)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == '__main__':
    main()
