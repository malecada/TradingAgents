# tradingagents/research/onchain_b8/cli.py
"""B8 stage runner: universe freeze, the sequential token_transfers pass (resumable by day
file, read watchdog), the panel, pooled forecasts (resumable per target) and the tables."""
from __future__ import annotations

import argparse
import ctypes
import gc
import json
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from ..onchain_b.runlog import Log
from ..onchain_b2.s3source import DayUnavailable
from ..onchain_b4.cli import MIN_FREE_LAUNCH, READ_TIMEOUT, STALL_EXIT, _peak_rss_mb, _write_json
from ..onchain_b6 import labels6
from ..onchain_b6.labels6 import LabelState
from ..onchain_b7.forecast7 import detail_report
from . import config, forecast8, hourly8, panel8, reader8, universe8

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B6 = config.B6_ARTIFACTS
_hard_exit = os._exit


def _require_disk(min_bytes, what):
    p = ARTIFACTS
    while not p.exists():
        p = p.parent
    free = shutil.disk_usage(p).free
    if free < min_bytes:
        raise SystemExit(f'only {free / 1e9:.1f} GB disk free; {what} needs {min_bytes / 1e9:.1f} GB')


def filesystem():
    import pyarrow.fs as pafs
    return pafs.S3FileSystem(anonymous=True, region=config.load()['s3']['region'])


def stage_universe(args):
    c = config.load()
    out = STUDY / 'config' / 'universe.json'
    if out.exists():
        raise SystemExit('universe already frozen')
    tokens = universe8.build(config.TOKEN_MAP, config.KLINES, c['universe']['min_rows'], exclude=c['universe'].get('exclude', ()))
    _write_json(out, {'tokens': tokens, 'min_rows': c['universe']['min_rows'], 'exclude': list(c['universe'].get('exclude', ())),
                      'token_map': str(config.TOKEN_MAP), 'klines': str(config.KLINES)})
    print(json.dumps({'tokens': len(tokens)}))


def day_status(day):
    if (ARTIFACTS / 'days' / f'{day}.parquet').exists():
        return 'done'
    if (ARTIFACTS / 'days' / f'{day}.unavailable.json').exists():
        return 'unavailable'
    return None


def pass_complete():
    return all(day_status(d) is not None for d in config.days(config.load()))


def _state():
    doc = labels6.load(B6 / 'labels' / 'labels6.json')
    st = LabelState(doc, doc.get('issuer', {}).get('usdt_treasury', '0x5754284f345afc66a98fbb0a0afe71e0f007b949'))
    z = np.load(B6 / 'state' / 'state.npz')
    st.ex_first = z['ex_first'].copy()
    return st


def _bars_all(tokens):
    return [universe8.load_bars(config.KLINES, t['symbol']) for t in tokens]


def stage_pass(args):
    c = config.load()
    _require_disk(MIN_FREE_LAUNCH, 'pass launch')
    tokens = config.universe()
    contracts = {t['address']: (i, t['decimals']) for i, t in enumerate(tokens)}
    days = [d for d in config.days(c) if args.end is None or d <= args.end]
    hours = pd.date_range(days[0], periods=24 * len(days), freq='h')
    prices = hourly8.price_matrix(_bars_all(tokens), hours, multipliers=[t.get('multiplier', 1) for t in tokens])
    st = _state()
    log = Log(ARTIFACTS / 'logs' / 'pass.jsonl')
    fs, p = filesystem(), c['pass']
    out = ARTIFACTS / 'days'
    out.mkdir(parents=True, exist_ok=True)
    todo = [d for d in days if day_status(d) != 'done']        # unavailable days are retried on every launch

    def fetch(day):
        return reader8.read_day8(day, filesystem=fs, root=c['s3']['bucket'], contracts=contracts, retries=c['s3']['retries'])

    consecutive = 0
    pool = ThreadPoolExecutor(max_workers=max(1, p['prefetch']))
    try:
        futures = {}
        for i, day in enumerate(todo):
            for nxt in todo[i:i + p['prefetch'] + 1]:
                if nxt not in futures:
                    futures[nxt] = pool.submit(fetch, nxt)
            t = time.time()
            try:
                d = futures.pop(day).result(timeout=READ_TIMEOUT)
            except FuturesTimeout:
                log.event(event='stall', day=day, after_seconds=READ_TIMEOUT)
                pool.shutdown(wait=False, cancel_futures=True)
                _hard_exit(STALL_EXIT)
            except DayUnavailable as e:
                _write_json(out / f'{day}.unavailable.json', {'day': day, 'errors': e.errors})
                log.event(event='day', day=day, status='unavailable')
                consecutive += 1
                if consecutive >= p['max_consecutive_unavailable']:
                    raise SystemExit(f'{consecutive} consecutive unavailable days up to {day}: stopping the pass')
                continue
            consecutive = 0
            st.begin_day(config.day_ord(day))
            k = days.index(day)
            rows = hourly8.day_rows(day, d, st, prices[24 * k:24 * (k + 1)], c['big_usd'])
            tmp = out / f'.{day}.parquet.tmp'
            rows.to_parquet(tmp)
            os.replace(tmp, out / f'{day}.parquet')
            (out / f'{day}.unavailable.json').unlink(missing_ok=True)
            log.event(event='day', day=day, status='done', seconds=round(time.time() - t, 1), transfers=int(len(d.src)), peak_rss_mb=_peak_rss_mb())
            del d
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def stage_panel(args):
    if not pass_complete():
        raise SystemExit('pass incomplete: build or mark every day first')
    c = config.load()
    tokens = config.universe()
    days = config.days(c)
    hours = pd.date_range(days[0], periods=24 * len(days), freq='h')
    frames = [pd.read_parquet(ARTIFACTS / 'days' / f'{d}.parquet') for d in days if day_status(d) == 'done']
    bars = _bars_all(tokens)
    parts = []
    for i, t in enumerate(tokens):
        f = panel8.token_frame(panel8.token_series(frames, hours, i), bars[i], c)
        f['token'] = np.int16(i)
        parts.append(f)
    del frames, bars
    panel = pd.concat(parts).sort_index(kind='stable')
    del parts
    panel = panel8.cross_section(panel, c)
    (ARTIFACTS / 'panel').mkdir(parents=True, exist_ok=True)
    panel.to_parquet(ARTIFACTS / 'panel' / 'panel.parquet')
    print(json.dumps({'rows': len(panel), 'tokens': int(panel['token'].nunique()), 'columns': panel.shape[1],
                      'first': str(panel.index.min()), 'last': str(panel.index.max())}))


def _release():
    """Return freed arenas to the OS so the cgroup charge follows the live data."""
    gc.collect()
    try:
        import pyarrow as pa
        pa.default_memory_pool().release_unused()
    except Exception:                                         # the pool may not support it
        pass
    try:
        ctypes.CDLL('libc.so.6').malloc_trim(0)
    except (OSError, AttributeError):
        pass


def stage_forecast(args):
    c = config.load()
    only = set(args.only.split(',')) if args.only else None
    out = ARTIFACTS / 'forecast'
    out.mkdir(parents=True, exist_ok=True)
    log = Log(ARTIFACTS / 'logs' / 'forecast.jsonl')
    path = ARTIFACTS / 'panel' / 'panel.parquet'
    n = forecast8.support(path, c)
    _release()
    for target in c['targets']:
        unit = out / f'{target}.json'
        if (only is not None and target not in only) or unit.exists():
            continue
        t0 = time.time()
        b = forecast8.load_bundle(path, target, c)             # arrays only: no pandas frame of the panel
        _release()
        log.event(event='samples', target=target, rows=int(len(b['y'])))
        P, meta = forecast8.predict_bundle(b, target, c, log=log.event)
        del b
        _release()
        res = forecast8.compare(P, target, c)
        P.to_parquet(out / f'pred_{target}.parquet')
        forecast8.per_token(P, target, c).to_csv(out / f'per_token_{target}.csv', index=False)
        _write_json(unit, {'results': res, 'meta': meta, 'seconds': round(time.time() - t0, 1)})
        log.event(event='unit', target=target, seconds=round(time.time() - t0, 1), passed=sum(r['passed'] for r in res))
        del P, res, meta
        _release()
    units = [out / f'{t}.json' for t in c['targets'] if (out / f'{t}.json').exists()]
    docs = {u.stem: json.loads(u.read_text()) for u in units}
    results = [r for d in docs.values() for r in d['results']]
    pt = [out / f'per_token_{t}.csv' for t in c['targets'] if (out / f'per_token_{t}.csv').exists()]
    if pt:
        pd.concat([pd.read_csv(p) for p in pt]).to_csv(out / 'per_token.csv', index=False)
    _write_json(out / 'results.json', {'results': results, 'meta': {k: d['meta'] for k, d in docs.items()}, 'n': n,
                                       'seconds': {k: d['seconds'] for k, d in docs.items()}})
    print(json.dumps({'units': len(units), 'rows': len(results), 'passed': sum(r['passed'] for r in results)}))


def stage_report(args):
    res = json.loads((ARTIFACTS / 'forecast' / 'results.json').read_text())
    lines = ['# B8 tables (generated; interpretation in RESULTS.md)', '', '## Samples', '',
             '| target | rows | mean | per year rows / hours / tokens |', '|---|---|---|---|']
    for t, v in res['n'].items():
        per = ', '.join(f"{yr} {d['rows']} / {d['hours']} / {d['tokens']}" for yr, d in sorted(v['years'].items(), key=lambda kv: int(kv[0])))
        lines.append(f"| {t} | {v['n']} | {v['mean']:.4f} | {per} |")
    lines += ['', '## Comparisons', '', 'Differences, intervals and years are hour-weighted (per-hour means over tokens); losses and gains are row-weighted.', '',
              forecast8.report(res['results']), '', '## Model detail', '', detail_report(res['meta']),
              '', 'Per-token differences (post hoc): `research_artifacts/onchain-b8/forecast/per_token.csv`.']
    STUDY.mkdir(parents=True, exist_ok=True)
    (STUDY / 'TABLES.md').write_text('\n'.join(lines) + '\n')
    print(f'{len(lines)} lines')


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b8')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('universe').set_defaults(fn=stage_universe)
    a = sub.add_parser('pass')
    a.add_argument('--end', default=None)
    a.set_defaults(fn=stage_pass)
    sub.add_parser('panel').set_defaults(fn=stage_panel)
    f = sub.add_parser('forecast')
    f.add_argument('--only', default=None, help='comma-separated targets')
    f.set_defaults(fn=stage_forecast)
    sub.add_parser('report').set_defaults(fn=stage_report)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == '__main__':
    main()
