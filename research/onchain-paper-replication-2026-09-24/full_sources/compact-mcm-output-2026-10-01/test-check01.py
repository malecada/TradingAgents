"""Fresh compact MCM artifact checks; no registered fit or historical replay."""
import json
import numpy as np
import pytest
from tests.research.onchain_replication.test_compact_stage import completed
from tradingagents.research.onchain_replication import compact_stage


def source(tmp_path, monkeypatch):
    root = tmp_path / 'stage'; root.mkdir()
    contract = completed(root, 'mcm', monkeypatch)
    ref = compact_stage.seal(root, lease=lambda: None, **contract)
    start = json.loads((root / 'stream/start.json').read_bytes())
    return dict(stage_root=root, stage_sha256=ref, contract=contract,
        expected_scope=start['scope'], max_output_bytes=8192 + 4 * contract['pairs'])


def expected_values(root):
    return np.concatenate([np.frombuffer(p.read_bytes(), dtype='<f8')
        for p in sorted((root / 'stream/batches').glob('chunk-*.bin'))]).astype('<f4')


def test_actual_completed_matching_becomes_exact_readonly_float32_matrix(tmp_path, monkeypatch):
    from tradingagents.research.onchain_replication import compact_mcm_output as api
    kw = source(tmp_path, monkeypatch); output = tmp_path / 'output'
    ref = api.publish(output, **kw, lease=lambda: None)
    result = api.verify(output, expected_sha256=ref, **kw, lease=lambda: None)
    assert result['execution_admitted'] is False and result['array_bytes'] == 56
    with api.open_verified(output, expected_sha256=ref, **kw, lease=lambda: None) as values:
        assert values.shape == (7, 2) and values.dtype == np.dtype('<f4')
        assert values.tobytes() == expected_values(kw['stage_root']).tobytes()
        assert not values.flags.writeable
        with pytest.raises(ValueError): values[0, 0] = 0
    with pytest.raises((FileExistsError, ValueError)): api.publish(output, **kw, lease=lambda: None)


@pytest.mark.parametrize('mismatch', ['capacity', 'scope', 'stage_ref', 'dictionary_kind'])
def test_external_scope_and_capacity_refuse_before_output_creation(tmp_path, monkeypatch, mismatch):
    from tradingagents.research.onchain_replication import compact_mcm_output as api
    kw = source(tmp_path, monkeypatch)
    if mismatch == 'capacity': kw['max_output_bytes'] -= 1
    if mismatch == 'scope': kw['expected_scope'] = kw['expected_scope'] | {'dictionary': 'f' * 64}
    if mismatch == 'stage_ref': kw['stage_sha256'] = 'f' * 64
    if mismatch == 'dictionary_kind': kw['contract'] = kw['contract'] | {'kind': 'dictionary'}
    with pytest.raises(ValueError): api.publish(tmp_path / 'output', **kw, lease=lambda: None)
    assert not (tmp_path / 'output').exists()


@pytest.mark.parametrize('target', ['matrix', 'stream', 'extra', 'redirect'])
def test_saved_reader_refuses_changed_output_or_matching_evidence(tmp_path, monkeypatch, target):
    from tradingagents.research.onchain_replication import compact_mcm_output as api
    kw = source(tmp_path, monkeypatch); output = tmp_path / 'output'
    ref = api.publish(output, **kw, lease=lambda: None)
    path = output / 'matrix.f32'
    if target == 'matrix': path.write_bytes(b'x' * path.stat().st_size)
    if target == 'stream':
        p = kw['stage_root'] / 'stream/batches/chunk-000000000000.bin'
        p.write_bytes(b'x' * p.stat().st_size)
    if target == 'extra': (output / 'orphan').write_bytes(b'preserve')
    if target == 'redirect':
        path.rename(output / 'original.f32'); path.symlink_to(output / 'original.f32')
    with pytest.raises((ValueError, OSError)):
        api.verify(output, expected_sha256=ref, **kw, lease=lambda: None)


def test_interrupted_publication_retains_namespace_and_refuses_retry(tmp_path, monkeypatch):
    from tradingagents.research.onchain_replication import compact_mcm_output as api
    kw = source(tmp_path, monkeypatch); output = tmp_path / 'output'
    def lease():
        path = output / 'matrix.f32'
        if path.exists() and path.stat().st_size:
            raise RuntimeError('synthetic owner loss after first chunk')
    with pytest.raises(RuntimeError, match='owner loss'): api.publish(output, **kw, lease=lease)
    assert (output / 'matrix.f32').stat().st_size > 0
    assert not (output / 'manifest.json').exists()
    with pytest.raises((FileExistsError, ValueError)): api.publish(output, **kw, lease=lambda: None)


def test_late_publication_callback_cannot_acknowledge_corrupt_matrix(tmp_path, monkeypatch):
    from tradingagents.research.onchain_replication import compact_mcm_output as api
    kw = source(tmp_path, monkeypatch); output = tmp_path / 'output'
    def lease():
        if (output / 'manifest.json').exists():
            p = output / 'matrix.f32'; p.write_bytes(b'x' * p.stat().st_size)
    with pytest.raises(ValueError): api.publish(output, **kw, lease=lease)
    assert (output / 'manifest.json').exists()


def test_mapping_exit_rechecks_changes_during_consumption(tmp_path, monkeypatch):
    from tradingagents.research.onchain_replication import compact_mcm_output as api
    kw = source(tmp_path, monkeypatch); output = tmp_path / 'output'
    ref = api.publish(output, **kw, lease=lambda: None)
    with pytest.raises(ValueError):
        with api.open_verified(output, expected_sha256=ref, **kw, lease=lambda: None):
            p = output / 'matrix.f32'; p.write_bytes(b'x' * p.stat().st_size)
