"""Registered graph mapping admission and lifetime, using synthetic inputs."""
import copy
import importlib
import json
from pathlib import Path

import numpy as np
import pytest

from tests.research.test_lifecycle import registered, start, commit, git
from tests.research.onchain_replication.test_run import setup as run_setup, register_plan
from tests.research.onchain_replication.test_dataset import fixture
from tests.research.onchain_replication.test_feature_pipeline import configs
from tradingagents.research.onchain_replication.feature_pipeline import prepare_features
from tradingagents.research.onchain_replication.graph_store import save_graph
from tradingagents.research.onchain_replication.neighborhoods import graph_hash
from tradingagents.research.onchain_replication.provenance import canonical_bytes, file_hash
from tradingagents.research.onchain_replication.registered_features import representation_descriptor, prepare_registered_features
from tradingagents.research.onchain_replication.job_payload import execute_fit_payload, population_record


POLICY = {'schema_version': 1, 'mode': 'mapped', 'max_graph_file_bytes': 10 * 1024**2, 'max_open_arrays': 1000}


def setup_job(registered, policy=None, payload_limit=10 * 1024**2):
    registered, populations, plan = run_setup(registered)
    root, spec, _ = registered
    graphs, _, fold, _ = fixture()
    examples, _ = populations['whole']
    config = configs()
    config['dictionary'].update(sample_count=2, size=2)
    required = {h for row in (*examples.train, *examples.test) for h in row.graph_hashes}
    graphs = [g for g in graphs if graph_hash(g) in required]
    descriptor = representation_descriptor(graphs, examples, fold, 'proposed', 11, config)
    references = {}
    manifests = []
    for i, graph in enumerate(graphs):
        path = save_graph(root / 'graphs' / str(i), graph)
        name = 'graph_' + str(i)
        spec['experiments']['example-a']['inputs'][name] = {'path': str(path.relative_to(root)), 'sha256': file_hash(path), 'dataset': 'sample'}
        h = graph_hash(graph)
        references[h] = {'input': name}
        manifests.append((path, file_hash(path), h))
    producer = {'descriptor': descriptor, 'graphs': references, 'max_entries': 100000,
                'max_array_bytes': 1024**2, 'binding_output': 'proposed-binding.json',
                'journal_output': 'proposed-journal.json', 'graph_residency_input': 'graph_policy'}
    plan['cells'][0]['cell']['arm'] = 'proposed'
    plan['cells'][0]['representation'] = 'proposed-11'
    plan['representations']['proposed-11'] = {'output': 'proposed-binding.json', 'failure_output': 'proposed-failed.json'}
    spec['experiments']['example-a']['outputs'] += ['proposed-binding.json', 'proposed-journal.json', 'proposed-failed.json']
    payload = {'population_inputs': {'whole': 'population'}, 'batch_plan_input': 'batch_plan',
               'representation_jobs': {'proposed-11': {'operation': 'produce', 'descriptor': descriptor,
                   'plan_input': 'representation_plan', 'producer': 'proposed-11', 'population': 'whole',
                   'max_graph_payload_bytes': payload_limit, 'graph_residency_input': 'graph_policy'}}}
    if callable(policy): policy = policy(manifests)
    registration = register_plan((root, spec, None), plan, [
        ('population', population_record(*populations['whole'])),
        ('representation_plan', {'schema_version': 1, 'producers': {'proposed-11': producer}}),
        ('graph_policy', POLICY if policy is None else policy),
        ('execution_job', {'kind': 'fit', 'payload': payload})])
    return registration, payload, (graphs, examples, fold, 'proposed', 11, config), manifests


def test_real_registered_job_maps_graphs_and_closes_before_batch(registered, monkeypatch):
    import tradingagents.research.onchain_replication.run as runner
    registration, payload, args, _ = setup_job(registered)
    eager = prepare_features(*args, max_entries=100000, checkpoint=lambda *a: None)
    opened = []
    load = np.load
    def tracked(path, **kwargs):
        value = load(path, **kwargs)
        if 'graphs' in Path(path).parts:
            assert isinstance(value, np.memmap)
            opened.append(value._mmap)
        return value
    monkeypatch.setattr(np, 'load', tracked)
    def batch(run, populations, prepared, **kwargs):
        assert opened and all(m.closed for m in opened)
        result = prepared['proposed-11']
        assert result.binding == eager.binding
        assert result.dictionary.identity == eager.dictionary.identity
        for h in eager.features:
            np.testing.assert_array_equal(result.features[h]['mcm'], eager.features[h]['mcm'])
        return prepared
    monkeypatch.setattr(runner, 'execute_batch', batch)
    with start(registration) as run:
        execute_fit_payload(run, payload)
        claim, = (registration[0] / 'research_artifacts/onchain_representations').glob('*/example-a/claim.json')
        record = json.loads(claim.read_bytes())
        assert record['graph_residency_input'] == 'graph_policy'
        assert record['graph_residency_policy_sha256'] == run.admission.inputs['graph_policy']['sha256']


@pytest.mark.parametrize('fault', ['schema', 'bool_limit', 'mode', 'extra', 'mismatch', 'reuse', 'later'])
def test_all_graph_policies_preflight_before_population(registered, fault, monkeypatch):
    import tradingagents.research.onchain_replication.population_assembly as assembly
    policy = dict(POLICY)
    if fault == 'schema': policy['schema_version'] = True
    if fault == 'bool_limit': policy['max_open_arrays'] = True
    if fault == 'mode': policy['mode'] = 'eager'
    if fault == 'extra': policy['path'] = '/tmp/foreign'
    if fault == 'later': policy['max_graph_file_bytes'] = 0
    job = {'operation': 'reuse' if fault == 'reuse' else 'produce', 'graph_residency_input': 'graph',
           'plan_input': 'plan', 'producer': 'p', 'descriptor': {'arm': 'proposed'}}
    jobs = {'p': job}
    if fault == 'later': jobs = {'earlier': {**job, 'graph_residency_input': 'valid', 'producer': 'earlier'}, **jobs}
    payload = {'population_inputs': {'whole': {'producer_input': 'population'}}, 'representation_jobs': jobs}
    values = {'execution_job': {'kind': 'fit', 'payload': payload}, 'graph': policy, 'valid': POLICY,
              'plan': {'producers': {'p': {'graph_residency_input': 'other' if fault == 'mismatch' else 'graph'},
                                     'earlier': {'graph_residency_input': 'valid'}}}}
    root, spec, _ = registered
    for name, value in values.items():
        path = root / (name + '.json')
        path.write_bytes(canonical_bytes(value))
        spec['experiments']['example-a']['inputs'][name] = {
            'path': path.name, 'sha256': file_hash(path), 'dataset': 'sample'}
    git(root, 'add', *(name + '.json' for name in values))
    source = commit(root, spec)
    monkeypatch.setattr(assembly, 'produce_registered_population', lambda *a: pytest.fail('population before policy admission'))
    with start((root, spec, source)) as run:
        with pytest.raises(ValueError, match='graph'): execute_fit_payload(run, payload)


@pytest.mark.parametrize('fault', ['bytes', 'arrays', 'late_file', 'aggregate_bytes', 'aggregate_arrays', 'legacy_limit'])
def test_whole_population_admission_precedes_first_map(registered, monkeypatch, fault):
    import tradingagents.research.onchain_replication.run as runner
    policy = dict(POLICY)
    if fault == 'bytes': policy['max_graph_file_bytes'] = 1
    if fault == 'arrays': policy['max_open_arrays'] = 1
    if fault in {'aggregate_bytes', 'aggregate_arrays'}:
        def policy(manifests):
            records = [json.loads(p.read_bytes())['arrays'] for p, _, _ in manifests]
            sizes = [sum(x['bytes'] for x in r.values()) for r in records]
            counts = [len(r) for r in records]
            assert sum(sizes) > max(sizes) and sum(counts) > max(counts)
            return {**POLICY, ('max_graph_file_bytes' if fault == 'aggregate_bytes' else 'max_open_arrays'):
                    max(sizes) if fault == 'aggregate_bytes' else max(counts)}
    registration, payload, _, manifests = setup_job(registered, policy,
        payload_limit=1 if fault == 'legacy_limit' else 10 * 1024**2)
    if fault == 'late_file':
        (manifests[-1][0].parent / 'node_features.npy').write_bytes(b'corrupted')
    monkeypatch.setattr(np, 'load', lambda *a, **k: pytest.fail('invalid population reached first map'))
    monkeypatch.setattr(runner, 'execute_batch', lambda run, populations, prepared, **kw: prepared)
    with start(registration) as run:
        assert execute_fit_payload(run, payload) == {}
        record = json.loads((run.directory / 'outputs/proposed-failed.json').read_bytes())
        assert record['status'] == 'failed'
        assert not (registration[0] / 'research_artifacts/onchain_representations').exists()


@pytest.mark.parametrize('fault', ['closed', 'eager', 'omitted', 'foreign'])
def test_direct_producer_requires_live_bound_population_before_hashing(registered, monkeypatch, fault):
    module = importlib.import_module('tradingagents.research.onchain_replication.graph_residency')
    import tradingagents.research.onchain_replication.registered_features as features
    registration, _, args, manifests = setup_job(registered)
    with start(registration) as run:
        with module.open_graph_population(manifests, POLICY) as lease:
            graphs = args[0] if fault == 'eager' else lease
            if fault == 'closed':
                pass
            else:
                if fault == 'foreign':
                    # Same numerical graphs, wrong admitted source path identity.
                    from dataclasses import replace
                    graphs = replace(lease, manifests=tuple((str(p)+'-other', sha, h) for p, sha, h in lease.manifests))
                monkeypatch.setattr(features, 'representation_descriptor', lambda *a: pytest.fail('invalid mapped ownership reached hash'))
                with pytest.raises(ValueError, match='graph|population'):
                    prepare_registered_features(run, 'proposed-11', graphs, *args[1:], plan_input='representation_plan',
                        max_entries=100000, max_array_bytes=1024**2,
                        graph_residency_input=None if fault == 'omitted' else 'graph_policy')
        if fault == 'closed':
            monkeypatch.setattr(features, 'representation_descriptor', lambda *a: pytest.fail('closed maps reached hash'))
            with pytest.raises(ValueError, match='graph|population'):
                prepare_registered_features(run, 'proposed-11', lease, *args[1:], plan_input='representation_plan',
                    max_entries=100000, max_array_bytes=1024**2, graph_residency_input='graph_policy')
        assert not (registration[0] / 'research_artifacts/onchain_representations').exists()


def test_failed_numerical_producer_closes_maps_and_preserves_journal(registered, monkeypatch):
    import tradingagents.research.onchain_replication.registered_features as features
    import tradingagents.research.onchain_replication.run as runner
    registration, payload, args, manifests = setup_job(registered)
    oracle = prepare_features(*args, max_entries=100000, checkpoint=lambda *a: None)
    opened = []
    original = features.prepare_features
    def interrupted(graphs, *args, checkpoint, **kwargs):
        opened.extend(g.node_features._mmap for g in graphs)
        def save(stage, context, data):
            checkpoint(stage, context, data)
            if stage == 'samples_complete': raise InterruptedError('after durable samples')
        return original(graphs, *args, checkpoint=save, **kwargs)
    monkeypatch.setattr(features, 'prepare_features', interrupted)
    def batch(run, populations, prepared, **kwargs):
        assert opened and all(m.closed for m in opened)
        assert prepared == {}
    monkeypatch.setattr(runner, 'execute_batch', batch)
    with start(registration) as run:
        execute_fit_payload(run, payload)
        failed, = (registration[0] / 'research_artifacts/onchain_representations').glob('*/example-a/failed.json')
        assert json.loads(failed.read_bytes())['events'][0]['stage'] == 'samples_complete'
    # A new registered owner may change execution allowance, never sample again.
    root, spec, _ = registration
    preserved = file_hash(failed)
    child = copy.deepcopy(spec['experiments']['example-a'])
    child['parent'] = 'example-a'
    child['inputs']['prior'] = {'path': str(failed.relative_to(root)), 'sha256': preserved, 'dataset': 'sample'}
    policy = {**POLICY, 'max_open_arrays': POLICY['max_open_arrays'] + 1}
    policy_path = root / 'graph-policy-successor.json'
    policy_path.write_bytes(canonical_bytes(policy))
    child['inputs']['graph_policy'] = {'path': str(policy_path.relative_to(root)), 'sha256': file_hash(policy_path), 'dataset': 'sample'}
    spec['experiments']['example-b'] = child
    source = commit(root, spec)
    monkeypatch.setattr(features, 'prepare_features', original)
    import tradingagents.research.onchain_replication.feature_pipeline as pipeline
    module = importlib.import_module('tradingagents.research.onchain_replication.graph_residency')
    monkeypatch.setattr(pipeline, 'sample_neighborhoods', lambda *a, **k: pytest.fail('saved samples were recomputed'))
    with start((root, spec, source), experiment='example-b') as run:
        with module.open_graph_population(manifests, policy) as lease:
            result, _ = prepare_registered_features(run, 'proposed-11', lease, *args[1:],
                plan_input='representation_plan', max_entries=100000, max_array_bytes=1024**2,
                graph_residency_input='graph_policy', continuation_input='prior')
        assert result.binding == oracle.binding
        assert result.dictionary.identity == oracle.dictionary.identity
    assert file_hash(failed) == preserved


def test_foreign_mappings_cannot_be_relabelled_as_admitted_lease(registered, monkeypatch):
    from dataclasses import replace
    module = importlib.import_module('tradingagents.research.onchain_replication.graph_residency')
    import tradingagents.research.onchain_replication.registered_features as features
    registration, _, args, manifests = setup_job(registered)
    foreign = []
    for i, graph in enumerate(args[0]):
        path = save_graph(registration[0] / 'foreign' / str(i), graph)
        foreign.append((path, file_hash(path), graph_hash(graph)))
    admitted = tuple((str(p.resolve()), sha, h) for p, sha, h in manifests)
    with start(registration) as run:
        with module.open_graph_population(foreign, POLICY) as lease:
            forged = replace(lease, manifests=admitted)
            reached_hash = []
            def mark_hash(*args):
                reached_hash.append(True)
                raise ValueError('population hash sentinel')
            monkeypatch.setattr(features, 'representation_descriptor', mark_hash)
            with pytest.raises(ValueError, match='population|ownership'):
                prepare_registered_features(run, 'proposed-11', forged, *args[1:],
                    plan_input='representation_plan', max_entries=100000,
                    max_array_bytes=1024**2, graph_residency_input='graph_policy')
        assert not reached_hash, 'foreign maps reached descriptor hashing'


@pytest.mark.parametrize('partial', [False, True])
def test_unclosed_maps_abort_job_before_model_batch(registered, monkeypatch, partial):
    import tradingagents.research.onchain_replication.mapped_graph as mapped
    import tradingagents.research.onchain_replication.run as runner
    module = importlib.import_module('tradingagents.research.onchain_replication.graph_residency')
    registration, payload, _, _ = setup_job(registered)
    leaked = []
    monkeypatch.setattr(mapped, '_close_maps', lambda maps, **kw: leaked.extend(maps))
    monkeypatch.setattr(runner, 'execute_batch', lambda *a, **k: pytest.fail('fit after unresolved cleanup'))
    if partial:
        load = np.load
        count = 0
        def fail_second(path, **kwargs):
            nonlocal count
            count += 1
            if count == 2: raise OSError('partial graph opening failed')
            return load(path, **kwargs)
        monkeypatch.setattr(np, 'load', fail_second)
    try:
        with start(registration) as run:
            with pytest.raises(module.GraphPopulationCleanupError, match='fitting forbidden') as error:
                execute_fit_payload(run, payload)
            assert leaked and any(not m.closed for m in leaked)
            if partial:
                assert isinstance(error.value.__cause__, OSError)
            else:
                assert list((registration[0] / 'research_artifacts/onchain_representations').glob('*/example-a/complete.json'))
    finally:
        for mapping in leaked:
            if not mapping.closed: mapping.close()


def test_admitted_graph_policy_byte_drift_is_refused(registered, monkeypatch):
    import tradingagents.research.onchain_replication.population_assembly as assembly
    registration, payload, _, _ = setup_job(registered)
    with start(registration) as run:
        info = run.admission.inputs['graph_policy']
        (registration[0] / info['path']).write_bytes(canonical_bytes({**POLICY, 'max_open_arrays': 1001}))
        monkeypatch.setattr(assembly, 'produce_registered_population', lambda *a: pytest.fail('policy drift reached population'))
        with pytest.raises(ValueError): execute_fit_payload(run, payload)
        assert not (registration[0] / 'research_artifacts/onchain_representations').exists()


def test_closed_graph_metadata_repr_is_safe_in_error_reporting(tmp_path):
    import subprocess
    import sys
    # Isolate the old unsafe NumPy repr in a bounded child, with core dumps off.
    script = '''
import resource,sys,json
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
from tests.research.onchain_replication.test_subsets import fixture
from tradingagents.research.onchain_replication.graph_store import save_graph,open_mapped_graph
from tradingagents.research.onchain_replication.provenance import file_hash
path=save_graph(Path(sys.argv[1])/'graph',fixture())
size=sum(x['bytes'] for x in json.loads(path.read_bytes())['arrays'].values())
with open_mapped_graph(path,file_hash(path),max_mapped_bytes=size) as graph: pass
print(repr(graph))
'''
    result = subprocess.run([sys.executable, '-B', '-c', script, str(tmp_path)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, f'metadata repr child failed: {result.returncode}'
    assert 'MappedGraphSnapshot' in result.stdout
