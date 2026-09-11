import importlib.util
from pathlib import Path
import sys

PATH=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11/resource_guard.py'
spec=importlib.util.spec_from_file_location('resource_guard', PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_success_under_resident_cap_and_two_cpu_affinity():
    result=m.run_guard([sys.executable,'-c','import os,resource; assert len(os.sched_getaffinity(0))<=2; assert resource.getrlimit(resource.RLIMIT_AS)[0]==resource.RLIM_INFINITY'], wall_seconds=10)
    assert result['child_exit_code']==0 and result['limit_reason'] is None


def test_memory_and_wall_limits_stop_invented_children():
    result=m.run_guard([sys.executable,'-c','import time; data=bytearray(80*1024**2); time.sleep(5)'], rss_limit_bytes=32*1024**2, wall_seconds=10)
    assert result['limit_reason']=='sampled aggregate RSS limit exceeded'
    result=m.run_guard([sys.executable,'-c','import time; time.sleep(5)'], wall_seconds=.1)
    assert result['limit_reason']=='wall-clock limit exceeded'


def test_launch_failure_has_structured_unknown_metrics():
    result=m.run_guard(['/nonexistent/research-synthetic-executable'])
    assert result['child_exit_code'] is None
    assert result['peak_sampled_tree_rss_bytes'] is None
    assert result['limit_reason'].startswith('launch/setup failed:')
    assert result['retry'] is False
