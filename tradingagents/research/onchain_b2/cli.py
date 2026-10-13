"""B2 stage runner. Each stage is idempotent at week / run granularity and logs JSON lines."""
from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import shutil
import tempfile
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

import numpy as np

from ..onchain_b import config as b_config
from ..onchain_b import weekly as W
from ..onchain_b.matching.agreement import MatchConfig
from ..onchain_b.runlog import Log
from ..onchain_b.weekly import admitted_events
from . import config, dataset, holdout, labels, market, motiffeat, periods, s3source, screen, weekbuild

# torch-dependent modules (onchain_b.dictionary, onchain_b.mcm) are imported inside the stages
# that need them, so week-build workers never carry torch.
ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY


def _torch():
    import torch
    torch.set_num_threads(2)
    return torch


def _peak_rss_mb():
    try:
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmHWM:'):
                return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        pass
    return None


def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))
    os.replace(tmp, path)


def build_one(week, scratch):
    cfg = config.load()
    out = ARTIFACTS / 'weeks' / f'{week}.json'
    if out.exists():
        return {'week': week, 'status': 'skip'}
    events, counters, receipts = [], [], []
    for day in periods.week_days(week):
        try:
            t, r = s3source.read_day(day, scratch=scratch)
        except s3source.DayUnavailable as e:
            _write_json(ARTIFACTS / 'weeks' / f'{week}.unavailable.json', {'week': week, 'day': e.day, 'errors': e.errors})
            return {'week': week, 'status': 'unavailable', 'day': e.day}
        ev, c = admitted_events(t)
        del t                          # keep only the three admitted columns per day
        events.append(ev)
        counters.append(c)
        receipts.append(r)
    exchanges = labels.exchange_array(ARTIFACTS / 'labels' / 'labels.json')
    summary, graph = weekbuild.build_week_from_events(week, events, counters, exchanges, cfg)
    del events
    summary['receipts'] = receipts
    gdir = ARTIFACTS / 'graphs' / week
    if gdir.exists():
        shutil.rmtree(gdir)            # a graph without its summary marker is from an interrupted run
    W.save(graph, gdir)
    _write_json(out, summary)          # summary last: it is the completion marker
    for stale in ('unavailable', 'failed'):
        (ARTIFACTS / 'weeks' / f'{week}.{stale}.json').unlink(missing_ok=True)
    return {'week': week, 'status': 'done', 'rows': sum(r['rows'] for r in receipts)}


def week_status(week):
    """None when the week has both its summary and MCM features, else the reason it is missing."""
    wdir = ARTIFACTS / 'weeks'
    if (wdir / f'{week}.json').exists():
        return None if (ARTIFACTS / 'mcm' / f'{week}.npy').exists() else 'no_mcm'
    if (wdir / f'{week}.unavailable.json').exists():
        return 'unavailable: ' + json.loads((wdir / f'{week}.unavailable.json').read_text()).get('day', '?')
    if (wdir / f'{week}.failed.json').exists():
        return 'failed: ' + json.loads((wdir / f'{week}.failed.json').read_text()).get('error', '?')
    return 'not_built'


def _build_job(args):
    week, scratch = args
    t = time.time()
    try:
        res = build_one(week, scratch)
    except Exception as e:             # one bad week must not end the stage; its reason is recorded
        _write_json(ARTIFACTS / 'weeks' / f'{week}.failed.json',
                    {'week': week, 'error': repr(e), 'traceback': traceback.format_exc()})
        res = {'week': week, 'status': 'failed', 'error': repr(e)}
    res['seconds'] = round(time.time() - t, 1)
    res['peak_rss_mb'] = _peak_rss_mb()
    return res


def stage_weeks(args):
    log = Log(ARTIFACTS / 'logs' / 'weeks.jsonl')
    weeks = [w for w in periods.all_weeks() if (args.start or '0') <= w <= (args.end or '9')]
    todo = [w for w in weeks if not (ARTIFACTS / 'weeks' / f'{w}.json').exists()]
    log.event(event='start', weeks=len(weeks), todo=len(todo))
    (ARTIFACTS / 'scratch').mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ARTIFACTS / 'scratch') as scratch:
        jobs = [(w, scratch) for w in todo]
        if args.workers == 1:
            results = map(_build_job, jobs)
            for r in results:
                log.event(event='week', **r)
        else:
            ctx = multiprocessing.get_context('forkserver')
            try:
                with ProcessPoolExecutor(args.workers, mp_context=ctx, max_tasks_per_child=1) as ex:
                    for r in ex.map(_build_job, jobs):
                        log.event(event='week', **r)
            except BrokenProcessPool as e:
                log.event(event='pool_broken', error=repr(e))
                raise SystemExit('week build pool broke (a worker died); completed weeks are kept — rerun to resume')


def stage_labels(args):
    print(json.dumps(labels.fetch_and_store(market.http_get, ARTIFACTS / 'labels'), indent=1))


def stage_market(args):
    from datetime import date
    m = config.load()['market']
    prices, p_raw = market.fetch_coinmetrics(market.http_get, date.fromisoformat(m['price_start']), date.fromisoformat(m['end']))
    vols, v_raw = market.fetch_binance(market.http_get, date.fromisoformat(m['volume_start']), date.fromisoformat(m['end']))
    print(json.dumps(market.store(prices, vols, {'coinmetrics': p_raw, 'binance': v_raw}, ARTIFACTS, periods.DEV_END), indent=1))


def _done_weeks():
    return [w for w in periods.all_weeks() if (ARTIFACTS / 'weeks' / f'{w}.json').exists()]


def stage_dictionary(args):
    _torch()
    from ..onchain_b import dictionary as D
    c = config.load()['dictionary']
    log = Log(ARTIFACTS / 'logs' / 'dictionary.jsonl')
    out = ARTIFACTS / 'dictionary'
    if (out / 'dictionary.json').exists():
        log.event(event='skip')
        return
    done = set(_done_weeks())
    weeks = {w: W.load(ARTIFACTS / 'graphs' / w) for w in periods.dictionary_weeks() if w in done}
    t = time.time()
    d = D.build(weeks, MatchConfig.from_json(b_config.load('matching')), c['sample_count'], c['size'],
                config.load()['n_max'], c['seed'])
    D.save(d, out)
    log.event(event='done', weeks=len(weeks), seconds=round(time.time() - t, 1))


def stage_mcm(args):
    _torch()
    from ..onchain_b import dictionary as D
    from ..onchain_b import mcm
    i, n = map(int, args.shard.split('/'))
    log = Log(ARTIFACTS / 'logs' / f'mcm-{i}of{n}.jsonl')
    d = D.load(ARTIFACTS / 'dictionary')
    cfg = MatchConfig.from_json(b_config.load('matching'))
    out = ARTIFACTS / 'mcm'
    out.mkdir(parents=True, exist_ok=True)
    for w in _done_weeks()[i::n]:
        target = out / f'{w}.npy'
        if target.exists():
            continue
        t = time.time()
        F = mcm.compute_week(W.load(ARTIFACTS / 'graphs' / w), d, cfg, config.load()['n_max'])
        tmp = out / f'.{w}.tmp.npy'
        np.save(tmp, F)
        os.replace(tmp, target)
        log.event(event='week', week=w, seconds=round(time.time() - t, 1), cells=int(F.size))


def stage_features(args):
    import pyarrow as pa
    import pyarrow.parquet as pq
    exchanges = set(labels.load(ARTIFACTS / 'labels' / 'labels.json'))
    rows, missing = {}, {}
    for w in periods.all_weeks():
        s_path, m_path = ARTIFACTS / 'weeks' / f'{w}.json', ARTIFACTS / 'mcm' / f'{w}.npy'
        why = week_status(w)
        if why:
            missing[w] = why
            continue
        s = json.loads(s_path.read_text())
        mf = motiffeat.motif_features(np.load(m_path), W.load(ARTIFACTS / 'graphs' / w), exchanges, set(s['whales']))
        rows[w] = {**s['f1'], **s['f3a'], **mf}
    raw = dataset.raw_table(rows)
    (ARTIFACTS / 'features').mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(raw, preserve_index=True), ARTIFACTS / 'features' / 'weekly_raw.parquet')
    _write_json(ARTIFACTS / 'features' / 'missing.json', missing)
    print(json.dumps({'weeks': len(rows), 'missing': len(missing), 'columns': raw.shape[1]}))


def _transformed():
    import pyarrow.parquet as pq
    raw = pq.read_table(ARTIFACTS / 'features' / 'weekly_raw.parquet').to_pandas()
    t = config.load()['transforms']
    return dataset.transform(raw, t['z_window'], t['z_min'], t['z_clip'])


def _samples(trans, prices, volumes, window):
    weekly, ex_w = dataset.weekly_samples(trans, prices, volumes, window)
    daily, ex_d = dataset.daily_samples(trans, prices, volumes, window)
    return {'weekly': weekly, 'daily': daily}, {'weekly': ex_w, 'daily': ex_d}


def stage_screen(args):
    if (STUDY / 'selection.json').exists():
        raise SystemExit('selection.json exists: the screen has already run; a new screen needs a new registration')
    cfg = config.load()
    prices, volumes = market.load_dev(ARTIFACTS / 'market' / 'dev.json', periods.DEV_END)
    samples, excluded = _samples(_transformed(), prices, volumes, 'dev')
    results = screen.run_screen(samples, cfg)
    selection = screen.select(results, cfg)
    _write_json(ARTIFACTS / 'screen' / 'screen.json', {'results': results, 'excluded': excluded,
                                                     'n': {k: len(v) for k, v in samples.items()}})
    head = (f"# B2 screen — development 2017-10 → 2024 (walk-forward 2019–2024)\n\n"
            f"Samples: weekly {len(samples['weekly'])} (excluded {len(excluded['weekly'])}), "
            f"daily {len(samples['daily'])} (excluded {len(excluded['daily'])}).\n\n")
    (STUDY / 'SCREEN.md').write_text(head + screen.report(results, selection) + '\n')
    _write_json(STUDY / 'selection.json', {'registered_from': 'screen.json', 'selected': selection})
    print(screen.report(results, selection))


def stage_holdout(args):
    lock = ARTIFACTS / 'screen' / 'holdout.lock.json'
    if lock.exists():
        raise SystemExit(f'holdout already opened ({lock}); it is one-shot')
    cfg = config.load()
    selection = holdout.committed_selection(STUDY / 'selection.json', config.ROOT)
    if not selection['selected']:
        print('screen negative: holdout not opened')
        return
    identity = holdout.selection_identity(STUDY / 'selection.json', config.ROOT)
    _write_json(lock, {'opened_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), **identity})
    trans = _transformed()
    p_dev, v_dev = market.load_dev(ARTIFACTS / 'market' / 'dev.json', periods.DEV_END)
    p_all, v_all = market.load_all(ARTIFACTS / 'market' / 'dev.json', ARTIFACTS / 'sealed' / 'market_sealed.json')
    dev, _ = _samples(trans, p_dev, v_dev, 'dev')
    hold, excluded = _samples(trans, p_all, v_all, 'holdout')
    res = holdout.evaluate(dev, hold, selection, cfg)
    _write_json(ARTIFACTS / 'screen' / 'holdout.json', {'results': res, 'excluded': excluded, **identity})
    lines = ['# B2 holdout — sealed 2025-01-06 → 2026-10-05', '',
             f"Opened once from selection.json blob {identity['blob']} at commit {identity['head']}.", '',
             '| target | family | comparison | n | mean loss diff | p (one-sided) | p Holm | pass |', '|---|---|---|---|---|---|---|---|']
    lines += [f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n']} | {r['mean_diff']:+.5f} | "
              f"{r['p']:.4f} | {r['p_holm']:.4f} | {'PASS' if r['passed'] else '—'} |" for r in res]
    (STUDY / 'HOLDOUT.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b2')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('labels').set_defaults(fn=stage_labels)
    sub.add_parser('market').set_defaults(fn=stage_market)
    a = sub.add_parser('weeks')
    a.add_argument('--start')
    a.add_argument('--end')
    a.add_argument('--workers', type=int, default=2)
    a.set_defaults(fn=stage_weeks)
    sub.add_parser('dictionary').set_defaults(fn=stage_dictionary)
    a = sub.add_parser('mcm')
    a.add_argument('--shard', default='0/1')
    a.set_defaults(fn=stage_mcm)
    sub.add_parser('features').set_defaults(fn=stage_features)
    sub.add_parser('screen').set_defaults(fn=stage_screen)
    sub.add_parser('holdout').set_defaults(fn=stage_holdout)
    args = p.parse_args(argv)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    args.fn(args)


if __name__ == '__main__':
    main()