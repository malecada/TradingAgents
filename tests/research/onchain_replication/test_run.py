import json
from dataclasses import replace, asdict

import pytest

from tests.research.test_lifecycle import registered, start, commit
from tests.research.onchain_replication.test_dataset import fixture
from tests.research.onchain_replication.test_evaluation import CONFIG
from tests.research.onchain_replication.test_training import CFG
from tradingagents.research.onchain_replication.dataset import build_examples, fit_scaler
from tradingagents.research.onchain_replication.evaluation import example_binding
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest, file_hash
from tradingagents.research.onchain_replication.run import execute_batch
from tradingagents.research.onchain_replication.verification import independent_classification, compare_summary


def setup(registered):
    root, spec, _ = registered
    graphs, prices, fold, config = fixture()
    examples = build_examples(graphs, prices, fold, config)
    examples = replace(examples, train=examples.train[:40], test=examples.test[:4],
        train_hash=digest(canonical_bytes([asdict(x) for x in examples.train[:40]])),
        test_mask_hash=digest(canonical_bytes([x.decision_at for x in examples.test[:4]])))
    scaler = fit_scaler(examples, prices, fold)
    common = {'asset': 'ETH', 'fold': '2024', 'seed': 11, 'variant': 'whole', 'lane': 'algorithm'}
    cells = [{'cell': {**common, 'id': name, 'arm': 'svm', 'task': task},
              'status': 'ready', 'population': 'whole', 'representation': None}
             for name, task in [('sum', 'direction'), ('count', 'regression')]]
    cells.append({'cell': {**common, 'id': 'blocked', 'arm': 'proposed', 'task': 'direction'},
                  'status': 'unavailable', 'reason': 'synthetic missing representation', 'evidence_inputs': ['blocked_evidence']})
    binding = example_binding(examples, scaler)
    plan = {'schema_version': 1, 'cells': cells, 'populations': {'whole': {
        'input': 'example_binding', 'binding': binding, 'train_examples': 40, 'test_examples': 4,
        'asset': 'ETH', 'fold': '2024', 'variant': 'whole'}}, 'representations': {},
        'model': CONFIG, 'training': {**CFG, 'epochs': 1},
        'ledger_output': 'ledger.json', 'controls_output': 'controls.json'}
    values = {'batch_plan': plan, 'example_binding': binding, 'blocked_evidence': {'status': 'unavailable', 'fixture': True}}
    for name, value in values.items():
        path = root/(name+'.json')
        path.write_bytes(canonical_bytes(value))
        spec['experiments']['example-a']['inputs'][name] = {'path': path.name, 'sha256': file_hash(path), 'dataset': 'sample'}
    spec['experiments']['example-a']['cells'] = ['sum', 'count', 'blocked']
    spec['experiments']['example-a']['outputs'] = ['ledger.json', 'controls.json']
    return (root, spec, commit(root, spec)), {'whole': (examples, scaler)}, plan


def test_prepared_batch_retains_controls_and_full_denominator(registered):
    registered, populations, _ = setup(registered)
    with start(registered) as run:
        rows, controls = execute_batch(run, populations, {})
        assert [x['status'] for x in rows] == ['complete', 'complete', 'unavailable']
        assert rows[2]['attempts'] == [] and rows[0]['attempts'] == [run.admission.experiment_id]
        assert controls['whole']['fit_count'] == 0
        for name, values in controls['whole']['probabilities'].items():
            assert compare_summary(controls['whole']['metrics'][name],
                   independent_classification(controls['whole']['labels'], values))['passed']
        ledger = json.loads((run.directory/'outputs/ledger.json').read_bytes())
        assert not ledger['all_mandatory_complete'] and len(ledger['cells']) == 3
        with pytest.raises(FileExistsError):
            execute_batch(run, populations, {})


def test_failed_cell_does_not_discard_an_independent_cell(registered, monkeypatch):
    import tradingagents.research.onchain_replication.run as module
    registered, populations, _ = setup(registered)
    actual = module.evaluate_cell
    calls = []
    def fail_first(run, cell, *args, **kwargs):
        calls.append(cell['id'])
        if cell['id'] == 'sum':
            raise ValueError('synthetic isolated cell failure')
        return actual(run, cell, *args, **kwargs)
    monkeypatch.setattr(module, 'evaluate_cell', fail_first)
    with start(registered) as run:
        rows, _ = execute_batch(run, populations, {})
        assert [x['status'] for x in rows] == ['failed', 'complete', 'unavailable']
        assert 'isolated cell failure' in rows[0]['reason'] and calls == ['sum', 'count']


def test_population_change_refuses_before_any_fit(registered, monkeypatch):
    import tradingagents.research.onchain_replication.run as module
    registered, populations, _ = setup(registered)
    examples, scaler = populations['whole']
    populations['whole'] = replace(examples, test=examples.test[:-1]), scaler
    monkeypatch.setattr(module, 'evaluate_cell', lambda *a, **kw: pytest.fail('changed population fitted'))
    with start(registered) as run, pytest.raises(ValueError, match='membership'):
        execute_batch(run, populations, {})


@pytest.mark.parametrize('partition,mutation', [('train', 'duplicate'), ('test', 'duplicate'),
                                              ('train', 'reverse'), ('test', 'reverse')])
def test_nonunique_or_unordered_decisions_refuse_before_any_fit(registered, monkeypatch, partition, mutation):
    import tradingagents.research.onchain_replication.run as module
    registered, populations, _ = setup(registered)
    examples, scaler = populations['whole']
    rows = getattr(examples, partition)
    rows = (rows[0], rows[0], *rows[2:]) if mutation == 'duplicate' else tuple(reversed(rows))
    populations['whole'] = replace(examples, **{partition: rows}), scaler
    monkeypatch.setattr(module, 'evaluate_cell', lambda *a, **kw: pytest.fail('invalid chronology fitted'))
    with start(registered) as run, pytest.raises(ValueError, match='unique and chronological'):
        execute_batch(run, populations, {})


def register_plan(registered, plan, additions=()):
    root, spec, _ = registered
    for name, value in [('batch_plan', plan), *additions]:
        path = root/(name+'.json')
        path.write_bytes(canonical_bytes(value))
        spec['experiments']['example-a']['inputs'][name] = {'path': path.name, 'sha256': file_hash(path), 'dataset': 'sample'}
    return root, spec, commit(root, spec)


@pytest.mark.parametrize('field', ['up', 'target_price', 'fold_hash'])
def test_equal_dates_cannot_hide_different_labels_or_fold(registered, monkeypatch, field):
    import tradingagents.research.onchain_replication.run as module
    registered, populations, plan = setup(registered)
    examples, scaler = populations['whole']
    if field == 'fold_hash':
        changed = replace(examples, fold_hash='f'*64)
    else:
        row = examples.test[0]
        changed = replace(examples, test=(replace(row, **{field: 1-row.up if field == 'up' else row.target_price+1}), *examples.test[1:]))
    populations['other'] = changed, scaler
    plan['populations']['other'] = {**plan['populations']['whole'], 'binding': example_binding(changed, scaler), 'input': 'other_binding'}
    plan['cells'][1]['population'] = 'other'
    registered = register_plan(registered, plan, [('other_binding', example_binding(changed, scaler))])
    monkeypatch.setattr(module, 'evaluate_cell', lambda *a, **kw: pytest.fail('incompatible comparison fitted'))
    with start(registered) as run, pytest.raises(ValueError, match='frozen labels/splits'):
        execute_batch(run, populations, {})


def test_full_motif_architecture_executes_through_registered_batch(registered):
    from tests.research.onchain_replication.test_feature_pipeline import configs
    from tradingagents.research.onchain_replication.feature_pipeline import prepare_features
    registered, populations, plan = setup(registered)
    graphs, _, fold, _ = fixture()
    examples, _ = populations['whole']
    config = configs()
    config['dictionary'] = {**config['dictionary'], 'sample_count': 32, 'size': 32}
    stages = []
    prepared = prepare_features(graphs, examples, fold, 'proposed', 11, config,
        max_entries=100000, checkpoint=lambda stage, *args: stages.append(stage))
    plan['cells'][0]['cell']['arm'] = 'proposed'
    plan['cells'][0]['representation'] = 'motif-11'
    plan['representations']['motif-11'] = {'binding': prepared.binding, 'input': 'feature_binding'}
    registered = register_plan(registered, plan, [('feature_binding', prepared.binding)])
    with start(registered) as run:
        rows, _ = execute_batch(run, populations, {'motif-11': prepared})
        assert rows[0]['status'] == 'complete'
        assert 'dictionary_complete' in stages and 'graph_complete' in stages
        path = run.admission.root/rows[0]['cell_record']
        record = json.loads(path.read_bytes())
        assert record['provenance']['dictionary_hash'] == prepared.dictionary.identity
        predictions = json.loads((path.parent/'predictions.json').read_bytes())
        assert compare_summary(record['metrics'], independent_classification(
            [r['y_true'] for r in predictions], [r['probability_up'] for r in predictions]))['passed']


def test_same_width_wrong_graph_representation_is_rejected(registered, monkeypatch):
    from types import SimpleNamespace
    import tradingagents.research.onchain_replication.run as module
    registered, populations, plan = setup(registered)
    plan['cells'][0]['cell']['arm'] = 'node2vec'
    plan['cells'][0]['representation'] = 'graph-11'
    binding = {'representation': 'watchyourstep', 'asset': 'ETH'}
    plan['representations']['graph-11'] = {'binding': binding, 'input': 'feature_binding'}
    registered = register_plan(registered, plan, [('feature_binding', binding)])
    monkeypatch.setattr(module, 'evaluate_cell', lambda *a, **kw: pytest.fail('wrong algorithm fitted'))
    with start(registered) as run, pytest.raises(ValueError, match='representation/asset'):
        execute_batch(run, populations, {'graph-11': SimpleNamespace(binding=binding)})


def test_published_representation_failure_preserves_independent_price_fit(registered):
    registered, populations, plan = setup(registered)
    plan['cells'][0]['cell']['arm'] = 'proposed'
    plan['cells'][0]['representation'] = 'motif-11'
    plan['representations']['motif-11'] = {'output': 'motif-binding.json', 'failure_output': 'motif-failed.json'}
    root, spec, _ = registered
    spec['experiments']['example-a']['outputs'] += ['motif-binding.json', 'motif-failed.json']
    registered = register_plan((root, spec, None), plan)
    with start(registered) as run:
        run.write_json('motif-failed.json', {'status': 'failed', 'representation': 'motif-11', 'reason': 'synthetic capacity refusal'})
        rows, _ = execute_batch(run, populations, {})
        assert [r['status'] for r in rows] == ['unavailable', 'complete', 'unavailable']
        assert rows[0]['attempts'] == [] and 'capacity refusal' in rows[0]['reason']


def test_batch_prediction_recovery_uses_completed_parent_fit_without_refitting(registered, monkeypatch):
    import copy
    from pathlib import Path
    from tests.research.test_lifecycle import api, commit
    import tradingagents.research.onchain_replication.evaluation as evaluation
    registered, populations, plan = setup(registered)
    root, spec, _ = registered
    with start(registered) as run:
        original, _ = execute_batch(run, populations, {})
    record = json.loads((root/original[0]['cell_record']).read_bytes())
    parent_predictions = json.loads((root/original[0]['cell_record']).with_name('predictions.json').read_bytes())
    completion = root/'research_artifacts/onchain_fit_cells'/digest(b'sum')/'example-a/complete.json'
    checkpoint = Path(json.loads(completion.read_bytes())['checkpoint'])
    child = copy.deepcopy(spec['experiments']['example-a'])
    child['parent'] = 'example-a'
    child['cells'] = ['sum']
    child_plan = copy.deepcopy(plan)
    child_plan['cells'] = [child_plan['cells'][0]]
    child_plan['cells'][0]['recovery'] = {'mode': 'prediction_only', 'checkpoint_input': 'parent_checkpoint',
        'completion_input': 'parent_completion', 'provenance_input': 'parent_provenance'}
    for name, value in [('child_plan', child_plan), ('parent_provenance', record['provenance'])]:
        path = root/(name+'.json')
        path.write_bytes(canonical_bytes(value))
        child['inputs'][name] = {'path': path.name, 'sha256': file_hash(path), 'dataset': 'sample'}
    child['inputs']['batch_plan'] = child['inputs'].pop('child_plan')
    for name, path in [('parent_checkpoint', checkpoint), ('parent_completion', completion)]:
        child['inputs'][name] = {'path': str(path.relative_to(root)), 'sha256': file_hash(path), 'dataset': 'sample'}
    spec['experiments']['example-b'] = child
    source = commit(root, spec)
    monkeypatch.setattr(evaluation, '_reserve', lambda *a, **kw: pytest.fail('completed model was refitted'))
    Run, _, _ = api()
    with Run.start(root=root, registration='registration.json', experiment='example-b', source=source) as run:
        rows, _ = execute_batch(run, populations, {})
        assert rows[0]['status'] == 'complete'
        recovered = json.loads((root/rows[0]['cell_record']).with_name('predictions.json').read_bytes())
        assert recovered == parent_predictions
    assert len(list((root/'research_artifacts/onchain_fit_cells'/digest(b'sum')).glob('*/claim.json'))) == 1
