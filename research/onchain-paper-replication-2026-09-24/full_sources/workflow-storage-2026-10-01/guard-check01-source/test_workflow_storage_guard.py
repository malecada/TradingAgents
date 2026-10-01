"""New storage boundary tests; kernel unit behavior is isolated by the existing mock."""
import json
from pathlib import Path
from tests.research.onchain_replication.test_resources import mock_unit
from tradingagents.research.onchain_replication import resources as guard

def budget(tmp_path):
    root=tmp_path/'outputs';root.mkdir()
    return {'root':str(root),'limits':{'max_allocated_bytes':1024*1024,'max_logical_bytes':8192,'max_entries':100,'max_depth':8,'max_scan_seconds':1}}

def test_storage_startup_refusal_never_dispatches(tmp_path,monkeypatch):
    policy=budget(tmp_path);(Path(policy['root'])/'huge').write_bytes(b'x'*9000)
    monkeypatch.setattr(guard.subprocess,'run',lambda *a,**k:(_ for _ in ()).throw(AssertionError('dispatched')))
    result=guard.guarded_run(['true'],cwd=tmp_path,receipt_dir=tmp_path/'r',storage_budget=policy)
    assert result['phase']=='failed' and 'storage logical' in result['limit_reason']
    assert result['storage_breach']['logical_file_bytes']==9000
    assert not (tmp_path/'r/release.json').exists()

def test_storage_runtime_breach_stops_owned_unit(tmp_path,monkeypatch):
    receipt,calls=mock_unit(tmp_path,monkeypatch,completed=True);policy=budget(tmp_path);atomic=guard._atomic
    def write(path,value):
        atomic(path,value)
        if path.name=='release.json':(Path(policy['root'])/'overflow').write_bytes(b'a'*9000)
    monkeypatch.setattr(guard,'_atomic',write)
    result=guard.guarded_run(['true'],cwd=tmp_path,receipt_dir=receipt,storage_budget=policy)
    assert result['phase']=='failed' and result['cleanup_verified']
    assert 'storage logical' in result['limit_reason'] and result['storage_breach']['logical_file_bytes']==9000
    assert any('stop' in c for c in calls)
    assert json.loads((receipt/'final.json').read_text())==result

def test_valid_storage_policy_and_terminal_observation(tmp_path,monkeypatch):
    receipt,calls=mock_unit(tmp_path,monkeypatch,completed=True);policy=budget(tmp_path)
    (Path(policy['root'])/'value').write_bytes(b'abc')
    result=guard.guarded_run(['true'],cwd=tmp_path,receipt_dir=receipt,storage_budget=policy)
    assert result['phase']=='complete' and result['storage_budget']==policy
    assert result['storage_observation']['logical_file_bytes']==3
    assert result['storage_peak_logical_file_bytes']==3
