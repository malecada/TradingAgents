import json

import pytest

from tests.research.test_lifecycle import registered, start
from tests.research.onchain_replication.test_run import setup, register_plan
from tests.research.onchain_replication.test_dataset import fixture
from tests.research.onchain_replication.test_feature_pipeline import configs
from tradingagents.research.onchain_replication.job_payload import population_record, population_from_record, execute_fit_payload
from tradingagents.research.onchain_replication.graph_store import save_graph
from tradingagents.research.onchain_replication.neighborhoods import graph_hash
from tradingagents.research.onchain_replication.registered_features import representation_descriptor
from tradingagents.research.onchain_replication.provenance import file_hash, canonical_bytes


def test_registered_population_roundtrip_and_payload_execution(registered):
    registered, populations, plan = setup(registered)
    record = population_record(*populations['whole'])
    restored = population_from_record(json.loads(canonical_bytes(record)))
    assert canonical_bytes(population_record(*restored)) == canonical_bytes(record)
    payload = {'population_inputs': {'whole': 'population'}, 'batch_plan_input': 'batch_plan', 'representation_jobs': {}}
    registered = register_plan(registered, plan, [('population', record), ('execution_job', {'kind': 'fit', 'payload': payload})])
    with start(registered) as run:
        rows, _ = execute_fit_payload(run, payload)
        assert [r['status'] for r in rows] == ['complete', 'complete', 'unavailable']
        with pytest.raises(ValueError, match='registration'):
            execute_fit_payload(run, {**payload, 'representation_jobs': {'unexpected': {}}})


@pytest.mark.parametrize('capacity,fault', [(1, None), (10*1024**2, None), (10*1024**2, 'labels'), (10*1024**2, 'descriptor')])
def test_producer_in_same_claim_publishes_dynamic_binding_or_visible_capacity_failure(registered, capacity, fault, monkeypatch):
    registered, populations, plan = setup(registered)
    root, spec, _ = registered
    graphs, _, fold, _ = fixture()
    examples, scaler = populations['whole']
    required = {h for row in (*examples.train, *examples.test) for h in row.graph_hashes}
    graphs = [g for g in graphs if graph_hash(g) in required]
    descriptor = representation_descriptor(graphs, examples, fold, 'gin', 11, configs())
    references = {}
    for i, graph in enumerate(graphs):
        path = save_graph(root/'graphs'/str(i), graph)
        name = 'graph_'+str(i)
        spec['experiments']['example-a']['inputs'][name] = {'path': str(path.relative_to(root)), 'sha256': file_hash(path), 'dataset': 'sample'}
        references[graph_hash(graph)] = {'input': name}
    producer = {'descriptor': descriptor, 'graphs': references, 'max_entries': 100000,
                'max_array_bytes': 1024**2, 'binding_output': 'gin-binding.json', 'journal_output': 'gin-journal.json'}
    plan['cells'][0]['cell']['arm'] = 'gin'
    plan['cells'][0]['representation'] = 'gin-11'
    plan['representations']['gin-11'] = {'output': 'gin-binding.json', 'failure_output': 'gin-failed.json'}
    spec['experiments']['example-a']['outputs'] += ['gin-binding.json', 'gin-journal.json', 'gin-failed.json']
    payload = {'population_inputs': {'whole': 'population'}, 'batch_plan_input': 'batch_plan',
        'representation_jobs': {'gin-11': {'operation': 'produce', 'descriptor': descriptor,
            'plan_input': 'representation_plan', 'producer': 'gin-11', 'population': 'whole',
            'max_graph_payload_bytes': capacity}}}
    extra = []
    if fault == 'labels':
        from dataclasses import replace
        from tradingagents.research.onchain_replication.evaluation import example_binding
        changed = replace(examples, test=(replace(examples.test[0], up=1-examples.test[0].up), *examples.test[1:]))
        plan['populations']['other'] = {**plan['populations']['whole'], 'binding': example_binding(changed, scaler), 'input': 'other_binding'}
        plan['cells'][1]['population'] = 'other'
        payload['population_inputs']['other'] = 'other_population'
        extra += [('other_binding', example_binding(changed, scaler)), ('other_population', population_record(changed, scaler))]
    elif fault == 'descriptor':
        descriptor['seed'] = 23
    registered = register_plan((root, spec, None), plan, [
        ('population', population_record(examples, scaler)),
        ('representation_plan', {'schema_version': 1, 'producers': {'gin-11': producer}}),
        ('execution_job', {'kind': 'fit', 'payload': payload}), *extra])
    with start(registered) as run:
        if fault:
            import tradingagents.research.onchain_replication.registered_features as features
            import tradingagents.research.onchain_replication.graph_store as store
            monkeypatch.setattr(features, 'prepare_registered_features', lambda *a, **kw: pytest.fail('invalid science reached representation fitting'))
            monkeypatch.setattr(store, 'load_graph', lambda *a, **kw: pytest.fail('invalid science reached graph loading'))
            with pytest.raises(ValueError, match='before fitting|frozen labels/splits'):
                execute_fit_payload(run, payload)
            assert not (root/'research_artifacts/onchain_representations').exists()
            return
        rows, _ = execute_fit_payload(run, payload)
        assert rows[0]['status'] == ('complete' if capacity > 1 else 'unavailable')
        assert rows[1]['status'] == 'complete'
        failure = json.loads((run.directory/'outputs/gin-failed.json').read_bytes())
        assert failure['status'] == ('complete' if capacity > 1 else 'failed')
        if capacity == 1:
            assert 'capacity' in rows[0]['reason']
            assert not (root/'research_artifacts/onchain_representations').exists()
        else:
            assert list((root/'research_artifacts/onchain_representations').glob('*/example-a/complete.json'))
