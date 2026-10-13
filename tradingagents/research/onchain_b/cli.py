"""Stage runner. Every stage is idempotent at week / seed granularity and logs JSON lines.

Stages: build-graphs, calibrate, dictionary, mcm (data), fit, report (training/evaluation).
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from pathlib import Path

import numpy as np

from . import calendar as cal
from . import config
from . import dictionary as D
from . import mcm
from . import sources
from . import weekly as W
from .matching.agreement import MatchConfig
from .runlog import Log

ARTIFACTS = config.ARTIFACTS
CALIBRATION_WEEKS = ['2022-03-07', '2022-09-05', '2023-03-06', '2023-09-04']
CALIBRATION_K = [5000, 10000, 20000, 34000, 50000]
TARGET_DENSITY = 0.003


def _read_day_tables(week, scratch):
    plan = sources.load_plan()
    return [sources.read_day(sources.day_manifest(plan, day), scratch, sources.COLUMNS) for day in cal.week_days(week)]


def _week_pairs(week, scratch, log):
    tables, counters = [], []
    for table in _read_day_tables(week, scratch):
        ev, c = W.admitted_events(table)
        tables.append(ev)
        counters.append(c)
    pairs = W.aggregate_pairs(tables)
    log.event(event='week_aggregated', week=week, rows=sum(c['rows'] for c in counters),
              admitted=sum(c['admitted'] for c in counters))
    return pairs, counters


def _k():
    k = config.load('graph')['paper_scale']['K']
    if k is None:
        raise SystemExit('graph.json paper_scale.K is not frozen; run calibrate and commit CALIBRATION.md first')
    return int(k)


def build_graphs(args):
    log = Log(ARTIFACTS / 'logs' / 'build-graphs.jsonl')
    k = args.k or _k()
    weeks = args.weeks or cal.weeks()
    with tempfile.TemporaryDirectory(dir=ARTIFACTS) as scratch:
        for week in weeks:
            out = ARTIFACTS / 'graphs' / week
            if (out / 'summary.json').exists():
                log.event(event='week_skip', week=week)
                continue
            t = time.time()
            pairs, counters = _week_pairs(week, Path(scratch), log)
            g = W.top_k_subgraph(pairs, k, week)
            g.summary['day_counters'] = counters
            W.save(g, out)
            log.event(event='week_done', week=week, seconds=round(time.time() - t, 1),
                      **{kk: v for kk, v in g.summary.items() if kk != 'day_counters'})


def calibrate(args):
    """Label-free: density of top-K induced subgraphs on four training weeks vs the paper's 0.003."""
    log = Log(ARTIFACTS / 'logs' / 'calibrate.jsonl')
    rows = []
    with tempfile.TemporaryDirectory(dir=ARTIFACTS) as scratch:
        for week in CALIBRATION_WEEKS:
            pairs, _ = _week_pairs(week, Path(scratch), log)
            full = W.full_summary(pairs)
            for k in CALIBRATION_K:
                g = W.top_k_subgraph(pairs, k, week)
                rows.append({'week': week, 'K': k, 'nodes': g.n, 'edges': g.e, 'density': g.summary['density'], **full})
                log.event(event='calibration_point', **rows[-1])
            n = full['full_nodes']
            # random-50k alternative for the record: expected induced edges = E * (50000/n)^2
            rows.append({'week': week, 'K': 'random50000_expected',
                         'edges_expected': full['full_edges'] * (min(50000, n) / n) ** 2, **full})
    summary = {}
    for k in CALIBRATION_K:
        dens = [r['density'] for r in rows if r.get('K') == k]
        summary[k] = {'mean_density': float(np.mean(dens)),
                      'log_gap': float(abs(np.log(np.mean(dens)) - np.log(TARGET_DENSITY)))}
    chosen = min(summary, key=lambda kk: summary[kk]['log_gap'])
    out = ARTIFACTS / 'calibration'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'density.json').write_text(json.dumps({'rows': rows, 'summary': summary, 'chosen_K': chosen,
                                                  'target_density': TARGET_DENSITY}, indent=1))
    print(json.dumps({'summary': summary, 'chosen_K': chosen}, indent=1))


def _training_weeks():
    first_test = cal.decision_dates('test')[0]
    return [w for w in cal.weeks() if cal.week_end(w) + cal.LAG <= first_test]   # available before any test decision


def _load_weeks(weeks):
    return {w: W.load(ARTIFACTS / 'graphs' / w) for w in weeks}


def dictionary(args):
    log = Log(ARTIFACTS / 'logs' / f'dictionary-seed{args.seed}.jsonl')
    dcfg = config.load('dictionary')
    mcfg = MatchConfig.from_json(config.load('matching'))
    out = ARTIFACTS / 'dictionary' / f'seed{args.seed}'
    if (out / 'dictionary.json').exists():
        log.event(event='skip')
        return
    weeks = _load_weeks(_training_weeks())
    assert all(w < '2024' for w in weeks)
    t = time.time()
    d = D.build(weeks, mcfg, dcfg['sample_count'], dcfg['size'], dcfg['n_max'], args.seed)
    D.save(d, out)
    log.event(event='done', seconds=round(time.time() - t, 1),
              motif_sizes=[int(m.x.shape[0]) for m in d.motifs],
              motif_edges=[int(m.edge_index.shape[1]) for m in d.motifs])


def mcm_stage(args):
    log = Log(ARTIFACTS / 'logs' / f'mcm-seed{args.seed}.jsonl')
    dcfg = config.load('dictionary')
    mcfg = MatchConfig.from_json(config.load('matching'))
    d = D.load(ARTIFACTS / 'dictionary' / f'seed{args.seed}')
    out = ARTIFACTS / 'mcm' / f'seed{args.seed}'
    out.mkdir(parents=True, exist_ok=True)
    for week in (args.weeks or cal.weeks()):
        target = out / f'{week}.npy'
        if target.exists():
            log.event(event='week_skip', week=week)
            continue
        g = W.load(ARTIFACTS / 'graphs' / week)
        t = time.time()
        F = mcm.compute_week(g, d, mcfg, dcfg['n_max'], log=log)
        tmp = target.with_suffix('.tmp.npy')
        np.save(tmp, F)
        os.replace(tmp, target)
        dt = max(time.time() - t, 1e-9)
        log.event(event='week_done', week=week, seconds=round(dt, 1), cells=int(F.size), cells_per_s=round(F.size / dt, 1))


def fit_stage(args):
    from . import data as Dt
    from . import train as T
    name = args.arm + (f'-{args.diag}' if args.diag else '')
    frozen = args.epochs is None or args.epochs == config.load('training')['epochs']
    out = ARTIFACTS / ('fits' if frozen else 'fits-smoke') / args.task / name / f'seed{args.seed}'
    if (out / 'predictions.json').exists():
        print('exists', out)
        return
    store = Dt.WeekStore(ARTIFACTS / 'graphs', ARTIFACTS / 'mcm' / f'seed{args.seed}') if args.arm == 'full' else None
    print(json.dumps(T.fit(args.arm, args.task, args.seed, out, store=store, epochs=args.epochs, diag=args.diag)))


def report_stage(args):
    from . import evaluate as E
    text = E.report(ARTIFACTS / 'fits')
    path = config.STUDY / 'RESULT.md'
    path.write_text('# Branch B results — initial ETH fold (sealed 2024)\n\n'
                    'Generated by `cli report`; every fit is one-shot.\n\n' + text + '\n')
    print(text)


def main(argv=None):
    p = argparse.ArgumentParser(prog='onchain_b')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('build-graphs'); a.add_argument('--weeks', nargs='*'); a.add_argument('--k', type=int); a.set_defaults(fn=build_graphs)
    a = sub.add_parser('calibrate'); a.set_defaults(fn=calibrate)
    a = sub.add_parser('dictionary'); a.add_argument('--seed', type=int, required=True); a.set_defaults(fn=dictionary)
    a = sub.add_parser('mcm'); a.add_argument('--seed', type=int, required=True); a.add_argument('--weeks', nargs='*'); a.set_defaults(fn=mcm_stage)
    a = sub.add_parser('fit')
    a.add_argument('--arm', required=True, choices=('full', 'lstm', 'gru', 'hlstm', 'svm'))
    a.add_argument('--task', required=True, choices=('classification', 'regression'))
    a.add_argument('--seed', type=int, required=True)
    a.add_argument('--diag', choices=('constant_graph', 'label_permutation'))
    a.add_argument('--epochs', type=int)
    a.set_defaults(fn=fit_stage)
    a = sub.add_parser('report'); a.set_defaults(fn=report_stage)
    args = p.parse_args(argv)
    import torch
    torch.set_num_threads(2)      # CALIBRATION.md §2: 5k-node graphs; more threads only add overhead
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    args.fn(args)


if __name__ == '__main__':
    main()
