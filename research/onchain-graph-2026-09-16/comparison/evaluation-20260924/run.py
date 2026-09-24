"""Claim-bound fixed retrospective comparison. No acquisition or retry path."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import uuid
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import zstandard

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUTPUT_LIMIT_BYTES = 64 * 1024**2
GRAPH_SOURCE = '87b6ac39d12a4f9a2ac1832f34f68647c52c53c8'
GRAPH_ROOT = Path('/home/malecada/Data/onchain-research/TradingAgents-onchain-fullpanel-resume2')
GRAPH_BASE = 'research/onchain-graph-2026-09-16/fullpanel_resume2'
QUALIFICATION = ('Retrospective classification screening only. Availability clocks are protocol '
                 'assumptions, not verified historical availability. No PnL or strategy validation.')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = load_module('matched_run_adapter', HERE.parent/'input_adapter.py')
features = load_module('matched_run_features', HERE.parent/'features.py')
model = load_module('matched_run_model', HERE.parent/'model.py')
require = adapter.require


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_value(value):
    """Encode evidence without NaN tokens or loss of UTC clock meaning."""
    if isinstance(value, pd.DataFrame):
        return json_value(value.to_dict('records'))
    if isinstance(value, dict):
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray, pd.Series, pd.Index)):
        return [json_value(v) for v in value]
    if value is None or value is pd.NaT or value is pd.NA:
        return None
    if isinstance(value, pd.Timestamp):
        return value.tz_convert('UTC').isoformat()
    if isinstance(value, np.generic):
        return json_value(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value



class OutputPublisher:
    """Bound the aggregate payload using the lifecycle writer's exact encoding."""
    def __init__(self, run):
        self.run = run
        self.published_bytes = 0

    def encoded(self, value):
        raw = (json.dumps(json_value(value), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        require(self.published_bytes + len(raw) <= OUTPUT_LIMIT_BYTES,
                'aggregate output payload exceeds 64 MiB bound')
        return raw

    def __call__(self, name, value):
        value = json_value(value)
        raw = self.encoded(value)
        self.run.write_json(name, value)
        self.published_bytes += len(raw)



class FitCheckpoints:
    """Exclusive claim-bound fit archive, durable before another fit can start."""
    def __init__(self, run, publisher):
        self.publisher = publisher
        claim_raw = (run.directory/'claim.json').read_bytes()
        claim = json.loads(claim_raw)
        self.identity = dict(schema_version=1, experiment_id=claim['experiment_id'],
                             source=claim['source'], claim_sha256=sha(claim_raw))
        self.directory = run.directory/'fit-checkpoints'
        self.directory.mkdir(exist_ok=False)
        descriptor = os.open(run.directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        self.sequence = 0

    def __call__(self, fit):
        fold, arm = fit['fold'], fit['arm']
        require(fold in [f'2024-{month:02d}' for month in range(1, 13)]
                and arm in ('M0', 'M1', 'M2'), 'invalid fit checkpoint identity')
        record = dict(self.identity, sequence=self.sequence, fit=json_value(fit))
        raw = self.publisher.encoded(record)
        target = self.directory/f'{fold}-{arm}.json'
        temporary = self.directory/('.pending-'+uuid.uuid4().hex)
        try:
            with temporary.open('xb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, target)
            descriptor = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        finally:
            temporary.unlink(missing_ok=True)
        self.publisher.published_bytes += len(raw)
        self.sequence += 1


def decode_stored(stored, metadata):
    """Bound decompression by hash-bound capture metadata, never by raw content."""
    n, stored_n = metadata['raw_bytes'], metadata['stored_bytes']
    require(type(n) is int and 0 < n <= adapter.spot.RESPONSE_LIMIT
            and type(stored_n) is int and 0 < stored_n <= adapter.spot.RESPONSE_LIMIT*2
            and metadata.get('codec') == 'zstd', 'invalid response metadata bounds/codec')
    require(len(stored) == stored_n and sha(stored) == metadata['stored_sha256'],
            'stored response size/hash mismatch')
    require(zstandard.frame_content_size(stored) == n, 'zstd content size mismatch')
    raw = zstandard.ZstdDecompressor().decompress(stored, max_output_size=n, allow_extra_data=False)
    require(len(raw) == n and sha(raw) == metadata['raw_sha256'], 'raw response size/hash mismatch')
    return raw


def graph_admission(root, inputs):
    panel_raw, terminal_raw = inputs['graph_panel'], inputs['graph_terminal']
    report, guard = (json.loads(inputs[k]) for k in ('graph_review', 'graph_review_guard'))
    adapter.require_graph_review(panel_raw, terminal_raw, report, guard, source=GRAPH_SOURCE)
    command = [str(Path(root)/'.venv/bin/python'), '-B', str(GRAPH_ROOT/GRAPH_BASE/'check_final.py'),
               '--root', str(GRAPH_ROOT), '--source', GRAPH_SOURCE,
               '--report', str(GRAPH_ROOT/GRAPH_BASE/'independent-report.json')]
    require(guard.get('command') == command and guard.get('cwd') == str(GRAPH_ROOT),
            'graph review exact command/root mismatch')
    require(guard.get('memory_high_bytes') == 6*1024**3
            and guard.get('memory_max_bytes') == 6*1024**3
            and guard.get('memory_swap_max_bytes') == 512*1024**2
            and guard.get('cpus') == [0, 1]
            and all(type(guard['memory_events'].get(k)) is int and guard['memory_events'][k] == 0
                    for k in ('high', 'max')),
            'graph review resource limits/events mismatch')
    panel = json.loads(panel_raw)
    expected = pd.date_range('2022-01-01', '2024-12-31').strftime('%Y-%m-%d').tolist()
    require([d['day'] for d in panel['days']] == expected, 'exact graph source calendar required')
    require(all(d.get('source_admitted') is True and d.get('source_status') == 'complete'
                for d in panel['days']), 'all graph source days must be admitted')
    graph, exclusions = adapter.graph_rows(panel)
    require([d['day'] for d in exclusions] == ['2022-01-01', '2024-12-31'],
            'exact graph boundary exclusions required')
    return graph, exclusions


def spot_admission(run, inputs):
    manifest = json.loads(inputs['spot_manifest'])
    review = json.loads(inputs['spot_capture_review'])
    stage = review['spot_stage']
    require(stage.get('independent_archive_check') == 'passed' and stage.get('months') == 38
            and stage.get('manifest_sha256') == sha(inputs['spot_manifest'])
            and review['final_closure'].get('status') == 'verified'
            and review['final_closure'].get('complete_spot_months') == 38,
            'spot capture review/manifest binding mismatch')
    require(manifest.get('status') == 'complete' and manifest.get('months') == list(adapter.MONTHS)
            and (manifest.get('market'), manifest.get('symbol'), manifest.get('interval')) == ('spot','ETHUSDT','1d')
            and manifest.get('requests') == 76 and manifest.get('complete_months') == 38,
            'spot capture cohort mismatch')
    require([c['month'] for c in manifest['cells']] == list(adapter.MONTHS), 'spot manifest cells mismatch')
    artifacts = {a['path']: a for a in manifest['artifacts']}
    require(len(artifacts) == len(manifest['artifacts']), 'duplicate spot artifact paths')
    months, total = {}, 0
    for month, cell in zip(adapter.MONTHS, manifest['cells']):
        prefix = f'spot_{month}_'
        metadata_raw = run.read_input(prefix+'metadata')
        metadata = json.loads(metadata_raw)
        entry = artifacts[f'month-{month}.json']
        require(metadata == cell and entry['bytes'] == len(metadata_raw) and entry['sha256'] == sha(metadata_raw)
                and metadata.get('status') == 'complete' and metadata.get('month') == month
                and metadata.get('network_requests') == 2 and metadata.get('acquisition_attempted') is True,
                'spot monthly metadata binding mismatch')
        require(len(metadata['receipts']) == 2, 'two spot receipts required')
        decoded = []
        for index, kind in enumerate(('zip', 'checksum')):
            blob = metadata[kind+'_blob']
            receipt = metadata['receipts'][index]
            require(metadata[kind+'_url'] == adapter.spot.registered_url(month, kind == 'checksum')
                    and receipt['blob'] == blob and receipt['status'] == 200 and receipt.get('error') is None
                    and receipt['bytes'] == blob['raw_bytes']
                    and receipt['sha256'] == blob['raw_sha256'] == metadata[kind+'_sha256'],
                    'spot receipt identity mismatch')
            stored = run.read_input(prefix+kind)
            entry = artifacts[blob['path']]
            require(entry['bytes'] == len(stored) and entry['sha256'] == sha(stored),
                    'spot stored manifest binding mismatch')
            decoded.append(decode_stored(stored, blob))
            total += len(decoded[-1])
        checked = adapter.spot.validate_month(month, *decoded)
        require(all(metadata.get(k) == v for k, v in checked.items()), 'spot archive metadata mismatch')
        months[month] = tuple(decoded)
    require(total == manifest['raw_bytes'] and total <= adapter.spot.TOTAL_LIMIT, 'spot total raw byte mismatch')
    return adapter.market_rows(months)


def execute(root, run):
    """Consume registered bytes after claim, publish evidence, return all 77 cells."""
    names = ('config', 'protocol', 'history', 'approval', 'amendment', 'graph_panel',
             'graph_terminal', 'graph_review', 'graph_review_guard', 'spot_capture_review', 'spot_manifest')
    inputs = {name: run.read_input(name) for name in names}
    config = json.loads(inputs['config'])
    require(config == json.loads((HERE.parent/'config.json').read_bytes()), 'registered/frozen config mismatch')
    graph, exclusions = graph_admission(root, inputs)
    market = spot_admission(run, inputs)
    panel, sets = features.build_panel(market, graph, start=config['decisions']['start'],
                                       end=config['decisions']['end_exclusive'])
    require(sets == config['feature_sets'], 'frozen feature order mismatch')
    publish = OutputPublisher(run)
    publish('inputs-admission.json', dict(graph_source=GRAPH_SOURCE,
            source_sha256={name: sha(raw) for name, raw in inputs.items()},
            graph_exclusions=exclusions, historical_availability_verified=False,
            availability_basis='protocol_assumption', qualification=QUALIFICATION))
    publish('market.json', dict(rows=market))
    publish('graph.json', dict(rows=graph, exclusions=exclusions))
    publish('panel.json', dict(rows=panel, feature_sets=sets))
    fits = []
    checkpoints = FitCheckpoints(run, publish)
    def audit_fit(fold, arm, learner, train, test):
        fit = dict(fold=fold, arm=arm, train_days=train.decision_at.tolist(),
                   test_days=test.decision_at.tolist(), params=dict(model.MODEL_PARAMS),
                   model_text=learner.booster_.model_to_string())
        checkpoints(fit)
        fits.append(fit)
    error = None
    try:
        result = model.evaluate(panel, audit_fit=audit_fit)
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
        # A fatal evaluator/inference error cannot silently discard completed fits.
        result = dict(predictions=pd.DataFrame(), admission=model.validate_panel(panel, sets)[1],
            attempts=pd.DataFrame([dict(fold=f['id'], status='failed', error=error) for f in config['folds']]),
            monthly=pd.DataFrame(), pooled_metrics={}, fold_metrics=pd.DataFrame(), counts=pd.DataFrame(),
            inference=dict(status='unavailable', reason=error), screening=dict(status='unavailable', supported=None),
            error=error)
    finally:
        publish('fits.json', dict(fits=fits))
    publish('predictions.json', dict(rows=result['predictions']))
    publish('evaluation.json', {k:v for k,v in result.items() if k != 'predictions'})
    cells = [dict(id='spot-'+month, status='complete') for month in adapter.MONTHS]
    cells.append(dict(id='graph-panel', status='complete'))
    for attempt in result['attempts'].to_dict('records'):
        for arm in ('M0', 'M1', 'M2'):
            cell = dict(id=f'fold-{attempt["fold"]}-{arm}',
                        status='complete' if attempt['status'] == 'complete' else 'unavailable')
            if cell['status'] == 'unavailable':
                cell['reason'] = attempt['error']
            cells.append(cell)
    for name in ('inference', 'screening'):
        available = result[name]['status'] == 'available'
        cell = dict(id=name, status='complete' if available else 'unavailable')
        if not available:
            cell['reason'] = result[name].get('reason') or result['inference'].get('reason') or 'complete pooled coverage required'
        cells.append(cell)
    require(len(cells) == 77 and len({c['id'] for c in cells}) == 77, 'fixed lifecycle cell mismatch')
    publish('summary.json', dict(cells=cells, cell_count=len(cells),
            unavailable_count=sum(c['status'] == 'unavailable' for c in cells),
            market_rows=len(market), graph_rows=len(graph), panel_rows=len(panel),
            fit_count=len(fits), prediction_rows=len(result['predictions']),
            screening=result['screening'], qualification=QUALIFICATION, error=error))
    return cells


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    admission = load_module('matched_execution_admission', HERE/'admission.py')
    from tradingagents.research.lifecycle import ResearchRun
    admission.admit_execution(ROOT, args.source)
    with ResearchRun.start(root=ROOT, registration=admission.BASE+'/gates.json',
                           experiment=admission.EXPERIMENT, source=args.source) as run:
        run.finish(execute(ROOT, run))


if __name__ == '__main__':
    main()
