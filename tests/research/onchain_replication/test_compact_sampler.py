"""Current-owner durable draws, before separately admitted numeric publication."""
from pathlib import Path
from types import SimpleNamespace
import json
import shutil
from tests.research.test_lifecycle import git
import pytest
import numpy as np
from tests.research.onchain_replication import test_compact_training as training
from tradingagents.research.onchain_replication import neighborhoods
from tradingagents.research.onchain_replication.provenance import canonical_bytes, file_hash, thaw

ROOT = Path(__file__).resolve().parents[3]
CORE = 'research/onchain-paper-replication-2026-09-24/full_sources/sampler-leased-core-2026-10-01/core.py'


def policy():
    return {'schema_version': 1, 'kernel': 'resident-leased-v1', 'max_metadata_bytes': 65536,
        'max_attempt_bytes': 6 * 65536, 'limits': {'schema_version': 1, 'max_centers': 1000,
        'max_direct_weight_bytes': 16000, 'neighborhood': {'schema_version': 1, 'mode': 'array',
        'max_buffer_bytes': 65536, 'edge_chunk': 8, 'max_sample_array_bytes': 65536}}}


@pytest.fixture
def admitted(request, monkeypatch):
    original = training.first.Tests.fixture
    option = getattr(request, 'param', 'valid')
    def fixture(helper, mutate):
        def prepare(t):
            mutate(t); p = policy()
            if option == 'budget': p['max_attempt_bytes'] -= 1
            if option == 'schema': p['schema_version'] = True
            t.input('compact_sampler', p)
            for item in (t.item, t.execution['payload']['representation_jobs']['r']):
                item['compact_sampler_input'] = 'compact_sampler'
            if option == 'route': t.item['compact_sampler_input'] = 'sample'
            target = t.root / CORE; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / CORE, target)
            git(t.root, "add", "--", CORE)
            if option != 'source': t.exp['source_files'][CORE] = file_hash(target)
        return original(helper, prepare)
    monkeypatch.setattr(training.first.Tests, 'fixture', fixture)
    fixture_gen = training.admitted.__wrapped__(SimpleNamespace(param='valid'))
    owner, args, t = next(fixture_gen)
    try: yield training.admit(owner, args), t
    finally:
        try: next(fixture_gen)
        except StopIteration: pass


def api():
    from tradingagents.research.onchain_replication import compact_sampler
    return compact_sampler


def test_actual_draws_equal_existing_sampler_and_durable_current_owner_evidence(admitted):
    route, t = admitted; m = api()
    expected = neighborhoods.sample_neighborhoods(route.graphs, thaw(route.settings), route.seed)
    result = m.produce(route, input_name='compact_sampler'); result.check()
    assert result.samples.identity == expected.identity
    for actual, reference in zip(result.samples.graphs, expected.graphs, strict=True):
        assert (actual.node_ids, actual.parent_hash, actual.center_id) == (reference.node_ids, reference.parent_hash, reference.center_id)
        for name in ('node_features', 'edge_index', 'edge_features'):
            np.testing.assert_array_equal(getattr(actual, name), getattr(reference, name))
    assert canonical_bytes(result.samples.records) == canonical_bytes(expected.records)
    proof = json.loads((result.directory / 'complete.json').read_bytes())
    assert proof['draw_count'] == 3 and proof['reserved_logical_bytes'] == 6 * 65536
    assert result.record['sample_provenance_admitted'] is False
    assert result.record['numeric_artifact_published'] is False
    assert len(list(result.directory.glob('draw-*.json'))) == 3
    before = {p.name: p.read_bytes() for p in result.directory.iterdir()}
    with pytest.raises(ValueError, match='already'): m.produce(route, input_name='compact_sampler')
    assert before == {p.name: p.read_bytes() for p in result.directory.iterdir()}


@pytest.mark.parametrize('admitted', ['budget', 'schema', 'route', 'source'], indirect=True)
def test_preflight_refuses_before_sampling_or_namespace(admitted, monkeypatch):
    route, t = admitted; m = api()
    with pytest.raises(ValueError): m.produce(route, input_name='compact_sampler')
    assert not m.directory(route).exists()
    assert not route.owner.poisoned


def test_interrupted_draw_write_retains_attempt_and_revokes_owner(admitted, monkeypatch):
    route, t = admitted; m = api(); original = m.io._write
    def fail(fd, name, raw):
        if name == 'draw-000001.json': raise OSError('synthetic draw interruption')
        return original(fd, name, raw)
    monkeypatch.setattr(m.io, '_write', fail)
    with pytest.raises(OSError, match='interruption'): m.produce(route, input_name='compact_sampler')
    path = m.directory(route)
    assert (path / 'start.json').is_file() and (path / 'draw-000000.json').is_file()
    assert (path / 'failed.json').is_file() and not (path / 'complete.json').exists()
    assert route.owner.poisoned
    with pytest.raises(ValueError): m.produce(route, input_name='compact_sampler')


def test_draw_damage_and_resident_sample_drift_refuse(admitted):
    route, t = admitted; m = api(); result = m.produce(route, input_name='compact_sampler')
    g = result.samples.graphs[0]; original = g.node_features
    object.__setattr__(g, 'node_features', original + 1)
    with pytest.raises(ValueError, match='sample'): result.check()
    object.__setattr__(g, 'node_features', original)
    path = result.directory / 'draw-000001.json'; body = path.read_bytes(); path.write_bytes(body + b' ')
    with pytest.raises(ValueError, match='draw|metadata'): result.check()


def test_last_lease_callback_cannot_hide_changed_draw(admitted, monkeypatch):
    route, t = admitted; m = api(); result = m.produce(route, input_name='compact_sampler')
    original = route.lease
    def changed():
        original(); (result.directory / 'draw-000000.json').write_bytes(b'{}')
    monkeypatch.setattr(route, 'lease', changed)
    with pytest.raises(ValueError): result.check()


def test_corrupt_acknowledgement_stops_before_next_draw(admitted, monkeypatch):
    route, t = admitted; m = api(); calls = []; original_draw = m._draw; original_lease = route.lease
    def draw(value, index, *args):
        calls.append(index); return original_draw(value, index, *args)
    def corrupt():
        original_lease(); path = m.directory(route) / 'draw-000000.json'
        if path.exists(): path.write_bytes(b'{}')
    monkeypatch.setattr(m, '_draw', draw); monkeypatch.setattr(route, 'lease', corrupt)
    with pytest.raises(Exception) as caught: m.produce(route, input_name='compact_sampler')
    assert calls == [0], 'a later RNG draw occurred after corrupt acknowledgement'
    assert isinstance(caught.value, ValueError)
    assert route.owner.poisoned
    assert not (m.directory(route) / 'draw-000001.json').exists()
