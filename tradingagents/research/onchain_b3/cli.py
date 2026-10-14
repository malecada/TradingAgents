"""B3 stage runner. Week builds run one week per process (shell loop), write the summary last,
and record failures; later stages refuse to start until all 510 weeks are built or marked."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np

from ..onchain_b import config as b_config
from ..onchain_b import weekly as W
from ..onchain_b.matching.agreement import MatchConfig
from ..onchain_b.runlog import Log
from ..onchain_b.weekly import admitted_events
from ..onchain_b2 import dataset as DS2
from ..onchain_b2 import holdout as H2
from ..onchain_b2 import labels, market, motiffeat, periods, s3source
from ..onchain_b2 import screen as SC2
from . import config, dataset3, history, screen3, weekbuild3

ARTIFACTS = config.ARTIFACTS
STUDY = config.STUDY
B2 = config.B2_ARTIFACTS


def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))
    os.replace(tmp, path)


def _torch():
    import torch
    torch.set_num_threads(2)


def _peak_rss_mb():
    try:
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmHWM:'):
                return round(int(line.split()[1]) / 1024, 1)
    except OSError:
        pass
    return None


def week_status(week):
    wdir = ARTIFACTS / 'weeks'
    if (wdir / f'{week}.json').exists():
        return None
    for kind in ('unavailable', 'failed'):
        p = wdir / f'{week}.{kind}.json'
        if p.exists():
            doc = json.loads(p.read_text())
            return f"{kind}: {doc.get('day') or doc.get('error', '?')}"
    return 'not_built'


def capture_complete():
    return all(week_status(w) != 'not_built' for w in periods.all_weeks())


def _require_capture():
    if not capture_complete():
        raise SystemExit('capture incomplete: build or mark all 510 weeks first')


def build_one3(week, scratch):
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
        del t
        events.append(ev)
        counters.append(c)
        receipts.append(r)
    ex = labels.exchange_array(B2 / 'labels' / 'labels.json')
    ex_bytes = np.array(ex.to_pylist(), dtype='S42')
    summary, graph, keys = weekbuild3.build_week3(week, events, counters, ex, ex_bytes, cfg,
                                                  periods.all_weeks().index(week))
    del events
    summary['receipts'] = receipts
    gdir = ARTIFACTS / 'graphs' / week
    if gdir.exists():
        shutil.rmtree(gdir)
    W.save(graph, gdir)
    kdir = ARTIFACTS / 'keys'
    kdir.mkdir(parents=True, exist_ok=True)
    tmpk = kdir / f'.{week}.tmp.npy'
    np.save(tmpk, keys)
    os.replace(tmpk, kdir / f'{week}.npy')
    _write_json(out, summary)
    for stale in ('unavailable', 'failed'):
        (ARTIFACTS / 'weeks' / f'{week}.{stale}.json').unlink(missing_ok=True)
    return {'week': week, 'status': 'done', 'rows': sum(r['rows'] for r in receipts)}


def stage_weeks(args):
    log = Log(ARTIFACTS / 'logs' / 'weeks.jsonl')
    weeks = [w for w in periods.all_weeks() if (args.start or '0') <= w <= (args.end or '9')]
    (ARTIFACTS / 'scratch').mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ARTIFACTS / 'scratch') as scratch:
        for w in weeks:
            if (ARTIFACTS / 'weeks' / f'{w}.json').exists():
                continue
            t = time.time()
            try:
                res = build_one3(w, scratch)
            except Exception as e:
                _write_json(ARTIFACTS / 'weeks' / f'{w}.failed.json', {'week': w, 'error': repr(e), 'traceback': traceback.format_exc()})
                res = {'week': w, 'status': 'failed', 'error': repr(e)}
            log.event(event='week', seconds=round(time.time() - t, 1), peak_rss_mb=_peak_rss_mb(), **res)


def stage_history(args):
    _require_capture()
    c = config.load()['history']
    weeks = periods.all_weeks()

    def load(w):
        p = ARTIFACTS / 'keys' / f'{w}.npy'
        return np.load(p) if week_status(w) is None and p.exists() else None

    out = history.history_pass(weeks, load, c['bloom_bits_log2'], c['bloom_hashes'])
    built = sum(1 for w in weeks if week_status(w) is None)
    computed = sum(1 for v in out.values() if v is not None)
    if computed != built:
        raise SystemExit(f'history covers {computed} weeks but {built} are built')
    _write_json(ARTIFACTS / 'history.json', out)
    if args.delete_keys:
        shutil.rmtree(ARTIFACTS / 'keys')
    print(json.dumps({'weeks': computed, 'keys_deleted': bool(args.delete_keys)}))


def stage_dictionary(args):
    _require_capture()
    _torch()
    from ..onchain_b import dictionary as D
    c, cfg = config.load()['dictionary'], config.load()
    out = ARTIFACTS / 'dictionary'
    if (out / 'dictionary.json').exists():
        return
    weeks = {w: W.load(ARTIFACTS / 'graphs' / w) for w in periods.dictionary_weeks() if week_status(w) is None}
    d = D.build(weeks, MatchConfig.from_json(b_config.load('matching')), c['sample_count'], c['size'], cfg['n_max'], c['seed'])
    D.save(d, out)
    print(json.dumps({'weeks': len(weeks), 'motif_sizes': [int(m.x.shape[0]) for m in d.motifs]}))


def stage_mcm(args):
    _require_capture()
    _torch()
    from ..onchain_b import dictionary as D
    from ..onchain_b import mcm
    i, n = map(int, args.shard.split('/'))
    log = Log(ARTIFACTS / 'logs' / f'mcm-{i}of{n}.jsonl')
    d = D.load(ARTIFACTS / 'dictionary')
    cfg = MatchConfig.from_json(b_config.load('matching'))
    out = ARTIFACTS / 'mcm'
    out.mkdir(parents=True, exist_ok=True)
    for w in [w for w in periods.all_weeks() if week_status(w) is None][i::n]:
        target = out / f'{w}.npy'
        if target.exists():
            continue
        t = time.time()
        F = mcm.compute_week(W.load(ARTIFACTS / 'graphs' / w), d, cfg, config.load()['n_max'])
        tmp = out / f'.{w}.{i}.tmp.npy'
        np.save(tmp, F)
        os.replace(tmp, target)
        log.event(event='week', week=w, seconds=round(time.time() - t, 1), cells=int(F.size))


def stage_features(args):
    _require_capture()
    import pyarrow as pa
    import pyarrow.parquet as pq
    hist = json.loads((ARTIFACTS / 'history.json').read_text())
    exchanges = set(labels.load(B2 / 'labels' / 'labels.json'))
    rows, missing = {}, {}
    for w in periods.all_weeks():
        why = week_status(w)
        if why is None and not (ARTIFACTS / 'mcm' / f'{w}.npy').exists():
            why = 'no_mcm'
        if why is None and hist.get(w) is None:
            why = 'no_history'
        if why:
            missing[w] = why
            continue
        s = json.loads((ARTIFACTS / 'weeks' / f'{w}.json').read_text())
        mf = motiffeat.motif_features(np.load(ARTIFACTS / 'mcm' / f'{w}.npy'), W.load(ARTIFACTS / 'graphs' / w),
                                      exchanges, set(s['whales']))
        f5 = {'f5_' + k[3:]: v for k, v in mf.items() if k.startswith('f2_')}
        rows[w] = {**s['f1'], **s['f3a'], **s['f4'], **hist[w], **f5}
    raw = DS2.raw_table(rows)
    (ARTIFACTS / 'features').mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(raw, preserve_index=True), ARTIFACTS / 'features' / 'weekly_raw.parquet')
    _write_json(ARTIFACTS / 'features' / 'missing.json', missing)
    print(json.dumps({'weeks': len(rows), 'missing': len(missing), 'columns': raw.shape[1]}))


def _samples(trans, prices, volumes, window):
    weekly, ex_w = dataset3.weekly_samples3(trans, prices, volumes, window)
    daily, ex_d = DS2.daily_samples(trans, prices, volumes, window)
    return {'weekly': weekly, 'daily': daily}, {'weekly': ex_w, 'daily': ex_d}


def _transformed():
    import pyarrow.parquet as pq
    raw = pq.read_table(ARTIFACTS / 'features' / 'weekly_raw.parquet').to_pandas()
    t = config.load()['transforms']
    return dataset3.transform3(raw, t['z_window'], t['z_min'], t['z_clip'])


def stage_screen(args):
    if (STUDY / 'selection.json').exists():
        raise SystemExit('selection.json exists: the B3 screen has already run')
    cfg = config.load()
    prices, volumes = market.load_dev(B2 / 'market' / 'dev.json', periods.DEV_END)
    samples, excluded = _samples(_transformed(), prices, volumes, 'dev')
    results = screen3.run_screen3(samples, cfg)
    selection = screen3.select3(results, cfg)
    _write_json(ARTIFACTS / 'screen' / 'screen.json', {'results': results, 'excluded': excluded,
                                                     'n': {k: len(v) for k, v in samples.items()}})
    head = (f"# B3 screen — development 2017-10 → 2024 (walk-forward 2019–2024)\n\n"
            f"Samples: weekly {len(samples['weekly'])} (excluded {len(excluded['weekly'])}), "
            f"daily {len(samples['daily'])} (excluded {len(excluded['daily'])}).\n\n")
    (STUDY / 'SCREEN.md').write_text(head + SC2.report(results, selection) + '\n')
    _write_json(STUDY / 'selection.json', {'registered_from': 'screen.json', 'selected': selection})
    print(SC2.report(results, selection))


def stage_holdout(args):
    lock = ARTIFACTS / 'screen' / 'holdout.lock.json'
    if lock.exists():
        raise SystemExit(f'holdout already opened ({lock}); it is one-shot')
    cfg = config.load()
    selection = H2.committed_selection(STUDY / 'selection.json', config.ROOT)
    if not selection['selected']:
        print('screen negative: holdout not opened')
        return
    identity = H2.selection_identity(STUDY / 'selection.json', config.ROOT)
    _write_json(lock, {'opened_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), **identity})
    trans = _transformed()
    p_dev, v_dev = market.load_dev(B2 / 'market' / 'dev.json', periods.DEV_END)
    p_all, v_all = market.load_all(B2 / 'market' / 'dev.json', B2 / 'sealed' / 'market_sealed.json')
    dev, _ = _samples(trans, p_dev, v_dev, 'dev')
    hold, excluded = _samples(trans, p_all, v_all, 'holdout')
    res = screen3.evaluate3(dev, hold, selection, cfg)
    _write_json(ARTIFACTS / 'screen' / 'holdout.json', {'results': res, 'excluded': excluded, **identity})
    lines = ['# B3 holdout — sealed 2025-01-06 → 2026-10-05', '',
             f"Opened once from selection.json blob {identity['blob']} at commit {identity['head']}.", '',
             '| target | family | comparison | n | mean loss diff | p (one-sided) | p Holm | pass |', '|---|---|---|---|---|---|---|---|']
    lines += [f"| {r['target']} | {r['family']} | {r['set']} vs {r['comparator']} | {r['n']} | {r['mean_diff']:+.5f} | "
              f"{r['p']:.4f} | {r['p_holm']:.4f} | {'PASS' if r['passed'] else '—'} |" for r in res]
    (STUDY / 'HOLDOUT.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b3')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('weeks')
    a.add_argument('--start')
    a.add_argument('--end')
    a.set_defaults(fn=stage_weeks)
    a = sub.add_parser('history')
    a.add_argument('--delete-keys', action='store_true')
    a.set_defaults(fn=stage_history)
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