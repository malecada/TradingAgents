import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch
import pytest

P=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11/resource_guard_v2.py'
spec=importlib.util.spec_from_file_location('resource_guard_v2',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_transient_missing_memory_field_rechecks_exit_or_recovery():
    with patch.object(Path,'read_text',side_effect=['State:\tR (running)\n','',FileNotFoundError()]), patch.object(m.time,'sleep'):
        assert m.tree_rss(123)==0
    with patch.object(Path,'read_text',side_effect=['State:\tR (running)\n','','State:\tR (running)\nVmRSS:\t64 kB\n','']), patch.object(m.time,'sleep'):
        assert m.tree_rss(123)==65536


def test_persistent_missing_memory_field_fails_closed_with_pid_state():
    with patch.object(Path,'read_text',side_effect=['State:\tR (running)\n','','State:\tR (running)\n','']), patch.object(m.time,'sleep'):
        with pytest.raises(RuntimeError,match='PID 123 still has no VmRSS'):
            m.tree_rss(123)


def test_resource_limits_and_launch_failure_retained():
    result=m.run_guard([sys.executable,'-c','import time; data=bytearray(80*1024**2); time.sleep(5)'],rss_limit_bytes=32*1024**2)
    assert result['limit_reason']=='sampled aggregate RSS limit exceeded'
    result=m.run_guard([sys.executable,'-c','import time; time.sleep(5)'],wall_seconds=.1)
    assert result['limit_reason']=='wall-clock limit exceeded'
    assert m.run_guard(['/nonexistent/research-synthetic-executable'])['child_exit_code'] is None


def test_proc_esrch_is_a_confirmed_departed_process():
    with patch.object(Path,'read_text',side_effect=ProcessLookupError(3,'No such process')):
        assert m.tree_rss(123)==0
