"""Fresh full-engine stage seal checks; no empirical admission or historical replay."""
import hashlib
import json
import pytest
from tests.research.onchain_replication.test_mcm_score_stream import fixture, POLICY as MCM_POLICY
from tests.research.onchain_replication.test_compact_workload_integration import consumer, dictionary_scope
from tests.research.onchain_replication.test_compact_policy import candidate
from tradingagents.research.onchain_replication import compact_matcher as matcher_api
from tradingagents.research.onchain_replication.mcm_score_stream import MCMScoreStream


def completed(root, kind, monkeypatch, progress=False, wrong_score=False):
    _, f, d, kernel = fixture(); matcher = None
    if progress:
        original = matcher_api.engine.advance; first = True
        def advance(state, a, b, config, *, max_operations):
            nonlocal first
            amount = 1 if first else max_operations; first = False
            return original(state, a, b, config, max_operations=amount)
        monkeypatch.setattr(matcher_api.engine, 'advance', advance)
    stream = None
    if kind == 'mcm':
        def compute(p, a, b):
            result = matcher(p, a, b)
            if wrong_score and stream.cells == 0:
                return result | {'score': 0. if result['score'] != 0. else 1.}
            return result
        stream = MCMScoreStream(root / 'stream', graph=f.g, dictionary=d,
            matching_config=f.match, workflow=f.kw['workflow'], backend=f.kw['backend'],
            owner='e' * 64, chunk_cells=4, compute=compute, lease=lambda: None)
    p = candidate(); p['pair']['normalization_chunk_entries'] = 64
    p['schedule']['calls_per_checkpoint'] = 1
    p['schedule']['max_total_checkpoints'] = 128
    p['schedule']['max_total_checkpoint_bytes'] = 64000000
    p['max_retained_logical_bytes'] = 80000000
    matcher, log = consumer(root, f, stream.workload if stream else dictionary_scope(f), p['schedule'])
    if stream:
        kernel.mcm(f.g, d, f.match, **f.kw, score_pair=stream, policy=MCM_POLICY, lease=lambda: None)
        stream_ref = stream.finish()['terminal_sha256']
    else:
        f.fit(matcher); stream_ref = None
    count = log.state['completed_pairs']; terminal = log.finish()
    # Match the actual consumer fixture's exact log policy, not candidate defaults.
    p['log'] = dict(log.start['limits'])
    return dict(owner='e' * 64, scope=log.start['scope'], policy=p, kind=kind, pairs=count,
        log_terminal_sha256=terminal, stream_terminal_sha256=stream_ref)


@pytest.mark.parametrize('kind', ['dictionary', 'mcm'])
def test_complete_stage_joins_actual_log_scores_and_retained_progress(tmp_path, monkeypatch, kind):
    from tradingagents.research.onchain_replication.compact_stage import seal, verify
    contract = completed(tmp_path, kind, monkeypatch, progress=True)
    reference = seal(tmp_path, **contract, lease=lambda: None)
    result = verify(tmp_path, expected_sha256=reference, **contract, lease=lambda: None)
    assert result['completed_pairs'] == contract['pairs'] and result['checkpoints'] > 0
    assert result['checkpoint_logical_bytes'] > 0 and result['execution_admitted'] is False
    assert result['stream_terminal_sha256'] == contract['stream_terminal_sha256']
    raw = (tmp_path / 'stage-complete.json').read_bytes()
    assert reference == hashlib.sha256(raw).hexdigest()
    with pytest.raises((ValueError, FileExistsError)): seal(tmp_path, **contract, lease=lambda: None)
    assert (tmp_path / 'stage-complete.json').read_bytes() == raw


@pytest.mark.parametrize('target', ['checkpoint', 'score', 'extra_checkpoint', 'denominator'])
def test_corrupt_or_mismatched_stage_cannot_publish_completion(tmp_path, monkeypatch, target):
    from tradingagents.research.onchain_replication.compact_stage import seal
    contract = completed(tmp_path, 'mcm', monkeypatch, progress=True)
    if target == 'checkpoint':
        path = next((tmp_path / 'checkpoints').glob('*/state/annealing/M.npy'))
        path.write_bytes(b'x' * path.stat().st_size)
    if target == 'score':
        path = tmp_path / 'stream/batches/chunk-000000000000.bin'; path.write_bytes(b'x' * 32)
    if target == 'extra_checkpoint': (tmp_path / 'checkpoints/orphan').mkdir()
    if target == 'denominator': contract['pairs'] += 1
    with pytest.raises(ValueError): seal(tmp_path, **contract, lease=lambda: None)
    assert not (tmp_path / 'stage-complete.json').exists()


def test_late_owner_callback_corruption_leaves_failed_seal_bytes_without_success(tmp_path, monkeypatch):
    from tradingagents.research.onchain_replication.compact_stage import seal, verify
    contract = completed(tmp_path, 'mcm', monkeypatch)
    def lease():
        if (tmp_path / 'stage-complete.json').exists():
            p = tmp_path / 'stream/batches/chunk-000000000000.bin'; p.write_bytes(b'x' * 32)
    with pytest.raises(ValueError): seal(tmp_path, **contract, lease=lease)
    assert (tmp_path / 'stage-complete.json').exists()
    ref = hashlib.sha256((tmp_path / 'stage-complete.json').read_bytes()).hexdigest()
    with pytest.raises(ValueError): verify(tmp_path, expected_sha256=ref, **contract, lease=lambda: None)


def test_internally_valid_stream_with_changed_score_refuses_exact_pair_log_join(tmp_path, monkeypatch):
    from tradingagents.research.onchain_replication.compact_stage import seal, stream
    contract = completed(tmp_path, 'mcm', monkeypatch, wrong_score=True)
    # Every stream/tail/batch checksum is valid; only the matcher-to-score join differs.
    stream(tmp_path / 'stream', owner=contract['owner'], scope=contract['scope'],
        terminal=contract['stream_terminal_sha256'], policy=contract['policy'], pairs=contract['pairs'])
    with pytest.raises(ValueError, match='matching and retained score purposes/values differ'):
        seal(tmp_path, **contract, lease=lambda: None)
    assert not (tmp_path / 'stage-complete.json').exists()
