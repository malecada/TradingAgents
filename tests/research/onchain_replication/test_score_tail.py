"""Durability and interruption tests using only synthetic scalar scores."""
import hashlib
import os
import numpy as np
import pytest

from tests.research.onchain_replication.test_score_batches import SCOPE, OWNER


def api():
    from tradingagents.research.onchain_replication import score_tail
    return score_tail


def tail(tmp_path, lease=lambda: None, destination='d' * 64):
    return api().ScoreTail(tmp_path / 'tail', scope=SCOPE, owner=OWNER,
        start_cell=0, cells=2, destination=destination, lease=lease)


def verify(tmp_path, ref):
    return api().verify(tmp_path / 'tail', scope=SCOPE, owner=OWNER,
        terminal_sha256=ref, lease=lambda: None)


def test_each_score_is_synced_before_acknowledgement_and_seals_exact_values(tmp_path, monkeypatch):
    from tradingagents.research.onchain_replication.score_batches import ScoreBatches, verify as check
    batches = ScoreBatches(tmp_path / 'batches', scope=SCOPE, owner=OWNER,
        rows=1, motifs=2, chunk_cells=2, lease=lambda: None)
    module = api(); obj = tail(tmp_path, destination=module.destination(batches))
    original = os.fsync; counts = []
    def sync(fd):
        counts.append(os.fstat(fd).st_size); return original(fd)
    monkeypatch.setattr(module.os, 'fsync', sync)
    one = obj.append(0, 'b' * 64, 1/3)
    assert 80 in counts
    assert (tmp_path / 'tail/records.bin').stat().st_size == 80
    assert one == {'purpose_sha256': 'b' * 64, 'score': 1/3}
    obj.append(1, 'c' * 64, -0.0)
    ref = obj.finish(); result = verify(tmp_path, ref)
    assert result['acknowledged_cells'] == 2 and result['pending_bytes'] == 0
    assert result['values'].tobytes() == np.array([1/3, -0.], dtype='<f8').tobytes()
    module.seal(tmp_path / 'tail', terminal_sha256=ref, batches=batches, lease=lambda: None)
    end = batches.finish()
    assert check(tmp_path / 'batches', scope=SCOPE, owner=OWNER,
        terminal_sha256=end, lease=lambda: None)['cells'] == 2
    assert (tmp_path / 'tail/records.bin').stat().st_size == 160


def test_failed_tail_preserves_acknowledged_prefix_and_refuses_restart(tmp_path):
    obj = tail(tmp_path); obj.append(0, 'b' * 64, 0.125)
    with pytest.raises(ValueError): obj.finish()
    ref = obj.fail('synthetic interruption'); result = verify(tmp_path, ref)
    assert result['status'] == 'failed' and result['acknowledged_cells'] == 1
    assert result['values'].tolist() == [0.125]
    with pytest.raises(ValueError): obj.append(1, 'c' * 64, 1.)
    with pytest.raises(FileExistsError): tail(tmp_path)


def test_partial_write_is_retained_and_not_acknowledged(tmp_path, monkeypatch):
    module = api(); obj = tail(tmp_path); original = os.write; calls = 0
    def interrupted(fd, raw):
        nonlocal calls
        calls += 1
        if calls == 1: return original(fd, raw[:13])
        raise OSError('simulated interrupted write')
    monkeypatch.setattr(module.os, 'write', interrupted)
    with pytest.raises(OSError): obj.append(0, 'b' * 64, 0.5)
    assert (tmp_path / 'tail/records.bin').stat().st_size == 13
    with pytest.raises(ValueError): obj.append(0, 'b' * 64, 0.5)
    ref = obj.fail('simulated interrupted write'); result = verify(tmp_path, ref)
    assert result['acknowledged_cells'] == 0 and result['pending_bytes'] == 13


def test_revoked_lease_after_fsync_never_acknowledges_score(tmp_path, monkeypatch):
    module = api(); alive = True
    def lease():
        if not alive: raise RuntimeError('owner lost')
    obj = tail(tmp_path, lease); original = os.fsync
    def revoke(fd):
        nonlocal alive
        original(fd); alive = False
    monkeypatch.setattr(module.os, 'fsync', revoke)
    with pytest.raises(RuntimeError): obj.append(0, 'b' * 64, 0.25)
    assert obj.acknowledged == 0
    assert (tmp_path / 'tail/records.bin').stat().st_size == 80
    obj.close()


@pytest.mark.parametrize('change', ['payload', 'order', 'owner', 'scope', 'extra', 'symlink'])
def test_corruption_and_identity_changes_are_refused(tmp_path, change):
    obj = tail(tmp_path); obj.append(0, 'b' * 64, 0.125); obj.append(1, 'c' * 64, 0.25)
    ref = obj.finish(); path = tmp_path / 'tail/records.bin'; raw = path.read_bytes()
    scope = dict(SCOPE); owner = OWNER
    if change == 'payload': path.write_bytes(raw[:8] + b'x' * 8 + raw[16:])
    if change == 'order': path.write_bytes(raw[80:] + raw[:80])
    if change == 'owner': owner = 'c' * 64
    if change == 'scope': scope['matching'] = 'd' * 64
    if change == 'extra': (tmp_path / 'tail/extra').write_bytes(b'foreign')
    if change == 'symlink':
        path.rename(tmp_path / 'elsewhere'); path.symlink_to(tmp_path / 'elsewhere')
    with pytest.raises((ValueError, OSError)):
        api().verify(tmp_path / 'tail', scope=scope, owner=owner,
            terminal_sha256=ref, lease=lambda: None)


def test_wrong_order_range_and_capacity_refused_before_writes(tmp_path):
    obj = tail(tmp_path)
    for index, purpose, value in [(1, 'b' * 64, 0.5), (0, 'bad', 0.5),
        (0, 'b' * 64, float('nan')), (0, 'b' * 64, -1.), (0, 'b' * 64, True)]:
        with pytest.raises(ValueError): obj.append(index, purpose, value)
    assert (tmp_path / 'tail/records.bin').stat().st_size == 0
    obj.close()
    with pytest.raises(ValueError):
        api().ScoreTail(tmp_path / 'oversized', scope=SCOPE, owner=OWNER,
            start_cell=0, cells=2**30, destination='d' * 64, lease=lambda: None)
    assert not (tmp_path / 'oversized').exists()


def test_failed_tail_cannot_be_sealed(tmp_path):
    obj = tail(tmp_path); obj.append(0, 'b' * 64, 0.5); ref = obj.fail('stopped')
    from tradingagents.research.onchain_replication.score_batches import ScoreBatches
    batches = ScoreBatches(tmp_path / 'batches', scope=SCOPE, owner=OWNER,
        rows=1, motifs=2, chunk_cells=2, lease=lambda: None)
    with pytest.raises(ValueError):
        api().seal(tmp_path / 'tail', terminal_sha256=ref, batches=batches, lease=lambda: None)
    assert batches.cells == 0
    batches.close()


def test_tail_lease_loss_during_batch_publication_refuses_seal_success(tmp_path, monkeypatch):
    module = api()
    from tradingagents.research.onchain_replication import score_batches as b
    batches = b.ScoreBatches(tmp_path / 'batches', scope=SCOPE, owner=OWNER,
        rows=1, motifs=2, chunk_cells=2, lease=lambda: None)
    obj = tail(tmp_path, destination=module.destination(batches))
    obj.append(0, 'b' * 64, 0.2); obj.append(1, 'c' * 64, 0.3); ref = obj.finish()
    alive = True
    def lease():
        if not alive: raise RuntimeError('tail owner lost')
    original = b._write
    def revoke(fd, name, raw):
        nonlocal alive
        result = original(fd, name, raw)
        if name == 'chunk-000000000000.json': alive = False
        return result
    monkeypatch.setattr(b, '_write', revoke)
    with pytest.raises(RuntimeError):
        module.seal(tmp_path / 'tail', terminal_sha256=ref, batches=batches, lease=lease)
    assert (tmp_path / 'batches/chunk-000000000000.bin').exists()
    batches.close()


def test_final_tail_lease_cannot_change_published_destination_undetected(tmp_path):
    module = api()
    from tradingagents.research.onchain_replication import score_batches as b
    batches = b.ScoreBatches(tmp_path / 'batches', scope=SCOPE, owner=OWNER,
        rows=1, motifs=2, chunk_cells=2, lease=lambda: None)
    obj = tail(tmp_path, destination=module.destination(batches))
    obj.append(0, 'b' * 64, 0.2); obj.append(1, 'c' * 64, 0.3); ref = obj.finish()
    def lease():
        path = tmp_path / 'batches/chunk-000000000000.bin'
        if path.exists(): path.write_bytes(b'x' * 16)
    with pytest.raises(ValueError):
        module.seal(tmp_path / 'tail', terminal_sha256=ref, batches=batches, lease=lease)
    batches.close()
