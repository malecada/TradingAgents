"""Synthetic checks for reusing verified bundles from a failed controller.

Catch double counting, gaps, unverified receipts and insufficient scratch before
any network operation; no raw research bytes or network are used.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[3] / 'research/onchain-paper-replication-2026-09-24/storage/raw-preservation-2026-09-25-04/transfer.py'


def fixture(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('backup04', SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, 'ROOT', tmp_path)
    c = {'reused_batches': [], 'input_sha256': {},
         'phases': {'bulk01': {'start': 3, 'stop': 4}},
         'local_free_floor_bytes': 20, 'maximum_temporary_bytes': 2}
    batches = [dict(index=0, start=0, stop=1, files=1, raw_bytes=5),
               dict(index=1, start=1, stop=3, files=2, raw_bytes=12),
               dict(index=2, start=3, stop=4, files=1, raw_bytes=7),
               dict(index=3, start=4, stop=5, files=1, raw_bytes=9)]
    for i, files, size, start in [(1, 2, 12, 1), (2, 1, 7, 3)]:
        name = f'complete{i}.json'
        body = dict(status='complete', files=files, raw_bytes=size,
                    start_index=start, originals_preserved=True,
                    downloaded_members_verified=True, source_hashes_verified=True)
        raw = json.dumps(body).encode(); (tmp_path/name).write_bytes(raw)
        c['input_sha256'][name] = hashlib.sha256(raw).hexdigest()
        c['reused_batches'].append({'index': i, 'complete_path': name})
    return m, c, batches


def test_reuses_completed_prefix_from_failed_parent_without_repeating_it(tmp_path, monkeypatch):
    m, c, batches = fixture(tmp_path, monkeypatch)
    before = sorted(tmp_path.iterdir())
    result = m.reused_prefix(c, batches)
    assert (result['files'], result['raw_bytes']) == (3, 19)
    assert sorted(tmp_path.iterdir()) == before


@pytest.mark.parametrize('fault', ['duplicate', 'gap', 'overlap', 'hash', 'status',
                                  'files', 'start_index', 'raw_bytes',
                                  'downloaded_members_verified', 'source_hashes_verified',
                                  'originals_preserved'])
def test_rejects_unsafe_reuse(tmp_path, monkeypatch, fault):
    m, c, batches = fixture(tmp_path, monkeypatch)
    if fault == 'duplicate': c['reused_batches'][1]['index'] = 1
    elif fault == 'gap': c['reused_batches'].pop(0)
    elif fault == 'overlap': c['phases']['bulk01']['start'] = 2
    else:
        p = tmp_path/'complete1.json'; body = json.loads(p.read_text())
        body['files' if fault == 'hash' else fault] = (
            'failed' if fault == 'status' else False if fault.endswith('verified') or fault == 'originals_preserved' else 99)
        raw = json.dumps(body).encode(); p.write_bytes(raw)
        if fault != 'hash': c['input_sha256']['complete1.json'] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError): m.reused_prefix(c, batches)


def test_disk_preflight_requires_floor_plus_scratch(tmp_path, monkeypatch):
    m, c, _ = fixture(tmp_path, monkeypatch)
    from types import SimpleNamespace
    monkeypatch.setattr(m.shutil, 'disk_usage', lambda _: SimpleNamespace(free=21))
    with pytest.raises(RuntimeError): m.check_local_scratch(c)
    monkeypatch.setattr(m.shutil, 'disk_usage', lambda _: SimpleNamespace(free=22))
    m.check_local_scratch(c)
