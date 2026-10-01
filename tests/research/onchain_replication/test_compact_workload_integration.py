"""Fresh directional dictionary and full MCM failure checks; no fit admission."""
import json
import numpy as np
import pytest

from tests.research.onchain_replication.test_mcm_score_stream import fixture, POLICY as MCM_POLICY
from tests.research.onchain_replication.test_compact_matcher import CONTEXT, POLICY, SCHEDULE
from tradingagents.research.onchain_replication import compact_matcher as compact
from tradingagents.research.onchain_replication.compact_pair_log import PairLog, FRAME, RECORD_BYTES, verify
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.mcm_score_stream import MCMScoreStream


def consumer(root, f, workload, schedule=SCHEDULE):
    policy = POLICY | {'normalization_chunk_entries': 64}
    log = PairLog(root / 'matching', owner='e' * 64,
        scope=compact.scope(f.match, CONTEXT, policy, workload, schedule),
        limits={'chunk_events': 16, 'max_events': 200, 'max_pairs': 64, 'max_logical_bytes': 60000},
        max_iterations=f.match['max_iterations'], lease=lambda: None)
    matcher = compact.CompactMatcher(log, config=f.match, context=CONTEXT, policy=policy,
        workload_sha256=workload, schedule=schedule, lease=lambda: None)
    return matcher, log


def dictionary_scope(f):
    return cache_key({'schema_version': 1, 'kind': 'dictionary', 'workflow': f.kw['workflow'],
        'backend': f.kw['backend'], 'sample': f.samples.identity,
        'typed_sample_graphs': [graph_identity(g) for g in f.samples.graphs],
        'matching': f.match, 'dictionary': f.settings, 'seed': f.samples.seed})


def records(log):
    return [FRAME.unpack(raw[offset:offset + FRAME.size])
        for path in sorted(log.root.glob('events-*.bin'))
        for raw in [path.read_bytes()] for offset in range(0, len(raw), RECORD_BYTES)]


def test_dictionary_compact_engine_preserves_both_directions_hierarchy_matrices_and_identity(tmp_path):
    base, f, _, _ = fixture()
    oracle = base.Scores(f.match); expected = f.fit(oracle)
    matcher, log = consumer(tmp_path, f, dictionary_scope(f))
    asked = []
    def compute(p, a, b):
        asked.append(p)
        return matcher(p, a, b)
    actual = f.fit(compute)
    ref = log.finish()
    proof = verify(log.root, owner='e' * 64, scope=log.start['scope'],
        terminal_sha256=ref, lease=lambda: None)
    assert asked == oracle.asked and len(asked) > 2
    assert len({p['block_sha256'] for p in asked}) > 1
    for a, b in zip(asked[::2], asked[1::2], strict=True):
        assert a['sample_indices'] == b['sample_indices'][::-1]
        assert a['typed_graphs'] == b['typed_graphs'][::-1]
        assert cache_key(a) != cache_key(b)
    assert actual['dictionary'].identity == expected['dictionary'].identity
    assert actual['dictionary'].hierarchy == expected['dictionary'].hierarchy
    assert actual['dictionary'].memberships == expected['dictionary'].memberships
    assert len(actual['dictionary'].hierarchy) > 0
    for a, b in zip(actual['matrices'], expected['matrices'], strict=True):
        assert a['indices'] == b['indices'] and a['block_sha256'] == b['block_sha256']
        assert a['matrix'].tobytes() == b['matrix'].tobytes()
    completions = [r for r in records(log) if r[1] in (1, 2)]
    assert [r[5].hex() for r in completions] == [cache_key(p) for p in asked]
    assert np.array([r[3] for r in completions], dtype='<f8').tobytes() == np.array(
        [oracle.saved[cache_key(p)]['score'] for p in asked], dtype='<f8').tobytes()
    assert proof['completed_pairs'] == len(asked) and proof['pending'] is None
    assert proof['events'] == 2 * len(asked) and proof['progress_events'] == 0
    assert not list(tmp_path.glob('**/owner.json')) and not list(tmp_path.glob('**/artifact-*'))


def test_dictionary_failure_in_reverse_direction_preserves_first_score_without_replay(tmp_path, monkeypatch):
    _, f, _, _ = fixture(); matcher, log = consumer(tmp_path, f, dictionary_scope(f))
    original = compact.engine.create; calls = 0
    def create(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2: raise RuntimeError('synthetic reverse direction allocation failure')
        return original(*args, **kwargs)
    monkeypatch.setattr(compact.engine, 'create', create)
    with pytest.raises(RuntimeError, match='reverse direction'): f.fit(matcher)
    assert calls == 2 and log.state['completed_pairs'] == 1
    assert log.state['pending']['ordinal'] == 1 and matcher.poisoned
    # A poisoned consumer rejects even an invalid request before any allocation.
    with pytest.raises(ValueError, match='poisoned'): matcher({}, None, None)
    assert calls == 2
    ref = log.fail('synthetic reverse direction allocation failure')
    proof = verify(log.root, owner='e' * 64, scope=log.start['scope'],
        terminal_sha256=ref, lease=lambda: None)
    assert proof['status'] == 'failed' and proof['events'] == 3 and proof['completed_pairs'] == 1


@pytest.mark.parametrize('failure', ['checkpoint_stop', 'cleanup'])
def test_actual_mcm_failure_preserves_pending_matcher_and_never_acknowledges_score(tmp_path, monkeypatch, failure):
    _, f, d, kernel = fixture(); matcher = None
    stream = MCMScoreStream(tmp_path / 'stream', graph=f.g, dictionary=d,
        matching_config=f.match, workflow=f.kw['workflow'], backend=f.kw['backend'],
        owner='e' * 64, chunk_cells=4, compute=lambda p, a, b: matcher(p, a, b), lease=lambda: None)
    schedule = SCHEDULE if failure == 'cleanup' else SCHEDULE | {
        'operations_per_call': 1, 'calls_per_checkpoint': 1, 'max_checkpoints': 1}
    matcher, log = consumer(tmp_path, f, stream.workload, schedule)
    released = []; original = compact.engine.close
    def close(state):
        original(state); released.append(state)
        if failure == 'cleanup': raise OSError('synthetic failure after actual release')
    monkeypatch.setattr(compact.engine, 'close', close)
    error = compact.CleanupFailure if failure == 'cleanup' else compact.CheckpointStop
    with pytest.raises(error):
        kernel.mcm(f.g, d, f.match, **f.kw, score_pair=stream, policy=MCM_POLICY, lease=lambda: None)
    assert len(released) == 1 and released[0]['safe'] is False and released[0]['annealing'] is None
    assert matcher.poisoned and log.state['completed_pairs'] == 0 and log.state['pending']['ordinal'] == 0
    assert log.state['progress_events'] == (failure == 'checkpoint_stop')
    assert (tmp_path / 'stream/tails/tail-000000000000/records.bin').stat().st_size == 0
    assert not (tmp_path / 'stream/complete.json').exists()
    with pytest.raises(ValueError): stream.finish()
    ref = log.fail('synthetic ' + failure)
    proof = verify(log.root, owner='e' * 64, scope=log.start['scope'],
        terminal_sha256=ref, lease=lambda: None)
    assert proof['status'] == 'failed' and proof['completed_pairs'] == 0
    if failure == 'checkpoint_stop':
        saved = tmp_path / 'checkpoints/event-000000000001'
        meta = json.loads((saved / 'manifest.json').read_text())
        assert records(log)[1][7].hex() == __import__('hashlib').sha256((saved / 'manifest.json').read_bytes()).hexdigest()
        assert meta['state_logical_bytes'] > 0 and (saved / 'state/annealing/M.npy').is_file()
