"""Synthetic persistence checks; no market inputs, fitting or matching runs."""
import hashlib
import json
import numpy as np
import pytest


def api():
    from tradingagents.research.onchain_replication import score_batches
    return score_batches


SCOPE = {key: digit * 64 for key, digit in zip(
    ('graph', 'node_order', 'dictionary', 'ordered_motifs', 'matching', 'workflow'),
    '123456')}
OWNER = 'a' * 64


def writer(tmp_path, **kw):
    return api().ScoreBatches(tmp_path / 'scores', scope=SCOPE, owner=OWNER,
        rows=3, motifs=2, chunk_cells=4, lease=lambda: None, **kw)


def test_binary_values_and_cell_order_survive_complete_publication(tmp_path):
    store = writer(tmp_path)
    store.append(0, np.array([0., -0., 1/3, 0.7], dtype='<f8'))
    store.append(4, np.array([0.9, 1.], dtype='<f8'))
    ref = store.finish()
    result = api().verify(tmp_path / 'scores', scope=SCOPE, owner=OWNER,
        terminal_sha256=ref, lease=lambda: None)
    assert result['status'] == 'complete' and result['cells'] == 6
    assert result['chunks'] == 2 and result['payload_bytes'] == 48
    raw = (tmp_path / 'scores/chunk-000000000000.bin').read_bytes()
    assert raw == np.array([0., -0., 1/3, 0.7], dtype='<f8').tobytes()
    # Row-major ordinal 4 means row 2, motif 0, with no per-cell metadata.
    header = json.loads((tmp_path / 'scores/chunk-000000000001.json').read_text())
    assert header['start_cell'] == 4 and header['cells'] == 2
    assert len(list((tmp_path / 'scores').iterdir())) == 6


def test_duplicate_out_of_order_short_and_nonfinite_chunks_are_refused(tmp_path):
    store = writer(tmp_path)
    for offset, value in [(1, np.ones(4)), (0, np.ones(3)),
                          (0, np.array([0., 0., np.nan, 1.])),
                          (0, np.ones(4, dtype=np.float32))]:
        with pytest.raises(ValueError): store.append(offset, value)
    assert len(list((tmp_path / 'scores').iterdir())) == 1
    store.append(0, np.ones(4))
    with pytest.raises(ValueError): store.append(0, np.ones(4))
    with pytest.raises(ValueError): store.finish()
    ref = store.fail('synthetic interruption')
    got = api().verify(tmp_path / 'scores', scope=SCOPE, owner=OWNER,
        terminal_sha256=ref, lease=lambda: None)
    assert got['status'] == 'failed' and got['cells'] == 4
    with pytest.raises(ValueError): store.append(4, np.ones(2))
    with pytest.raises(FileExistsError): writer(tmp_path)


@pytest.mark.parametrize('damage', ['payload', 'scope', 'owner', 'terminal', 'missing', 'symlink'])
def test_corrupt_or_wrong_identity_cannot_verify(tmp_path, damage):
    store = writer(tmp_path); store.append(0, np.arange(4, dtype='<f8'))
    store.append(4, np.ones(2)); ref = store.finish()
    root = tmp_path / 'scores'; scope = dict(SCOPE); owner = OWNER
    if damage == 'payload': (root / 'chunk-000000000000.bin').write_bytes(b'x' * 32)
    if damage == 'scope': scope['graph'] = 'f' * 64
    if damage == 'owner': owner = 'b' * 64
    if damage == 'terminal': ref = '0' * 64
    if damage == 'missing': (root / 'chunk-000000000001.json').unlink()
    if damage == 'symlink':
        path = root / 'chunk-000000000000.bin'; raw = path.read_bytes(); path.unlink()
        (tmp_path / 'outside').write_bytes(raw); path.symlink_to(tmp_path / 'outside')
    with pytest.raises((ValueError, OSError)):
        api().verify(root, scope=scope, owner=owner, terminal_sha256=ref, lease=lambda: None)


def test_failed_write_preserves_unpublished_bytes_and_requires_terminal_failure(tmp_path, monkeypatch):
    module = api(); store = writer(tmp_path); original = module._write
    def broken(fd, name, body):
        if name.endswith('.json') and name.startswith('chunk-'):
            raise OSError('synthetic disk failure')
        return original(fd, name, body)
    monkeypatch.setattr(module, '_write', broken)
    with pytest.raises(OSError): store.append(0, np.ones(4))
    assert (tmp_path / 'scores/chunk-000000000000.bin').stat().st_size == 32
    with pytest.raises(ValueError): store.append(0, np.ones(4))
    ref = store.fail('synthetic disk failure')
    got = module.verify(tmp_path / 'scores', scope=SCOPE, owner=OWNER,
        terminal_sha256=ref, lease=lambda: None)
    assert got['cells'] == 0 and got['pending_files'] == ['chunk-000000000000.bin']


def test_revoked_lease_prevents_writes_and_oversized_policy_prevents_creation(tmp_path):
    alive = True
    def lease():
        if not alive: raise RuntimeError('owner gone')
    store = api().ScoreBatches(tmp_path / 'scores', scope=SCOPE, owner=OWNER,
        rows=3, motifs=2, chunk_cells=4, lease=lease)
    alive = False
    with pytest.raises(RuntimeError): store.append(0, np.ones(4))
    assert len(list((tmp_path / 'scores').iterdir())) == 1
    with pytest.raises(ValueError):
        api().ScoreBatches(tmp_path / 'too-large', scope=SCOPE, owner=OWNER,
            rows=3, motifs=2, chunk_cells=2**30, lease=lambda: None)
    assert not (tmp_path / 'too-large').exists()


def test_unknown_files_and_changed_root_are_refused(tmp_path):
    store = writer(tmp_path)
    old = tmp_path / 'scores'; old.rename(tmp_path / 'moved'); old.mkdir()
    with pytest.raises(ValueError): store.append(0, np.ones(4))
    assert not list(old.iterdir())


def test_logical_bound_counts_chunks_without_per_cell_reservations():
    # 6 values, 2 chunks: 48 raw bytes + 4 compact metadata caps.
    assert api().logical_bound(rows=3, motifs=2, chunk_cells=4) == 32816


@pytest.mark.parametrize('terminal', [False, True])
def test_lease_loss_during_publication_cannot_return_success(tmp_path, monkeypatch, terminal):
    module = api(); alive = True
    def lease():
        if not alive: raise RuntimeError('owner revoked during write')
    store = module.ScoreBatches(tmp_path / 'scores', scope=SCOPE, owner=OWNER,
        rows=1, motifs=2, chunk_cells=2, lease=lease)
    if terminal: store.append(0, np.ones(2))
    original = module._write
    def interrupt(fd, name, raw):
        nonlocal alive
        result = original(fd, name, raw)
        if name == ('terminal.json' if terminal else 'chunk-000000000000.json'):
            alive = False
        return result
    monkeypatch.setattr(module, '_write', interrupt)
    with pytest.raises(RuntimeError):
        if terminal: store.finish()
        else: store.append(0, np.ones(2))
    store.close()


def test_late_mutation_of_previously_read_payload_is_refused(tmp_path):
    store = writer(tmp_path); store.append(0, np.ones(4)); store.append(4, np.ones(2))
    ref = store.finish(); calls = 0
    def lease():
        nonlocal calls
        calls += 1
        if calls == 4:
            (tmp_path / 'scores/chunk-000000000000.bin').write_bytes(b'x' * 32)
    with pytest.raises(ValueError):
        api().verify(tmp_path / 'scores', scope=SCOPE, owner=OWNER,
            terminal_sha256=ref, lease=lease)


def test_store_parent_entry_is_synced_before_publication(tmp_path, monkeypatch):
    import os
    module = api(); original = os.fsync; seen = []
    parent_identity = (tmp_path.stat().st_dev, tmp_path.stat().st_ino)
    def record(fd):
        info = os.fstat(fd); seen.append((info.st_dev, info.st_ino)); return original(fd)
    monkeypatch.setattr(module.os, 'fsync', record)
    store = writer(tmp_path)
    assert seen[0] == parent_identity
    store.close()


def test_late_rewrite_with_coalesced_metadata_still_checks_content(tmp_path, monkeypatch):
    module = api(); store = writer(tmp_path)
    store.append(0, np.ones(4)); store.append(4, np.ones(2)); ref = store.finish()
    original = module._signature
    # Filesystem clocks can coalesce. Retain real inode/type/size/block metadata,
    # but deterministically model unchanged modification/change timestamps.
    monkeypatch.setattr(module, '_signature', lambda info: original(info)[:5] + (0, 0) + original(info)[7:])
    calls = 0
    def lease():
        nonlocal calls
        calls += 1
        if calls == 4:
            (tmp_path / 'scores/chunk-000000000000.bin').write_bytes(b'x' * 32)
    with pytest.raises(ValueError):
        module.verify(tmp_path / 'scores', scope=SCOPE, owner=OWNER,
            terminal_sha256=ref, lease=lease)
