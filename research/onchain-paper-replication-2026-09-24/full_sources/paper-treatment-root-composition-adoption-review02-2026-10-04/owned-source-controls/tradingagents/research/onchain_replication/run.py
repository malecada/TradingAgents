"""Execute a finite admitted batch from verified prepared components.

Source/graph preparation, guarded process ownership and feature production are
separate stages. This executor does not admit missing inputs or alter masks to
make an arm run. Individual failures remain visible while independent cells
continue. An interrupted batch directory is never reopened or automatically
restarted; its outer observer must close the original claim.
"""
from dataclasses import asdict
import json

from ..lifecycle import ResearchRun, _immutable
from .baselines import training_controls
from .cells import lifecycle_cell_id, reconcile_cells
from .evaluation import evaluate_cell, example_binding, validate_scientific_cell, prediction_directory, validate_manifest
from .model_registry import PRICE_ARMS, GRAPH_ARMS, VECTOR_WIDTHS
from .metrics import classification_metrics
from .provenance import canonical_bytes, digest, file_hash, durable_mkdir, sync_directory


def _configuration(cell, model, training, binding, scaler):
    return digest(canonical_bytes({'model': model, 'training': training,
        'cell': {k: cell[k] for k in ('id', 'lane', 'asset', 'arm', 'task', 'seed', 'fold', 'variant')},
        'feature_binding': binding, 'scaler': asdict(scaler)}))


def _published(run, name):
    raw = (run.directory/'outputs'/name).read_bytes()
    if run._published_outputs.get(name) != digest(raw):
        raise ValueError('dependency output is not published by this run')
    return json.loads(raw)


def preflight_batch(run, populations, representations=None, *, plan_input='batch_plan'):
    """Validate science before fitting; None defers dynamic feature-byte checks."""
    if not isinstance(run, ResearchRun):
        raise ValueError('admitted batch run required')
    run._active()
    run._check_source()
    plan = json.loads(run.read_input(plan_input))
    if set(plan) != {'schema_version', 'cells', 'populations', 'representations', 'model', 'training', 'ledger_output', 'controls_output'} or plan['schema_version'] != 1:
        raise ValueError('batch plan schema differs')
    items = plan['cells']
    expected = [item['cell'] for item in items]
    ids = [c['id'] for c in expected]
    if not ids or len(ids) != len(set(ids)) or [lifecycle_cell_id(x) for x in ids] != run.admission.experiment['cells']:
        raise ValueError('registered batch cell denominator differs')
    if plan['ledger_output'] == plan['controls_output'] or not {plan['ledger_output'], plan['controls_output']} <= set(run.admission.experiment['outputs']):
        raise ValueError('batch outputs not registered')
    common_populations = {}
    representation_failures = {}
    for item in items:
        cell = item['cell']
        validate_scientific_cell(cell)
        if cell['arm'] not in PRICE_ARMS | GRAPH_ARMS | set(VECTOR_WIDTHS) or cell['task'] not in ('direction', 'regression') or cell['asset'] not in ('BTC', 'ETH') or type(cell['seed']) is not int:
            raise ValueError('unknown scientific cell arm/task/asset/seed')
        if item['status'] == 'unavailable':
            if set(item) != {'cell', 'status', 'reason', 'evidence_inputs'} or not item['reason'] or not item['evidence_inputs']:
                raise ValueError('unavailable cell requires registered evidence and reason')
            for name in item['evidence_inputs']:
                run.read_input(name)
            continue
        if item['status'] != 'ready' or set(item)-{'recovery'} != {'cell', 'status', 'population', 'representation'}:
            raise ValueError('batch cell state/schema differs')
        if item.get('recovery') is not None:
            recovery = item['recovery']
            required = {'mode', 'checkpoint_input', 'provenance_input'} | ({'completion_input'} if recovery['mode'] == 'prediction_only' else set())
            if set(recovery) != required or recovery['mode'] not in ('continuation', 'prediction_only') or run.admission.experiment['parent'] is None:
                raise ValueError('registered recovery requires new parent and exact mode inputs')
            for key in required-{'mode'}:
                run.read_input(recovery[key])
        reference = plan['populations'][item['population']]
        examples, scaler = populations[item['population']]
        for partition in (examples.train, examples.test):
            decisions = [x.decision_at for x in partition]
            if decisions != sorted(set(decisions)):
                raise ValueError('population decisions must be unique and chronological before fitting')
        if not examples.train or not examples.test or digest(canonical_bytes([asdict(x) for x in examples.train])) != examples.train_hash or digest(canonical_bytes([x.decision_at for x in examples.test])) != examples.test_mask_hash or scaler.train_hash != examples.train_hash:
            raise ValueError('actual prepared population bytes/membership differ before fitting')
        if canonical_bytes(reference['binding']) != canonical_bytes(example_binding(examples, scaler)):
            raise ValueError('prepared population differs from registered membership')
        validate_manifest(run, reference.get('input'), reference.get('output'), example_binding(examples, scaler))
        if (reference['train_examples'], reference['test_examples']) != (len(examples.train), len(examples.test)):
            raise ValueError('prepared population denominator differs')
        if reference['asset'] != cell['asset'] or reference['fold'] != cell['fold'] or reference['variant'] != cell['variant']:
            raise ValueError('population asset/fold/variant differs')
        mask_key = (cell['asset'], cell['fold'])
        fields = ('decision_at', 'label_start', 'label_end', 'input_dates', 'input_prices', 'target_price', 'up')
        common = digest(canonical_bytes({'fold_hash': examples.fold_hash, 'test_mask_hash': examples.test_mask_hash,
            'train': [{k: getattr(x, k) for k in fields} for x in examples.train],
            'test': [{k: getattr(x, k) for k in fields} for x in examples.test], 'scaler_dates': scaler.dates,
            'scaler_mean': scaler.mean, 'scaler_std': scaler.std}))
        if mask_key in common_populations and common_populations[mask_key] != common:
            raise ValueError('batch comparators do not share frozen labels/splits/prices/mask')
        common_populations[mask_key] = common
        if cell['arm'] in PRICE_ARMS | {'constant_graph'}:
            if item['representation'] is not None:
                raise ValueError('price/constant arm must not consume a fitted representation')
        else:
            feature = plan['representations'][item['representation']]
            if (feature.get('input') is None) == (feature.get('output') is None):
                raise ValueError('one admitted feature reference required')
            if representations is None:
                continue
            if item['representation'] not in representations:
                failed = _published(run, feature['failure_output'])
                if failed.get('status') != 'failed' or failed.get('representation') != item['representation'] or not failed.get('reason'):
                    raise ValueError('missing representation lacks exact published failure evidence')
                representation_failures[item['representation']] = failed
                continue
            prepared = representations[item['representation']]
            registered_binding = json.loads(run.read_input(feature['input'])) if feature.get('input') else _published(run, feature['output'])
            if canonical_bytes(registered_binding) != canonical_bytes(prepared.binding) or ('binding' in feature and canonical_bytes(feature['binding']) != canonical_bytes(prepared.binding)):
                raise ValueError('prepared representation differs from registered binding')
            wanted = 'motif_mcm' if cell['arm'] in {'proposed', 'mcm_without_gat', 'training_label_permutation'} else cell['arm']
            if prepared.binding.get('representation') != wanted or prepared.binding.get('asset') != cell['asset']:
                raise ValueError('prepared representation/asset differs from requested cell')
    return plan, expected, representation_failures


def execute_batch(run, populations, representations, *, plan_input='batch_plan'):
    """Fit/evaluate every admitted prepared cell once, retaining all dispositions."""
    plan, expected, representation_failures = preflight_batch(run, populations, representations, plan_input=plan_input)
    items = plan['cells']
    ids = [c['id'] for c in expected]
    directory = run.admission.root / 'research_artifacts/onchain-paper-replication-2026-09-24/batches' / run.admission.experiment_id
    durable_mkdir(directory.parent)
    directory.mkdir(exist_ok=False)
    sync_directory(directory.parent)
    _immutable(directory/'claim.json', {'source': run.admission.source, 'experiment': run.admission.experiment_id,
                                      'plan_input': plan_input, 'plan_sha256': digest(canonical_bytes(plan)), 'cells': ids})
    dispositions = []
    controls = {}
    for index, item in enumerate(items):
        run._active()
        run._check_source()
        cell = item['cell']
        row = {'id': cell['id'], 'status': 'unavailable', 'attempts': []}
        if item['status'] == 'unavailable':
            row.update(reason=item['reason'], evidence_inputs=item['evidence_inputs'])
        elif item['representation'] in representation_failures:
            failed = representation_failures[item['representation']]
            row.update(reason='Required representation unavailable: '+failed['reason'],
                       evidence_output=plan['representations'][item['representation']]['failure_output'])
        else:
            name = item['population']
            reference = plan['populations'][name]
            examples, scaler = populations[name]
            if name not in controls:
                control_values = training_controls([x.up for x in examples.train], [x.input_prices for x in examples.test])
                controls[name] = {'test_mask_hash': examples.test_mask_hash,
                                 'decision_at': [x.decision_at for x in examples.test],
                                 'labels': [x.up for x in examples.test], 'probabilities': control_values,
                                 'metrics': {k: classification_metrics([x.up for x in examples.test], v) for k, v in control_values.items()},
                                 'fit_count': 0}
                _immutable(directory/f'controls-{index:04d}.json', controls[name])
            feature_reference = plan['representations'].get(item['representation'], {})
            prepared = representations.get(item['representation'])
            features = {} if prepared is None else prepared.features
            binding = {} if prepared is None else prepared.binding
            provenance = {'source_hashes': list(examples.source_hashes),
                          'config_hash': _configuration(cell, plan['model'], plan['training'], binding, scaler),
                          'input_hash': examples.train_hash, 'fold_id': cell['fold'],
                          'dictionary_hash': binding.get('dictionary_hash', digest(canonical_bytes({'component': 'no_graph_representation'}))),
                          'cell_id': lifecycle_cell_id(cell['id']), 'source_commit': run.admission.source}
            row['attempts'].append(run.admission.experiment_id)
            recovery_args = {}
            if item.get('recovery') is not None:
                recovery = item['recovery']
                old = json.loads(run.read_input(recovery['provenance_input']))
                if recovery['mode'] == 'continuation':
                    info = run.admission.inputs[recovery['checkpoint_input']]
                    recovery_args['continuation'] = {'checkpoint': run.admission.root/info['path'], 'provenance': old}
                else:
                    recovery_args['completed_fit'] = {'provenance': old, 'checkpoint_input': recovery['checkpoint_input'],
                                                       'completion_input': recovery['completion_input']}
            try:
                _, metrics = evaluate_cell(run, cell, examples, scaler, features, plan['model'], plan['training'], provenance,
                    expected_test_mask=reference['binding']['test_mask_hash'], feature_binding=binding,
                    example_binding_input=reference.get('input'), example_binding_output=reference.get('output'),
                    feature_binding_input=feature_reference.get('input'),
                    feature_binding_output=feature_reference.get('output'), **recovery_args)
                path = prediction_directory(run, lifecycle_cell_id(cell['id']))/'cell.json'
                row.update(status='complete', metrics=metrics, cell_record=str(path.relative_to(run.admission.root)),
                           cell_record_sha256=file_hash(path), test_mask_hash=examples.test_mask_hash)
            except (ValueError, RuntimeError, OSError) as error:
                # Fatal signals, MemoryError and BaseException propagate to the
                # owned outer observer. A local failed fit never becomes a retry.
                row.update(status='failed', reason=type(error).__name__+': '+str(error))
        _immutable(directory/f'cell-{index:04d}.json', row)
        dispositions.append(row)
    summary = reconcile_cells(expected, dispositions)
    run.write_json(plan['controls_output'], controls)
    run.write_json(plan['ledger_output'], {'cells': dispositions, 'summary': summary,
        'all_mandatory_complete': summary['statuses']['complete'] == len(expected),
        'qualification': 'finite cell execution; independent metric/model replay and paper agreement remain separate'})
    _immutable(directory/'complete.json', {'cells': len(dispositions), 'summary': summary,
                                         'scientifically_complete': summary['statuses']['complete'] == len(expected)})
    return dispositions, controls
