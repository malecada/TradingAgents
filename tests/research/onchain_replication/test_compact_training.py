"""Actual compact training population joins; no sampling or financial fitting."""
import copy
from dataclasses import asdict, replace
import pytest
from tests.research.onchain_replication import test_first_owner as first
from tests.research.onchain_replication.test_compact_policy import candidate
from tests.research.onchain_replication.test_feature_pipeline import population, configs
from tradingagents.research.onchain_replication import compact_owner, matching_pair
from tradingagents.research.onchain_replication.registered_features import representation_descriptor
from tradingagents.research.onchain_replication.neighborhoods import graph_hash
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest, thaw, utc
from tradingagents.research.onchain_replication.calendar import stamp


@pytest.fixture
def admitted(request):
    helper = first.Tests(); option = getattr(request, 'param', 'valid')
    graphs, fold, examples = population(); config = configs()
    if option == 'duplicate_week':
        duplicate = replace(graphs[0], start_utc=stamp(graphs[0].start_utc))
        assert duplicate.start_utc != graphs[0].start_utc
        graphs = (*graphs, duplicate)
    config['dictionary'].update(sample_count=3, size=2, partition_threshold=4, partition_size=4)
    if option == 'future':
        row = replace(examples.train[0], max_input_available_at=fold.test_end)
        rows = (row, *examples.train[1:])
        examples = replace(examples, train=rows, train_hash=digest(canonical_bytes([asdict(x) for x in rows])))
    def prepare(t):
        p = candidate()
        t.policy['limits'] = p['pair']; t.input('pair_policy', t.policy)
        t.input('compact_policy', {'schema_version': 1, 'backend': p['backend'],
            'stage_policy': p, 'max_workflow_retained_logical_bytes': 30000000})
        control = {'schema_version': 1, 'example_manifest_sha256': digest(canonical_bytes({
            **vars(examples), 'train': [asdict(x) for x in examples.train],
            'test': [asdict(x) for x in examples.test]}))}
        if option == 'schema': control['schema_version'] = True
        t.input('compact_training', control)
        descriptor = representation_descriptor(graphs, examples, fold, 'proposed', 11, config)
        descriptor.update(pair_execution={'backend': matching_pair.BACKEND,
            'policy_sha256': t.exp['inputs']['pair_policy']['sha256']},
            compact_execution={'backend': p['backend'], 'policy_sha256': t.exp['inputs']['compact_policy']['sha256']},
            compact_training={'input': 'compact_training', 'sha256': t.exp['inputs']['compact_training']['sha256']})
        t.descriptor = descriptor
        refs = {}
        for i, g in enumerate(graphs):
            h = graph_hash(g); name = 'graph-' + str(i)
            t.input(name, {'graph_hash': 'f' * 64 if option == 'manifest' and i == 0 else h})
            refs[h] = {'input': name}
        for item in (t.item, t.execution['payload']['representation_jobs']['r']):
            item.update(descriptor=descriptor, native_backend=p['backend'],
                compact_policy_input='compact_policy', compact_training_input='compact_training', graphs=refs)
        if option == 'route': t.item['compact_training_input'] = 'sample'
    t = helper.fixture(prepare); journal, bound = helper.open(t)
    owner = compact_owner.attach(bound, policy_input='compact_policy')
    try: yield owner, dict(graphs=graphs, examples=examples, fold=fold, seed=11, configs=config), t
    finally: helper.doCleanups()


def admit(owner, args):
    from tradingagents.research.onchain_replication.compact_training import admit
    return admit(owner, input_name='compact_training', **args)


def test_actual_training_population_is_bound_without_sampling_or_pair_creation(admitted):
    owner, args, t = admitted
    route = admit(owner, args); route.check(); route.lease()
    expected = sorted((g for g in args['graphs'] if utc(g.start_utc) >= utc(args['fold'].train_start)
        and utc(g.available_at) < utc(args['fold'].train_end)), key=lambda g: (g.start_utc, g.asset, graph_hash(g)))
    assert route.training_hashes == tuple(map(graph_hash, expected))
    assert tuple(route.training_graphs) == tuple(expected)
    assert thaw(route.settings) == args['configs']['dictionary'] | {
        'train_start': args['fold'].train_start, 'train_end': args['fold'].train_end}
    assert route.seed == 11 and route.owner is owner
    assert route.record['sample_provenance_admitted'] is False
    assert set(p.name for p in owner.root.iterdir()) == {'owner.json'}


@pytest.mark.parametrize('admitted', ['route', 'schema', 'manifest'], indirect=True)
def test_metadata_refusal_precedes_graph_iteration(admitted):
    owner, args, t = admitted
    def forbidden():
        raise AssertionError('graphs read before metadata admission')
        yield
    with pytest.raises(ValueError): admit(owner, args | {'graphs': forbidden()})


def test_actual_graph_examples_seed_config_and_fold_cannot_use_registered_descriptor(admitted):
    owner, args, t = admitted
    changed = replace(args['graphs'][0], node_features=args['graphs'][0].node_features + 1)
    cfg = copy.deepcopy(args['configs']); cfg['matching']['max_iterations'] += 1
    rows = tuple(reversed(args['examples'].test))
    changed_examples = replace(args['examples'], test=rows,
        test_mask_hash=digest(canonical_bytes([r.decision_at for r in rows])))
    for edits in ({'graphs': (changed, *args['graphs'][1:])}, {'graphs': args['graphs'][1:]},
                  {'seed': 12}, {'configs': cfg}, {'examples': changed_examples},
                  {'fold': replace(args['fold'], train_end='2023-12-01T00:00:00Z')}):
        with pytest.raises(ValueError): admit(owner, args | edits)


@pytest.mark.parametrize('admitted', ['future'], indirect=True)
def test_even_registered_future_input_is_refused(admitted):
    owner, args, t = admitted
    with pytest.raises(ValueError, match='future'): admit(owner, args)


def test_route_views_cannot_redirect_owner_or_training_inputs_and_terminal_owner_revokes(admitted):
    owner, args, t = admitted; route = admit(owner, args)
    for name, value in [('owner', object()), ('graphs', ()), ('training_graphs', ()), ('settings', {}), ('seed', 12)]:
        with pytest.raises((AttributeError, TypeError)): setattr(route, name, value)
    t.run.fail('synthetic revoked training route')
    with pytest.raises(ValueError): route.lease()


def test_registered_metadata_drift_is_refused_at_boundary(admitted):
    owner, args, t = admitted; route = admit(owner, args)
    (t.root / 'compact_training.json').write_bytes(b'{}')
    with pytest.raises(ValueError): route.check()


@pytest.mark.parametrize('field', ['graph', 'examples'])
def test_full_boundary_rechecks_resident_input_drift(admitted, field):
    owner, args, t = admitted; route = admit(owner, args)
    if field == 'graph':
        g = args['graphs'][0]
        object.__setattr__(g, 'node_features', g.node_features + 1)
    else:
        object.__setattr__(args['examples'], 'test', tuple(reversed(args['examples'].test)))
    with pytest.raises(ValueError): route.check()


def test_training_admission_precedes_stages_but_existing_route_remains_checkable(admitted):
    owner, args, t = admitted; route = admit(owner, args)
    owner.begin('dictionary', workload_sha256='a' * 64, pairs=0)
    route.check()
    with pytest.raises(ValueError, match='precede'): admit(owner, args)


def test_last_owner_callback_cannot_change_route_views(admitted, monkeypatch):
    owner, args, t = admitted; route = admit(owner, args)
    original = owner.lease
    def changed():
        original(); route._seed = 12
    monkeypatch.setattr(owner, 'lease', changed)
    with pytest.raises(ValueError, match='route changed'): route.lease()


@pytest.mark.parametrize('admitted', ['duplicate_week'], indirect=True)
def test_registered_equivalent_timestamp_week_cannot_duplicate_training_exposure(admitted):
    owner, args, t = admitted
    assert len({g.start_utc for g in args['graphs']}) == len(args['graphs'])
    assert len({utc(g.start_utc) for g in args['graphs']}) == len(args['graphs']) - 1
    with pytest.raises(ValueError, match='duplicate weekly'): admit(owner, args)
