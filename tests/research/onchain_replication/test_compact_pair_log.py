"""Synthetic fixed-record matcher history; no financial or graph execution."""
import os
import pytest
from tests.research.onchain_replication.test_score_batches import OWNER

SCOPE = {key: digit * 64 for key, digit in zip(
    ('workflow', 'config', 'policy', 'context', 'numerical_source'), '12345')}
POLICY = {'chunk_events': 3, 'max_events': 12, 'max_pairs': 4, 'max_logical_bytes': 18400}


def api():
    from tradingagents.research.onchain_replication import compact_pair_log
    return compact_pair_log


def writer(tmp_path, lease=lambda: None):
    return api().PairLog(tmp_path / 'log', owner=OWNER, scope=SCOPE,
        limits=POLICY, max_iterations=10, lease=lease)


def check(tmp_path, ref, lease=lambda: None):
    return api().verify(tmp_path / 'log', owner=OWNER, scope=SCOPE,
        terminal_sha256=ref, lease=lease)


def test_complete_history_keeps_order_iterations_and_checkpoint_binding(tmp_path):
    log = writer(tmp_path)
    log.begin('b' * 64, 'c' * 64)
    log.progress('d' * 64)
    got = log.complete(0.125, 'temperature_complete', 7)
    assert got == {'purpose_sha256': 'b' * 64, 'score': 0.125}
    log.begin('e' * 64, 'f' * 64)
    log.complete(-0.0, 'iteration_cap', 10)
    ref = log.finish(); result = check(tmp_path, ref)
    assert result['events'] == 5 and result['completed_pairs'] == 2
    assert result['progress_events'] == 1 and result['pending'] is None
    assert result['record_bytes'] == 840 and result['chunks'] == 2
    assert len(list((tmp_path / 'log').iterdir())) == 4


def test_pending_pair_blocks_new_pair_and_success_and_survives_failure(tmp_path):
    log = writer(tmp_path); log.begin('b' * 64, 'c' * 64)
    with pytest.raises(ValueError): log.begin('d' * 64, 'e' * 64)
    with pytest.raises(ValueError): log.finish()
    ref = log.fail('synthetic interruption'); result = check(tmp_path, ref)
    assert result['pending']['purpose_sha256'] == 'b' * 64
    assert result['completed_pairs'] == 0
    with pytest.raises(FileExistsError): writer(tmp_path)


def test_invalid_result_cannot_consume_pending_identity(tmp_path):
    log = writer(tmp_path); log.begin('b' * 64, 'c' * 64)
    for score, convergence, iterations in [(float('nan'), 'iteration_cap', 10),
        (True, 'iteration_cap', 10), (1.1, 'iteration_cap', 10),
        (0.2, 'made_up', 3), (0.2, 'iteration_cap', 11), (0.2, 'iteration_cap', True)]:
        with pytest.raises(ValueError): log.complete(score, convergence, iterations)
    log.complete(0.2, 'iteration_cap', 10)
    assert check(tmp_path, log.finish())['completed_pairs'] == 1


def test_short_write_is_not_acknowledged_and_is_never_retried(tmp_path, monkeypatch):
    module = api(); log = writer(tmp_path); original = os.write; calls = 0
    def broken(fd, raw):
        nonlocal calls
        calls += 1
        if calls == 1: return original(fd, raw[:17])
        raise OSError('synthetic disk interruption')
    monkeypatch.setattr(module.os, 'write', broken)
    with pytest.raises(OSError): log.begin('b' * 64, 'c' * 64)
    with pytest.raises(ValueError): log.begin('b' * 64, 'c' * 64)
    ref = log.fail('synthetic disk interruption'); result = check(tmp_path, ref)
    assert result['events'] == 0 and result['unacknowledged_bytes'] == 17
    assert (tmp_path / 'log/events-000000000000.bin').stat().st_size == 17


def test_lease_loss_after_sync_preserves_bytes_without_acknowledgement(tmp_path, monkeypatch):
    module = api(); alive = True
    def lease():
        if not alive: raise RuntimeError('lease lost')
    log = writer(tmp_path, lease); original = os.fsync
    def revoke(fd):
        original(fd)
        nonlocal alive
        alive = False
    monkeypatch.setattr(module.os, 'fsync', revoke)
    with pytest.raises(RuntimeError): log.begin('b' * 64, 'c' * 64)
    assert log.events == 0
    log.close()


@pytest.mark.parametrize('kind', ['payload', 'extra', 'symlink', 'late'])
def test_corruption_or_late_mutation_prevents_verification(tmp_path, kind):
    log = writer(tmp_path); log.begin('b' * 64, 'c' * 64)
    log.complete(0.3, 'temperature_complete', 3); ref = log.finish()
    path = tmp_path / 'log/events-000000000000.bin'
    if kind == 'payload': path.write_bytes(b'x' * path.stat().st_size)
    if kind == 'extra': (tmp_path / 'log/foreign').write_bytes(b'x')
    if kind == 'symlink':
        path.rename(tmp_path / 'elsewhere'); path.symlink_to(tmp_path / 'elsewhere')
    calls = 0
    def lease():
        nonlocal calls
        calls += 1
        if kind == 'late' and calls >= 2: path.write_bytes(b'x' * path.stat().st_size)
    with pytest.raises((ValueError, OSError)): check(tmp_path, ref, lease)


def test_event_and_pair_caps_refuse_before_allocation(tmp_path):
    module = api()
    with pytest.raises(ValueError):
        module.PairLog(tmp_path / 'bad', owner=OWNER, scope=SCOPE,
            limits=POLICY | {'max_logical_bytes': 18000}, max_iterations=10, lease=lambda: None)
    assert not (tmp_path / 'bad').exists()
    log = module.PairLog(tmp_path / 'log', owner=OWNER, scope=SCOPE,
        limits=POLICY | {'max_events': 2, 'max_pairs': 1}, max_iterations=10, lease=lambda: None)
    log.begin('b' * 64, 'c' * 64); log.complete(0.1, 'iteration_cap', 10)
    with pytest.raises(ValueError): log.begin('d' * 64, 'e' * 64)
    assert check(tmp_path, log.finish())['events'] == 2
