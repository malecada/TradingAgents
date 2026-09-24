"""Invented bytes and panels only; never read captured prices."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import zstandard

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'research/onchain-graph-2026-09-16/comparison'


def load(path):
    spec = importlib.util.spec_from_file_location('test_matched_'+path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runner():
    return load(BASE/'evaluation-20260924/run.py')


def test_json_preserves_unavailable_and_utc():
    value = pd.DataFrame({'day': [pd.Timestamp('2024-01-01', tz='UTC')],
                          'value': [np.nan], 'clock': [pd.NaT]})
    assert runner().json_value(value) == [dict(day='2024-01-01T00:00:00+00:00', value=None, clock=None)]


def test_stored_chain_rejects_tampering_and_extra_frames():
    raw = b'invented response'
    stored = zstandard.ZstdCompressor().compress(raw)
    sha = lambda b: hashlib.sha256(b).hexdigest()
    meta = dict(codec='zstd', raw_bytes=len(raw), raw_sha256=sha(raw),
                stored_bytes=len(stored), stored_sha256=sha(stored))
    assert runner().decode_stored(stored, meta) == raw
    for changed in ({**meta, 'raw_bytes': 2**30}, {**meta, 'raw_sha256': '0'*64},
                    {**meta, 'stored_sha256': '0'*64}):
        with pytest.raises(ValueError):
            runner().decode_stored(stored, changed)
    extra = stored+stored
    with pytest.raises((ValueError, zstandard.ZstdError)):
        runner().decode_stored(extra, {**meta, 'stored_bytes': len(extra), 'stored_sha256': sha(extra)})


def test_audit_retains_fit_before_prediction_failure(monkeypatch):
    model = load(BASE/'model.py')
    dates = pd.date_range('2023-01-01', periods=100, tz='UTC')
    panel = pd.DataFrame(dict(decision_at=dates, label_start=dates,
                              label_end=dates+pd.Timedelta(days=1), y=np.arange(100)%2))
    for name in ('a','b','c'):
        panel[name] = np.arange(100)
        panel[name+'__available_at'] = dates
    sets = dict(M0=['a'], M1=['a','b'], M2=['a','b','c'])
    def fail(*args, **kwargs):
        raise RuntimeError('invented inference failure')
    monkeypatch.setattr(model.LGBMClassifier, 'predict_proba', fail)
    fits = []
    with pytest.raises(RuntimeError, match='invented inference'):
        model.run_comparison(panel, sets, [dict(id='x', start=dates[80], end=dates[-1])],
                             audit_fit=lambda fold,arm,learner,train,test: fits.append(
                                 (fold, arm, learner.booster_.model_to_string(), len(train), len(test))))
    assert [(x[0],x[1],x[3],x[4]) for x in fits] == [('x','M0',80,19)]
    assert 'feature_names=a' in fits[0][2]


def invented_inputs():
    import calendar
    import io
    import zipfile
    mod = runner()
    encode = lambda x: json.dumps(x, sort_keys=True).encode()
    sha = lambda x: hashlib.sha256(x).hexdigest()
    inputs = {'config': (BASE/'config.json').read_bytes(), 'protocol': b'invented protocol',
              'history': b'{}', 'approval': b'{}', 'amendment': b'{}'}
    cells, artifacts = [], []
    total = 0
    for number, month in enumerate(mod.adapter.MONTHS):
        unit = 1000000 if month.startswith('2025') else 1000
        days = pd.date_range(month+'-01', periods=calendar.monthrange(*map(int, month.split('-')))[1], tz='UTC')
        lines = []
        for day in days:
            opening = 100 + day.day%2
            stamp = int(day.timestamp())*unit
            lines.append(f'{stamp},{opening},103,99,100,10,{stamp+86400*unit-1},1000,1,1,1,0')
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr(f'ETHUSDT-1d-{month}.csv', '\n'.join(lines)+'\n')
        zip_raw = stream.getvalue()
        checksum = f'{sha(zip_raw)}  ETHUSDT-1d-{month}.zip\n'.encode()
        cell = dict(mod.adapter.spot.validate_month(month, zip_raw, checksum), status='complete', receipts=[])
        for index,(kind,raw) in enumerate((('zip',zip_raw),('checksum',checksum))):
            stored = zstandard.ZstdCompressor().compress(raw)
            path = f'request-{number*2+index+1:04d}.body.zst'
            blob = dict(path=path, codec='zstd', raw_bytes=len(raw), raw_sha256=sha(raw),
                        stored_bytes=len(stored), stored_sha256=sha(stored))
            cell[kind+'_blob'] = blob
            cell[kind+'_url'] = mod.adapter.spot.registered_url(month, kind=='checksum')
            cell['receipts'].append(dict(blob=blob, bytes=len(raw), sha256=sha(raw), status=200, error=None))
            artifacts.append(dict(path=path, bytes=len(stored), sha256=sha(stored)))
            inputs[f'spot_{month}_{kind}'] = stored
            total += len(raw)
        cell.update(network_requests=2, acquisition_attempted=True)
        raw_meta = encode(cell)
        inputs[f'spot_{month}_metadata'] = raw_meta
        artifacts.append(dict(path=f'month-{month}.json', bytes=len(raw_meta), sha256=sha(raw_meta)))
        cells.append(cell)
    manifest = dict(status='complete', months=list(mod.adapter.MONTHS), cells=cells, artifacts=artifacts,
                    market='spot', symbol='ETHUSDT', interval='1d', raw_bytes=total, requests=76, complete_months=38)
    inputs['spot_manifest'] = encode(manifest)
    inputs['spot_capture_review'] = encode(dict(spot_stage=dict(independent_archive_check='passed',
            manifest_sha256=sha(inputs['spot_manifest']), months=38), final_closure=dict(status='verified', complete_spot_months=38)))
    graph = []
    for day in pd.date_range('2022-01-01','2024-12-31'):
        item = dict(day=str(day.date()), source_admitted=True, graph_admitted=True,
                    source_status='complete', graph_status='complete', available_at=None,
                    events=10, nodes=4, directed_pairs=6, stars=0, dyads=0, triangles=0,
                    overlap_nodes=4, nonzero_nodes=0,
                    local40=dict(local40_sums=[0]*40, unique_occurrences=0, overlap_node_count=4, nonzero_nodes=0))
        if str(day.date()) in ('2022-01-01','2024-12-31'):
            item.update(graph_admitted=False, reason='invented boundary')
        graph.append(item)
    inputs['graph_panel'] = encode(dict(global_uniqueness_admitted=True, days=graph))
    hashes = {'panel.json': sha(inputs['graph_panel'])}
    inputs['graph_terminal'] = encode(dict(status='complete', experiment_id=mod.adapter.GRAPH_EXPERIMENT,
                                           source=mod.GRAPH_SOURCE, output_sha256=hashes))
    inputs['graph_review'] = encode(dict(passed=True, passing_full_panel=True, source=mod.GRAPH_SOURCE,
                                        terminal_sha256=sha(inputs['graph_terminal']), output_sha256=hashes))
    inputs['graph_review_guard'] = encode(dict(phase='complete', child_exit_code=0, limit_reason=None,
                cleanup_verified=True, memory_events=dict(oom=0,oom_kill=0,oom_group_kill=0,high=0,max=0),
                memory_high_bytes=6*1024**3, memory_max_bytes=6*1024**3,
                memory_swap_max_bytes=512*1024**2, cpus=[0,1],
                cwd=str(mod.GRAPH_ROOT), command=[str(ROOT/'.venv/bin/python'), '-B',
                str(mod.GRAPH_ROOT/mod.GRAPH_BASE/'check_final.py'), '--root', str(mod.GRAPH_ROOT),
                '--source', mod.GRAPH_SOURCE, '--report', str(mod.GRAPH_ROOT/mod.GRAPH_BASE/'independent-report.json')]))
    return inputs


class MemoryRun:
    def __init__(self, inputs, directory=None):
        self.inputs, self.outputs = inputs, {}
        self.directory = directory
        if directory is not None:
            directory.mkdir(exist_ok=True)
            (directory/'claim.json').write_text(json.dumps(dict(source='invented-source', experiment_id='eth-matched-direction-20260924')))
    def read_input(self, name):
        return self.inputs[name]
    def write_json(self, name, value):
        assert name not in self.outputs
        self.outputs[name] = json.loads(json.dumps(value, allow_nan=False))


def test_execute_retains_failed_arms_partial_fits_and_all_cells(monkeypatch, tmp_path):
    mod = runner()
    run = MemoryRun(invented_inputs(), tmp_path)
    original = mod.model.LGBMClassifier.predict_proba
    def fail_second(learner, X, *args, **kwargs):
        if len(X.columns) == 13:
            raise RuntimeError('invented M1 inference failure')
        return original(learner, X, *args, **kwargs)
    monkeypatch.setattr(mod.model.LGBMClassifier, 'predict_proba', fail_second)
    cells = mod.execute(ROOT, run)
    assert len(cells) == 77 and len({c['id'] for c in cells}) == 77
    assert len(run.outputs['fits.json']['fits']) == 24
    assert run.outputs['predictions.json']['rows'] == []
    assert run.outputs['evaluation.json']['inference']['status'] == 'unavailable'
    assert len(run.outputs['evaluation.json']['attempts']) == 12
    assert sum(c['status']=='unavailable' for c in cells) == 38
    assert all(c.get('reason') for c in cells if c['status']=='unavailable')
    assert list(run.outputs)[:4] == ['inputs-admission.json','market.json','graph.json','panel.json']
    assert len(run.outputs['market.json']['rows']) == 1128
    assert len(run.outputs['panel.json']['rows']) == 1088


def test_graph_guard_wrong_root_rejected_before_prices(monkeypatch):
    mod = runner()
    inputs = invented_inputs()
    guard = json.loads(inputs['graph_review_guard']); guard['command'][4] = '/wrong'
    inputs['graph_review_guard'] = json.dumps(guard).encode()
    def never(*args):
        pytest.fail('decoded prices before graph identity checks')
    monkeypatch.setattr(mod, 'decode_stored', never)
    with pytest.raises(ValueError, match='command'):
        mod.execute(ROOT, MemoryRun(inputs))


def rebind_graph(inputs):
    sha = lambda x: hashlib.sha256(x).hexdigest()
    terminal = json.loads(inputs['graph_terminal'])
    terminal['output_sha256']['panel.json'] = sha(inputs['graph_panel'])
    inputs['graph_terminal'] = json.dumps(terminal).encode()
    review = json.loads(inputs['graph_review'])
    review['terminal_sha256'] = sha(inputs['graph_terminal'])
    review['output_sha256'] = terminal['output_sha256']
    inputs['graph_review'] = json.dumps(review).encode()


@pytest.mark.parametrize('late', [False, True])
def test_successful_months_preserve_missing_test_days(late, tmp_path):
    mod = runner()
    inputs = invented_inputs()
    if late:
        graph = json.loads(inputs['graph_panel'])
        next(d for d in graph['days'] if d['day']=='2024-03-01')['available_at'] = '2025-01-01T00:00:00Z'
        inputs['graph_panel'] = json.dumps(graph).encode()
        rebind_graph(inputs)
    run = MemoryRun(inputs, tmp_path)
    cells = mod.execute(ROOT, run)
    result = run.outputs['evaluation.json']
    assert len(run.outputs['fits.json']['fits']) == 36
    assert all(a['status']=='complete' for a in result['attempts'])
    assert result['inference']['status'] == ('unavailable' if late else 'available')
    assert sum(c['status']=='unavailable' for c in cells) == (2 if late else 0)
    if late:
        assert '2024-03-03T00:00:00+00:00' in result['inference']['missing_dates']
    else:
        assert len(run.outputs['predictions.json']['rows']) == 366
        assert result['inference']['result']['n'] == 366
    # Replay one saved model on saved test features without fitting again.
    from lightgbm import Booster
    fit = run.outputs['fits.json']['fits'][0]
    panel = pd.DataFrame(run.outputs['panel.json']['rows']).set_index('decision_at')
    X = panel.loc[fit['test_days'], run.outputs['panel.json']['feature_sets']['M0']]
    expected = pd.DataFrame(run.outputs['predictions.json']['rows']).set_index('decision_at').loc[fit['test_days'],'M0_probability']
    np.testing.assert_allclose(Booster(model_str=fit['model_text']).predict(X), expected, atol=1e-14)


@pytest.mark.parametrize('mutation', ['graph_calendar','source_day','metadata','manifest_hash'])
def test_rejects_unbound_or_wrong_source_inputs(mutation):
    mod = runner()
    inputs = invented_inputs()
    if mutation in ('graph_calendar','source_day'):
        graph = json.loads(inputs['graph_panel'])
        if mutation == 'graph_calendar':
            graph['days'].pop(20)
        else:
            graph['days'][20]['source_admitted'] = False
        inputs['graph_panel'] = json.dumps(graph).encode()
        rebind_graph(inputs)
    elif mutation == 'metadata':
        meta = json.loads(inputs['spot_2021-12_metadata'])
        meta['zip_blob']['raw_sha256'] = '0'*64
        inputs['spot_2021-12_metadata'] = json.dumps(meta).encode()
    else:
        inputs['spot_manifest'] += b' '
    run = MemoryRun(inputs)
    with pytest.raises(ValueError):
        mod.execute(ROOT, run)
    assert run.outputs == {}


def test_fatal_inference_error_keeps_fits_and_explicit_failure(monkeypatch, tmp_path):
    mod = runner()
    run = MemoryRun(invented_inputs(), tmp_path)
    def fail(*args, **kwargs):
        raise RuntimeError('invented bootstrap failure')
    monkeypatch.setattr(mod.model, 'paired_loss_summary', fail)
    cells = mod.execute(ROOT, run)
    assert len(run.outputs['fits.json']['fits']) == 36
    assert len(cells) == 77
    assert sum(c['status']=='unavailable' for c in cells) == 2
    assert len(run.outputs['predictions.json']['rows']) == 366
    assert run.outputs['evaluation.json']['inference']['error_type'] == 'inference_failed'
    assert run.outputs['evaluation.json']['inference']['reason'] == 'RuntimeError: invented bootstrap failure'
    assert len(run.outputs['panel.json']['rows']) == 1088
    assert run.outputs['evaluation.json']['screening']['supported'] is None


def test_output_budget_counts_exact_aggregate_bytes_and_keeps_prior_evidence(monkeypatch):
    mod = runner()
    run = MemoryRun({})
    first = {'unicode': 'ž', 'rows': [None, 1]}
    first_size = len((json.dumps(first, sort_keys=True, indent=2, allow_nan=False)+'\n').encode())
    monkeypatch.setattr(mod, 'OUTPUT_LIMIT_BYTES', first_size)
    publish = mod.OutputPublisher(run)
    publish('first.json', first)
    with pytest.raises(ValueError, match='output payload'):
        publish('second.json', {})
    assert run.outputs == {'first.json': first}


@pytest.mark.parametrize('field,value', [('memory_high_bytes', 1), ('memory_max_bytes', 1),
        ('memory_swap_max_bytes', 0), ('cpus', [0]), ('memory_events', dict(oom=0,oom_kill=0,oom_group_kill=0,max=1,high=0))])
def test_graph_guard_limits_and_clean_limit_events(field, value):
    mod = runner()
    inputs = invented_inputs()
    guard = json.loads(inputs['graph_review_guard'])
    guard[field] = value
    inputs['graph_review_guard'] = json.dumps(guard).encode()
    with pytest.raises(ValueError, match='graph review resource'):
        mod.graph_admission(ROOT, inputs)


def test_checkpoint_bound_atomic_no_overwrite_and_shared_budget(tmp_path, monkeypatch):
    mod = runner()
    run = MemoryRun({}, tmp_path)
    publisher = mod.OutputPublisher(run)
    checkpoints = mod.FitCheckpoints(run, publisher)
    fit = dict(fold='2024-01', arm='M0', train_days=[], test_days=[], params={}, model_text='invented')
    checkpoints(fit)
    path = tmp_path/'fit-checkpoints/2024-01-M0.json'
    raw = path.read_bytes(); receipt = json.loads(raw)
    assert receipt == dict(schema_version=1, source='invented-source', sequence=0, experiment_id='eth-matched-direction-20260924',
                           claim_sha256=hashlib.sha256((tmp_path/'claim.json').read_bytes()).hexdigest(), fit=fit)
    assert publisher.published_bytes == len(raw)
    with pytest.raises(FileExistsError):
        checkpoints(fit)
    assert path.read_bytes() == raw
    monkeypatch.setattr(mod, 'OUTPUT_LIMIT_BYTES', len(raw))
    with pytest.raises(ValueError, match='output payload'):
        publisher('fits.json', {'fits':[fit]})
    assert list((tmp_path/'fit-checkpoints').iterdir()) == [path]


def test_checkpoint_failure_stops_further_fitting_and_retains_prior(tmp_path, monkeypatch):
    mod = runner()
    run = MemoryRun(invented_inputs(), tmp_path)
    original = mod.FitCheckpoints.__call__
    def fail_second(self, fit):
        if fit['arm'] == 'M1':
            raise OSError('invented checkpoint storage failure')
        return original(self, fit)
    monkeypatch.setattr(mod.FitCheckpoints, '__call__', fail_second)
    fits = []
    fit_original = mod.model.LGBMClassifier.fit
    def observed_fit(self, *args, **kwargs):
        fits.append(1)
        return fit_original(self, *args, **kwargs)
    monkeypatch.setattr(mod.model.LGBMClassifier, 'fit', observed_fit)
    cells = mod.execute(ROOT, run)
    assert len(fits) == 2
    assert len(list((tmp_path/'fit-checkpoints').glob('*.json'))) == 1
    assert len(run.outputs['fits.json']['fits']) == 1
    assert 'checkpoint storage failure' in run.outputs['summary.json']['error']
    assert sum(c['status']=='unavailable' for c in cells) == 38


def test_fit_checkpoint_survives_abrupt_process_exit(tmp_path):
    import subprocess
    import sys
    MemoryRun({}, tmp_path)
    script = '''
import importlib.util, os, sys
from pathlib import Path
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('checkpoint_child',sys.argv[1])
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
r=SimpleNamespace(directory=Path(sys.argv[2]))
c=m.FitCheckpoints(r,m.OutputPublisher(r))
c(dict(fold='2024-01',arm='M0',train_days=[],test_days=[],params={},model_text='invented'))
os._exit(17)
'''
    result = subprocess.run([sys.executable, '-B', '-c', script,
                             str(BASE/'evaluation-20260924/run.py'), str(tmp_path)], check=False)
    assert result.returncode == 17
    checkpoint = json.loads((tmp_path/'fit-checkpoints/2024-01-M0.json').read_bytes())
    assert checkpoint['sequence'] == 0 and checkpoint['fit']['model_text'] == 'invented'
    assert checkpoint['claim_sha256'] == hashlib.sha256((tmp_path/'claim.json').read_bytes()).hexdigest()
