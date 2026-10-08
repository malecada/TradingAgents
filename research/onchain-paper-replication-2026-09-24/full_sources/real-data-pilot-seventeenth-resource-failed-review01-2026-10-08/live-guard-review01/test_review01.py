"""Independent delta probes using inspected synthetic admission/kernel fixtures."""
import hashlib, importlib.util, json
from pathlib import Path
import pytest
from tradingagents.research.lifecycle import _lock
H=Path(__file__).resolve().parent
W=H.parent.parent/'real-data-pilot-live-guard-correction01-2026-10-08'
spec=importlib.util.spec_from_file_location('independent_live_fixtures',W/'test_live_guard01.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
registered,context,live,guard_call=w.registered,w.context,w.live,w.guard_call

def test_fallback_reauthenticates_every_call_under_lock(context,guard_call,monkeypatch):
    ad,_=context;actual=w.caller._read;reads=[]
    def tracked(ad,name):
        reads.append(name);return actual(ad,name)
    monkeypatch.setattr(w.caller,'_read',tracked)
    with _lock(ad.root):
        guard_call();guard_call()
    assert reads==['execution_job','execution_job','pilot']*2

@pytest.mark.parametrize('mutation',['missing','corrupt'])
def test_valid_then_changed_input_is_refused(context,guard_call,mutation):
    ad,_=context;guard_call();path=ad.root/'execution_job.json'
    if mutation=='missing':path.unlink()
    else:path.write_text('{}')
    with pytest.raises((FileNotFoundError,ValueError)):
        guard_call()

def test_authenticated_malformed_json_refuses(context,guard_call):
    ad,_=context;path=ad.root/'execution_job.json';path.write_text('{bad')
    ad.inputs['execution_job']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(json.JSONDecodeError):guard_call()

def test_explicit_context_avoids_fallback_but_retains_current_policy_auth(context,guard_call,monkeypatch):
    ad,e=context;actual=w.caller._read;reads=[]
    def tracked(ad,name):reads.append(name);return actual(ad,name)
    monkeypatch.setattr(w.caller,'_read',tracked)
    with _lock(ad.root):guard_call(execution=e)
    assert reads==['execution_job','pilot']
    (ad.root/'pilot.json').write_text('{}')
    with _lock(ad.root),pytest.raises(ValueError):guard_call(execution=e)

def test_legacy_does_not_enter_any_pilot_reader(context,live,guard_call,monkeypatch):
    ad,e=context;receipt,value=live
    e['resources'].update(reserve_bytes=3*w.G,start_reserve_bytes=9*w.G)
    value.update(e['resources']);(receipt/'live.json').write_text(json.dumps(value))
    def refuse(*args):raise AssertionError('legacy entered pilot metadata reader')
    monkeypatch.setattr(w.caller,'_read',refuse)
    with _lock(ad.root):guard_call()
