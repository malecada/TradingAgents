# tradingagents/research/onchain_b6/cli.py
"""B6 stage runner: labels, minute bars, the sequential day pass, the Tron stream, feature
tables, forecast comparisons, the event study and the tables."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from pathlib import Path

import numpy as np
import pandas as pd

from ..onchain_b.runlog import Log
from ..onchain_b2 import market
from ..onchain_b2.s3source import DayUnavailable
from ..onchain_b3.history import Bloom
from ..onchain_b4 import hourmarket
from ..onchain_b4.cli import MIN_FREE_LAUNCH, MIN_FREE_SNAPSHOT, READ_TIMEOUT, STALL_EXIT, _peak_rss_mb, _write_json
from ..onchain_b5 import cli as B5CLI
from ..onchain_b5 import config as b5config
from ..onchain_b5.decisions import load_bars
from . import config, dataset6, forecast6, hourly6, labels6, minutes, reader6, tron
from .labels6 import LabelState

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B2 = config.B2_ARTIFACTS
B4 = config.B4_ARTIFACTS
B5 = config.B5_ARTIFACTS
ROOT = config.ROOT
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


def post_json(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'User-Agent': 'onchain-b6'})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code in (429, 529, 503):
            raise tron.Overloaded(e.code)
        raise


def stage_labels(args):
    c = config.load()
    out = ARTIFACTS / 'labels' / 'labels6.json'
    if out.exists():
        raise SystemExit('labels already frozen')
    doc = labels6.build(market.http_get, B2 / 'labels' / 'labels.json', c)
    labels6.save(doc, out)
    s = c['labels']['spellbook']
    txt = market.http_get(f"https://raw.githubusercontent.com/{s['repo']}/{s['branch']}/{s['tron']}").decode()
    addrs = re.findall(r"'tron'\s*,\s*'(T[1-9A-HJ-NP-Za-km-z]{33})'", txt)
    _write_json(ARTIFACTS / 'labels' / 'tron_labels.json', {'addresses': sorted(set(addrs)), 'hex': sorted({tron.b58_to_hex(a) for a in addrs}),
                                                            'commit': doc['sources']['spellbook_commit']})
    print(json.dumps({**doc['sources']['counts'], 'tron': len(set(addrs))}))


def stage_market(args):
    c = config.load()['minutes']
    (ARTIFACTS / 'market').mkdir(parents=True, exist_ok=True)
    for asset, sym in c['symbols'].items():
        s = minutes.fetch(market.http_get, sym, c['start'], c['end'])
        s.to_frame().to_parquet(ARTIFACTS / 'market' / f'minutes_{asset}.parquet')
        print(json.dumps({'asset': asset, 'minutes': len(s), 'first': str(s.index.min()), 'last': str(s.index.max())}))


def day_status(day):
    if (ARTIFACTS / 'hours' / f'{day}.parquet').exists():
        return 'done'
    if (ARTIFACTS / 'hours' / f'{day}.unavailable.json').exists():
        return 'unavailable'
    return None


def pass_complete():
    return all(day_status(d) is not None for d in config.days(config.load()))


def _load_state(c):
    # one atomic bundle: label first-seen tables, Bloom bits and last_day change together on resume
    doc = labels6.load(ARTIFACTS / 'labels' / 'labels6.json')
    st_c = c['structure']
    st = LabelState(doc, c['issuer']['usdt_treasury'])
    bloom = Bloom(st_c['bloom_bits_log2'], st_c['bloom_hashes'])
    p = ARTIFACTS / 'state' / 'state.npz'
    if not p.exists():
        return st, bloom, None
    z = np.load(p)
    st.ex_first = z['ex_first'].copy()
    for cname in labels6.CLASSES:
        st.cls_first[cname] = z[f'cls_first_{cname}'].copy()
    bloom.bits = z['bits'].copy()
    return st, bloom, str(z['last_day'][0]) or None


def _save_state(st, bloom, last_day):
    d = ARTIFACTS / 'state'
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / '.state.tmp.npz'
    np.savez(tmp, ex_first=st.ex_first, **{f'cls_first_{cname}': st.cls_first[cname] for cname in labels6.CLASSES},
             bits=bloom.bits, last_day=np.array([last_day or '']))
    os.replace(tmp, d / 'state.npz')


def stage_pass(args):
    c = config.load()
    _require_disk(MIN_FREE_LAUNCH, 'pass launch')
    days = [d for d in config.days(c) if args.end is None or d <= args.end]
    st, bloom, last = _load_state(c)
    todo = [d for d in days if last is None or d > last]
    log = Log(ARTIFACTS / 'logs' / 'pass.jsonl')
    fs, p = filesystem(), c['pass']
    hours, large = ARTIFACTS / 'hours', ARTIFACTS / 'large'
    hours.mkdir(parents=True, exist_ok=True)
    large.mkdir(parents=True, exist_ok=True)

    def fetch(day):
        return reader6.read_day6(day, filesystem=fs, root=c['s3']['bucket'], tokens=c['tokens'], retries=c['s3']['retries'])

    consecutive, since = 0, 0
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
                _require_disk(MIN_FREE_SNAPSHOT, 'snapshot')
                _save_state(st, bloom, last)
                pool.shutdown(wait=False, cancel_futures=True)
                _hard_exit(STALL_EXIT)
            except DayUnavailable as e:
                _write_json(hours / f'{day}.unavailable.json', {'day': day, 'errors': e.errors})
                log.event(event='day', day=day, status='unavailable')
                consecutive += 1
                if consecutive >= p['max_consecutive_unavailable']:
                    _require_disk(MIN_FREE_SNAPSHOT, 'snapshot')
                    _save_state(st, bloom, last)
                    raise SystemExit(f'{consecutive} consecutive unavailable days up to {day}: stopping the pass')
                continue
            consecutive = 0
            st.begin_day(config.day_ord(day))
            rows, lg = hourly6.day_rows(day, d, st, bloom, c)
            for df, path in ((rows, hours / f'{day}.parquet'), (lg, large / f'{day}.parquet')):
                tmp = path.with_name('.' + path.name + '.tmp')
                df.to_parquet(tmp)
                os.replace(tmp, path)
            (hours / f'{day}.unavailable.json').unlink(missing_ok=True)
            last = day
            log.event(event='day', day=day, status='done', seconds=round(time.time() - t, 1), transfers=int(len(d.src)),
                      large=int(len(lg)), peak_rss_mb=_peak_rss_mb(), **d.rows)
            del d
            since += 1
            if since >= p['snapshot_every']:
                _require_disk(MIN_FREE_SNAPSHOT, 'snapshot')
                _save_state(st, bloom, last)
                since = 0
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    _require_disk(MIN_FREE_SNAPSHOT, 'snapshot')
    _save_state(st, bloom, last)


def stage_tron(args):
    c = config.load()
    lab = json.loads((ARTIFACTS / 'labels' / 'tron_labels.json').read_text())['hex']
    (ARTIFACTS / 'tron').mkdir(parents=True, exist_ok=True)
    tron.run(lambda body: post_json(c['tron']['url'], body), lab, ARTIFACTS / 'tron' / 'state.json',
             ARTIFACTS / 'tron' / 'hourly.parquet', c)
    print('tron stream complete')


def tron_complete():
    p = ARTIFACTS / 'tron' / 'hourly.parquet'
    if not p.exists():
        return False
    df = pd.read_parquet(p)
    return len(df) and df.index.max() >= pd.Timestamp(config.load()['tron']['end']) - pd.Timedelta(days=2)


def _require_pass():
    if not pass_complete():
        raise SystemExit('pass incomplete: build or mark every day first')


def stage_features(args):
    _require_pass()
    c = config.load()
    days = config.days(c)
    frames = [pd.read_parquet(ARTIFACTS / 'hours' / f'{d}.parquet') for d in days if day_status(d) == 'done']
    raw = pd.concat(frames).sort_index().reindex(pd.date_range(days[0], periods=24 * len(days), freq='h'))
    if tron_complete():
        t = pd.read_parquet(ARTIFACTS / 'tron' / 'hourly.parquet').reindex(raw.index)
        raw = raw.join(t)
    trans = dataset6.transform_raw(raw, c['transforms'])
    flows = pd.read_parquet(B4 / 'features' / 'hourly.parquet')
    flows = flows[[x for x in flows.columns if x.startswith(tuple(c['blocks']['F']))]]
    feats = trans.join(flows, how='left')
    bars = hourmarket.load_all(B4 / 'market' / 'hourly_dev.json', B4 / 'sealed' / 'hourly_sealed.json')
    dvol = pd.read_parquet(B5 / 'market' / 'dvol_ETH.parquet')['dvol']
    iv = dataset6.iv_hourly(B5CLI.trades_loader('ETH'), b5config.days(b5config.load()), c['iv']['min_trades'], c['iv']['ffill_hours'],
                            {**b5config.load()['implied'], 'iv_min_ahead_h': b5config.load()['events']['iv_min_ahead_h']})
    mk = dataset6.market_hourly(bars, dvol, iv)[['mk_dvol', 'mk_dvol_chg24', 'mk_iv']]
    out = ARTIFACTS / 'features'
    out.mkdir(parents=True, exist_ok=True)
    raw.to_parquet(out / 'hourly_raw.parquet')
    feats.to_parquet(out / 'features_A.parquet')
    feats.join(mk, how='left').to_parquet(out / 'features_B.parquet')
    print(json.dumps({'hours': len(raw), 'raw_columns': raw.shape[1], 'feature_columns': feats.shape[1], 'tron': bool(tron_complete())}))


def stage_forecast(args):
    c = config.load()
    bars = hourmarket.load_all(B4 / 'market' / 'hourly_dev.json', B4 / 'sealed' / 'hourly_sealed.json')
    with_tron = tron_complete()
    sb = {tr: dataset6.samples(tr, pd.read_parquet(ARTIFACTS / 'features' / f'features_{tr}.parquet'), bars, c) for tr in ('A', 'B')}
    res = forecast6.run_all(sb, c, with_tron)
    (ARTIFACTS / 'forecast').mkdir(parents=True, exist_ok=True)
    _write_json(ARTIFACTS / 'forecast' / 'results.json', {'results': res, 'with_tron': with_tron, 'n': {k: len(v) for k, v in sb.items()}})
    print(json.dumps({'rows': len(res), 'passed': sum(r['passed'] for r in res), 'with_tron': with_tron}))


def stage_events(args):
    c = config.load()
    m = c['minutes']
    large = pd.concat([pd.read_parquet(p) for p in sorted((ARTIFACTS / 'large').glob('*.parquet'))], ignore_index=True)
    ev = minutes.select_events(large, c)
    out = {'events': int(len(ev))}
    for asset in m['symbols']:
        closes = pd.read_parquet(ARTIFACTS / 'market' / f'minutes_{asset}.parquet')['close']
        out[asset] = {}
        for (direction, tier), g in ev.groupby(['direction', 'tier']):
            key = f"{'deposit' if direction == 1 else 'withdrawal'}_tier{tier}"
            pl = minutes.placebo(g, closes, m)
            out[asset][key] = {}
            for gname, yrs in m['groups'].items():
                e = pd.DatetimeIndex(g.loc[g['minute'].dt.year.isin(yrs), 'minute'])
                p = pl[np.isin(pl.year, yrs)]
                out[asset][key][gname] = {'events': minutes.responses(e, closes, m), 'placebo': minutes.responses(p, closes, m)}
    (ARTIFACTS / 'events').mkdir(parents=True, exist_ok=True)
    _write_json(ARTIFACTS / 'events' / 'results.json', out)
    print(json.dumps({'events': out['events']}))


def _cell(s):
    return f"{s['mean']:+.4f} [{s['lo']:+.4f}, {s['hi']:+.4f}]" if s and s['mean'] == s['mean'] else '—'


def stage_report(args):
    res = json.loads((ARTIFACTS / 'forecast' / 'results.json').read_text())
    lines = ['# B6 tables (generated; interpretation in RESULTS.md)', '', f"Tron block: {'included' if res['with_tron'] else 'not run'}", '',
             '## Forecast comparisons', '', forecast6.report(res['results'])]
    ep = ARTIFACTS / 'events' / 'results.json'
    if ep.exists():
        ev = json.loads(ep.read_text())
        lines += ['', f"## Minute-level events ({ev['events']} events)", '',
                  '| asset | events | group | kind | n | vol 5 | vol 15 | vol 30 | vol 60 | ret 1 | ret 5 | ret 15 | ret 30 | ret 60 | pre ret 15 |',
                  '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
        for asset, keys in ev.items():
            if asset == 'events':
                continue
            for key, groups in keys.items():
                for g, kinds in groups.items():
                    for kind, r in kinds.items():
                        lines.append(f"| {asset} | {key} | {g} | {kind} | {r['n']} | " + ' | '.join(_cell(r.get(k)) for k in
                                     ('vol5', 'vol15', 'vol30', 'vol60', 'ret1', 'ret5', 'ret15', 'ret30', 'ret60', 'pre_ret')) + ' |')
    (STUDY / 'TABLES.md').write_text('\n'.join(lines) + '\n')
    print(f'{len(lines)} lines')


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b6')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('pass')
    a.add_argument('--end', default=None)
    a.set_defaults(fn=stage_pass)
    for name, fn in (('labels', stage_labels), ('market', stage_market), ('tron', stage_tron), ('features', stage_features),
                     ('forecast', stage_forecast), ('events', stage_events), ('report', stage_report)):
        sub.add_parser(name).set_defaults(fn=fn)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == '__main__':
    main()
