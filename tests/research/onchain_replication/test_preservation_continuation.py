"""Synthetic admission of a completed pilot into a new backup identity."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / 'research/onchain-paper-replication-2026-09-24/storage/raw-preservation-2026-09-25-03/transfer.py'


def module():
    spec = importlib.util.spec_from_file_location('backup_continuation03', SCRIPT)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def fixture(tmp_path, monkeypatch):
    m = module()
    monkeypatch.setattr(m, 'ROOT', tmp_path)
    parent = {'status': 'complete', 'contract_sha256': 'a'*64,
              'files': 2, 'raw_bytes': 12, 'batches': [{'index': 0}]}
    guard = {'phase': 'complete', 'cleanup_verified': True, 'child_exit_code': 0}
    paths = {'pilot.json': parent, 'guard.json': guard}
    c = {'reused_pilot': {'complete_path': 'pilot.json', 'guard_path': 'guard.json',
                         'contract_sha256': 'a'*64, 'files': 2, 'raw_bytes': 12},
         'input_sha256': {}}
    for name, body in paths.items():
        raw = json.dumps(body).encode(); (tmp_path/name).write_bytes(raw)
        c['input_sha256'][name] = hashlib.sha256(raw).hexdigest()
    return m, c


def test_reuse_reads_original_completion_without_copying_or_relaunching(tmp_path, monkeypatch):
    m,c = fixture(tmp_path,monkeypatch)
    result = m.reused_pilot(c)
    assert (result['files'],result['raw_bytes']) == (2,12)
    assert sorted(p.name for p in tmp_path.iterdir()) == ['guard.json','pilot.json']


@pytest.mark.parametrize('fault', ['hash','contract','status','cleanup','exit','batch','files'])
def test_invalid_pilot_reuse_refused(tmp_path, monkeypatch, fault):
    m,c = fixture(tmp_path,monkeypatch)
    name = 'guard.json' if fault in ('cleanup','exit') else 'pilot.json'
    body = json.loads((tmp_path/name).read_bytes())
    if fault == 'hash': body['raw_bytes'] = 99
    elif fault == 'contract': body['contract_sha256'] = 'b'*64
    elif fault == 'status': body['status'] = 'failed'
    elif fault == 'cleanup': body['cleanup_verified'] = False
    elif fault == 'exit': body['child_exit_code'] = 1
    elif fault == 'batch': body['batches'][0]['index'] = 1
    elif fault == 'files': body['files'] = 3
    raw=json.dumps(body).encode();(tmp_path/name).write_bytes(raw)
    if fault != 'hash': c['input_sha256'][name] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError): m.reused_pilot(c)
