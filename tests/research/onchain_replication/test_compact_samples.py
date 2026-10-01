"""Bounded publication joins actual compact sampler result to saved numeric bytes."""
from pathlib import Path
from types import SimpleNamespace
import shutil
import json
import pytest
from tests.research.onchain_replication import test_compact_sampler as sampling
from tests.research.test_lifecycle import git
from tradingagents.research.onchain_replication.provenance import file_hash

READER = 'research/onchain-paper-replication-2026-09-24/full_sources/pair-component-reader-2026-10-01/reader.py'


@pytest.fixture
def admitted(request, monkeypatch):
    original = sampling.training.first.Tests.fixture
    option = getattr(request, 'param', 'valid')
    def fixture(helper, mutate):
        def prepare(t):
            mutate(t)
            p = {'schema_version': 1, 'max_manifest_bytes': 65536, 'max_artifact_bytes': 1000000,
                'max_resident_array_bytes': 65536, 'max_attempt_bytes': 1000000 + 3 * 8192}
            if option == 'budget': p['max_attempt_bytes'] -= 1
            if option == 'manifest': p['max_manifest_bytes'] = 1
            if option == 'array': p['max_resident_array_bytes'] = 1
            t.input('compact_samples', p)
            for item in (t.item, t.execution['payload']['representation_jobs']['r']):
                item['compact_samples_input'] = 'compact_samples'
            if option == 'route': t.item['compact_samples_input'] = 'sample'
            target = t.root / READER; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(sampling.ROOT / READER, target); git(t.root, 'add', '--', READER)
            if option != 'source': t.exp['source_files'][READER] = file_hash(target)
        return original(helper, prepare)
    monkeypatch.setattr(sampling.training.first.Tests, 'fixture', fixture)
    fixture_gen = sampling.admitted.__wrapped__(SimpleNamespace(param='valid'), monkeypatch)
    route, t = next(fixture_gen)
    try: yield sampling.api().produce(route, input_name='compact_sampler'), t
    finally:
        try: next(fixture_gen)
        except StopIteration: pass


def api():
    from tradingagents.research.onchain_replication import compact_samples
    return compact_samples


def test_saved_numeric_arrays_exactly_join_current_draws_without_redrawing(admitted, monkeypatch):
    draws, t = admitted; m = api()
    monkeypatch.setattr(sampling.api(), '_kernel', lambda: (_ for _ in ()).throw(AssertionError('no redraw')))
    saved = m.publish(draws, input_name='compact_samples'); saved.check()
    assert saved.samples is draws.samples
    assert saved.record['draw_receipt_sha256'] == draws.receipt_sha256
    assert saved.record['numeric_artifact_published'] is True
    assert saved.record['sample_provenance_admitted'] is False
    assert (saved.directory / 'artifact/manifest.json').is_file()
    manifest = json.loads((saved.directory / 'artifact/manifest.json').read_bytes())
    assert len(manifest['arrays']) == 9
    assert sum(x['bytes'] for x in manifest['arrays'].values()) + (saved.directory / 'artifact/manifest.json').stat().st_size == saved.record['encoded_artifact_bytes']
    with pytest.raises(ValueError, match='already'): m.publish(draws, input_name='compact_samples')


@pytest.mark.parametrize('admitted', ['budget', 'manifest', 'array', 'route', 'source'], indirect=True)
def test_bound_route_and_source_refusals_precede_output_namespace(admitted):
    draws, t = admitted; m = api()
    with pytest.raises(ValueError): m.publish(draws, input_name='compact_samples')
    assert not m.directory(draws).exists()
    assert not draws._training.owner.poisoned


def test_partial_numeric_write_is_retained_and_owner_revoked(admitted, monkeypatch):
    draws, t = admitted; m = api()
    def fail(path, payload, context):
        path.mkdir(); (path / 'partial.npy').write_bytes(b'partial'); raise OSError('synthetic array write')
    monkeypatch.setattr(m.component_store, 'save_component', fail)
    with pytest.raises(OSError, match='array write'): m.publish(draws, input_name='compact_samples')
    assert (m.directory(draws) / 'artifact/partial.npy').read_bytes() == b'partial'
    assert (m.directory(draws) / 'failed.json').is_file()
    assert draws._training.owner.poisoned
    with pytest.raises(ValueError): m.publish(draws, input_name='compact_samples')


def test_saved_array_tampering_is_refused_before_allocating_payload(admitted, monkeypatch):
    draws, t = admitted; m = api(); saved = m.publish(draws, input_name='compact_samples')
    path = saved.directory / 'artifact/array-000000.npy'; raw = path.read_bytes()
    path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    def forbidden(*args, **kwargs): raise AssertionError('allocation preceded hash admission')
    class ReaderNumpy:
        empty = staticmethod(forbidden)
        def __getattr__(self, name): return getattr(m.np, name)
    monkeypatch.setattr(saved._reader, 'np', ReaderNumpy())
    with pytest.raises(ValueError, match='hash'): saved.check()


def test_late_reader_callback_cannot_hide_changed_numeric_file(admitted, monkeypatch):
    draws, t = admitted; m = api(); saved = m.publish(draws, input_name='compact_samples')
    original = saved._reader.read_component
    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        path = saved.directory / 'artifact/array-000000.npy'; raw = path.read_bytes()
        path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1])); return result
    monkeypatch.setattr(saved._reader, 'read_component', changed)
    with pytest.raises(ValueError, match='hash'): saved.check()


@pytest.mark.parametrize('target', ['resident', 'draw'])
def test_last_publication_lease_cannot_break_original_sample_or_draw_join(admitted, monkeypatch, target):
    draws, t = admitted; m = api(); saved = m.publish(draws, input_name='compact_samples')
    armed = False; equal = m._equal_numeric; lease = draws.lease
    def compare(*args):
        nonlocal armed
        equal(*args); armed = True
    def changed():
        lease()
        if armed:
            if target == 'resident':
                g = draws.samples.graphs[0]; object.__setattr__(g, 'node_features', g.node_features + 1)
            else: (draws.directory / 'draw-000000.json').write_bytes(b'{}')
    monkeypatch.setattr(m, '_equal_numeric', compare); monkeypatch.setattr(draws, 'lease', changed)
    with pytest.raises(ValueError, match='sample|draw|metadata'): saved.check()


def test_growth_after_preflight_is_refused_before_numeric_writer(admitted, monkeypatch):
    draws, t = admitted; m = api(); prepared = False; prepare = m._prepare; lease = draws.lease
    def sized(*args):
        nonlocal prepared
        result = prepare(*args); prepared = True; return result
    def changed():
        lease()
        if prepared:
            g = draws.samples.graphs[0]
            object.__setattr__(g, 'node_features', m.np.zeros((len(g.node_ids), 100000)))
    def forbidden(*args): raise AssertionError('resized sample reached numerical writer')
    monkeypatch.setattr(m, '_prepare', sized); monkeypatch.setattr(draws, 'lease', changed)
    monkeypatch.setattr(m.component_store, 'save_component', forbidden)
    with pytest.raises(ValueError, match='sample'): m.publish(draws, input_name='compact_samples')
    assert not (m.directory(draws) / 'artifact').exists()
