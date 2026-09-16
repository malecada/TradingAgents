"""No large allocation: simulated guard samples test the changed resource boundary."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import signal

import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('motif8_guard',ROOT/'research/onchain-graph-2026-09-16/motifs8gib/launch.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


@pytest.mark.parametrize('rss,killed',[(3*1024**3,False),(8*1024**3,False),(8*1024**3+1,True)])
def test_eight_gib_sample_boundary(monkeypatch,tmp_path,rss,killed):
    calls=[]
    class Process:
        pid=123456
        def __init__(self):self.polls=0;self.killed=False
        def poll(self):self.polls+=1;return None if self.polls==1 else 0
        def wait(self,timeout=None):return -15 if self.killed else 0
    process=Process();limits=lambda:None
    def popen(command,**kwargs):
        assert kwargs['preexec_fn'] is limits and kwargs['start_new_session']
        assert kwargs['env']['OMP_NUM_THREADS']=='2'
        return process
    def kill(pid,sig):
        assert pid==process.pid;calls.append(sig);process.killed=True
    monkeypatch.setattr(module.subprocess,'Popen',popen)
    monkeypatch.setattr(module.os,'killpg',kill)
    monkeypatch.setattr(module.time,'sleep',lambda _:None)
    result=module.run_with_limit(['invented'],SimpleNamespace(_limits=limits,tree_rss=lambda _:rss),tmp_path)
    assert result['rss_limit_bytes']==8589934592
    assert result['elapsed_time_kill'] is False
    assert result['peak_sampled_tree_rss_bytes']==rss
    assert bool(result['limit_reason'])==killed
    assert calls==([signal.SIGTERM] if killed else [])
    assert result['child_exit_code']==(-15 if killed else 0)


def test_monitor_failure_stops_child(monkeypatch,tmp_path):
    process=SimpleNamespace(pid=123456,poll=lambda:None,wait=lambda timeout=None:-15)
    def bad_rss(_):raise RuntimeError('invented monitor error')
    monkeypatch.setattr(module.subprocess,'Popen',lambda *a,**k:process)
    signals=[];monkeypatch.setattr(module.os,'killpg',lambda p,s:signals.append(s))
    result=module.run_with_limit(['invented'],SimpleNamespace(_limits=lambda:None,tree_rss=bad_rss),tmp_path)
    assert result['limit_reason']=='resource monitor failed: invented monitor error'
    assert signals==[signal.SIGTERM]


def test_setup_failure_is_recorded(monkeypatch,tmp_path):
    def fail(*a,**k):raise OSError('invented setup failure')
    monkeypatch.setattr(module.subprocess,'Popen',fail)
    result=module.run_with_limit(['invented'],SimpleNamespace(_limits=lambda:None),tmp_path)
    assert result['child_exit_code'] is None and result['retry'] is False
    assert result['limit_reason']=='launch/setup failed: invented setup failure'
    assert result['rss_limit_bytes']==8*1024**3


def test_no_elapsed_kill_for_long_simulated_run(monkeypatch,tmp_path):
    polls=iter([None,None,0]);times=iter([0,1000000000])
    process=SimpleNamespace(pid=123456,poll=lambda:next(polls),wait=lambda:0)
    monkeypatch.setattr(module.subprocess,'Popen',lambda *a,**k:process)
    monkeypatch.setattr(module.time,'monotonic',lambda:next(times))
    monkeypatch.setattr(module.time,'sleep',lambda _:None)
    monkeypatch.setattr(module.os,'killpg',lambda *a:pytest.fail('unexpected elapsed-time kill'))
    result=module.run_with_limit(['invented'],SimpleNamespace(_limits=lambda:None,tree_rss=lambda _:5*1024**3),tmp_path)
    assert result['elapsed_seconds']==1000000000 and result['limit_reason'] is None
    assert result['peak_sampled_tree_rss_bytes']==5*1024**3 and result['child_exit_code']==0


def test_ignored_term_escalates_to_kill(monkeypatch,tmp_path):
    signals=[]
    def wait(timeout=None):
        if timeout is not None:raise module.subprocess.TimeoutExpired('invented',timeout)
        return -9
    process=SimpleNamespace(pid=123456,poll=lambda:None,wait=wait)
    monkeypatch.setattr(module.subprocess,'Popen',lambda *a,**k:process)
    monkeypatch.setattr(module.os,'killpg',lambda p,s:signals.append(s))
    result=module.run_with_limit(['invented'],SimpleNamespace(_limits=lambda:None,tree_rss=lambda _:9*1024**3),tmp_path)
    assert signals==[signal.SIGTERM,signal.SIGKILL] and result['child_exit_code']==-9
    assert result['limit_reason']=='sampled aggregate RSS limit exceeded'


def test_exit_between_term_timeout_and_kill_preserves_receipt(monkeypatch,tmp_path):
    signals=[]
    def wait(timeout=None):
        if timeout is not None:raise module.subprocess.TimeoutExpired('invented',timeout)
        return -15
    def kill(pid,sig):
        signals.append(sig)
        if sig==signal.SIGKILL:raise ProcessLookupError('already exited')
    process=SimpleNamespace(pid=123456,poll=lambda:None,wait=wait)
    monkeypatch.setattr(module.subprocess,'Popen',lambda *a,**k:process)
    monkeypatch.setattr(module.os,'killpg',kill)
    result=module.run_with_limit(['invented'],SimpleNamespace(_limits=lambda:None,tree_rss=lambda _:9*1024**3),tmp_path)
    assert signals==[signal.SIGTERM,signal.SIGKILL] and result['child_exit_code']==-15
    assert result['limit_reason']=='sampled aggregate RSS limit exceeded'
    assert result['peak_sampled_tree_rss_bytes']==9*1024**3
