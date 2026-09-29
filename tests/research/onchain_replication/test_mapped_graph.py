"""Synthetic mapped graph ownership, identity and consumer regressions."""
from contextlib import ExitStack
from dataclasses import replace
import hashlib
import json

import numpy as np
import pytest

from tests.research.onchain_replication.test_subsets import fixture
from tradingagents.research.onchain_replication import graph_store as store
from tradingagents.research.onchain_replication.contracts import graph_to_dict
from tradingagents.research.onchain_replication.neighborhoods import graph_hash
from tradingagents.research.onchain_replication.provenance import canonical_bytes, file_hash


def saved(tmp_path, graph=None):
    graph = fixture() if graph is None else graph
    path = store.save_graph(tmp_path / 'graph', graph)
    manifest = json.loads(path.read_bytes())
    return graph, path, sum(x['bytes'] for x in manifest['arrays'].values())


def test_mapped_storage_preserves_exact_graph_and_closes_owned_maps(tmp_path):
    original = replace(fixture(), node_ids=('a"', 'b\\', 'c\n', 'é'))
    graph, path, size = saved(tmp_path, original)
    expected = hashlib.sha256(canonical_bytes(graph_to_dict(graph))).hexdigest()
    with store.open_mapped_graph(path, file_hash(path), max_mapped_bytes=size) as mapped:
        assert graph_hash(mapped) == expected
        assert canonical_bytes(graph_to_dict(mapped)) == canonical_bytes(graph_to_dict(graph))
        arrays = [getattr(mapped, n) for n in
                  ('node_ids', 'node_features', 'edge_index', 'edge_features', 'edge_aggregates')]
        for array in arrays:
            assert isinstance(array, np.memmap) and array.mode == 'r'
            with pytest.raises(ValueError):
                array.setflags(write=True)
        mappings = [a._mmap for a in arrays]
        assert all(not m.closed for m in mappings)
    assert all(m.closed for m in mappings)


@pytest.mark.parametrize('limit', [0, -1, True, 1])
def test_budget_refused_before_any_mapping(tmp_path, monkeypatch, limit):
    _, path, _ = saved(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail('budget refusal must precede mapping')
    monkeypatch.setattr(store.np, 'load', forbidden)
    with pytest.raises(ValueError, match='bound|budget'):
        with store.open_mapped_graph(path, file_hash(path), max_mapped_bytes=limit):
            pytest.fail('invalid mapping budget was admitted')


@pytest.mark.parametrize('fault', ['bytes', 'boolean_bytes', 'member_hash', 'manifest_hash', 'symlink', 'missing'])
def test_bad_manifest_or_member_refused_before_mapping(tmp_path, monkeypatch, fault):
    _, path, size = saved(tmp_path)
    data = json.loads(path.read_bytes())
    if fault == 'bytes':
        data['arrays']['edge_features']['bytes'] -= 1
    elif fault == 'boolean_bytes':
        data['arrays']['edge_features']['bytes'] = True
    elif fault == 'member_hash':
        data['arrays']['edge_features']['sha256'] = '0' * 64
    elif fault == 'missing':
        del data['arrays']['edge_features']
    elif fault == 'symlink':
        member = path.parent / 'edge_features.npy'
        target = tmp_path / 'retained.npy'
        member.rename(target)
        member.symlink_to(target)
    path.write_bytes(canonical_bytes(data))
    expected = '0' * 64 if fault == 'manifest_hash' else file_hash(path)
    monkeypatch.setattr(store.np, 'load', lambda *a, **k: pytest.fail('invalid files reached mapping'))
    with pytest.raises(ValueError):
        with store.open_mapped_graph(path, expected, max_mapped_bytes=size):
            pytest.fail('invalid graph files admitted')


@pytest.mark.parametrize('fault', ['unsorted', 'duplicate', 'empty_id', 'nonfinite', 'identity', 'consumer'])
def test_failed_validation_or_consumer_closes_all_maps(tmp_path, monkeypatch, fault):
    graph, path, size = saved(tmp_path)
    data = json.loads(path.read_bytes())
    if fault in {'unsorted', 'duplicate', 'empty_id'}:
        ids = {'unsorted': ['b', 'a', 'c', 'd'], 'duplicate': ['a', 'a', 'c', 'd'],
               'empty_id': ['', 'b', 'c', 'd']}[fault]
        np.save(path.parent / 'node_ids.npy', np.asarray(ids), allow_pickle=False)
        data['arrays']['node_ids']['sha256'] = file_hash(path.parent / 'node_ids.npy')
    elif fault == 'nonfinite':
        values = np.array(graph.node_features)
        values[0, 0] = np.nan
        np.save(path.parent / 'node_features.npy', values, allow_pickle=False)
        data['arrays']['node_features']['sha256'] = file_hash(path.parent / 'node_features.npy')
    elif fault == 'identity':
        data['graph_hash'] = '0' * 64
    path.write_bytes(canonical_bytes(data))
    opened = []
    original_load = store.np.load
    def tracked(*args, **kwargs):
        array = original_load(*args, **kwargs)
        opened.append(array._mmap)
        return array
    monkeypatch.setattr(store.np, 'load', tracked)
    with pytest.raises(ValueError):
        with store.open_mapped_graph(path, file_hash(path), max_mapped_bytes=size):
            if fault == 'consumer':
                raise ValueError('interrupted consumer')
            pytest.fail('invalid graph accepted')
    assert opened and all(m.closed for m in opened)


def test_default_snapshot_stays_detached_and_accepts_unsorted_ids(tmp_path):
    original, path, _ = saved(tmp_path, replace(fixture(), node_ids=('b', 'a', 'c', 'd')))
    graph = store.load_graph(path, file_hash(path))
    assert graph.node_ids == original.node_ids
    assert not isinstance(graph.node_features, np.memmap)
    values = np.load(path.parent / 'node_features.npy', mmap_mode='r+')
    values[0, 0] = 999
    values.flush()
    assert graph.node_features[0, 0] == original.node_features[0, 0]
    with pytest.raises(ValueError):
        graph.node_features.setflags(write=True)


def test_mapped_pipeline_matches_eager_dictionary_samples_mcm_and_binding(tmp_path):
    from tests.research.onchain_replication.test_feature_pipeline import population, configs
    from tradingagents.research.onchain_replication.feature_pipeline import prepare_features
    graphs, fold, examples = population()
    config = configs()
    config['dictionary'] = {**config['dictionary'], 'sample_count': 2, 'size': 2}
    events = []
    eager = prepare_features(graphs, examples, fold, 'proposed', 11, config,
        max_entries=100000, checkpoint=lambda *args: events.append(args))
    with ExitStack() as stack:
        mapped = []
        for i, graph in enumerate(graphs):
            path = store.save_graph(tmp_path / str(i), graph)
            size = sum(v['bytes'] for v in json.loads(path.read_bytes())['arrays'].values())
            mapped.append(stack.enter_context(store.open_mapped_graph(
                path, file_hash(path), max_mapped_bytes=size)))
        actual_events = []
        result = prepare_features(mapped, examples, fold, 'proposed', 11, config,
            max_entries=100000, checkpoint=lambda *args: actual_events.append(args))
        assert result.binding == eager.binding
        assert result.dictionary.identity == eager.dictionary.identity
        a = next(e for e in events if e[0] == 'samples_complete')
        b = next(e for e in actual_events if e[0] == 'samples_complete')
        assert canonical_bytes(a) == canonical_bytes(b)
    # Fixed features and local dictionary slices must survive raw-map closure.
    for identity in eager.features:
        for key in eager.features[identity]:
            np.testing.assert_array_equal(result.features[identity][key].numpy(),
                                          eager.features[identity][key].numpy())
    for left, right in zip(result.dictionary.representatives, eager.dictionary.representatives):
        np.testing.assert_array_equal(left.node_features, right.node_features)


def test_mapped_id_validation_and_hash_do_not_materialize_full_python_ids(tmp_path, monkeypatch):
    import tradingagents.research.onchain_replication.contracts as contracts
    from tradingagents.research.onchain_replication.neighborhoods import node_order_hash
    ids = tuple(f'node-{i:06}' for i in range(65538))
    graph = replace(fixture(), node_ids=ids, node_features=np.zeros((len(ids), 4)),
                    edge_index=np.empty((2, 0), dtype=np.int64),
                    edge_features=np.empty((0, 2)), edge_aggregates=None)
    _, path, size = saved(tmp_path, graph)
    expected = hashlib.sha256(canonical_bytes(ids)).hexdigest()
    monkeypatch.setattr(contracts, 'sorted', lambda *a, **k: pytest.fail('full ID sort'), raising=False)
    with store.open_mapped_graph(path, file_hash(path), max_mapped_bytes=size) as mapped:
        contracts.validate_graph(mapped)
        assert node_order_hash(mapped.node_ids) == expected
        assert node_order_hash(()) == hashlib.sha256(b'[]').hexdigest()
    # A duplicate spanning the validator's block boundary must still fail.
    raw_ids = np.asarray(ids)
    raw_ids[65536] = raw_ids[65535]
    np.save(path.parent / 'node_ids.npy', raw_ids, allow_pickle=False)
    manifest = json.loads(path.read_bytes())
    manifest['arrays']['node_ids']['sha256'] = file_hash(path.parent / 'node_ids.npy')
    path.write_bytes(canonical_bytes(manifest))
    with pytest.raises(ValueError, match='sorted unique'):
        with store.open_mapped_graph(path, file_hash(path), max_mapped_bytes=size):
            pytest.fail('cross-block duplicate admitted')


@pytest.mark.parametrize('dtype', ['>f8', '<f8'])
def test_storage_layout_and_byteorder_do_not_change_canonical_identity(tmp_path, dtype):
    graph = fixture()
    graph = replace(graph, node_features=np.asarray(graph.node_features, dtype=dtype),
                    edge_aggregates=None)
    _, path, _ = saved(tmp_path, graph)
    np.save(path.parent / 'node_features.npy', np.asfortranarray(graph.node_features), allow_pickle=False)
    manifest = json.loads(path.read_bytes())
    member = path.parent / 'node_features.npy'
    manifest['arrays']['node_features'].update(sha256=file_hash(member), bytes=member.stat().st_size)
    path.write_bytes(canonical_bytes(manifest))
    size = sum(v['bytes'] for v in manifest['arrays'].values())
    with store.open_mapped_graph(path, file_hash(path), max_mapped_bytes=size) as mapped:
        assert graph_hash(mapped) == graph_hash(graph)
        assert mapped.node_features.flags.f_contiguous


@pytest.mark.parametrize('fault', ['ids_bytes', 'ids_2d', 'features_complex', 'trailing', 'not_npy'])
def test_wrong_array_type_or_extent_is_rejected(tmp_path, fault):
    _, path, _ = saved(tmp_path)
    name = 'node_ids' if fault.startswith('ids') else 'node_features'
    member = path.parent / (name + '.npy')
    if fault == 'ids_bytes':
        np.save(member, np.asarray(['a', 'b', 'c', 'd'], dtype='S1'))
    elif fault == 'ids_2d':
        np.save(member, np.asarray([['a', 'b', 'c', 'd']]))
    elif fault == 'features_complex':
        np.save(member, np.ones((4, 4), dtype=np.complex128))
    elif fault == 'trailing':
        with member.open('ab') as f:
            f.write(b'unaccounted trailing bytes')
    else:
        with member.open('wb') as f:
            np.savez(f, data=np.zeros((4, 4)))
    manifest = json.loads(path.read_bytes())
    manifest['arrays'][name].update(sha256=file_hash(member), bytes=member.stat().st_size)
    path.write_bytes(canonical_bytes(manifest))
    with pytest.raises(ValueError):
        with store.open_mapped_graph(path, file_hash(path),
                max_mapped_bytes=sum(v['bytes'] for v in manifest['arrays'].values())):
            pytest.fail('invalid stored array admitted')


def test_non_npy_rejected_before_numpy_loader_opens_archive(tmp_path, monkeypatch):
    _, path, _ = saved(tmp_path)
    member = path.parent / 'node_features.npy'
    with member.open('wb') as f:
        np.savez(f, data=np.zeros((4, 4)))
    manifest = json.loads(path.read_bytes())
    manifest['arrays']['node_features'].update(sha256=file_hash(member), bytes=member.stat().st_size)
    path.write_bytes(canonical_bytes(manifest))
    monkeypatch.setattr(store.np, 'load', lambda *a, **k: pytest.fail('NPZ reached numpy loader'))
    with pytest.raises(ValueError):
        with store.open_mapped_graph(path, file_hash(path),
                max_mapped_bytes=sum(v['bytes'] for v in manifest['arrays'].values())):
            pytest.fail('non-NPY accepted')


def test_late_mapping_failure_closes_previously_opened_arrays(tmp_path, monkeypatch):
    _, path, size = saved(tmp_path)
    real_load = store.np.load
    opened = []
    def failing(*args, **kwargs):
        if len(opened) == 2:
            raise OSError('third map failed')
        value = real_load(*args, **kwargs)
        opened.append(value._mmap)
        return value
    monkeypatch.setattr(store.np, 'load', failing)
    with pytest.raises(OSError, match='third map'):
        with store.open_mapped_graph(path, file_hash(path), max_mapped_bytes=size):
            pytest.fail('failed mapping admitted')
    assert len(opened) == 2 and all(m.closed for m in opened)


@pytest.mark.parametrize('body_failure', [False, True])
def test_cleanup_attempts_remaining_real_maps_and_preserves_primary(tmp_path, body_failure):
    from tradingagents.research.onchain_replication.mapped_graph import _close_maps
    _, path, _ = saved(tmp_path)
    first = np.load(path.parent / 'node_features.npy', mmap_mode='r')._mmap
    second = np.load(path.parent / 'edge_features.npy', mmap_mode='r')._mmap
    class CloseFailure:
        def close(self):
            second.close()
            raise OSError('injected cleanup failure')
    if body_failure:
        original = KeyboardInterrupt('injected body failure')
        with pytest.raises(KeyboardInterrupt) as result:
            try:
                raise original
            finally:
                _close_maps([first, CloseFailure()], primary=original)
        assert result.value is original
        assert any('cleanup failed' in note for note in original.__notes__)
    else:
        with pytest.raises(RuntimeError, match='cleanup failed'):
            _close_maps([first, CloseFailure()])
    assert first.closed and second.closed


def test_normal_context_exit_does_not_hide_cleanup_failure_in_ambient_exception(tmp_path, monkeypatch):
    import tradingagents.research.onchain_replication.mapped_graph as module
    _, path, size = saved(tmp_path)
    original_close = module._close_maps
    class CloseFailure:
        def close(self):
            raise OSError('injected close failure')
    def inject(mappings, **kwargs):
        return original_close([*mappings, CloseFailure()], **kwargs)
    monkeypatch.setattr(module, '_close_maps', inject)
    try:
        raise LookupError('unrelated handled exception')
    except LookupError:
        with pytest.raises(RuntimeError, match='cleanup failed'):
            with store.open_mapped_graph(path, file_hash(path), max_mapped_bytes=size) as graph:
                mappings = [graph.node_ids._mmap, graph.node_features._mmap]
    assert all(m.closed for m in mappings)
