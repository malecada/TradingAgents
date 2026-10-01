"""Fresh tiny real checkpoint-engine checks; no empirical admission."""
import json
import pytest
from tests.research.onchain_replication.test_matching_reference import graph, config
from tradingagents.research.onchain_replication.matching_reference import match_reference
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication import matching_pair as pair

CONTEXT = {'namespace': 'a' * 64, 'source_commit': 'b' * 40, 'runtime_hash': 'c' * 64}
POLICY = {'max_state_bytes': 100000, 'normalization_chunk_entries': 2,
    'hardening_chunk_entries': 2, 'hardening_buffer_bytes': 4096,
    'max_score_buffer_bytes': 4096, 'chunk_edges': 2, 'max_checkpoint_bytes': 400000,
    'max_publications': 10, 'total_checkpoint_bytes': 5000000}
SCHEDULE = {'operations_per_call': 10000, 'calls_per_checkpoint': 64, 'max_checkpoints': 4,
    'max_total_checkpoints': 10, 'max_total_checkpoint_bytes': 6000000}


def fixture(tmp_path, schedule=None):
    from tradingagents.research.onchain_replication import compact_matcher as module
    from tradingagents.research.onchain_replication.compact_pair_log import PairLog
    a = graph([[0.], [.3]], [(0, 1, .1)])
    b = graph([[.2], [.7]], [(1, 0, .4)])
    c = config() | {'beta_final': 1.}
    selected = SCHEDULE if schedule is None else schedule
    scope = module.scope(c, CONTEXT, POLICY, 'f' * 64, selected)
    log = PairLog(tmp_path / 'log', owner='d' * 64, scope=scope,
        limits={'chunk_events': 16, 'max_events': 100, 'max_pairs': 10, 'max_logical_bytes': 40000},
        max_iterations=c['max_iterations'], lease=lambda: None)
    matcher = module.CompactMatcher(log, config=c, context=CONTEXT, policy=POLICY,
        workload_sha256='f' * 64, schedule=SCHEDULE if schedule is None else schedule, lease=lambda: None)
    purpose = {'schema_version': 1, 'kind': 'mcm', 'workload_sha256': 'f' * 64,
        'typed_graphs': [graph_identity(a), graph_identity(b)], 'center_index': 0, 'motif_index': 0}
    return module, matcher, log, a, b, c, purpose


def test_real_engine_exact_score_and_cleanup_without_per_pair_files(tmp_path, monkeypatch):
    module, matcher, log, a, b, c, purpose = fixture(tmp_path)
    original = pair.engine.close; closed = []
    def close(state):
        original(state); closed.append(state)
    monkeypatch.setattr(pair.engine, 'close', close)
    got = matcher(purpose, a, b); expected = match_reference(a, b, c)
    assert got == {'purpose_sha256': cache_key(purpose), 'score': expected.score}
    assert len(closed) == 1 and closed[0]['safe'] is False and closed[0]['annealing'] is None
    assert log.state['completed_pairs'] == 1 and log.events == 2
    assert list((tmp_path / 'checkpoints').iterdir()) == []
    assert not list(tmp_path.glob('**/owner.json')) and not list(tmp_path.glob('**/artifact-*'))
    # Actual numeric identity remains exactly the original PairSession identity.
    assert matcher.pair_identity(a, b) == pair.identity(a, b, c, CONTEXT)
    log.finish()


def test_progress_checkpoint_is_saved_and_loadable_without_continuing(tmp_path):
    schedule = SCHEDULE | {'operations_per_call': 1, 'calls_per_checkpoint': 1, 'max_checkpoints': 1}
    module, matcher, log, a, b, c, purpose = fixture(tmp_path, schedule)
    with pytest.raises(module.CheckpointStop): matcher(purpose, a, b)
    assert log.events == 2 and log.state['pending'] is not None and log.state['progress_events'] == 1
    saved = tmp_path / 'checkpoints/event-000000000001'
    manifest = json.loads((saved / 'manifest.json').read_text())
    state = pair.engine.load(saved / 'state', a, b, c, expected_sha256=manifest['state_sha256'],
        **{k: POLICY[k] for k in pair.ENGINE_FIELDS})
    pair.engine.close(state)  # Read-only checkpoint validation, no advance/restart.
    with pytest.raises(ValueError): matcher(purpose, a, b)
    log.fail('synthetic checkpoint stop')


def test_cleanup_failure_is_fatal_and_no_completion_is_published(tmp_path, monkeypatch):
    module, matcher, log, a, b, c, purpose = fixture(tmp_path)
    original = pair.engine.close
    def close(state):
        original(state); raise OSError('synthetic cleanup failure after real release')
    monkeypatch.setattr(pair.engine, 'close', close)
    with pytest.raises(module.CleanupFailure): matcher(purpose, a, b)
    assert log.events == 1 and log.state['pending'] is not None
    with pytest.raises(ValueError): matcher(purpose, a, b)
    log.fail('synthetic fatal cleanup')


def test_insufficient_publication_capacity_refuses_before_engine_create(tmp_path, monkeypatch):
    module, matcher, log, a, b, c, purpose = fixture(tmp_path)
    log.start['limits']['max_events'] = 1
    monkeypatch.setattr(pair.engine, 'create', lambda *a, **k: pytest.fail('allocated before capacity'))
    with pytest.raises(ValueError): matcher(purpose, a, b)
    assert log.events == 0
    log.close()


def test_checkpoint_corruption_before_publication_keeps_begin_pending(tmp_path, monkeypatch):
    schedule = SCHEDULE | {'operations_per_call': 1, 'calls_per_checkpoint': 1, 'max_checkpoints': 1}
    module, matcher, log, a, b, c, purpose = fixture(tmp_path, schedule)
    original = pair.engine.save
    def corrupt(state, path, *args, **kwargs):
        sha = original(state, path, *args, **kwargs)
        p = path / 'annealing/M.npy'; p.write_bytes(b'x' * p.stat().st_size)
        return sha
    monkeypatch.setattr(pair.engine, 'save', corrupt)
    with pytest.raises(ValueError): matcher(purpose, a, b)
    assert log.events == 1 and log.state['progress_events'] == 0
    assert list((tmp_path / 'checkpoints').iterdir())
    log.fail('synthetic corrupt checkpoint')
